"""
Agent system for OIOIO MCP Agent.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Callable

from prefect import get_client
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import IntervalSchedule, CronSchedule

from oioio_mcp_agent.config import AgentConfig
from oioio_mcp_agent.engine.flow import create_flow_from_config


class Agent:
    """Agent that manages flows."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize the agent.
        
        Args:
            name: Agent name
            config: Agent configuration
        """
        self.name = name
        self.config = config
        self.flows: List[Dict[str, Any]] = config.get("flows", [])
        self.enabled = config.get("enabled", True)
        self.logger = logging.getLogger(f"agent.{name}")
    
    async def create_deployments(self) -> List[str]:
        """
        Create deployments for all flows.
        
        Returns:
            List of deployment IDs
        """
        if not self.enabled:
            self.logger.info(f"Agent '{self.name}' is disabled, skipping deployment creation")
            return []
        
        deployment_ids = []
        
        for flow_config in self.flows:
            flow_name = flow_config.get("name")
            if not flow_name:
                self.logger.warning(f"Flow name not specified in agent '{self.name}', skipping")
                continue
                
            # Create flow function from config
            flow_fn = create_flow_from_config(flow_name, flow_config)
            if not flow_fn:
                self.logger.warning(f"Flow '{flow_name}' not found in registry, skipping")
                continue
            
            # Create schedule if specified
            schedule = self._create_schedule(flow_config.get("schedule"))
            
            # Create deployment
            try:
                deployment = Deployment(
                    name=f"{self.name}-{flow_name}",
                    flow_name=flow_name,
                    schedule=schedule,
                    parameters=flow_config.get("params", {}),
                    tags=[self.name, flow_name],
                    is_schedule_active=self.enabled and flow_config.get("enabled", True),
                )
                
                # Apply the deployment
                self.logger.info(f"Creating deployment for flow '{flow_name}'")
                
                async with get_client() as client:
                    deployment_id = await deployment.apply(client)
                    deployment_ids.append(deployment_id)
                    self.logger.info(f"Created deployment '{deployment_id}' for flow '{flow_name}'")
            
            except Exception as e:
                self.logger.error(f"Failed to create deployment for flow '{flow_name}': {e}")
        
        return deployment_ids
    
    async def start(self) -> None:
        """Start the agent."""
        if not self.enabled:
            self.logger.info(f"Agent '{self.name}' is disabled, not starting")
            return
        
        self.logger.info(f"Starting agent '{self.name}'")
        
        # Create deployments for all flows
        await self.create_deployments()
    
    async def stop(self) -> None:
        """Stop the agent."""
        self.logger.info(f"Stopping agent '{self.name}'")
    
    def _create_schedule(self, schedule_spec: Optional[str]) -> Optional[Any]:
        """
        Create a schedule from a specification.
        
        Args:
            schedule_spec: Schedule specification (e.g., "interval:3600" or "cron:0 0 * * *")
            
        Returns:
            Schedule object or None if not specified
        """
        if not schedule_spec:
            return None
        
        try:
            schedule_type, value = schedule_spec.split(":", 1)
            
            if schedule_type == "interval":
                interval = int(value)
                return IntervalSchedule(interval=interval)
            
            elif schedule_type == "cron":
                return CronSchedule(cron=value)
            
            else:
                self.logger.warning(f"Unknown schedule type '{schedule_type}', ignoring")
                return None
        
        except Exception as e:
            self.logger.error(f"Failed to parse schedule '{schedule_spec}': {e}")
            return None


class AgentManager:
    """Manager for multiple agents."""
    
    def __init__(self):
        """Initialize the agent manager."""
        self.agents: Dict[str, Agent] = {}
        self.logger = logging.getLogger("agent_manager")
    
    def load_agents_from_config(self, agent_configs: List[Dict[str, Any]]) -> None:
        """
        Load agents from configuration.
        
        Args:
            agent_configs: List of agent configurations
        """
        for agent_config in agent_configs:
            name = agent_config.get("name", f"agent-{len(self.agents)}")
            self.agents[name] = Agent(name, agent_config)
            self.logger.info(f"Loaded agent '{name}' with {len(agent_config.get('flows', []))} flows")
    
    async def start_all_agents(self) -> None:
        """Start all agents."""
        for name, agent in self.agents.items():
            await agent.start()
    
    async def stop_all_agents(self) -> None:
        """Stop all agents."""
        for name, agent in self.agents.items():
            await agent.stop()