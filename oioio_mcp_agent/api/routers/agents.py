"""
Agents router for API.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import UUID4
from sqlalchemy.orm import Session

from oioio_mcp_agent.api.auth import get_current_active_user
from oioio_mcp_agent.api.db import get_db
from oioio_mcp_agent.api.models import AgentLog, Configuration, User, UserRole
from oioio_mcp_agent.api.schemas.configuration import (AgentLogCreate,
                                                 AgentLogResponse,
                                                 ConfigurationCreate,
                                                 ConfigurationResponse,
                                                 ConfigurationUpdate)
from oioio_mcp_agent.core import AgentManager
from oioio_mcp_agent.config import Config

# Create router
router = APIRouter()

# Setup logger
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[Dict[str, Any]])
async def list_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[Dict[str, Any]]:
    """List all agents for a tenant."""
    # Get agent configurations
    agent_configs = db.query(Configuration).filter(
        Configuration.tenant_id == current_user.tenant_id,
        Configuration.type == "agent",
    ).all()
    
    # Get agent status from manager
    agent_manager = AgentManager()
    
    result = []
    for config in agent_configs:
        agent_id = str(config.id)
        agent_name = config.name
        agent_data = config.data
        
        # Get agent status
        is_running = agent_manager.is_agent_running(agent_id)
        
        result.append({
            "id": agent_id,
            "name": agent_name,
            "description": config.description,
            "is_running": is_running,
            "is_active": config.is_active,
            "config": agent_data,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
        })
    
    return result


@router.post("/", response_model=ConfigurationResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_config: ConfigurationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Configuration:
    """Create a new agent configuration."""
    # Ensure type is "agent"
    if agent_config.type != "agent":
        agent_config.type = "agent"
    
    # Create configuration
    db_config = Configuration(**agent_config.model_dump())
    
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    return db_config


@router.get("/{agent_id}", response_model=Dict[str, Any])
async def get_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get agent details."""
    # Get agent configuration
    agent_config = db.query(Configuration).filter(
        Configuration.id == agent_id,
        Configuration.tenant_id == current_user.tenant_id,
        Configuration.type == "agent",
    ).first()
    
    if not agent_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    
    # Get agent status from manager
    agent_manager = AgentManager()
    is_running = agent_manager.is_agent_running(agent_id)
    
    # Get recent logs
    logs = db.query(AgentLog).filter(
        AgentLog.agent_name == agent_config.name,
        AgentLog.tenant_id == current_user.tenant_id,
    ).order_by(AgentLog.created_at.desc()).limit(10).all()
    
    return {
        "id": str(agent_config.id),
        "name": agent_config.name,
        "description": agent_config.description,
        "is_running": is_running,
        "is_active": agent_config.is_active,
        "config": agent_config.data,
        "created_at": agent_config.created_at,
        "updated_at": agent_config.updated_at,
        "recent_logs": [
            {
                "id": str(log.id),
                "level": log.level,
                "message": log.message,
                "flow_name": log.flow_name,
                "task_name": log.task_name,
                "created_at": log.created_at,
            }
            for log in logs
        ]
    }


@router.patch("/{agent_id}", response_model=ConfigurationResponse)
async def update_agent(
    agent_id: str,
    agent_update: ConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Configuration:
    """Update agent configuration."""
    # Get agent configuration
    agent_config = db.query(Configuration).filter(
        Configuration.id == agent_id,
        Configuration.tenant_id == current_user.tenant_id,
        Configuration.type == "agent",
    ).first()
    
    if not agent_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    
    # Update configuration
    update_data = agent_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(agent_config, key, value)
    
    db.commit()
    db.refresh(agent_config)
    
    return agent_config


@router.post("/{agent_id}/start", response_model=Dict[str, Any])
async def start_agent(
    agent_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Start an agent."""
    # Get agent configuration
    agent_config = db.query(Configuration).filter(
        Configuration.id == agent_id,
        Configuration.tenant_id == current_user.tenant_id,
        Configuration.type == "agent",
    ).first()
    
    if not agent_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    
    # Check if agent is already running
    agent_manager = AgentManager()
    if agent_manager.is_agent_running(agent_id):
        return {
            "message": f"Agent '{agent_config.name}' is already running",
            "agent_id": agent_id,
            "status": "running",
        }
    
    # Start agent in background
    background_tasks.add_task(
        agent_manager.start_agent,
        agent_id=agent_id,
        agent_config=agent_config.data,
        tenant_id=str(current_user.tenant_id),
    )
    
    # Log agent start
    db.add(AgentLog(
        agent_name=agent_config.name,
        level="INFO",
        message=f"Agent started by user {current_user.username}",
        tenant_id=current_user.tenant_id,
    ))
    db.commit()
    
    return {
        "message": f"Agent '{agent_config.name}' started",
        "agent_id": agent_id,
        "status": "starting",
    }


@router.post("/{agent_id}/stop", response_model=Dict[str, Any])
async def stop_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Stop an agent."""
    # Get agent configuration
    agent_config = db.query(Configuration).filter(
        Configuration.id == agent_id,
        Configuration.tenant_id == current_user.tenant_id,
        Configuration.type == "agent",
    ).first()
    
    if not agent_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    
    # Stop agent
    agent_manager = AgentManager()
    success = agent_manager.stop_agent(agent_id)
    
    if success:
        # Log agent stop
        db.add(AgentLog(
            agent_name=agent_config.name,
            level="INFO",
            message=f"Agent stopped by user {current_user.username}",
            tenant_id=current_user.tenant_id,
        ))
        db.commit()
        
        return {
            "message": f"Agent '{agent_config.name}' stopped",
            "agent_id": agent_id,
            "status": "stopped",
        }
    else:
        return {
            "message": f"Agent '{agent_config.name}' is not running",
            "agent_id": agent_id,
            "status": "not_running",
        }


@router.get("/{agent_id}/logs", response_model=List[AgentLogResponse])
async def get_agent_logs(
    agent_id: str,
    skip: int = 0,
    limit: int = 100,
    level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[AgentLog]:
    """Get agent logs."""
    # Get agent configuration
    agent_config = db.query(Configuration).filter(
        Configuration.id == agent_id,
        Configuration.tenant_id == current_user.tenant_id,
        Configuration.type == "agent",
    ).first()
    
    if not agent_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    
    # Query logs
    query = db.query(AgentLog).filter(
        AgentLog.agent_name == agent_config.name,
        AgentLog.tenant_id == current_user.tenant_id,
    )
    
    if level:
        query = query.filter(AgentLog.level == level)
    
    logs = query.order_by(AgentLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return logs