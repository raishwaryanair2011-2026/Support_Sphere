"""User and agent management endpoints (admin only)."""
from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import DBSession, RequireAdmin
from app.models.user import User, UserRole
from app.schemas.user import AgentCreateRequest, AgentCreateResponse, AgentUpdateRequest, UserResponse
from app.services import user as svc
from pydantic import BaseModel, EmailStr
from typing import Optional

router = APIRouter(prefix="/users", tags=["Users"])


# ── Agent endpoints ───────────────────────────────────────────────────────────
@router.post("/agents", response_model=AgentCreateResponse, status_code=201, dependencies=[RequireAdmin])
async def create_agent(data: AgentCreateRequest, db: DBSession):
    agent, password = await svc.create_agent(db, data)
    return AgentCreateResponse(id=agent.id, name=agent.name, email=agent.email, generated_password=password)


@router.get("/agents", response_model=list[UserResponse], dependencies=[RequireAdmin])
async def list_agents(db: DBSession):
    return await svc.get_agents(db)


@router.put("/agents/{agent_id}", response_model=UserResponse, dependencies=[RequireAdmin])
async def update_agent(agent_id: int, data: AgentUpdateRequest, db: DBSession):
    return await svc.update_agent(db, agent_id, data)


@router.delete("/agents/{agent_id}", status_code=204, dependencies=[RequireAdmin])
async def delete_agent(agent_id: int, db: DBSession):
    await svc.delete_agent(db, agent_id)


# ── Customer endpoints ────────────────────────────────────────────────────────
class CustomerUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


@router.get("/customers", response_model=list[UserResponse], dependencies=[RequireAdmin])
async def list_customers(db: DBSession):
    result = await db.execute(
        select(User).where(User.role == UserRole.CUSTOMER).order_by(User.name)
    )
    return list(result.scalars().all())


@router.put("/customers/{customer_id}", response_model=UserResponse, dependencies=[RequireAdmin])
async def update_customer(customer_id: int, data: CustomerUpdateRequest, db: DBSession):
    from app.core.exceptions import NotFoundException, ConflictException
    result = await db.execute(select(User).where(User.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise NotFoundException("Customer not found")
    if data.name is not None:
        customer.name = data.name
    if data.email is not None:
        dupe = await db.execute(select(User).where(User.email == data.email, User.id != customer_id))
        if dupe.scalar_one_or_none():
            raise ConflictException("Email already in use")
        customer.email = data.email
    if data.is_active is not None:
        customer.is_active = data.is_active
    await db.commit()
    await db.refresh(customer)
    return customer


@router.delete("/customers/{customer_id}", status_code=204, dependencies=[RequireAdmin])
async def delete_customer(customer_id: int, db: DBSession):
    from app.core.exceptions import NotFoundException
    result = await db.execute(select(User).where(User.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise NotFoundException("Customer not found")
    await db.delete(customer)
    await db.commit()


@router.post("/agents/{agent_id}/reset-password", dependencies=[RequireAdmin])
async def reset_agent_password(agent_id: int, db: DBSession):
    """Admin: generate a new temporary password for an agent."""
    from app.core.exceptions import NotFoundException
    from app.core.security import hash_password
    from app.services.user import _generate_password

    result = await db.execute(select(User).where(User.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundException("Agent not found")

    new_password = _generate_password()
    agent.hashed_password = hash_password(new_password)
    agent.temp_password = new_password
    await db.commit()

    return {"generated_password": new_password, "message": "Password reset successfully"}


@router.get("/agents/workload", dependencies=[RequireAdmin])
async def agent_workload(db: DBSession):
    """Admin: see active ticket count per agent."""
    from app.services.ticket import get_agent_workload
    return await get_agent_workload(db)