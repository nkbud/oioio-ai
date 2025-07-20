"""
Task system for OIOIO MCP Agent.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from prefect import task

from oioio_mcp_agent.engine.registry import TaskRegistry


T = TypeVar('T', bound='BaseTask')


class BaseTask:
    """Base class for tasks."""
    
    task_name: str
    task_description: str = ""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the task.
        
        Args:
            config: Task configuration parameters
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"task.{self.task_name}")
    
    def run(self, **kwargs) -> Any:
        """
        Run the task.
        
        Args:
            **kwargs: Task parameters
            
        Returns:
            Task result
        """
        raise NotImplementedError("Subclasses must implement run()")


def register_task(task_name: Optional[str] = None, 
                 description: Optional[str] = None,
                 retries: int = 0,
                 retry_delay_seconds: Optional[int] = None,
                 **task_options) -> Callable[[Type[T]], Type[T]]:
    """
    Register a task class.
    
    This function can be used as a decorator.
    
    Args:
        task_name: Name of the task (default: class name)
        description: Description of the task
        retries: Number of times to retry the task
        retry_delay_seconds: Delay between retries in seconds
        **task_options: Additional options for Prefect task
        
    Returns:
        Decorator function
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # Set task name and description
        cls.task_name = task_name or cls.__name__
        if description:
            cls.task_description = description
        
        # Create Prefect task wrapper function
        @task(
            name=cls.task_name,
            description=cls.task_description,
            retries=retries,
            retry_delay_seconds=retry_delay_seconds,
            **task_options
        )
        def prefect_task_wrapper(**kwargs):
            # Create task instance
            task_config = kwargs.pop("config", {})
            task_instance = cls(task_config)
            
            # Run the task
            return task_instance.run(**kwargs)
        
        # Save the wrapper function as a class attribute
        cls._prefect_task = prefect_task_wrapper
        
        # Register the task with the registry
        TaskRegistry.register(cls.task_name, cls)
        
        return cls
    
    return decorator


def create_task(task_name: str, config: Optional[Dict[str, Any]] = None) -> Optional[Callable]:
    """
    Create a task function from registry.
    
    Args:
        task_name: Name of the task
        config: Task configuration
        
    Returns:
        Task function or None if not registered
    """
    task_class = TaskRegistry.get(task_name)
    if not task_class:
        return None
    
    if config:
        # Create a new wrapper that includes the config
        @task(name=task_name)
        def configured_task_wrapper(**kwargs):
            # Include config in kwargs
            kwargs["config"] = config
            return task_class._prefect_task(**kwargs)
        
        return configured_task_wrapper
    
    return task_class._prefect_task