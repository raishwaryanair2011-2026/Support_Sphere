"""
Shared pytest fixtures.

Uses an in-memory SQLite database so tests run without any external services.
Each test function gets a fresh database via function-scoped session rollback.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_db_session
from app.main import app

# ── In-memory SQLite for tests ────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    """Create all tables once for the entire test session."""
    import app.models  # noqa: F401
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    """Provide a test DB session that rolls back after each test."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    """AsyncClient with the DB dependency overridden to use the test session."""

    async def override_db():
        yield db

    app.dependency_overrides[get_db_session] = override_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Helper: create a user and return their auth token ─────────────────────────
async def create_user_and_token(
    client: AsyncClient,
    email: str,
    password: str,
    name: str = "Test User",
    role: str = "customer",
) -> tuple[dict, str]:
    """
    Register a customer (or directly insert agent/admin) and return
    (user_dict, access_token).
    """
    if role == "customer":
        await client.post(
            "/api/v1/auth/register",
            json={"name": name, "email": email, "password": password},
        )
    else:
        # For agent/admin, insert directly via the DB (bypassing HTTP)
        from app.core.security import hash_password
        from app.models.user import User, UserRole
        from sqlalchemy import select

        # Reuse the db from the closure scope — get fresh via client override
        async for session in client.app.dependency_overrides[get_db_session]():
            user = User(
                name=name,
                email=email,
                hashed_password=hash_password(password),
                role=UserRole(role),
                is_active=True,
            )
            session.add(user)
            await session.commit()

    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return headers
