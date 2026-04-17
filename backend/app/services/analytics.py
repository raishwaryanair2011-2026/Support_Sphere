"""Admin analytics and dashboard aggregation service."""
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket, TicketMessage, TicketStatus
from app.models.user import User, UserRole
from app.schemas.admin import (
    AgentPerformanceResponse,
    DashboardResponse,
    MonthlyStatPoint,
    PriorityStatsResponse,
    QueueStatsResponse,
    TicketCountsResponse,
)

_MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


async def get_dashboard(db: AsyncSession) -> DashboardResponse:
    counts = await _ticket_counts(db)
    priority = await _priority_stats(db)
    queue = await _queue_stats(db)
    monthly = await _monthly_stats(db)
    agents = await _agent_performance_all(db)

    return DashboardResponse(
        counts=counts,
        priority=priority,
        queue=queue,
        monthly=monthly,
        agents=agents,
    )


async def _ticket_counts(db: AsyncSession) -> TicketCountsResponse:
    rows = await db.execute(
        select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
    )
    by_status = {r[0]: r[1] for r in rows}

    total_result = await db.execute(select(func.count(Ticket.id)))

    return TicketCountsResponse(
        total=total_result.scalar_one(),
        open=by_status.get(TicketStatus.OPEN, 0),
        in_progress=by_status.get(TicketStatus.IN_PROGRESS, 0),
        resolved=by_status.get(TicketStatus.RESOLVED, 0),
        closed=by_status.get(TicketStatus.CLOSED, 0),
    )


async def _priority_stats(db: AsyncSession) -> PriorityStatsResponse:
    rows = await db.execute(
        select(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority)
    )
    by_priority = {r[0]: r[1] for r in rows}
    return PriorityStatsResponse(
        low=by_priority.get("low", 0),
        medium=by_priority.get("medium", 0),
        high=by_priority.get("high", 0),
    )


async def _queue_stats(db: AsyncSession) -> QueueStatsResponse:
    rows = await db.execute(
        select(Ticket.queue, func.count(Ticket.id)).group_by(Ticket.queue)
    )
    stats = {(r[0] or "Unassigned"): r[1] for r in rows}
    return QueueStatsResponse(stats=stats)


async def _monthly_stats(db: AsyncSession) -> list[MonthlyStatPoint]:
    rows = await db.execute(
        select(
            extract("month", Ticket.created_at).label("month"),
            func.count(Ticket.id),
        ).group_by("month")
    )
    by_month = {int(r[0]): r[1] for r in rows}
    return [
        MonthlyStatPoint(month=_MONTH_NAMES[i - 1], count=by_month.get(i, 0))
        for i in range(1, 13)
    ]


async def _agent_performance_all(db: AsyncSession) -> list[AgentPerformanceResponse]:
    agents_result = await db.execute(
        select(User).where(User.role == UserRole.AGENT).order_by(User.id)
    )
    agents = agents_result.scalars().all()

    result = []
    for agent in agents:
        perf = await get_agent_performance(db, agent.id)
        result.append(perf)

    return result


async def get_agent_performance(db: AsyncSession, agent_id: int) -> AgentPerformanceResponse:
    # Resolved tickets
    resolved_result = await db.execute(
        select(Ticket).where(Ticket.resolved_by == agent_id)
    )
    resolved_tickets = resolved_result.scalars().all()
    resolved_count = len(resolved_tickets)

    # Messages sent (proxy for "open/active" engagement)
    msg_result = await db.execute(
        select(func.count(TicketMessage.id)).where(
            TicketMessage.sender_id == agent_id,
            TicketMessage.sender_role == "agent",
        )
    )
    messages_sent = msg_result.scalar_one()

    # Pending (in_progress assigned to this agent)
    pending_result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.agent_id == agent_id,
            Ticket.status == TicketStatus.IN_PROGRESS,
        )
    )
    pending = pending_result.scalar_one()

    # Average resolution time (hours)
    avg_resolution_hours = 0.0
    if resolved_tickets:
        total_seconds = sum(
            (t.closed_at - t.created_at).total_seconds()
            for t in resolved_tickets
            if t.closed_at and t.created_at
        )
        avg_resolution_hours = round((total_seconds / resolved_count) / 3600, 2)

    # Efficiency
    total_handled = resolved_count + messages_sent
    efficiency_pct = round((resolved_count / total_handled) * 100, 2) if total_handled else 0.0

    # Fetch name
    agent_result = await db.execute(select(User).where(User.id == agent_id))
    agent = agent_result.scalar_one_or_none()
    agent_name = agent.name or agent.email if agent else str(agent_id)

    return AgentPerformanceResponse(
        agent_id=agent_id,
        agent_name=agent_name,
        resolved=resolved_count,
        messages_sent=messages_sent,
        pending=pending,
        avg_resolution_hours=avg_resolution_hours,
        efficiency_pct=efficiency_pct,
    )
