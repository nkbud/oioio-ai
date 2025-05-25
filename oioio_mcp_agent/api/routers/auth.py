"""
Authentication router for API.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from oioio_mcp_agent.api.auth import (ACCESS_TOKEN_EXPIRE_MINUTES,
                                authenticate_user,
                                authenticate_user_google, create_access_token,
                                get_current_active_user,
                                get_oauth_redirect_url, oauth)
from oioio_mcp_agent.api.db import get_db
from oioio_mcp_agent.api.models import User
from oioio_mcp_agent.api.schemas.auth import (GoogleAuthResponse, TokenRequest,
                                        TokenResponse)

# Create router
router = APIRouter()


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get access token from credentials."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.email,
            "tenant_id": str(user.tenant_id),
            "scopes": [user.role],
        },
        expires_delta=access_token_expires,
    )

    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.get("/google/login")
async def login_google(request: Request) -> RedirectResponse:
    """Login with Google."""
    redirect_uri = get_oauth_redirect_url(request)
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback/google", response_model=GoogleAuthResponse)
async def auth_callback_google(
    request: Request, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Handle Google OAuth callback."""
    user, is_new_user = await authenticate_user_google(request, db)

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.email,
            "tenant_id": str(user.tenant_id),
            "scopes": [user.role],
        },
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "is_new_user": is_new_user,
    }


@router.get("/me", response_model=Dict[str, Any])
async def read_users_me(current_user: User = Depends(get_current_active_user)) -> Dict[str, Any]:
    """Get current user info."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id,
    }