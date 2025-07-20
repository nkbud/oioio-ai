"""
Configuration schemas for API.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, UUID4

from oioio_mcp_agent.api.models import ConfigurationType


class ConfigurationBase(BaseModel):
    """Base configuration schema."""

    name: str
    type: ConfigurationType
    description: Optional[str] = None
    is_active: bool = True


class ConfigurationCreate(ConfigurationBase):
    """Schema for configuration creation."""

    data: Dict[str, Any]
    parent_id: Optional[UUID4] = None
    tenant_id: UUID4


class ConfigurationUpdate(BaseModel):
    """Schema for configuration update."""

    name: Optional[str] = None
    description: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ConfigurationResponse(ConfigurationBase):
    """Response schema for configuration."""

    id: UUID4
    data: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None
    tenant_id: UUID4
    parent_id: Optional[UUID4] = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class KnowledgeFileBase(BaseModel):
    """Base knowledge file schema."""

    filename: str
    title: str
    path: str
    tags: List[str] = []


class KnowledgeFileCreate(KnowledgeFileBase):
    """Schema for knowledge file creation."""

    metadata: Dict[str, Any] = {}
    tenant_id: UUID4


class KnowledgeFileUpdate(BaseModel):
    """Schema for knowledge file update."""

    title: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeFileResponse(KnowledgeFileBase):
    """Response schema for knowledge file."""

    id: UUID4
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None
    tenant_id: UUID4

    class Config:
        """Pydantic config."""

        from_attributes = True


class AgentLogCreate(BaseModel):
    """Schema for agent log creation."""

    agent_name: str
    flow_name: Optional[str] = None
    task_name: Optional[str] = None
    level: str = "INFO"
    message: str
    metadata: Dict[str, Any] = {}
    tenant_id: UUID4


class AgentLogResponse(BaseModel):
    """Response schema for agent log."""

    id: UUID4
    agent_name: str
    flow_name: Optional[str] = None
    task_name: Optional[str] = None
    level: str
    message: str
    metadata: Dict[str, Any]
    created_at: datetime
    tenant_id: UUID4

    class Config:
        """Pydantic config."""

        from_attributes = True