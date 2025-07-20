"""
Configuration schema definitions for validating YAML configurations.
"""

from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator


class DockerServiceConfig(BaseModel):
    """Configuration for a Docker service."""
    name: str = Field(description="Service name")
    image: str = Field(description="Docker image")
    port: Optional[int] = Field(None, description="Service port")
    environment: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Environment variables"
    )
    volumes: Optional[List[str]] = Field(
        default_factory=list,
        description="Volume mappings"
    )


class DockerConfig(BaseModel):
    """Docker configuration."""
    compose_file: str = Field("docker-compose.yml", description="Docker Compose file path")
    services: List[DockerServiceConfig] = Field(
        default_factory=list,
        description="Service configurations"
    )


class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: str = Field("openrouter", description="LLM provider name")
    model: str = Field("gemini-2.0-flash-lite", description="Default model name")
    temperature: float = Field(0.7, description="Sampling temperature")
    max_tokens: int = Field(500, description="Maximum tokens to generate")
    timeout: int = Field(30, description="API timeout in seconds")


class ScheduleConfig(BaseModel):
    """Schedule configuration."""
    type: str = Field(..., description="Schedule type (interval, cron)")
    value: Union[int, str] = Field(..., description="Schedule value (seconds or cron expr)")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        valid_types = ['interval', 'cron', 'once']
        if v not in valid_types:
            raise ValueError(f"Schedule type must be one of {valid_types}")
        return v


class FlowConfig(BaseModel):
    """Flow configuration."""
    name: str = Field(..., description="Flow name")
    schedule: Optional[str] = Field(None, description="Schedule specification")
    enabled: bool = Field(True, description="Whether the flow is enabled")
    tasks: List[str] = Field(..., description="List of tasks to execute")
    params: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Flow parameters"
    )


class TaskConfig(BaseModel):
    """Task configuration."""
    plugin: str = Field(..., description="Plugin to use for this task")
    params: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Task parameters"
    )
    retries: int = Field(0, description="Number of times to retry the task")
    depends_on: Optional[List[str]] = Field(
        default_factory=list, 
        description="Task dependencies"
    )


class AgentConfig(BaseModel):
    """Agent configuration."""
    name: str = Field(..., description="Agent name")
    enabled: bool = Field(True, description="Whether the agent is enabled")
    flows: List[Dict[str, Any]] = Field(..., description="Flows to run for this agent")


class CoreConfig(BaseModel):
    """Core configuration."""
    knowledge_dir: str = Field("knowledge", description="Knowledge directory path")
    checkpoint_dir: str = Field(".prefect", description="Checkpoint directory path")
    log_level: str = Field("INFO", description="Logging level")
    log_file: Optional[str] = Field(None, description="Log file path")


class Config(BaseModel):
    """Main configuration model."""
    version: str = Field("1.0", description="Configuration version")
    core: CoreConfig = Field(default_factory=CoreConfig, description="Core configuration")
    docker: DockerConfig = Field(default_factory=DockerConfig, description="Docker configuration")
    llm: LLMConfig = Field(default_factory=LLMConfig, description="LLM configuration")
    agents: List[AgentConfig] = Field(default_factory=list, description="Agent configurations")
    flows: Dict[str, FlowConfig] = Field(default_factory=dict, description="Flow configurations")
    tasks: Dict[str, TaskConfig] = Field(default_factory=dict, description="Task configurations")