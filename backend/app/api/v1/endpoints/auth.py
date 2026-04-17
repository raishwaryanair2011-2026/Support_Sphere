"""Authentication endpoints: register, login, refresh, me."""
from fastapi import APIRouter

from app.core.deps import CurrentUser, DBSession
from app.core.exceptions import UnauthorizedException
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.user import UserRole
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserInToken
from app.schemas.user import ChangePasswordRequest
from app.services.user import change_password, register_customer

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=201)
async def register(data: RegisterRequest, db: DBSession):
    """Public: register a new customer account."""
    user = await register_customer(db, data.name, data.email, data.password)
    return {"message": "Account created successfully", "user_id": user.id}


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: DBSession):
    """Exchange credentials for access + refresh tokens."""
    from sqlalchemy import select
    from app.models.user import User
    from app.core.security import verify_password

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedException("Account is deactivated")

    token_payload = {"user_id": user.id, "role": user.role.value}
    return TokenResponse(
        access_token=create_access_token(token_payload),
        refresh_token=create_refresh_token(token_payload),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: DBSession):
    """Use a refresh token to get a new access token."""
    payload = decode_token(data.refresh_token)

    if payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid token type")

    from sqlalchemy import select
    from app.models.user import User

    result = await db.execute(select(User).where(User.id == payload["user_id"]))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise UnauthorizedException("User not found or deactivated")

    token_payload = {"user_id": user.id, "role": user.role.value}
    return TokenResponse(
        access_token=create_access_token(token_payload),
        refresh_token=create_refresh_token(token_payload),
    )


@router.get("/me", response_model=UserInToken)
async def me(user: CurrentUser):
    """Return the currently authenticated user's profile."""
    return UserInToken(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
    )


@router.post("/change-password", status_code=200)
async def change_my_password(data: ChangePasswordRequest, user: CurrentUser, db: DBSession):
    """Change authenticated user's password."""
    await change_password(db, user, data)
    return {"message": "Password updated successfully"}
