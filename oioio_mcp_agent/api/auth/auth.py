"""
Authentication module for the OIOIO MCP Agent API.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from oioio_mcp_agent.api.db import get_db
from oioio_mcp_agent.api.models import APIKey, Tenant, User
from oioio_mcp_agent.config import Config

# Constants
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ALGORITHM = "HS256"
API_KEY_HEADER = "X-API-Key"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


class Token(BaseModel):
    """Token model."""

    access_token: str
    token_type: str
    expires_at: datetime


class TokenData(BaseModel):
    """Token data model."""

    sub: str
    tenant_id: str
    exp: datetime
    scopes: list[str] = []


def get_secret_key() -> str:
    """Get JWT secret key from config."""
    config = Config.load()
    secret_key = config.get("api", {}).get("jwt_secret")
    if not secret_key:
        # Use a default for development only
        return "insecure_jwt_secret_not_for_production"
    return secret_key


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def get_user(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email, User.is_active == True).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password."""
    user = get_user(db, email)
    if not user or not user.hashed_password:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Create JWT token
    encoded_jwt = jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)
    return encoded_jwt


def verify_api_key(db: Session, api_key: str) -> Optional[Union[User, Tenant]]:
    """Verify API key and return the associated user or tenant."""
    key = db.query(APIKey).filter(
        APIKey.key == api_key, 
        APIKey.is_active == True
    ).first()
    
    if not key:
        return None
    
    # Check if key is expired
    if key.expires_at and key.expires_at < datetime.utcnow():
        return None
    
    # Return the associated user
    return key.user


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
        
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        
        token_data = TokenData(
            sub=email,
            tenant_id=payload.get("tenant_id"),
            exp=payload.get("exp"),
            scopes=payload.get("scopes", []),
        )
    except JWTError:
        raise credentials_exception
    
    user = get_user(db, email=token_data.sub)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user