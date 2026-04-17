"""Knowledge Base endpoints — document management (admin) and chatbot (public)."""
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile

from app.core.deps import CurrentUser, DBSession, RequireAdmin
from app.schemas.kb import KBAskRequest, KBAskResponse, KBDocumentResponse, KBDocumentUpdateRequest
from app.services import kb as svc
from app.services.ai.rag import answer_question

router = APIRouter(prefix="/kb", tags=["Knowledge Base"])


# ── Public: chatbot ───────────────────────────────────────────────────────────
@router.post("/ask", response_model=KBAskResponse)
async def ask(data: KBAskRequest):
    """
    Public chatbot endpoint.
    Accepts conversation history for multi-turn memory.
    No authentication required — customers use this before logging in.
    """
    question = data.question.strip()
    if not question:
        return KBAskResponse(
            answer="Please enter a question.",
            intent="empty",
            source="static",
            confidence=0.0,
            suggest_ticket=False,
        )
    return await answer_question(question, history=data.history)


# ── Public: article listing ───────────────────────────────────────────────────
@router.get("/articles")
async def public_articles(db: DBSession):
    """Public: list indexed KB articles with a content preview."""
    return await svc.get_public_articles(db)


# ── Admin: upload document ────────────────────────────────────────────────────
@router.post(
    "/documents",
    response_model=KBDocumentResponse,
    status_code=201,
    dependencies=[RequireAdmin],
)
async def upload_document(
    db: DBSession,
    uploader: CurrentUser,
    title: str = Form(...),
    category: str | None = Form(None),
    file: UploadFile = File(...),
):
    """Admin: upload and index a new KB document (PDF or TXT)."""
    return await svc.upload_kb_document(db, title, category, file, uploader)


# ── Admin: list documents ─────────────────────────────────────────────────────
@router.get("/documents", response_model=list[KBDocumentResponse], dependencies=[RequireAdmin])
async def list_documents(db: DBSession):
    """Admin: list all KB documents with their indexing status."""
    return await svc.list_kb_documents(db)


# ── Admin: update document metadata ──────────────────────────────────────────
@router.patch("/documents/{doc_id}", response_model=KBDocumentResponse, dependencies=[RequireAdmin])
async def update_document(doc_id: int, data: KBDocumentUpdateRequest, db: DBSession):
    """Admin: update a document's title or category."""
    return await svc.update_kb_document(db, doc_id, data.title, data.category)


# ── Admin: delete document ────────────────────────────────────────────────────
@router.delete("/documents/{doc_id}", status_code=204, dependencies=[RequireAdmin])
async def delete_document(doc_id: int, db: DBSession):
    """Admin: delete a KB document and its file from disk."""
    await svc.delete_kb_document(db, doc_id)