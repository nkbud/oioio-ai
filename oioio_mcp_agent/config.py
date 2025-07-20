"""
Configuration module for OIOIO MCP Agent.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration model for the knowledge agent."""
    
    knowledge_dir: Path = Field(
        default=Path("knowledge"),
        description="Directory to store knowledge markdown files"
    )
    
    checkpoint_dir: Path = Field(
        default=Path(".prefect"),
        description="Directory to store agent state and checkpoints"
    )
    
    openrouter_api_key: Optional[str] = Field(
        default=None,
        description="API key for OpenRouter"
    )
    
    mcp_server_url: str = Field(
        default="http://localhost:8080",
        description="URL of the MCP Brave Search server"
    )
    
    llm_model: str = Field(
        default="gemini-2.0-flash-lite",
        description="Default LLM model to use with OpenRouter"
    )
    
    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Create config from environment variables."""
        return cls(
            knowledge_dir=Path(os.environ.get("MCP_KNOWLEDGE_DIR", "knowledge")),
            checkpoint_dir=Path(os.environ.get("MCP_CHECKPOINT_DIR", ".prefect")),
            openrouter_api_key=os.environ.get("OPENROUTER_API_KEY"),
            mcp_server_url=os.environ.get("MCP_SERVER_URL", "http://localhost:8080"),
            llm_model=os.environ.get("MCP_LLM_MODEL", "gemini-2.0-flash-lite"),
        )