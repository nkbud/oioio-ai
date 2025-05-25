"""
Task for generating search terms based on knowledge gaps.
"""

import logging
from typing import List

from prefect import task

from oioio_mcp_agent.utils.llm_client import LLMClient


@task(name="generate_search_terms", retries=2)
def generate_search_terms(
    knowledge_gap: str,
    llm_client: LLMClient,
    max_terms: int = 5
) -> List[str]:
    """
    Prefect task to generate search terms for a knowledge gap using LLM.
    
    Args:
        knowledge_gap: The knowledge gap to generate search terms for
        llm_client: Configured LLM client
        max_terms: Maximum number of search terms to generate
        
    Returns:
        List of search terms
    """
    logger = logging.getLogger("prefect.search_terms")
    
    if not llm_client.is_available():
        logger.warning("LLM not available. Using default search terms.")
        # Generate simple search terms based on gap string
        return [knowledge_gap.replace("Missing knowledge about: ", "")]
    
    system_message = """You are a search query generation expert.
Given a knowledge gap about MCP (Model Context Protocol) servers, generate 3-5 effective search queries
that would help gather comprehensive information about this topic.

Generate each search query on a new line.
Focus on technical, specific search terms that would yield high-quality results."""

    search_terms_text = llm_client.generate_completion(
        system_message=system_message,
        user_message=f"Generate search queries for: {knowledge_gap}",
        temperature=0.4,
        max_tokens=200
    )
    
    if not search_terms_text:
        logger.warning("Failed to generate search terms with LLM. Using default.")
        return [knowledge_gap.replace("Missing knowledge about: ", "")]
    
    search_terms = [term.strip() for term in search_terms_text.split('\n') if term.strip()]
    logger.info(f"Generated {len(search_terms)} search terms for '{knowledge_gap}'")
    
    # Limit to max_terms
    return search_terms[:max_terms]