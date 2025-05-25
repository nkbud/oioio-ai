"""
Tenants router for API.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from oioio_mcp_agent.api.auth import get_current_active_user
from oioio_mcp_agent.api.db import get_db
from oioio_mcp_agent.api.models import Tenant, User, UserRole
from oioio_mcp_agent.api.schemas.user import (TenantCreate, TenantResponse,
                                        TenantUpdate)

# Create router
router = APIRouter()


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[Tenant]:
    """List tenants."""
    # Only admins can list all tenants
    if current_user.role == UserRole.ADMIN:
        return db.query(Tenant).offset(skip).limit(limit).all()
    
    # Other users can only see their own tenant
    return [db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()]


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_create: TenantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Tenant:
    """Create tenant."""
    # Only admins can create tenants
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Check if tenant with slug already exists
    existing_tenant = db.query(Tenant).filter(Tenant.slug == tenant_create.slug).first()
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant with this slug already exists",
        )
    
    # Create new tenant
    db_tenant = Tenant(**tenant_create.model_dump())
    
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    
    return db_tenant


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Tenant:
    """Get tenant by ID."""
    # Check permissions
    if current_user.role != UserRole.ADMIN and str(current_user.tenant_id) != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    
    return tenant


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    tenant_update: TenantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Tenant:
    """Update tenant."""
    # Check permissions
    if current_user.role != UserRole.ADMIN and (
        current_user.role != UserRole.TENANT_ADMIN or
        str(current_user.tenant_id) != tenant_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    
    # Update tenant
    update_data = tenant_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tenant, key, value)
    
    db.commit()
    db.refresh(tenant)
    
    return tenant