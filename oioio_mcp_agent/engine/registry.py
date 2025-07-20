"""
Registry for flows and tasks.
"""

from typing import Any, Callable, Dict, List, Optional, Type


class Registry:
    """Base class for registries."""
    
    def __init__(self, registry_type: str):
        """
        Initialize the registry.
        
        Args:
            registry_type: Type of registry
        """
        self.registry_type = registry_type
        self.items: Dict[str, Type] = {}
    
    def register(self, name: str, item: Type) -> None:
        """
        Register an item.
        
        Args:
            name: Item name
            item: Item class
        """
        self.items[name] = item
    
    def get(self, name: str) -> Optional[Type]:
        """
        Get an item by name.
        
        Args:
            name: Item name
            
        Returns:
            Item class or None if not found
        """
        return self.items.get(name)
    
    def list(self) -> List[str]:
        """
        List registered item names.
        
        Returns:
            List of item names
        """
        return list(self.items.keys())


class FlowRegistryClass(Registry):
    """Registry for flows."""
    
    def __init__(self):
        """Initialize the flow registry."""
        super().__init__("flow")


class TaskRegistryClass(Registry):
    """Registry for tasks."""
    
    def __init__(self):
        """Initialize the task registry."""
        super().__init__("task")


# Global registries
FlowRegistry = FlowRegistryClass()
TaskRegistry = TaskRegistryClass()