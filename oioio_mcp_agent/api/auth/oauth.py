"""
OAuth2 authentication for Google.
"""
import json
import os
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlencode

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from starlette.config import Config as StarletteConfig
from starlette.middleware.sessions import SessionMiddleware

from oioio_mcp_agent.api.db import get_db
from oioio_mcp_agent.api.models import Tenant, User, UserRole
from oioio_mcp_agent.config import Config

# Load config
config = Config.load()
oauth_config = config.get("api", {}).get("oauth", {})

# OAuth configuration
starlette_config = StarletteConfig(environ=os.environ)
oauth = OAuth(starlette_config)

# Google OAuth setup
oauth.register(
    name="google",
    client_id=oauth_config.get("google_client_id", ""),
    client_secret=oauth_config.get("google_client_secret", ""),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def get_oauth_redirect_url(request: Request) -> str:
    """Get OAuth redirect URL."""
    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}/api/auth/callback/google"


async def authenticate_user_google(
    request: Request, db: Session = Depends(get_db)
) -> Tuple[User, bool]:
    """Authenticate user with Google OAuth."""
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not fetch user info from Google",
        )
    
    # Get user email
    email = user_info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not provided by Google",
        )
    
    # Find user by Google ID or email
    google_id = user_info.get("sub")
    user = (
        db.query(User)
        .filter(
            (User.google_id == google_id) | (User.email == email),
            User.is_active == True,
        )
        .first()
    )
    
    is_new_user = False
    if not user:
        # Create new user
        is_new_user = True
        
        # Find or create default tenant
        default_tenant = db.query(Tenant).filter(Tenant.slug == "default").first()
        if not default_tenant:
            default_tenant = Tenant(
                name="Default Tenant",
                slug="default",
                description="Default tenant for new users",
            )
            db.add(default_tenant)
            db.flush()
        
        # Create user
        user = User(
            email=email,
            username=email.split("@")[0],  # Simple username from email
            first_name=user_info.get("given_name"),
            last_name=user_info.get("family_name"),
            google_id=google_id,
            is_active=True,
            is_verified=user_info.get("email_verified", False),
            role=UserRole.USER,
            tenant_id=default_tenant.id,
        )
        db.add(user)
        
    else:
        # Update existing user
        user.google_id = google_id
        user.is_verified = user_info.get("email_verified", False)
        user.first_name = user_info.get("given_name", user.first_name)
        user.last_name = user_info.get("family_name", user.last_name)
        user.last_login = datetime.utcnow()
    
    db.commit()
    return user, is_new_user


def get_session_middleware() -> SessionMiddleware:
    """Get session middleware."""
    secret_key = config.get("api", {}).get("session_secret", "insecure_session_key")
    return SessionMiddleware(None, secret_key=secret_key)