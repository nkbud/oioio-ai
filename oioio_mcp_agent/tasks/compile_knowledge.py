"""
Task for compiling knowledge content from search results.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from prefect import task

from oioio_mcp_agent.utils.llm_client import LLMClient


@task(name="compile_knowledge", retries=2)
def compile_knowledge(
    knowledge_gap: str,
    search_results: List[Dict[str, Any]],
    llm_client: LLMClient
) -> Dict[str, Any]:
    """
    Prefect task to compile knowledge content with citations from search results.
    
    Args:
        knowledge_gap: The knowledge gap to address
        search_results: List of search results to incorporate
        llm_client: Configured LLM client
        
    Returns:
        Dictionary with compiled knowledge content and metadata
    """
    logger = logging.getLogger("prefect.compile_knowledge")
    timestamp = datetime.now().isoformat()
    
    if not llm_client.is_available() or not search_results:
        # Fall back to generating content without citations
        return generate_content_without_citations(
            knowledge_gap=knowledge_gap,
            llm_client=llm_client,
            timestamp=timestamp
        )
    
    # Format search results for the LLM
    formatted_results = []
    for i, result in enumerate(search_results):
        formatted_results.append(f"""
Source {i+1}: 
Title: {result.get('title', 'Unknown Title')}
URL: {result.get('url', 'Unknown URL')}
Snippet: {result.get('snippet', result.get('description', 'No description available'))}
""")
    
    search_content = "\n".join(formatted_results)
    
    system_message = """You are an expert knowledge base creator for MCP (Model Context Protocol) servers.
Your task is to synthesize comprehensive markdown content using the provided search results,
filling a knowledge gap with accurate, well-cited information.

Create detailed, technical, but accessible content that would be valuable to developers and architects.

Your response MUST:
1. Have a clear, descriptive title (H1)
2. Include multiple sections with headings (H2, H3)
3. Provide technical details, examples, and where applicable, code snippets
4. Include citations to the sources provided, using numbered references [1], [2], etc.
5. Include a "References" section at the end listing all cited sources with their URLs
6. Be comprehensive but concise (600-1000 words)
7. Focus on factual information, properly attributed to sources

Format as markdown with proper headings, lists, code blocks, etc."""

    content_text = llm_client.generate_completion(
        system_message=system_message,
        user_message=f"Create knowledge content about: {knowledge_gap}\n\nSearch Results:\n{search_content}",
        temperature=0.5,
        max_tokens=1500  # Increased for more comprehensive content
    )
    
    if not content_text:
        logger.warning("Failed to generate content with citations. Falling back to basic content.")
        return generate_content_without_citations(
            knowledge_gap=knowledge_gap,
            llm_client=llm_client,
            timestamp=timestamp
        )
    
    # Extract title from the first line if it starts with #
    lines = content_text.split('\n')
    title = lines[0].strip('# ') if lines and lines[0].startswith('#') else knowledge_gap
    
    return {
        "title": title,
        "content": content_text,
        "source": "llm_with_citations",
        "search_results_count": len(search_results),
        "gathered_at": timestamp
    }


def generate_content_without_citations(
    knowledge_gap: str,
    llm_client: LLMClient,
    timestamp: str
) -> Dict[str, Any]:
    """
    Generate content without citations when web search is unavailable.
    
    Args:
        knowledge_gap: The knowledge gap to address
        llm_client: Configured LLM client
        timestamp: Current timestamp
        
    Returns:
        Dictionary with generated content and metadata
    """
    logger = logging.getLogger("prefect.compile_knowledge")
    
    if llm_client.is_available():
        # Create a system message with instructions for knowledge generation
        system_message = """You are an expert knowledge base creator for MCP (Model Context Protocol) servers.
Your task is to generate comprehensive markdown content to fill a knowledge gap.
Create detailed, technical, but accessible content that would be valuable to developers and architects.

Your response should:
1. Have a clear, descriptive title (H1)
2. Include multiple sections with headings (H2, H3)
3. Provide technical details, examples, and where applicable, code snippets
4. Be comprehensive but concise (400-800 words)
5. Focus on factual information

Format as markdown with proper headings, lists, code blocks, etc."""

        content_text = llm_client.generate_completion(
            system_message=system_message,
            user_message=f"Create knowledge content about: {knowledge_gap}",
            temperature=0.5,
            max_tokens=1000
        )
        
        if content_text:
            # Extract title from the first line if it starts with #
            lines = content_text.split('\n')
            title = lines[0].strip('# ') if lines and lines[0].startswith('#') else knowledge_gap
            
            return {
                "title": title,
                "content": content_text,
                "source": "llm_generated",
                "gathered_at": timestamp
            }
    
    # Placeholder implementation when LLM is not available or fails
    logger.info("Using fallback content generation logic")
    
    # Generate placeholder content based on the gap
    if "mcp_server_architecture" in knowledge_gap.lower():
        content = {
            "title": "MCP Server Architecture Overview",
            "content": """# MCP Server Architecture Overview

Model Context Protocol (MCP) servers follow a client-server architecture where:

- **Server**: Provides resources, tools, and prompts to clients
- **Client**: Consumes server capabilities to enhance AI model interactions
- **Transport Layer**: Handles communication between client and server

## Key Components

1. **Resource Handlers**: Manage access to external data sources
2. **Tool Handlers**: Provide callable functions for clients
3. **Prompt Templates**: Offer reusable prompt structures

## Communication Flow

```
Client Request → Transport → Server → Handler → Response
```

This architecture enables modular, scalable AI assistance systems.
""",
            "source": "placeholder_research",
            "gathered_at": timestamp
        }
    elif "protocol_basics" in knowledge_gap.lower():
        content = {
            "title": "MCP Protocol Basics",
            "content": """# MCP Protocol Basics

The Model Context Protocol (MCP) defines standard interfaces for AI model interactions.

## Core Concepts

- **Resources**: Static or dynamic data sources
- **Tools**: Functions that can be called by AI models
- **Prompts**: Templates for common interaction patterns

## Protocol Features

- JSON-RPC based communication
- Capability negotiation
- Error handling and recovery
- Streaming support for large data

## Benefits

- Standardized AI model interactions
- Improved security through controlled access
- Enhanced collaboration between AI systems
""",
            "source": "placeholder_research", 
            "gathered_at": timestamp
        }
    else:
        # Generic placeholder content
        content = {
            "title": f"Knowledge About: {knowledge_gap}",
            "content": f"""# {knowledge_gap}

This is placeholder content gathered for the knowledge gap: {knowledge_gap}

## Overview

Information about this topic would be gathered from various sources including:
- Technical documentation
- Research papers
- Community resources
- Expert interviews

## Key Points

- Point 1: Relevant information about the topic
- Point 2: Additional insights and details
- Point 3: Practical applications and examples

## References

- Source 1: Placeholder reference
- Source 2: Additional resource
- Source 3: Expert opinion

*Content gathered on: {timestamp}*
""",
            "source": "placeholder_research",
            "gathered_at": timestamp
        }
    
    logger.info(f"Created fallback content for gap: {knowledge_gap}")
    return content