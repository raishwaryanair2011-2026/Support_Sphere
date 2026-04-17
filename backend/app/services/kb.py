"""Knowledge Base document ingestion and management service."""
import asyncio
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.core.logging import get_logger
from app.models.kb import KBChunk, KBDocument
from app.models.user import User
from app.services.ai.rag import add_chunks, chunk_text
from app.utils.files import delete_file, extract_text_from_file, save_upload

logger = get_logger(__name__)


async def upload_kb_document(
    db: AsyncSession, title: str, category: str | None, file, uploader: User
) -> KBDocument:
    file_path, _ = await save_upload(file)
    file_type = Path(file_path).suffix.lstrip(".")

    doc = KBDocument(
        title=title,
        category=category,
        file_path=file_path,
        file_type=file_type,
        status="Processing",
        uploaded_by=uploader.id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Ingest in the background with its OWN session
    # Never pass the request session to a background task — it will be closed
    asyncio.create_task(_ingest_document(doc.id))
    return doc


async def _ingest_document(doc_id: int) -> None:
    """
    Background task: extract text, chunk, embed, store.
    Opens its own DB session so it never conflicts with the request session.
    """
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(KBDocument).where(KBDocument.id == doc_id))
        doc = result.scalar_one_or_none()
        if not doc:
            return

        try:
            text = extract_text_from_file(doc.file_path)

            if not text.strip():
                doc.status = "Failed (no text extracted)"
                await db.commit()
                return

            chunks = chunk_text(text)
            metadatas = [
                {"title": doc.title, "category": doc.category or "", "document_id": doc.id}
                for _ in chunks
            ]

            for chunk_text_piece in chunks:
                db.add(KBChunk(document_id=doc.id, content=chunk_text_piece))

            await add_chunks(chunks, metadatas)

            doc.chunk_count = len(chunks)
            doc.status = "Indexed"
            await db.commit()
            logger.info("kb_document_indexed", doc_id=doc_id, chunks=len(chunks), title=doc.title)

        except Exception as exc:
            logger.error("kb_ingest_failed", doc_id=doc_id, error=str(exc))
            try:
                doc.status = "Failed"
                await db.commit()
            except Exception:
                pass


async def list_kb_documents(db: AsyncSession) -> list[KBDocument]:
    result = await db.execute(
        select(KBDocument).order_by(KBDocument.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_kb_document(db: AsyncSession, doc_id: int) -> None:
    result = await db.execute(select(KBDocument).where(KBDocument.id == doc_id))
    doc = result.scalar_one_or_none()

    if not doc:
        raise NotFoundException("Document not found")

    delete_file(doc.file_path)
    await db.delete(doc)
    await db.commit()
    logger.info("kb_document_deleted", doc_id=doc_id)


async def update_kb_document(
    db: AsyncSession, doc_id: int, title: str | None, category: str | None
) -> KBDocument:
    result = await db.execute(select(KBDocument).where(KBDocument.id == doc_id))
    doc = result.scalar_one_or_none()

    if not doc:
        raise NotFoundException("Document not found")

    if title is not None:
        doc.title = title
    if category is not None:
        doc.category = category

    await db.commit()
    await db.refresh(doc)
    return doc


async def get_public_articles(db: AsyncSession) -> list[dict]:
    """Returns documents with a short content preview (no auth required)."""
    result = await db.execute(
        select(KBDocument).where(KBDocument.status == "Indexed").order_by(KBDocument.created_at.desc())
    )
    docs = result.scalars().all()

    articles = []
    for doc in docs:
        preview = ""
        try:
            text = extract_text_from_file(doc.file_path)
            preview = text[:800]
        except Exception:
            pass

        articles.append(
            {
                "id": doc.id,
                "title": doc.title,
                "category": doc.category,
                "content": preview,
            }
        )
    return articles