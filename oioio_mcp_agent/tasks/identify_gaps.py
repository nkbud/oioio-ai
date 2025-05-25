"""
Task for identifying knowledge gaps about MCP servers.
"""

import logging
from pathlib import Path
from typing import List, Optional

from prefect import task

from oioio_mcp_agent.utils.llm_client import LLMClient


@task(name="identify_knowledge_gaps", retries=2)
def identify_knowledge_gaps(
    knowledge_dir: Path,
    llm_client: LLMClient,
    prompt: str = "Identify knowledge gaps about MCP servers",
    max_gaps: int = 5,
) -> List[str]:
    """
    Prefect task to identify gaps in current knowledge base using LLM.
    
    Args:
        knowledge_dir: Directory containing knowledge files
        llm_client: Configured LLM client
        prompt: Prompt to guide the knowledge gap identification
        max_gaps: Maximum number of gaps to identify
        
    Returns:
        List of identified knowledge gaps
    """
    logger = logging.getLogger("prefect.identify_gaps")
    
    # Get existing files and their content
    existing_files = list(knowledge_dir.glob("*.md"))
    existing_file_content = {}
    
    for file_path in existing_files:
        try:
            with open(file_path, 'r') as f:
                existing_file_content[file_path.name] = f.read()
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
    
    if llm_client.is_available():
        # Build the prompt by including existing knowledge file names
        file_list = "\n".join([f"- {name}" for name in existing_file_content.keys()])
        
        # Create the system message with existing knowledge context
        system_message = f"""You are a knowledge management system for MCP (Model Context Protocol) servers.
Your task is to identify gaps in the current knowledge base.
Current knowledge files: {file_list if existing_file_content else 'No files yet'}

Review the existing content and identify 3-5 specific areas where knowledge is missing or incomplete.
Focus on important technical aspects of MCP servers that would be valuable to document."""

        # Generate knowledge gaps using the LLM
        gaps_text = llm_client.generate_completion(
            system_message=system_message,
            user_message=prompt,
            temperature=0.7,
            max_tokens=300
        )
        
        if gaps_text:
            # Split into individual gaps (assuming the LLM returns a list or numbered items)
            gaps = [line.strip().strip('*-1234567890.').strip() 
                   for line in gaps_text.split('\n') 
                   if line.strip() and not line.strip().startswith('#')]
            
            logger.info(f"LLM identified {len(gaps)} knowledge gaps")
            return gaps[:max_gaps]  # Limit to max_gaps
    
    # Fallback logic when LLM is not available or fails
    logger.info("Using fallback gap identification logic")
    
    # Sample gap identification - look for missing topics
    expected_topics = [
        "mcp_server_architecture",
        "mcp_protocol_basics", 
        "mcp_server_implementation",
        "mcp_client_integration",
        "mcp_security_considerations",
        "mcp_performance_optimization"
    ]
    
    gaps = []
    for topic in expected_topics:
        topic_files = [f for f in existing_files if topic in f.name.lower()]
        if not topic_files:
            gaps.append(f"Missing knowledge about: {topic}")
    
    return gaps[:max_gaps]