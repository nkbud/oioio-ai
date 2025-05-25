"""
User schemas for API.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, UUID4

from oioio_mcp_agent.api.models import UserRole


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = UserRole.USER


class UserCreate(UserBase):
    """Schema for user creation."""

    password: str
    tenant_id: UUID4


class UserUpdate(BaseModel):
    """Schema for user update."""

    email: Optional[EmailStr] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Response schema for user."""

    id: UUID4
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    tenant_id: UUID4

    class Config:
        """Pydantic config."""

        from_attributes = True


class TenantBase(BaseModel):
    """Base tenant schema."""

    name: str
    slug: str
    description: Optional[str] = None


class TenantCreate(TenantBase):
    """Schema for tenant creation."""

    pass


class TenantUpdate(BaseModel):
    """Schema for tenant update."""

    name: Optional[str] = None
    description: Optional[str] = None


class TenantResponse(TenantBase):
    """Response schema for tenant."""

    id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class APIKeyBase(BaseModel):
    """Base API key schema."""

    name: str


class APIKeyCreate(APIKeyBase):
    """Schema for API key creation."""

    expires_at: Optional[datetime] = None


class APIKeyResponse(APIKeyBase):
    """Response schema for API key."""

    id: UUID4
    key: str
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: UUID4

    class Config:
        """Pydantic config."""

        from_attributes = True