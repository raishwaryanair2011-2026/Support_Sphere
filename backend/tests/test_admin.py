"""Tests for admin and user management endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User, UserRole
from sqlalchemy import select


async def _setup_admin(db: AsyncSession, client: AsyncClient, suffix: str = "") -> dict:
    email = f"superadmin{suffix}@test.com"
    result = await db.execute(select(User).where(User.email == email))
    if not result.scalar_one_or_none():
        admin = User(
            name="Super Admin",
            email=email,
            hashed_password=hash_password("superpass123"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        await db.commit()

    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "superpass123"}
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


# ── Agent management ──────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_create_agent(client: AsyncClient, db: AsyncSession):
    headers = await _setup_admin(db, client, "1")
    resp = await client.post(
        "/api/v1/users/agents",
        json={"name": "New Agent", "email": "newagent@test.com"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newagent@test.com"
    assert "generated_password" in data
    assert len(data["generated_password"]) >= 8


@pytest.mark.asyncio
async def test_create_agent_duplicate_email(client: AsyncClient, db: AsyncSession):
    headers = await _setup_admin(db, client, "2")
    payload = {"name": "Agent Dupe", "email": "dupe_agent@test.com"}
    await client.post("/api/v1/users/agents", json=payload, headers=headers)
    resp = await client.post("/api/v1/users/agents", json=payload, headers=headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient, db: AsyncSession):
    headers = await _setup_admin(db, client, "3")
    resp = await client.get("/api/v1/users/agents", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_update_agent(client: AsyncClient, db: AsyncSession):
    headers = await _setup_admin(db, client, "4")
    create = await client.post(
        "/api/v1/users/agents",
        json={"name": "Agent To Update", "email": "update_agent@test.com"},
        headers=headers,
    )
    agent_id = create.json()["id"]

    resp = await client.put(
        f"/api/v1/users/agents/{agent_id}",
        json={"name": "Updated Name"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_agent(client: AsyncClient, db: AsyncSession):
    headers = await _setup_admin(db, client, "5")
    create = await client.post(
        "/api/v1/users/agents",
        json={"name": "Agent To Delete", "email": "delete_agent@test.com"},
        headers=headers,
    )
    agent_id = create.json()["id"]

    resp = await client.delete(f"/api/v1/users/agents/{agent_id}", headers=headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_agents_endpoint_requires_admin(client: AsyncClient):
    resp = await client.get("/api/v1/users/agents")
    assert resp.status_code == 401


# ── Admin dashboard ───────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_dashboard_requires_admin(client: AsyncClient):
    resp = await client.get("/api/v1/admin/dashboard")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_returns_structure(client: AsyncClient, db: AsyncSession):
    headers = await _setup_admin(db, client, "6")
    resp = await client.get("/api/v1/admin/dashboard", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "counts" in data
    assert "priority" in data
    assert "queue" in data
    assert "monthly" in data
    assert "agents" in data
    assert len(data["monthly"]) == 12  # one entry per month


@pytest.mark.asyncio
async def test_customer_cannot_access_dashboard(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Cust", "email": "cust_dash@test.com", "password": "password123"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "cust_dash@test.com", "password": "password123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    resp = await client.get("/api/v1/admin/dashboard", headers=headers)
    assert resp.status_code == 403
