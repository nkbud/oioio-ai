"""
Knowledge router for API.
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from oioio_mcp_agent.api.auth import get_current_active_user
from oioio_mcp_agent.api.db import get_db
from oioio_mcp_agent.api.models import KnowledgeFile, User
from oioio_mcp_agent.api.schemas.configuration import (KnowledgeFileCreate,
                                                 KnowledgeFileResponse,
                                                 KnowledgeFileUpdate)
from oioio_mcp_agent.config import Config

# Create router
router = APIRouter()


@router.get("/", response_model=List[KnowledgeFileResponse])
async def list_knowledge_files(
    skip: int = 0,
    limit: int = 100,
    tags: Optional[str] = Query(None, description="Comma-separated list of tags to filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[KnowledgeFile]:
    """List knowledge files."""
    query = db.query(KnowledgeFile).filter(
        KnowledgeFile.tenant_id == current_user.tenant_id
    )
    
    # Filter by tags if provided
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        # Note: This is a simple implementation that works for PostgreSQL
        # For other databases, you might need a different approach
        query = query.filter(KnowledgeFile.tags.contains(tag_list))
    
    files = query.order_by(KnowledgeFile.created_at.desc()).offset(skip).limit(limit).all()
    
    return files


@router.post("/", response_model=KnowledgeFileResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_file(
    file: UploadFile = File(...),
    title: str = Query(..., description="Title of the knowledge file"),
    tags: str = Query("", description="Comma-separated list of tags"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> KnowledgeFile:
    """Create a new knowledge file by uploading a file."""
    # Get knowledge directory from config
    config = Config.load()
    knowledge_dir = config.get("core", {}).get("knowledge_dir", "knowledge")
    
    # Ensure directory exists
    tenant_dir = Path(knowledge_dir) / str(current_user.tenant_id)
    tenant_dir.mkdir(exist_ok=True, parents=True)
    
    # Process filename and ensure it's safe
    filename = file.filename
    safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
    
    # Add timestamp to ensure uniqueness
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_filename = f"{timestamp}_{safe_filename}"
    
    # Save file
    file_path = tenant_dir / unique_filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Process tags
    tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
    
    # Create database record
    db_file = KnowledgeFile(
        filename=unique_filename,
        title=title,
        path=str(file_path),
        tags=tag_list,
        tenant_id=current_user.tenant_id,
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return db_file


@router.get("/{file_id}", response_model=KnowledgeFileResponse)
async def get_knowledge_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> KnowledgeFile:
    """Get knowledge file metadata."""
    # Get file
    file = db.query(KnowledgeFile).filter(
        KnowledgeFile.id == file_id,
        KnowledgeFile.tenant_id == current_user.tenant_id,
    ).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    return file


@router.get("/{file_id}/download")
async def download_knowledge_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileResponse:
    """Download knowledge file content."""
    # Get file
    file = db.query(KnowledgeFile).filter(
        KnowledgeFile.id == file_id,
        KnowledgeFile.tenant_id == current_user.tenant_id,
    ).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    # Check if file exists
    if not os.path.exists(file.path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk",
        )
    
    return FileResponse(
        path=file.path,
        filename=file.filename,
        media_type="application/octet-stream"
    )


@router.patch("/{file_id}", response_model=KnowledgeFileResponse)
async def update_knowledge_file(
    file_id: str,
    file_update: KnowledgeFileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> KnowledgeFile:
    """Update knowledge file metadata."""
    # Get file
    file = db.query(KnowledgeFile).filter(
        KnowledgeFile.id == file_id,
        KnowledgeFile.tenant_id == current_user.tenant_id,
    ).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    # Update file
    update_data = file_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(file, key, value)
    
    db.commit()
    db.refresh(file)
    
    return file


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete knowledge file."""
    # Get file
    file = db.query(KnowledgeFile).filter(
        KnowledgeFile.id == file_id,
        KnowledgeFile.tenant_id == current_user.tenant_id,
    ).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    # Delete file from disk
    if os.path.exists(file.path):
        os.remove(file.path)
    
    # Delete database record
    db.delete(file)
    db.commit()