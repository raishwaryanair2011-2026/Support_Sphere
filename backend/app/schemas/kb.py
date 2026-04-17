"""FAQ and Knowledge Base schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class _ORM(BaseModel):
    model_config = {"from_attributes": True}


# ── FAQ ───────────────────────────────────────────────────────────────────────
class FAQCreateRequest(BaseModel):
    question: str
    answer: str
    category: Optional[str] = None


class FAQUpdateRequest(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None


class FAQResponse(_ORM):
    id: int
    question: str
    answer: str
    category: Optional[str]
    created_at: datetime
    updated_at: datetime


# ── KB Document ───────────────────────────────────────────────────────────────
class KBDocumentResponse(_ORM):
    id: int
    title: str
    category: Optional[str]
    file_type: str
    status: str
    chunk_count: int
    created_at: datetime


class KBDocumentUpdateRequest(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None


# ── KB Chat ───────────────────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str   # "user" or "bot"
    text: str


class KBAskRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []   # last N messages for context


class KBAskResponse(BaseModel):
    answer: str
    intent: str
    source: str
    confidence: float
    suggest_ticket: bool
    videos: list[str] = []