"""Tests for ticket endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User, UserRole


# ── Helpers ───────────────────────────────────────────────────────────────────
async def _make_customer(client: AsyncClient, suffix: str = "1") -> dict:
    email = f"customer{suffix}@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"name": f"Customer {suffix}", "email": email, "password": "password123"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "password123"}
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _make_agent(db: AsyncSession, client: AsyncClient, suffix: str = "1") -> dict:
    email = f"agent{suffix}@test.com"
    agent = User(
        name=f"Agent {suffix}",
        email=email,
        hashed_password=hash_password("agentpass123"),
        role=UserRole.AGENT,
        is_active=True,
    )
    db.add(agent)
    await db.commit()
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "agentpass123"}
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


# ── Tests ─────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_create_ticket(client: AsyncClient):
    headers = await _make_customer(client, "c1")
    resp = await client.post(
        "/api/v1/tickets",
        json={"subject": "WiFi not working", "description": "Cannot connect to WiFi"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["subject"] == "WiFi not working"
    assert data["ticket_number"].startswith("SUP-")
    assert data["status"] == "open"


@pytest.mark.asyncio
async def test_create_ticket_empty_subject(client: AsyncClient):
    headers = await _make_customer(client, "c2")
    resp = await client.post(
        "/api/v1/tickets",
        json={"subject": "   ", "description": "Some issue"},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_agent_cannot_create_ticket(client: AsyncClient, db: AsyncSession):
    headers = await _make_agent(db, client, "a1")
    resp = await client.post(
        "/api/v1/tickets",
        json={"subject": "Test", "description": "Agent should not create tickets"},
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_my_tickets_pagination(client: AsyncClient):
    headers = await _make_customer(client, "c3")
    for i in range(3):
        await client.post(
            "/api/v1/tickets",
            json={"subject": f"Issue {i}", "description": f"Description {i}"},
            headers=headers,
        )
    resp = await client.get("/api/v1/tickets/my?page=1&page_size=2", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["total_pages"] == 2


@pytest.mark.asyncio
async def test_ticket_detail_access_control(client: AsyncClient, db: AsyncSession):
    cust_headers = await _make_customer(client, "c4")
    other_headers = await _make_customer(client, "c5")

    # Create ticket as c4
    create = await client.post(
        "/api/v1/tickets",
        json={"subject": "Private issue", "description": "My personal issue"},
        headers=cust_headers,
    )
    ticket_id = create.json()["id"]

    # c4 can view their own ticket
    resp = await client.get(f"/api/v1/tickets/{ticket_id}", headers=cust_headers)
    assert resp.status_code == 200

    # c5 cannot view c4's ticket
    resp = await client.get(f"/api/v1/tickets/{ticket_id}", headers=other_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_agent_can_reply(client: AsyncClient, db: AsyncSession):
    cust_headers = await _make_customer(client, "c6")
    agent_headers = await _make_agent(db, client, "a2")

    create = await client.post(
        "/api/v1/tickets",
        json={"subject": "Need help", "description": "Something broke"},
        headers=cust_headers,
    )
    ticket_id = create.json()["id"]

    resp = await client.post(
        f"/api/v1/tickets/{ticket_id}/reply",
        json={"message": "We are looking into this."},
        headers=agent_headers,
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_update_ticket_status(client: AsyncClient, db: AsyncSession):
    cust_headers = await _make_customer(client, "c7")
    agent_headers = await _make_agent(db, client, "a3")

    create = await client.post(
        "/api/v1/tickets",
        json={"subject": "Fix needed", "description": "Something is broken"},
        headers=cust_headers,
    )
    ticket_id = create.json()["id"]

    resp = await client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"status": "in_progress"},
        headers=agent_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_customer_cannot_update_status(client: AsyncClient):
    headers = await _make_customer(client, "c8")
    create = await client.post(
        "/api/v1/tickets",
        json={"subject": "My issue", "description": "Help me"},
        headers=headers,
    )
    ticket_id = create.json()["id"]

    resp = await client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"status": "resolved"},
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_open_ticket(client: AsyncClient):
    headers = await _make_customer(client, "c9")
    create = await client.post(
        "/api/v1/tickets",
        json={"subject": "To be deleted", "description": "Will delete this"},
        headers=headers,
    )
    ticket_id = create.json()["id"]

    resp = await client.delete(f"/api/v1/tickets/{ticket_id}", headers=headers)
    assert resp.status_code == 204

    resp = await client.get(f"/api/v1/tickets/{ticket_id}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_all_tickets_requires_agent(client: AsyncClient):
    cust_headers = await _make_customer(client, "c10")
    resp = await client.get("/api/v1/tickets/all", headers=cust_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_all_tickets_agent_access(client: AsyncClient, db: AsyncSession):
    agent_headers = await _make_agent(db, client, "a4")
    resp = await client.get("/api/v1/tickets/all", headers=agent_headers)
    assert resp.status_code == 200
    assert "items" in resp.json()
