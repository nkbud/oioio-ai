"""
Task for writing compiled knowledge to files.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Any

from prefect import task


@task(name="write_knowledge_file", retries=2)
def write_knowledge_file(
    knowledge_info: Dict[str, Any],
    knowledge_dir: Path
) -> Path:
    """
    Prefect task to write gathered information to a markdown file.
    
    Args:
        knowledge_info: Dictionary containing the information to write
        knowledge_dir: Directory to store knowledge files
        
    Returns:
        Path to the created file
    """
    logger = logging.getLogger("prefect.write_knowledge")
    
    # Ensure knowledge directory exists
    knowledge_dir.mkdir(exist_ok=True)
    
    # Generate filename from title
    title = knowledge_info.get("title", "unknown_topic")
    filename = title.lower().replace(" ", "_").replace(":", "")
    filename = f"{filename}_{int(time.time())}.md"
    
    filepath = knowledge_dir / filename
    
    try:
        with open(filepath, 'w') as f:
            f.write(knowledge_info["content"])
        
        logger.info(f"Created knowledge file: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Failed to write knowledge file: {e}")
        raise