"""User request / response schemas."""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from app.models.user import UserRole


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: Optional[str] = None
    email: str
    role: UserRole
    is_active: bool
    temp_password: Optional[str] = None
    department: Optional[str] = None


class AgentCreateRequest(BaseModel):
    name: str
    email: EmailStr
    department: Optional[str] = None


class AgentCreateResponse(BaseModel):
    id: int
    name: Optional[str] = None
    email: str
    generated_password: str


class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    department: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v