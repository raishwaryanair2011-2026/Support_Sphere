"""FAQ endpoints — public read, admin CRUD."""
from typing import Annotated

from fastapi import APIRouter

from app.core.deps import DBSession, RequireAdmin
from app.models.kb import FAQ
from app.schemas.kb import FAQCreateRequest, FAQResponse, FAQUpdateRequest
from app.core.exceptions import NotFoundException
from sqlalchemy import select

router = APIRouter(prefix="/faqs", tags=["FAQs"])


@router.get("", response_model=list[FAQResponse])
async def list_faqs(db: DBSession):
    """Public: list all FAQs ordered by newest first."""
    result = await db.execute(
        select(FAQ).order_by(FAQ.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=FAQResponse, status_code=201, dependencies=[RequireAdmin])
async def create_faq(data: FAQCreateRequest, db: DBSession):
    """Admin: create a new FAQ entry."""
    faq = FAQ(**data.model_dump())
    db.add(faq)
    await db.commit()
    await db.refresh(faq)
    return faq


@router.put("/{faq_id}", response_model=FAQResponse, dependencies=[RequireAdmin])
async def update_faq(faq_id: int, data: FAQUpdateRequest, db: DBSession):
    """Admin: update an existing FAQ."""
    result = await db.execute(select(FAQ).where(FAQ.id == faq_id))
    faq = result.scalar_one_or_none()
    if not faq:
        raise NotFoundException("FAQ not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(faq, field, value)

    await db.commit()
    await db.refresh(faq)
    return faq


@router.delete("/{faq_id}", status_code=204, dependencies=[RequireAdmin])
async def delete_faq(faq_id: int, db: DBSession):
    """Admin: permanently delete a FAQ."""
    result = await db.execute(select(FAQ).where(FAQ.id == faq_id))
    faq = result.scalar_one_or_none()
    if not faq:
        raise NotFoundException("FAQ not found")

    await db.delete(faq)
    await db.commit()