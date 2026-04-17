"""User and agent management service."""
import secrets
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.core.logging import get_logger
from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.user import AgentCreateRequest, AgentUpdateRequest, ChangePasswordRequest

logger = get_logger(__name__)


def _generate_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def register_customer(db: AsyncSession, name: str, email: str, password: str) -> User:
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise ConflictException("Email already registered")

    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("customer_registered", user_id=user.id, email=email)
    return user


async def create_agent(db: AsyncSession, data: AgentCreateRequest) -> tuple[User, str]:
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise ConflictException("Email already in use")

    password = _generate_password()

    agent = User(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(password),
        role=UserRole.AGENT,
        is_active=True,
        temp_password=password,  # shown once to admin
        department=data.department if hasattr(data, "department") else None,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    logger.info("agent_created", agent_id=agent.id, email=data.email)
    return agent, password


async def get_agents(db: AsyncSession) -> list[User]:
    result = await db.execute(
        select(User).where(User.role == UserRole.AGENT).order_by(User.id)
    )
    return list(result.scalars().all())


async def update_agent(db: AsyncSession, agent_id: int, data: AgentUpdateRequest) -> User:
    result = await db.execute(select(User).where(User.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise NotFoundException("Agent not found")

    if data.name is not None:
        agent.name = data.name
    if data.email is not None:
        # Check uniqueness
        dupe = await db.execute(
            select(User).where(User.email == data.email, User.id != agent_id)
        )
        if dupe.scalar_one_or_none():
            raise ConflictException("Email already in use")
        agent.email = data.email
    if data.is_active is not None:
        agent.is_active = data.is_active
    if hasattr(data, "department"):
        # Empty string means "no department" (all queues)
        agent.department = data.department if data.department else None

    await db.commit()
    await db.refresh(agent)
    return agent


async def delete_agent(db: AsyncSession, agent_id: int) -> None:
    result = await db.execute(select(User).where(User.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise NotFoundException("Agent not found")

    await db.delete(agent)
    await db.commit()
    logger.info("agent_deleted", agent_id=agent_id)


async def change_password(
    db: AsyncSession, user: User, data: ChangePasswordRequest
) -> None:
    if not verify_password(data.current_password, user.hashed_password):
        from app.core.exceptions import UnauthorizedException
        raise UnauthorizedException("Current password is incorrect")

    user.hashed_password = hash_password(data.new_password)
    user.temp_password = None  # clear one-time password once changed
    await db.commit()
    logger.info("password_changed", user_id=user.id)