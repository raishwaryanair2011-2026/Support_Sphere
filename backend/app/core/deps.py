"""
FastAPI dependency functions:
- Database session
- Authentication & role enforcement
"""
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_token
from app.db.session import get_db_session
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)

# ── Database ─────────────────────────────────────────────────────────────────
DBSession = Annotated[AsyncSession, Depends(get_db_session)]


# ── Auth ─────────────────────────────────────────────────────────────────────
async def get_current_user(
    db: DBSession,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ] = None,
) -> User:
    if not credentials:
        raise UnauthorizedException("Authentication required")

    payload = decode_token(credentials.credentials)

    user_id: int | None = payload.get("user_id")
    if user_id is None:
        raise UnauthorizedException("Invalid token payload")

    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException("User not found")
    if not user.is_active:
        raise UnauthorizedException("Account is deactivated")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: UserRole):
    """Returns a dependency that enforces one of the allowed roles."""

    async def _check(user: CurrentUser) -> User:
        if user.role not in roles:
            raise ForbiddenException(
                f"Access requires role: {', '.join(r.value for r in roles)}"
            )
        return user

    return Depends(_check)


# ── Convenience aliases ───────────────────────────────────────────────────────
RequireAdmin = require_role(UserRole.ADMIN)
RequireAgent = require_role(UserRole.AGENT, UserRole.ADMIN)   # admins can do agent things
RequireCustomer = require_role(UserRole.CUSTOMER)
RequireAny = Depends(get_current_user)
