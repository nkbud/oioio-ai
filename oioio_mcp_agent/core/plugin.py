"""
Plugin system for OIOIO MCP Agent.

This module provides base classes and registration mechanisms for plugins.
"""

import abc
import importlib
import inspect
import pkgutil
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Union


T = TypeVar('T')


class Plugin(abc.ABC):
    """Base plugin interface."""
    
    # Class variables to be defined by subclasses
    plugin_type: str
    plugin_name: str
    
    def __init__(self, **kwargs):
        """
        Initialize the plugin.
        
        Args:
            **kwargs: Plugin configuration parameters
        """
        self.config = kwargs
    
    def get_name(self) -> str:
        """Get plugin name."""
        return self.plugin_name
    
    def get_type(self) -> str:
        """Get plugin type."""
        return self.plugin_type


class PluginRegistry(Generic[T]):
    """Registry for plugins of a specific type."""
    
    def __init__(self, plugin_type: str):
        """
        Initialize the registry.
        
        Args:
            plugin_type: Type of plugins to register
        """
        self.plugin_type = plugin_type
        self.plugins: Dict[str, Type[T]] = {}
        
    def register(self, plugin_class: Type[T]) -> Type[T]:
        """
        Register a plugin class.
        
        Args:
            plugin_class: Plugin class to register
            
        Returns:
            The registered plugin class
        """
        if not hasattr(plugin_class, 'plugin_name'):
            raise ValueError(f"Plugin class {plugin_class.__name__} missing plugin_name")
        
        if not hasattr(plugin_class, 'plugin_type'):
            raise ValueError(f"Plugin class {plugin_class.__name__} missing plugin_type")
            
        if plugin_class.plugin_type != self.plugin_type:
            raise ValueError(f"Plugin type mismatch: {plugin_class.plugin_type} != {self.plugin_type}")
            
        name = plugin_class.plugin_name
        self.plugins[name] = plugin_class
        return plugin_class
        
    def get(self, name: str) -> Optional[Type[T]]:
        """
        Get a plugin class by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin class or None if not found
        """
        return self.plugins.get(name)
    
    def create(self, name: str, **kwargs) -> T:
        """
        Create a plugin instance by name.
        
        Args:
            name: Plugin name
            **kwargs: Plugin configuration parameters
            
        Returns:
            Plugin instance
        """
        plugin_class = self.get(name)
        if plugin_class is None:
            raise ValueError(f"Plugin not found: {name} (type: {self.plugin_type})")
        return plugin_class(**kwargs)
    
    def list_plugins(self) -> List[str]:
        """
        List registered plugin names.
        
        Returns:
            List of plugin names
        """
        return list(self.plugins.keys())


# Global registry of plugin registries, indexed by plugin type
_registries: Dict[str, PluginRegistry] = {}


def get_registry(plugin_type: str) -> PluginRegistry:
    """
    Get or create a plugin registry for a specific plugin type.
    
    Args:
        plugin_type: Type of plugins to register
        
    Returns:
        Plugin registry
    """
    if plugin_type not in _registries:
        _registries[plugin_type] = PluginRegistry(plugin_type)
    return _registries[plugin_type]


def register_plugin(cls: Type[Plugin]) -> Type[Plugin]:
    """
    Register a plugin class.
    
    This function can be used as a decorator.
    
    Args:
        cls: Plugin class to register
        
    Returns:
        The registered plugin class
    """
    registry = get_registry(cls.plugin_type)
    return registry.register(cls)


def discover_plugins(package: str) -> None:
    """
    Discover and register plugins in a package.
    
    Args:
        package: Package name to scan for plugins
    """
    try:
        package_module = importlib.import_module(package)
    except ImportError:
        return
    
    # Iterate over all modules in the package
    for _, name, is_pkg in pkgutil.iter_modules(package_module.__path__, package_module.__name__ + "."):
        try:
            # Import the module
            module = importlib.import_module(name)
            
            # If it's a package, recursively discover plugins
            if is_pkg:
                discover_plugins(name)
                
            # Find all plugin classes in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                # Check if it's a class that inherits from Plugin
                if (inspect.isclass(attr) and 
                    issubclass(attr, Plugin) and 
                    attr is not Plugin and
                    hasattr(attr, 'plugin_type') and
                    hasattr(attr, 'plugin_name')):
                    
                    # Register the plugin
                    registry = get_registry(attr.plugin_type)
                    registry.register(attr)
        
        except Exception as e:
            print(f"Error discovering plugins in {name}: {e}")


# Concrete plugin interfaces

class GapIdentifierPlugin(Plugin, abc.ABC):
    """Interface for knowledge gap identification plugins."""
    
    plugin_type = "gap_identifier"
    
    @abc.abstractmethod
    def identify_gaps(self, knowledge_dir: str, prompt: str, max_gaps: int) -> List[str]:
        """
        Identify knowledge gaps.
        
        Args:
            knowledge_dir: Directory containing knowledge files
            prompt: Prompt to guide gap identification
            max_gaps: Maximum number of gaps to identify
            
        Returns:
            List of identified knowledge gaps
        """
        pass


class SearchPlugin(Plugin, abc.ABC):
    """Interface for search plugins."""
    
    plugin_type = "search"
    
    @abc.abstractmethod
    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform a search.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results
        """
        pass


class LLMPlugin(Plugin, abc.ABC):
    """Interface for LLM plugins."""
    
    plugin_type = "llm"
    
    @abc.abstractmethod
    def generate(self, 
                system_message: str, 
                user_message: str, 
                temperature: float = 0.7,
                max_tokens: int = 500) -> str:
        """
        Generate text using an LLM.
        
        Args:
            system_message: System message
            user_message: User message
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        pass


class DocumentWriterPlugin(Plugin, abc.ABC):
    """Interface for document writer plugins."""
    
    plugin_type = "document_writer"
    
    @abc.abstractmethod
    def write(self, content: str, filename: str, directory: str) -> str:
        """
        Write content to a file.
        
        Args:
            content: Content to write
            filename: Filename
            directory: Directory to write to
            
        Returns:
            Path to the written file
        """
        pass