"""
Authentication schemas for API.
"""
from typing import List, Optional

from pydantic import BaseModel


class TokenRequest(BaseModel):
    """Schema for token request."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """Schema for token data."""

    sub: str
    scopes: List[str] = []


class GoogleAuthResponse(BaseModel):
    """Schema for Google OAuth response."""

    access_token: str
    token_type: str
    expires_in: int
    is_new_user: bool