"""Admin dashboard, analytics, and agent-performance endpoints."""
from typing import Annotated

from fastapi import APIRouter

from app.core.deps import DBSession, RequireAdmin
from app.schemas.admin import AgentPerformanceResponse, DashboardResponse
from app.services.analytics import get_agent_performance, get_dashboard

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", response_model=DashboardResponse, dependencies=[RequireAdmin])
async def dashboard(db: DBSession):
    """
    Full admin dashboard payload in a single request:
    ticket counts, priority breakdown, queue breakdown,
    monthly trend, and all-agent performance summary.
    """
    return await get_dashboard(db)


@router.get(
    "/agents/{agent_id}/performance",
    response_model=AgentPerformanceResponse,
    dependencies=[RequireAdmin],
)
async def agent_performance(agent_id: int, db: DBSession):
    """Detailed performance metrics for a single agent."""
    return await get_agent_performance(db, agent_id)
