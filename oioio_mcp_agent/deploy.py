"""
Deployment utilities for the MCP Knowledge Agent.
"""

import logging
from typing import Optional

from prefect.deployments import Deployment
from prefect.server.schemas.schedules import IntervalSchedule

from oioio_mcp_agent.flows.knowledge_flow import knowledge_agent_flow
from oioio_mcp_agent.config import AgentConfig


def create_deployment(
    name: str = "mcp-knowledge-agent",
    schedule_interval_seconds: Optional[int] = None,
    config: Optional[AgentConfig] = None,
    prompt: str = "Identify key knowledge gaps about MCP servers",
) -> Deployment:
    """
    Create a deployment for the MCP Knowledge Agent flow.
    
    Args:
        name: Name for the deployment
        schedule_interval_seconds: Interval in seconds to schedule the flow, None for no schedule
        config: Agent configuration
        prompt: Prompt to guide knowledge gap identification
    
    Returns:
        Prefect Deployment object
    """
    deployment_kwargs = {
        "flow": knowledge_agent_flow,
        "name": name,
        "parameters": {
            "config": config.model_dump() if config else None,
            "prompt": prompt,
        },
        "tags": ["mcp", "knowledge", "agent"],
    }
    
    # Add schedule if interval is specified
    if schedule_interval_seconds:
        deployment_kwargs["schedule"] = IntervalSchedule(
            interval=schedule_interval_seconds,
            anchor_date=None  # Use current time as anchor
        )
    
    return Deployment(**deployment_kwargs)


def deploy() -> None:
    """Create and apply deployment for the MCP Knowledge Agent flow."""
    deployment = create_deployment()
    deployment_id = deployment.apply()
    print(f"Created deployment with ID: {deployment_id}")
    print("You can run this deployment with the following command:")
    print(f"prefect deployment run {deployment.name}")


if __name__ == "__main__":
    deploy()