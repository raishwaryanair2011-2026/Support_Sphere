"""Tests for FAQ and Knowledge Base endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User, UserRole


async def _admin_headers(db: AsyncSession, client: AsyncClient) -> dict:
    email = "admin_faq@test.com"
    existing = await db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(User).where(User.email == email)
    )
    if not existing.scalar_one_or_none():
        admin = User(
            name="Test Admin",
            email=email,
            hashed_password=hash_password("adminpass123"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        await db.commit()

    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "adminpass123"}
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


# ── FAQ tests ─────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_faqs_public(client: AsyncClient):
    resp = await client.get("/api/v1/faqs")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_faq_admin(client: AsyncClient, db: AsyncSession):
    headers = await _admin_headers(db, client)
    resp = await client.post(
        "/api/v1/faqs",
        json={"question": "How do I reset my password?", "answer": "Use the forgot password link.", "category": "Account"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["question"] == "How do I reset my password?"
    assert data["category"] == "Account"


@pytest.mark.asyncio
async def test_create_faq_unauthenticated(client: AsyncClient):
    resp = await client.post(
        "/api/v1/faqs",
        json={"question": "Q?", "answer": "A."},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_faq(client: AsyncClient, db: AsyncSession):
    headers = await _admin_headers(db, client)
    create = await client.post(
        "/api/v1/faqs",
        json={"question": "Old question?", "answer": "Old answer.", "category": "General"},
        headers=headers,
    )
    faq_id = create.json()["id"]

    resp = await client.put(
        f"/api/v1/faqs/{faq_id}",
        json={"question": "Updated question?"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["question"] == "Updated question?"


@pytest.mark.asyncio
async def test_delete_faq(client: AsyncClient, db: AsyncSession):
    headers = await _admin_headers(db, client)
    create = await client.post(
        "/api/v1/faqs",
        json={"question": "To delete?", "answer": "Yes."},
        headers=headers,
    )
    faq_id = create.json()["id"]

    resp = await client.delete(f"/api/v1/faqs/{faq_id}", headers=headers)
    assert resp.status_code == 204

    all_faqs = await client.get("/api/v1/faqs")
    ids = [f["id"] for f in all_faqs.json()]
    assert faq_id not in ids


# ── KB chatbot tests ──────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_kb_ask_greeting(client: AsyncClient):
    resp = await client.post("/api/v1/kb/ask", json={"question": "hello"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "greeting"
    assert "Hi" in data["answer"]


@pytest.mark.asyncio
async def test_kb_ask_small_talk(client: AsyncClient):
    resp = await client.post("/api/v1/kb/ask", json={"question": "thanks"})
    assert resp.status_code == 200
    assert resp.json()["intent"] == "small_talk"


@pytest.mark.asyncio
async def test_kb_ask_empty_question(client: AsyncClient):
    resp = await client.post("/api/v1/kb/ask", json={"question": "   "})
    assert resp.status_code == 200
    assert resp.json()["intent"] == "empty"


@pytest.mark.asyncio
async def test_kb_articles_public(client: AsyncClient):
    resp = await client.get("/api/v1/kb/articles")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_kb_documents_requires_admin(client: AsyncClient):
    resp = await client.get("/api/v1/kb/documents")
    assert resp.status_code == 401
