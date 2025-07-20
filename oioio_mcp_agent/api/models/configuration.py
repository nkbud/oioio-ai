"""
Configuration models for storing tenant-specific settings.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from oioio_mcp_agent.api.db.base import Base


class ConfigurationType(str, Enum):
    """Configuration type enum."""

    SYSTEM = "system"
    AGENT = "agent"
    FLOW = "flow"
    TASK = "task"
    LLM = "llm"
    DOCKER = "docker"
    CUSTOM = "custom"


class Configuration(Base):
    """Configuration model for storing settings."""

    __tablename__ = "configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    type = Column(SQLEnum(ConfigurationType), nullable=False, default=ConfigurationType.CUSTOM)
    description = Column(Text, nullable=True)
    data = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Tenant relationship
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    tenant = relationship("Tenant", back_populates="configurations")
    
    # For nested configurations
    parent_id = Column(UUID(as_uuid=True), ForeignKey("configurations.id"), nullable=True)
    children = relationship("Configuration", backref="parent", remote_side=[id])


class KnowledgeFile(Base):
    """Knowledge file model for storing metadata."""

    __tablename__ = "knowledge_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    path = Column(String(512), nullable=False)
    tags = Column(JSON, nullable=True, default=list)
    metadata = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Tenant relationship
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)


class AgentLog(Base):
    """Agent log model for storing execution logs."""

    __tablename__ = "agent_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(100), nullable=False)
    flow_name = Column(String(100), nullable=True)
    task_name = Column(String(100), nullable=True)
    level = Column(String(20), nullable=False, default="INFO")
    message = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Tenant relationship
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)