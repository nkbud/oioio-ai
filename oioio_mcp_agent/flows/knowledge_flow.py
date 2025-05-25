"""
Prefect flow for the MCP Knowledge Agent.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from prefect import flow, get_run_logger
from prefect.context import get_run_context
from prefect.filesystems import LocalFileSystem
from prefect.task_runners import SequentialTaskRunner

from oioio_mcp_agent.config import AgentConfig
from oioio_mcp_agent.tasks.identify_gaps import identify_knowledge_gaps
from oioio_mcp_agent.tasks.search_terms import generate_search_terms
from oioio_mcp_agent.tasks.web_search import perform_web_search
from oioio_mcp_agent.tasks.compile_knowledge import compile_knowledge
from oioio_mcp_agent.tasks.write_knowledge import write_knowledge_file
from oioio_mcp_agent.utils.llm_client import LLMClient


@flow(
    name="mcp_knowledge_agent_flow",
    description="Flow to gather knowledge about MCP servers",
    task_runner=SequentialTaskRunner(),
    persist_result=True,
    result_storage=LocalFileSystem(basepath=".prefect/results"),
)
def knowledge_agent_flow(
    config: Optional[AgentConfig] = None,
    prompt: str = "Identify key knowledge gaps about MCP servers",
    max_gaps_to_process: int = 3,
) -> Dict[str, Any]:
    """
    Prefect flow for the MCP Knowledge Agent.
    
    Args:
        config: Agent configuration
        prompt: Prompt to guide knowledge gap identification
        max_gaps_to_process: Maximum number of gaps to process in a single flow run
        
    Returns:
        Dictionary with flow execution results
    """
    logger = get_run_logger()
    logger.info("Starting MCP Knowledge Agent flow")
    
    # Use provided config or create from environment
    agent_config = config or AgentConfig.from_env()
    
    # Ensure knowledge directory exists
    agent_config.knowledge_dir.mkdir(exist_ok=True)
    
    # Initialize LLM client
    llm_client = LLMClient(
        api_key=agent_config.openrouter_api_key,
        default_model=agent_config.llm_model
    )
    
    # Track flow execution results
    flow_results = {
        "gaps_found": 0,
        "files_created": 0,
        "search_results_found": 0,
        "created_files": [],
        "errors": []
    }
    
    try:
        # Step 1: Identify knowledge gaps
        knowledge_gaps = identify_knowledge_gaps(
            knowledge_dir=agent_config.knowledge_dir,
            llm_client=llm_client, 
            prompt=prompt,
            max_gaps=max_gaps_to_process
        )
        
        flow_results["gaps_found"] = len(knowledge_gaps)
        logger.info(f"Identified {len(knowledge_gaps)} knowledge gaps")
        
        # Step 2: Process each knowledge gap sequentially
        for gap in knowledge_gaps:
            try:
                # Generate search terms
                search_terms = generate_search_terms(
                    knowledge_gap=gap,
                    llm_client=llm_client
                )
                logger.info(f"Generated {len(search_terms)} search terms for '{gap}'")
                
                # Perform web searches
                search_results = perform_web_search(
                    search_terms=search_terms,
                    mcp_server_url=agent_config.mcp_server_url
                )
                flow_results["search_results_found"] += len(search_results)
                
                # Compile knowledge with citations
                knowledge_info = compile_knowledge(
                    knowledge_gap=gap,
                    search_results=search_results,
                    llm_client=llm_client
                )
                
                # Write to file
                file_path = write_knowledge_file(
                    knowledge_info=knowledge_info,
                    knowledge_dir=agent_config.knowledge_dir
                )
                
                flow_results["files_created"] += 1
                flow_results["created_files"].append(str(file_path))
                
            except Exception as e:
                error_msg = f"Failed to process gap '{gap}': {str(e)}"
                logger.error(error_msg)
                flow_results["errors"].append(error_msg)
        
        logger.info(f"Flow completed: found {flow_results['gaps_found']} gaps, "
                    f"created {flow_results['files_created']} files")
        return flow_results
        
    except Exception as e:
        error_msg = f"Flow failed: {str(e)}"
        logger.error(error_msg)
        flow_results["errors"].append(error_msg)
        return flow_results