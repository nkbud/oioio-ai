"""
MCP (Model Context Protocol) client for interacting with MCP servers.

This module provides a client implementation for connecting to and 
interacting with MCP servers, specifically the Brave Search server.
"""

import logging
from typing import Dict, List, Any, Optional

import requests


class MCPClient:
    """
    Client for interacting with MCP servers via the Model Context Protocol.
    
    This client handles the connection handshake and communication with
    MCP servers such as the Brave Search server for web search capabilities.
    """
    
    def __init__(self, server_url: str = "http://localhost:8080"):
        """
        Initialize the MCP client.
        
        Args:
            server_url: URL of the MCP server
        """
        self.server_url = server_url
        self.logger = logging.getLogger("mcp_client")
        self.session_id = None
        self.capabilities = {}
        
    def connect(self) -> bool:
        """
        Connect to the MCP server and perform the initial handshake.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Initial handshake with the MCP server
            response = requests.post(
                f"{self.server_url}/handshake", 
                json={
                    "client_name": "oioio_mcp_agent",
                    "client_version": "0.1.0",
                }
            )
            
            if response.status_code != 200:
                self.logger.error(f"Failed to connect to MCP server: {response.status_code}")
                return False
            
            data = response.json()
            self.session_id = data.get("session_id")
            self.capabilities = data.get("capabilities", {})
            
            self.logger.info(f"Connected to MCP server: {self.server_url}")
            self.logger.debug(f"Server capabilities: {self.capabilities}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting to MCP server: {e}")
            return False
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform a web search using the Brave Search MCP server.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results, each as a dictionary with title, snippet, and url
        """
        if not self.session_id:
            self.logger.error("Not connected to MCP server. Call connect() first.")
            return []
        
        try:
            response = requests.post(
                f"{self.server_url}/search",
                json={
                    "session_id": self.session_id,
                    "query": query,
                    "max_results": max_results
                }
            )
            
            if response.status_code != 200:
                self.logger.error(f"Search request failed: {response.status_code}")
                return []
            
            results = response.json().get("results", [])
            self.logger.info(f"Search for '{query}' returned {len(results)} results")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error performing search: {e}")
            return []
    
    def close(self) -> bool:
        """
        Close the connection to the MCP server.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.session_id:
            return True
        
        try:
            response = requests.post(
                f"{self.server_url}/close",
                json={"session_id": self.session_id}
            )
            
            if response.status_code != 200:
                self.logger.error(f"Failed to close MCP connection: {response.status_code}")
                return False
            
            self.session_id = None
            self.logger.info("Closed connection to MCP server")
            return True
            
        except Exception as e:
            self.logger.error(f"Error closing MCP connection: {e}")
            return False