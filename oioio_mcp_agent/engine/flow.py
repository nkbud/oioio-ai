"""
Flow system for OIOIO MCP Agent.
"""

import logging
from typing import Any, Dict, List, Optional, Union, Callable, Type, TypeVar

from prefect import flow, get_run_logger
from prefect.filesystems import LocalFileSystem
from prefect.task_runners import SequentialTaskRunner

from oioio_mcp_agent.config import FlowConfig
from oioio_mcp_agent.engine.registry import FlowRegistry


F = TypeVar('F', bound='BaseFlow')


class BaseFlow:
    """Base class for flows."""
    
    flow_name: str
    flow_description: str = ""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the flow.
        
        Args:
            config: Flow configuration parameters
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"flow.{self.flow_name}")
    
    def setup(self) -> None:
        """Set up the flow before execution."""
        pass
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the flow.
        
        Args:
            **kwargs: Flow parameters
            
        Returns:
            Flow results
        """
        raise NotImplementedError("Subclasses must implement run()")
    
    def teardown(self) -> None:
        """Tear down the flow after execution."""
        pass


def register_flow(flow_name: Optional[str] = None, 
                 description: Optional[str] = None) -> Callable[[Type[F]], Type[F]]:
    """
    Register a flow class.
    
    This function can be used as a decorator.
    
    Args:
        flow_name: Name of the flow (default: class name)
        description: Description of the flow
        
    Returns:
        Decorator function
    """
    def decorator(cls: Type[F]) -> Type[F]:
        # Set flow name and description
        cls.flow_name = flow_name or cls.__name__
        if description:
            cls.flow_description = description
        
        # Create Prefect flow wrapper function
        @flow(
            name=cls.flow_name,
            description=cls.flow_description,
            task_runner=SequentialTaskRunner(),
            persist_result=True,
            result_storage=LocalFileSystem(basepath=".prefect/results"),
        )
        def prefect_flow_wrapper(**kwargs):
            logger = get_run_logger()
            logger.info(f"Starting flow: {cls.flow_name}")
            
            # Create and set up flow instance
            flow_instance = cls(kwargs.get("config", {}))
            flow_instance.setup()
            
            try:
                # Run the flow
                result = flow_instance.run(**kwargs)
                logger.info(f"Flow completed: {cls.flow_name}")
                return result
            finally:
                # Tear down the flow
                flow_instance.teardown()
        
        # Save the wrapper function as a class attribute
        cls._prefect_flow = prefect_flow_wrapper
        
        # Register the flow with the registry
        FlowRegistry.register(cls.flow_name, cls)
        
        return cls
    
    return decorator


def create_flow_from_config(flow_name: str, flow_config: FlowConfig) -> Optional[Callable]:
    """
    Create a flow function from configuration.
    
    Args:
        flow_name: Name of the flow
        flow_config: Flow configuration
        
    Returns:
        Flow function or None if not registered
    """
    flow_class = FlowRegistry.get(flow_name)
    if not flow_class:
        return None
    
    return flow_class._prefect_flow