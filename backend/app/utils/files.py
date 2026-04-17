"""
File upload utilities.
Validates content type, size, and saves files with unique names.
"""
import os
import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import BadRequestException
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def _ensure_upload_dir() -> Path:
    path = Path(settings.UPLOAD_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


async def save_upload(file: UploadFile) -> tuple[str, str]:
    """
    Validate and persist an uploaded file.

    Returns:
        (file_path, original_filename)

    Raises:
        BadRequestException: if type or size is invalid.
    """
    # ── Content-type check ────────────────────────────────────────────────────
    if file.content_type not in settings.ALLOWED_UPLOAD_TYPES:
        raise BadRequestException(
            f"Unsupported file type '{file.content_type}'. "
            f"Allowed: {', '.join(settings.ALLOWED_UPLOAD_TYPES)}"
        )

    upload_dir = _ensure_upload_dir()
    ext = Path(file.filename or "file").suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = upload_dir / unique_name

    # ── Stream to disk + size check ───────────────────────────────────────────
    bytes_written = 0
    max_bytes = settings.max_upload_bytes

    with open(dest, "wb") as out:
        while chunk := await file.read(1024 * 64):  # 64 KB chunks
            bytes_written += len(chunk)
            if bytes_written > max_bytes:
                out.close()
                dest.unlink(missing_ok=True)
                raise BadRequestException(
                    f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB} MB."
                )
            out.write(chunk)

    logger.info(
        "file_uploaded",
        path=str(dest),
        size_bytes=bytes_written,
        original_name=file.filename,
    )

    return str(dest), file.filename or unique_name


def delete_file(file_path: str) -> None:
    """Remove a file from disk, logging but not raising on missing files."""
    try:
        Path(file_path).unlink(missing_ok=True)
        logger.info("file_deleted", path=file_path)
    except OSError as exc:
        logger.warning("file_delete_failed", path=file_path, error=str(exc))


def extract_text_from_file(file_path: str) -> str:
    """
    Extract plain text from .txt, .log, or .pdf files.
    Returns empty string on unsupported types or errors.
    """
    ext = Path(file_path).suffix.lower()

    try:
        if ext in (".txt", ".log"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(8000)

        if ext == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
            return text[:8000]

    except Exception as exc:
        logger.warning("text_extraction_failed", path=file_path, error=str(exc))

    return ""
