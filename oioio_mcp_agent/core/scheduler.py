"""
Scheduling system for OIOIO MCP Agent.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from prefect import flow, get_client
from prefect.deployments import run_deployment
from prefect.server.schemas.schedules import IntervalSchedule, CronSchedule

from oioio_mcp_agent.config import ScheduleConfig


class Scheduler:
    """Scheduler for agent flows."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.logger = logging.getLogger("scheduler")
    
    async def create_schedule(self, schedule_config: ScheduleConfig) -> Union[IntervalSchedule, CronSchedule]:
        """
        Create a Prefect schedule from configuration.
        
        Args:
            schedule_config: Schedule configuration
            
        Returns:
            Prefect schedule
        """
        if schedule_config.type == "interval":
            interval_seconds = int(schedule_config.value)
            return IntervalSchedule(interval=interval_seconds)
        
        elif schedule_config.type == "cron":
            cron_expr = str(schedule_config.value)
            return CronSchedule(cron=cron_expr)
        
        elif schedule_config.type == "once":
            # Run once after a delay (in seconds)
            delay_seconds = int(schedule_config.value)
            start_date = datetime.now() + timedelta(seconds=delay_seconds)
            return IntervalSchedule(interval=86400, anchor_date=start_date)  # 1 day interval
        
        else:
            raise ValueError(f"Unknown schedule type: {schedule_config.type}")
    
    async def apply_schedules_to_deployment(self, deployment_name: str, schedule: Any) -> None:
        """
        Apply a schedule to a deployment.
        
        Args:
            deployment_name: Deployment name
            schedule: Prefect schedule
        """
        try:
            async with get_client() as client:
                # Update deployment schedule
                await client.update_deployment(
                    deployment_name=deployment_name,
                    schedule=schedule,
                    is_schedule_active=True,
                )
                
                self.logger.info(f"Applied schedule to deployment '{deployment_name}'")
        
        except Exception as e:
            self.logger.error(f"Failed to apply schedule to deployment '{deployment_name}': {e}")
    
    async def run_flow_on_schedule(self, 
                                 deployment_name: str, 
                                 schedule_config: ScheduleConfig,
                                 parameters: Optional[Dict[str, Any]] = None) -> None:
        """
        Run a flow on a schedule.
        
        Args:
            deployment_name: Deployment name
            schedule_config: Schedule configuration
            parameters: Flow parameters
        """
        try:
            if schedule_config.type == "interval":
                interval_seconds = int(schedule_config.value)
                
                while True:
                    # Run the flow
                    self.logger.info(f"Running flow '{deployment_name}'")
                    flow_run = await run_deployment(
                        name=deployment_name,
                        parameters=parameters or {},
                    )
                    
                    self.logger.info(f"Flow run '{flow_run.id}' started, waiting {interval_seconds}s for next run")
                    
                    # Wait for the next run
                    await asyncio.sleep(interval_seconds)
            
            elif schedule_config.type == "cron":
                # For cron schedules, we let Prefect handle it
                schedule = await self.create_schedule(schedule_config)
                await self.apply_schedules_to_deployment(deployment_name, schedule)
            
            elif schedule_config.type == "once":
                # Run once after a delay
                delay_seconds = int(schedule_config.value)
                
                self.logger.info(f"Waiting {delay_seconds}s before running flow '{deployment_name}'")
                await asyncio.sleep(delay_seconds)
                
                self.logger.info(f"Running flow '{deployment_name}'")
                flow_run = await run_deployment(
                    name=deployment_name,
                    parameters=parameters or {},
                )
                
                self.logger.info(f"Flow run '{flow_run.id}' started (one-time run)")
        
        except Exception as e:
            self.logger.error(f"Error in scheduling flow '{deployment_name}': {e}")
    
    async def run_deployment(self, 
                           deployment_name: str, 
                           parameters: Optional[Dict[str, Any]] = None,
                           wait_for_completion: bool = False) -> str:
        """
        Run a deployment immediately.
        
        Args:
            deployment_name: Deployment name
            parameters: Flow parameters
            wait_for_completion: Whether to wait for the flow to complete
            
        Returns:
            Flow run ID
        """
        try:
            # Run the deployment
            flow_run = await run_deployment(
                name=deployment_name,
                parameters=parameters or {},
            )
            
            run_id = flow_run.id
            self.logger.info(f"Started flow run '{run_id}' for deployment '{deployment_name}'")
            
            if wait_for_completion:
                # Wait for the flow to complete
                self.logger.info(f"Waiting for flow run '{run_id}' to complete")
                
                async with get_client() as client:
                    while True:
                        # Get flow run status
                        flow_run = await client.read_flow_run(run_id)
                        
                        if flow_run.state.is_completed():
                            self.logger.info(f"Flow run '{run_id}' completed successfully")
                            break
                        
                        if flow_run.state.is_failed():
                            self.logger.error(f"Flow run '{run_id}' failed: {flow_run.state.message}")
                            break
                        
                        # Wait before checking again
                        await asyncio.sleep(2)
            
            return run_id
        
        except Exception as e:
            self.logger.error(f"Failed to run deployment '{deployment_name}': {e}")
            raise