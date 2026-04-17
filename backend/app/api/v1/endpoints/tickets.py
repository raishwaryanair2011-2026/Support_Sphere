"""Ticket CRUD, messaging, and file upload endpoints."""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.deps import CurrentUser, DBSession, RequireAdmin, RequireAgent
from app.schemas.ticket import (
    PaginatedTickets,
    ReplyRequest,
    TicketCreateRequest,
    TicketDetailResponse,
    TicketEditRequest,
    TicketResponse,
    TicketUpdateRequest,
)
from app.services import ticket as svc
from app.utils.pagination import PageParams, pagination_params

router = APIRouter(prefix="/tickets", tags=["Tickets"])

PageDep = Annotated[PageParams, Depends(pagination_params)]


# ── Customer: create ──────────────────────────────────────────────────────────
@router.post("", response_model=TicketResponse, status_code=201)
async def create_ticket(data: TicketCreateRequest, db: DBSession, user: CurrentUser):
    """Create a new support ticket (customers only)."""
    from app.core.exceptions import ForbiddenException
    from app.models.user import UserRole
    if user.role != UserRole.CUSTOMER:
        raise ForbiddenException("Only customers can create tickets")
    return await svc.create_ticket(db, data, user)


# ── Unified /my endpoint — works for customer, agent, and admin ───────────────
@router.get("/my", response_model=PaginatedTickets)
async def my_tickets(
    db: DBSession,
    user: CurrentUser,
    page: PageDep,
    status: Optional[str] = None,
    queue: Optional[str] = None,
    priority: Optional[str] = None,
):
    """
    Returns tickets relevant to the current user:
    - Customer: their own submitted tickets
    - Agent: only tickets assigned to them (Feature 1)
    - Admin: all tickets
    """
    from app.models.user import UserRole

    if user.role == UserRole.CUSTOMER:
        return await svc.get_customer_tickets(db, user.id, page)

    if user.role == UserRole.ADMIN:
        return await svc.get_all_tickets(
            db, page, status=status, queue=queue, priority=priority
        )

    # Agent — only assigned tickets
    return await svc.get_agent_tickets(
        db, user.id, page, status=status, queue=queue, priority=priority
    )


# ── Admin: all tickets (filterable) ──────────────────────────────────────────
@router.get("/all", response_model=PaginatedTickets)
async def all_tickets(
    db: DBSession,
    _agent: Annotated[None, RequireAgent],
    page: PageDep,
    status: Optional[str] = None,
    queue: Optional[str] = None,
    priority: Optional[str] = None,
):
    """All tickets — admins and agents (admin sees all, agent sees assigned)."""
    return await svc.get_all_tickets(
        db, page, status=status, queue=queue, priority=priority
    )


# ── Ticket detail ─────────────────────────────────────────────────────────────
@router.get("/{ticket_id}", response_model=TicketDetailResponse)
async def ticket_detail(ticket_id: int, db: DBSession, user: CurrentUser):
    """Full ticket detail including messages and attachments."""
    from sqlalchemy import select
    from app.models.user import User

    ticket = await svc.get_ticket_detail(db, ticket_id, user)

    customer_result = await db.execute(select(User).where(User.id == ticket.customer_id))
    customer = customer_result.scalar_one_or_none()

    agent_name = None
    if ticket.agent_id:
        agent_result = await db.execute(select(User).where(User.id == ticket.agent_id))
        agent = agent_result.scalar_one_or_none()
        agent_name = agent.name or agent.email if agent else None

    detail = TicketDetailResponse.model_validate(ticket)
    detail.customer_name = customer.name or customer.email if customer else None
    detail.agent_name = agent_name
    return detail


# ── Agent/Admin: update status / priority / queue / assignment ────────────────
@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    data: TicketUpdateRequest,
    db: DBSession,
    agent: Annotated[None, RequireAgent],
):
    """Update ticket status, priority, queue, or agent assignment."""
    return await svc.update_ticket(db, ticket_id, data, agent)


# ── Customer: edit open ticket ────────────────────────────────────────────────
@router.put("/{ticket_id}", response_model=TicketResponse)
async def edit_ticket(ticket_id: int, data: TicketEditRequest, db: DBSession, user: CurrentUser):
    """Customer can edit subject/description while ticket is still open."""
    return await svc.edit_ticket(db, ticket_id, data, user)


# ── Customer: delete open ticket ─────────────────────────────────────────────
@router.delete("/{ticket_id}", status_code=204)
async def delete_ticket(ticket_id: int, db: DBSession, user: CurrentUser):
    """Customer can delete an open ticket."""
    await svc.delete_ticket(db, ticket_id, user)


# ── Reply ─────────────────────────────────────────────────────────────────────
@router.post("/{ticket_id}/reply", status_code=201)
async def reply(ticket_id: int, data: ReplyRequest, db: DBSession, user: CurrentUser):
    msg = await svc.add_reply(db, ticket_id, data, user)
    return {"id": msg.id, "message": "Reply sent"}


# ── File upload ───────────────────────────────────────────────────────────────
@router.post("/{ticket_id}/attachments", status_code=201)
async def upload_attachment(
    ticket_id: int,
    db: DBSession,
    user: CurrentUser,
    file: UploadFile = File(...),
):
    """Upload a file attachment to a ticket (triggers AI summary)."""
    attachment = await svc.attach_file(db, ticket_id, file, user)
    return {
        "id": attachment.id,
        "file_path": attachment.file_path,
        "file_name": attachment.file_name,
        "message": "File uploaded successfully",
    }