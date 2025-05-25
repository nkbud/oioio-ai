"""
Schemas for the OIOIO MCP Agent API.
"""
from oioio_mcp_agent.api.schemas.auth import (GoogleAuthResponse, TokenData,
                                        TokenRequest, TokenResponse)
from oioio_mcp_agent.api.schemas.configuration import (AgentLogCreate,
                                                 AgentLogResponse,
                                                 ConfigurationBase,
                                                 ConfigurationCreate,
                                                 ConfigurationResponse,
                                                 ConfigurationUpdate,
                                                 KnowledgeFileBase,
                                                 KnowledgeFileCreate,
                                                 KnowledgeFileResponse,
                                                 KnowledgeFileUpdate)
from oioio_mcp_agent.api.schemas.user import (APIKeyBase, APIKeyCreate,
                                        APIKeyResponse, TenantBase,
                                        TenantCreate, TenantResponse,
                                        TenantUpdate, UserBase, UserCreate,
                                        UserResponse, UserUpdate)