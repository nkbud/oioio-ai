"""
Task for performing web searches using MCP Brave Search.
"""

import logging
from typing import Dict, List, Any

from prefect import task

from oioio_mcp_agent.utils.mcp_client import MCPClient


@task(name="perform_web_search", retries=3)
def perform_web_search(
    search_terms: List[str],
    mcp_server_url: str,
    results_per_term: int = 3
) -> List[Dict[str, Any]]:
    """
    Prefect task to perform web searches using the MCP Brave Search server.
    
    Args:
        search_terms: List of search terms to use
        mcp_server_url: URL of the MCP server
        results_per_term: Maximum number of results per search term
        
    Returns:
        List of search results with title, content, and url
    """
    logger = logging.getLogger("prefect.web_search")
    all_results = []
    
    # Create MCP client
    mcp_client = MCPClient(server_url=mcp_server_url)
    
    # Try to connect to the MCP server
    try:
        connected = mcp_client.connect()
        if not connected:
            logger.error("Failed to connect to MCP Brave Search server")
            return []
        
        # Perform searches for each term
        for term in search_terms:
            try:
                results = mcp_client.search(term, max_results=results_per_term)
                for result in results:
                    result["search_term"] = term
                all_results.extend(results)
                
                logger.info(f"Search for '{term}' returned {len(results)} results")
            except Exception as e:
                logger.error(f"Error searching for '{term}': {e}")
        
        # Close the connection
        mcp_client.close()
        
    except Exception as e:
        logger.error(f"Error with MCP client: {e}")
    
    logger.info(f"Web search completed with {len(all_results)} total results")
    return all_results