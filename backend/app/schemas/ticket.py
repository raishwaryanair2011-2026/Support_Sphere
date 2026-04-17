"""Ticket request / response schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.models.ticket import TicketPriority, TicketQueue, TicketStatus


# ── Shared config ─────────────────────────────────────────────────────────────
class _ORM(BaseModel):
    model_config = {"from_attributes": True}


# ── Messages ──────────────────────────────────────────────────────────────────
class MessageOut(_ORM):
    id: int
    sender_id: int
    sender_role: str
    message: str
    created_at: datetime


# ── Attachments ───────────────────────────────────────────────────────────────
class AttachmentOut(_ORM):
    id: int
    file_path: str
    file_name: str
    file_type: str
    uploaded_at: datetime


# ── Ticket create ─────────────────────────────────────────────────────────────
class TicketCreateRequest(BaseModel):
    subject: str
    description: str

    @field_validator("subject")
    @classmethod
    def subject_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Subject cannot be empty")
        if len(v) > 255:
            raise ValueError("Subject too long (max 255 chars)")
        return v

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Description cannot be empty")
        return v


# ── Ticket update (agent/admin) ───────────────────────────────────────────────
class TicketUpdateRequest(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    queue: Optional[TicketQueue] = None
    agent_id: Optional[int] = None


# ── Ticket edit (customer, open tickets only) ─────────────────────────────────
class TicketEditRequest(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None


# ── Reply ─────────────────────────────────────────────────────────────────────
class ReplyRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        return v


# ── Responses ─────────────────────────────────────────────────────────────────
class TicketResponse(_ORM):
    id: int
    ticket_number: str
    subject: str
    status: TicketStatus
    priority: TicketPriority
    queue: Optional[TicketQueue]
    customer_id: int
    agent_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    ai_summary: Optional[str]


class TicketDetailResponse(TicketResponse):
    messages: list[MessageOut] = []
    attachments: list[AttachmentOut] = []
    customer_name: Optional[str] = None
    agent_name: Optional[str] = None


# ── Pagination wrapper ────────────────────────────────────────────────────────
class PaginatedTickets(_ORM):
    items: list[TicketResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
