"""
Document summary service using Groq.
Extracts text from uploaded files and generates a concise summary.
"""
from groq import AsyncGroq

from app.core.config import get_settings
from app.core.logging import get_logger
from app.utils.files import extract_text_from_file

logger = get_logger(__name__)
settings = get_settings()

_SYSTEM_PROMPT = (
    "You are a support document analyst. "
    "Summarize the document in 3 concise sentences, focusing on the main issue or topic."
)


async def summarize_document(file_path: str) -> str:
    """
    Generate an AI summary for an uploaded file.
    Returns empty string on any failure — callers should treat this as optional.
    """
    if not settings.GROQ_API_KEY:
        logger.debug("summarize_document_skipped", reason="no GROQ_API_KEY configured")
        return ""

    text = extract_text_from_file(file_path)

    if not text.strip():
        logger.warning("summarize_document_no_text", path=file_path)
        return ""

    try:
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        response = await client.chat.completions.create(
            model=settings.GROQ_SUMMARY_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.2,
            max_tokens=200,
        )
        summary = (response.choices[0].message.content or "").strip()
        logger.info("document_summarized", path=file_path, chars=len(summary))
        return summary

    except Exception as exc:
        logger.error("summarize_document_failed", path=file_path, error=str(exc))
        return ""
