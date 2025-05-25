"""
API routers for OIOIO MCP Agent.
"""
from oioio_mcp_agent.api.routers.agents import router as agents_router
from oioio_mcp_agent.api.routers.auth import router as auth_router
from oioio_mcp_agent.api.routers.knowledge import router as knowledge_router
from oioio_mcp_agent.api.routers.tenants import router as tenants_router
from oioio_mcp_agent.api.routers.users import router as users_router