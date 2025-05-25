"""
Authentication module for the OIOIO MCP Agent API.
"""
from oioio_mcp_agent.api.auth.auth import (ACCESS_TOKEN_EXPIRE_MINUTES,
                                     ALGORITHM, API_KEY_HEADER, Token,
                                     TokenData, authenticate_user,
                                     create_access_token,
                                     get_current_active_user,
                                     get_current_user, get_password_hash,
                                     get_user, oauth2_scheme,
                                     verify_api_key, verify_password)
from oioio_mcp_agent.api.auth.oauth import (authenticate_user_google,
                                      get_oauth_redirect_url,
                                      get_session_middleware, oauth)