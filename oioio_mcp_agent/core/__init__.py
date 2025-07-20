"""
Core package for OIOIO MCP Agent.
"""

from oioio_mcp_agent.core.agent import Agent, AgentManager
from oioio_mcp_agent.core.plugin import (
    Plugin,
    PluginRegistry,
    register_plugin,
    discover_plugins,
    get_registry,
    GapIdentifierPlugin,
    SearchPlugin,
    LLMPlugin,
    DocumentWriterPlugin
)
from oioio_mcp_agent.core.scheduler import Scheduler

__all__ = [
    'Agent',
    'AgentManager',
    'Plugin',
    'PluginRegistry',
    'register_plugin',
    'discover_plugins',
    'get_registry',
    'GapIdentifierPlugin',
    'SearchPlugin',
    'LLMPlugin',
    'DocumentWriterPlugin',
    'Scheduler',
]