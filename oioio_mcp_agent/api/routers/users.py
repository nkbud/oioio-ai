"""
Users router for API.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from oioio_mcp_agent.api.auth import get_current_active_user, get_password_hash
from oioio_mcp_agent.api.db import get_db
from oioio_mcp_agent.api.models import Tenant, User, UserRole
from oioio_mcp_agent.api.schemas.user import (UserCreate, UserResponse,
                                        UserUpdate)

# Create router
router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    tenant_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[User]:
    """List users."""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.TENANT_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    query = db.query(User)
    
    # Filter by tenant
    if tenant_id:
        query = query.filter(User.tenant_id == tenant_id)
    elif current_user.role == UserRole.TENANT_ADMIN:
        # Tenant admins can only see users in their tenant
        query = query.filter(User.tenant_id == current_user.tenant_id)
    
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Create user."""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.TENANT_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Tenant admins can only create users in their tenant
    if current_user.role == UserRole.TENANT_ADMIN and user_create.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create users in other tenants",
        )
    
    # Check if user with email already exists
    existing_user = db.query(User).filter(User.email == user_create.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    
    # Check if tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == user_create.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant not found",
        )
    
    # Create new user
    hashed_password = get_password_hash(user_create.password)
    db_user = User(
        **user_create.model_dump(exclude={"password"}),
        hashed_password=hashed_password,
        is_active=True,
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get user by ID."""
    # Users can get their own details
    if str(current_user.id) == user_id:
        return current_user
    
    # Check permissions for other users
    if current_user.role not in [UserRole.ADMIN, UserRole.TENANT_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Tenant admins can only see users in their tenant
    if current_user.role == UserRole.TENANT_ADMIN and user.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Update user."""
    # Users can update their own details
    is_self_update = str(current_user.id) == user_id
    
    # Check permissions for other users
    if not is_self_update and current_user.role not in [UserRole.ADMIN, UserRole.TENANT_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Tenant admins can only update users in their tenant
    if (not is_self_update and
        current_user.role == UserRole.TENANT_ADMIN and 
        user.tenant_id != current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Users can't change their role
    if is_self_update and user_update.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change own role",
        )
    
    # Update user
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    
    return user