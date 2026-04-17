"""Admin analytics response schemas."""
from typing import Dict

from pydantic import BaseModel


class TicketCountsResponse(BaseModel):
    total: int
    open: int
    in_progress: int
    resolved: int
    closed: int


class PriorityStatsResponse(BaseModel):
    low: int = 0
    medium: int = 0
    high: int = 0


class QueueStatsResponse(BaseModel):
    stats: Dict[str, int]


class MonthlyStatPoint(BaseModel):
    month: str
    count: int


class AgentPerformanceResponse(BaseModel):
    agent_id: int
    agent_name: str
    resolved: int
    messages_sent: int
    pending: int
    avg_resolution_hours: float
    efficiency_pct: float


class DashboardResponse(BaseModel):
    counts: TicketCountsResponse
    priority: PriorityStatsResponse
    queue: QueueStatsResponse
    monthly: list[MonthlyStatPoint]
    agents: list[AgentPerformanceResponse]
