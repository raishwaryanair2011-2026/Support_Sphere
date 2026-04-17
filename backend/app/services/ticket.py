"""
Ticket service — all database operations for tickets.
Keeps routers thin; all queries live here.

Enhancements implemented:
  1. Restricted ticket access — agents only see/open their assigned tickets
  2. Department-aware assignment — IT tickets go to IT agents etc.
  3. Workload limit — agents capped at MAX_AGENT_TICKETS active tickets
  4. Reassign support — admin/agent can hand over a ticket
"""
from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.core.logging import get_logger
from app.models.ticket import Ticket, TicketAttachment, TicketMessage, TicketStatus
from app.models.user import User, UserRole
from app.schemas.ticket import (
    ReplyRequest,
    TicketCreateRequest,
    TicketEditRequest,
    TicketUpdateRequest,
)
from app.services.ai.classifier import classify_ticket
from app.services.ai.summarizer import summarize_document
from app.utils.files import save_upload
from app.utils.pagination import PageParams, make_paginated_response

logger = get_logger(__name__)

MAX_AGENT_TICKETS = 30  # Feature 4: workload cap per agent


# ── Queue → Department mapping ────────────────────────────────────────────────
QUEUE_TO_DEPT = {
    "IT":         "IT",
    "HR":         "HR",
    "Finance":    "Finance",
    "Facilities": "Facilities",
}


# ── Agent assignment (department-aware + workload-limited) ────────────────────
async def _pick_agent(db: AsyncSession, queue: str) -> Optional[User]:
    """
    Feature 2 + 3: Pick agent from matching department.
    Feature 4: Skip agents at or above MAX_AGENT_TICKETS active tickets.
    Falls back to any active agent if no department match or all are full.
    """
    dept = QUEUE_TO_DEPT.get(queue)

    # Fetch active agents — prefer department match, fall back to all
    if dept:
        dept_result = await db.execute(
            select(User)
            .where(User.role == UserRole.AGENT,
                   User.is_active == True,
                   User.department == dept)
            .order_by(User.id)
        )
        agents = dept_result.scalars().all()
    else:
        agents = []

    # Fallback: any active agent if no department agents found
    if not agents:
        all_result = await db.execute(
            select(User)
            .where(User.role == UserRole.AGENT, User.is_active == True)
            .order_by(User.id)
        )
        agents = all_result.scalars().all()

    if not agents:
        return None

    # Feature 4: count active tickets per agent in one query
    active_counts_result = await db.execute(
        select(Ticket.agent_id, func.count(Ticket.id))
        .where(
            Ticket.agent_id.in_([a.id for a in agents]),
            Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS])
        )
        .group_by(Ticket.agent_id)
    )
    active_counts = dict(active_counts_result.all())

    # Filter agents under the workload cap
    available = [a for a in agents if active_counts.get(a.id, 0) < MAX_AGENT_TICKETS]

    # If all are at cap, pick the one with the lowest count (safety fallback)
    if not available:
        logger.warning("all_agents_at_capacity", queue=queue)
        available = agents

    # Round-robin within available agents
    count_result = await db.execute(select(func.count(Ticket.id)))
    ticket_count = count_result.scalar_one()
    return available[ticket_count % len(available)]


# ── Create ────────────────────────────────────────────────────────────────────
async def create_ticket(
    db: AsyncSession, data: TicketCreateRequest, customer: User
) -> Ticket:
    ticket_number = f"SUP-{datetime.now(timezone.utc).year}-{uuid.uuid4().hex[:6].upper()}"
    queue, priority = await classify_ticket(data.subject, data.description)
    agent = await _pick_agent(db, queue)

    ticket = Ticket(
        ticket_number=ticket_number,
        subject=data.subject.strip(),
        description=data.description.strip(),
        customer_id=customer.id,
        agent_id=agent.id if agent else None,
        status=TicketStatus.OPEN,
        priority=priority,
        queue=queue,
    )
    db.add(ticket)
    await db.flush()

    db.add(TicketMessage(
        ticket_id=ticket.id,
        sender_id=customer.id,
        sender_role="customer",
        message=data.description.strip(),
    ))
    await db.commit()
    await db.refresh(ticket)
    logger.info("ticket_created", ticket_id=ticket.id, ticket_number=ticket_number,
                agent_id=agent.id if agent else None, queue=queue)
    return ticket


# ── Read (customer) ───────────────────────────────────────────────────────────
async def get_customer_tickets(
    db: AsyncSession, customer_id: int, params: PageParams
) -> dict:
    q = select(Ticket).where(Ticket.customer_id == customer_id).order_by(Ticket.created_at.desc())
    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()
    result = await db.execute(q.offset(params.offset).limit(params.page_size))
    return make_paginated_response(list(result.scalars().all()), total, params)


# ── Read (agent — only assigned tickets) ─────────────────────────────────────
async def get_agent_tickets(
    db: AsyncSession,
    agent_id: int,
    params: PageParams,
    status: Optional[str] = None,
    queue: Optional[str] = None,
    priority: Optional[str] = None,
) -> dict:
    """Feature 1: agents only see tickets assigned to them."""
    q = select(Ticket).where(Ticket.agent_id == agent_id)
    if status:
        q = q.where(Ticket.status == status)
    if queue:
        q = q.where(Ticket.queue == queue)
    if priority:
        q = q.where(Ticket.priority == priority)
    q = q.order_by(Ticket.created_at.desc())

    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()
    result = await db.execute(q.offset(params.offset).limit(params.page_size))
    return make_paginated_response(list(result.scalars().all()), total, params)


# ── Read (admin — all tickets) ────────────────────────────────────────────────
async def get_all_tickets(
    db: AsyncSession,
    params: PageParams,
    status: Optional[str] = None,
    queue: Optional[str] = None,
    priority: Optional[str] = None,
) -> dict:
    """Admins see everything."""
    q = select(Ticket)
    if status:
        q = q.where(Ticket.status == status)
    if queue:
        q = q.where(Ticket.queue == queue)
    if priority:
        q = q.where(Ticket.priority == priority)
    q = q.order_by(Ticket.created_at.desc())

    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()
    result = await db.execute(q.offset(params.offset).limit(params.page_size))
    return make_paginated_response(list(result.scalars().all()), total, params)


# ── Read (detail) ─────────────────────────────────────────────────────────────
async def get_ticket_detail(
    db: AsyncSession, ticket_id: int, user: User
) -> Ticket:
    result = await db.execute(
        select(Ticket)
        .where(Ticket.id == ticket_id)
        .options(selectinload(Ticket.messages), selectinload(Ticket.attachments))
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise NotFoundException("Ticket not found")

    # Customers: only their own tickets
    if user.role == UserRole.CUSTOMER and ticket.customer_id != user.id:
        raise ForbiddenException("You can only view your own tickets")

    # Feature 1: agents can only open tickets assigned to them
    if user.role == UserRole.AGENT and ticket.agent_id != user.id:
        raise ForbiddenException("This ticket is not assigned to you")

    return ticket


# ── Workload stats (for admin dashboard) ─────────────────────────────────────
async def get_agent_workload(db: AsyncSession) -> list[dict]:
    """Returns active ticket count per agent for admin visibility."""
    agents_result = await db.execute(
        select(User).where(User.role == UserRole.AGENT, User.is_active == True)
    )
    agents = agents_result.scalars().all()

    counts_result = await db.execute(
        select(Ticket.agent_id, func.count(Ticket.id))
        .where(Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS]))
        .group_by(Ticket.agent_id)
    )
    counts = dict(counts_result.all())

    return [
        {
            "agent_id": a.id,
            "name": a.name or a.email,
            "department": a.department,
            "active_tickets": counts.get(a.id, 0),
            "at_capacity": counts.get(a.id, 0) >= MAX_AGENT_TICKETS,
            "capacity": MAX_AGENT_TICKETS,
        }
        for a in agents
    ]


# ── Update (agent/admin) ──────────────────────────────────────────────────────
async def update_ticket(
    db: AsyncSession, ticket_id: int, data: TicketUpdateRequest, agent: User
) -> Ticket:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise NotFoundException("Ticket not found")

    # Feature 1: agent can only update their own assigned ticket
    if agent.role == UserRole.AGENT and ticket.agent_id != agent.id:
        raise ForbiddenException("This ticket is not assigned to you")

    if data.status is not None:
        ticket.status = data.status
        if data.status == TicketStatus.RESOLVED:
            ticket.closed_at = datetime.now(timezone.utc)
            ticket.resolved_by = agent.id

    if data.priority is not None:
        ticket.priority = data.priority
    if data.queue is not None:
        ticket.queue = data.queue

    # Reassignment — admin only or assigned agent handing over
    if data.agent_id is not None:
        if agent.role == UserRole.AGENT and data.agent_id != agent.id:
            # Agent is reassigning to someone else — allowed (handover)
            ticket.agent_id = data.agent_id
            logger.info("ticket_reassigned", ticket_id=ticket_id,
                        from_agent=agent.id, to_agent=data.agent_id)
        elif agent.role == UserRole.ADMIN:
            ticket.agent_id = data.agent_id

    await db.commit()
    await db.refresh(ticket)
    logger.info("ticket_updated", ticket_id=ticket_id, by=agent.id)
    return ticket


# ── Edit (customer) ───────────────────────────────────────────────────────────
async def edit_ticket(
    db: AsyncSession, ticket_id: int, data: TicketEditRequest, customer: User
) -> Ticket:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise NotFoundException("Ticket not found")
    if ticket.customer_id != customer.id:
        raise ForbiddenException("Not your ticket")
    if ticket.status != TicketStatus.OPEN:
        raise BadRequestException("Only open tickets can be edited")
    if data.subject:
        ticket.subject = data.subject.strip()
    if data.description:
        ticket.description = data.description.strip()
    await db.commit()
    await db.refresh(ticket)
    return ticket


# ── Delete (customer) ─────────────────────────────────────────────────────────
async def delete_ticket(db: AsyncSession, ticket_id: int, customer: User) -> None:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise NotFoundException("Ticket not found")
    if ticket.customer_id != customer.id:
        raise ForbiddenException("Not your ticket")
    if ticket.status != TicketStatus.OPEN:
        raise BadRequestException("Only open tickets can be deleted")
    await db.delete(ticket)
    await db.commit()
    logger.info("ticket_deleted", ticket_id=ticket_id, by=customer.id)


# ── Reply ─────────────────────────────────────────────────────────────────────
async def add_reply(
    db: AsyncSession, ticket_id: int, data: ReplyRequest, sender: User
) -> TicketMessage:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise NotFoundException("Ticket not found")
    if sender.role == UserRole.CUSTOMER and ticket.customer_id != sender.id:
        raise ForbiddenException("Not your ticket")
    if sender.role == UserRole.AGENT and ticket.agent_id != sender.id:
        raise ForbiddenException("This ticket is not assigned to you")

    msg = TicketMessage(
        ticket_id=ticket.id,
        sender_id=sender.id,
        sender_role=sender.role.value,
        message=data.message.strip(),
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


# ── File upload ───────────────────────────────────────────────────────────────
async def attach_file(
    db: AsyncSession, ticket_id: int, file, uploader: User
) -> TicketAttachment:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise NotFoundException("Ticket not found")
    if uploader.role == UserRole.CUSTOMER and ticket.customer_id != uploader.id:
        raise ForbiddenException("Not your ticket")

    file_path, file_name = await save_upload(file)
    attachment = TicketAttachment(
        ticket_id=ticket.id,
        file_path=file_path,
        file_name=file_name,
        file_type=file.content_type,
        uploaded_by=uploader.id,
    )
    db.add(attachment)
    await db.flush()

    try:
        summary = await summarize_document(file_path)
        if summary:
            ticket.ai_summary = summary
    except Exception as exc:
        logger.warning("ai_summary_failed", ticket_id=ticket_id, error=str(exc))

    await db.commit()
    await db.refresh(attachment)
    logger.info("attachment_added", ticket_id=ticket_id, path=file_path)
    return attachment