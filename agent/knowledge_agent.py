"""
Durable Background Knowledge Agent for MCP Server Knowledge Accumulation.

This module implements a background agent that can autonomously gather and
organize knowledge about MCP servers, with the ability to start, stop, and
resume execution while maintaining state through checkpoints.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import openai
from pydantic import BaseModel


class AgentCheckpoint(BaseModel):
    """Model for agent checkpoint state."""
    
    cycle_count: int = 0
    last_run_time: Optional[str] = None
    knowledge_files_created: List[str] = []
    gaps_identified: List[str] = []
    status: str = "stopped"  # stopped, running, paused
    created_at: str
    updated_at: str


class KnowledgeAgent:
    """
    A durable background agent for autonomously accumulating knowledge about MCP servers.
    
    Features:
    - Start, stop, and resume execution
    - Maintain state in checkpoint files
    - Identify knowledge gaps
    - Gather new information (placeholder)
    - Write knowledge as markdown files
    - Traceable progress via checkpoints
    """
    
    def __init__(self, 
                 knowledge_dir: str = "knowledge",
                 checkpoint_file: str = ".agent_checkpoint.json",
                 openai_api_key: Optional[str] = None):
        """
        Initialize the Knowledge Agent.
        
        Args:
            knowledge_dir: Directory to store knowledge markdown files
            checkpoint_file: File to store agent checkpoint state
            openai_api_key: Optional API key for OpenAI. If not provided, will use OPENAI_API_KEY env var
        """
        self.knowledge_dir = Path(knowledge_dir)
        self.checkpoint_file = Path(checkpoint_file)
        self.logger = self._setup_logging()
        
        # Configure OpenAI client
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        if self.openai_api_key:
            self.client = openai.OpenAI(api_key=self.openai_api_key)
        else:
            self.client = None
            self.logger.warning("No OpenAI API key provided. LLM features will be disabled.")
        
        # Ensure knowledge directory exists
        self.knowledge_dir.mkdir(exist_ok=True)
        
        # Load or create checkpoint
        self.checkpoint = self._load_checkpoint()
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the agent."""
        logger = logging.getLogger("knowledge_agent")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _load_checkpoint(self) -> AgentCheckpoint:
        """Load checkpoint from file or create new one."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)
                    self.logger.info(f"Loaded checkpoint from {self.checkpoint_file}")
                    return AgentCheckpoint(**data)
            except Exception as e:
                self.logger.warning(f"Failed to load checkpoint: {e}")
        
        # Create new checkpoint
        now = datetime.now().isoformat()
        checkpoint = AgentCheckpoint(
            created_at=now,
            updated_at=now
        )
        self.logger.info("Created new checkpoint")
        return checkpoint
    
    def _save_checkpoint(self) -> None:
        """Save current checkpoint to file."""
        self.checkpoint.updated_at = datetime.now().isoformat()
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(self.checkpoint.model_dump(), f, indent=2)
            self.logger.debug("Checkpoint saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
    
    def _identify_knowledge_gaps(self, prompt: str = "Identify knowledge gaps about MCP servers") -> List[str]:
        """
        Identify gaps in current knowledge base using LLM.
        
        Args:
            prompt: Prompt to guide the knowledge gap identification
            
        Returns:
            List of identified knowledge gaps
        """
        # Get existing files and their content
        existing_files = list(self.knowledge_dir.glob("*.md"))
        existing_file_content = {}
        
        for file_path in existing_files:
            try:
                with open(file_path, 'r') as f:
                    existing_file_content[file_path.name] = f.read()
            except Exception as e:
                self.logger.warning(f"Failed to read {file_path}: {e}")
        
        if self.client:
            # Use LLM to identify knowledge gaps
            try:
                # Build the prompt by including existing knowledge file names
                file_list = "\n".join([f"- {name}" for name in existing_file_content.keys()])
                
                # Create the system message with existing knowledge context
                system_message = f"""You are a knowledge management system for MCP (Model Context Protocol) servers.
Your task is to identify gaps in the current knowledge base.
Current knowledge files: {file_list if existing_file_content else 'No files yet'}

Review the existing content and identify 3-5 specific areas where knowledge is missing or incomplete.
Focus on important technical aspects of MCP servers that would be valuable to document."""

                # Call the OpenAI API
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=300
                )
                
                # Extract the knowledge gaps from the response
                gaps_text = response.choices[0].message.content.strip()
                
                # Split into individual gaps (assuming the LLM returns a list or numbered items)
                # This is a simple approach - may need refinement based on actual response format
                gaps = [line.strip().strip('*-1234567890.').strip() 
                       for line in gaps_text.split('\n') 
                       if line.strip() and not line.strip().startswith('#')]
                
                self.logger.info(f"LLM identified {len(gaps)} knowledge gaps")
                return gaps
                
            except Exception as e:
                self.logger.error(f"Error using LLM for gap identification: {e}")
                # Fall back to placeholder implementation
        
        # Placeholder logic when LLM is not available or fails
        self.logger.info("Using fallback gap identification logic")
        
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
        
        # Add some dynamic gaps based on cycle count
        if self.checkpoint.cycle_count % 3 == 0:
            gaps.append(f"Dynamic gap identified at cycle {self.checkpoint.cycle_count}")
        
        return gaps
    
    def _gather_information(self, gap: str) -> Dict[str, Any]:
        """
        Gather information for a specific knowledge gap using LLM.
        
        Args:
            gap: The knowledge gap to address
            
        Returns:
            Dictionary containing gathered information
        """
        timestamp = datetime.now().isoformat()
        
        if self.client:
            try:
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

                # Call the OpenAI API
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": f"Create knowledge content about: {gap}"}
                    ],
                    temperature=0.5,
                    max_tokens=1000
                )
                
                # Extract the content from the response
                content_text = response.choices[0].message.content.strip()
                
                # Extract title from the first line if it starts with #
                lines = content_text.split('\n')
                title = lines[0].strip('# ') if lines and lines[0].startswith('#') else gap
                
                return {
                    "title": title,
                    "content": content_text,
                    "source": "llm_generated",
                    "gathered_at": timestamp
                }
                
            except Exception as e:
                self.logger.error(f"Error using LLM for content generation: {e}")
                # Fall back to placeholder implementation
                
        # Placeholder implementation when LLM is not available or fails
        self.logger.info("Using fallback content generation logic")
        
        # Generate placeholder content based on the gap
        if "mcp_server_architecture" in gap.lower():
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
        elif "protocol_basics" in gap.lower():
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
                "title": f"Knowledge About: {gap}",
                "content": f"""# {gap}

This is placeholder content gathered for the knowledge gap: {gap}

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
        
        self.logger.info(f"Gathered information for gap: {gap}")
        return content
    
    def _write_knowledge_file(self, information: Dict[str, Any]) -> str:
        """
        Write gathered information to a markdown file.
        
        Args:
            information: Dictionary containing the information to write
            
        Returns:
            Path to the created file
        """
        # Generate filename from title
        title = information.get("title", "unknown_topic")
        filename = title.lower().replace(" ", "_").replace(":", "")
        filename = f"{filename}_{int(time.time())}.md"
        
        filepath = self.knowledge_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                f.write(information["content"])
            
            self.logger.info(f"Created knowledge file: {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Failed to write knowledge file: {e}")
            raise
    
    def run_cycle(self, prompt: str = "Identify key knowledge gaps about MCP servers") -> Dict[str, Any]:
        """
        Run a single agent cycle.
        
        Args:
            prompt: The prompt to guide knowledge gap identification
            
        Returns:
            Dictionary containing cycle results
        """
        cycle_start = time.time()
        self.checkpoint.cycle_count += 1
        self.checkpoint.status = "running"
        self.checkpoint.last_run_time = datetime.now().isoformat()
        
        self.logger.info(f"Starting cycle {self.checkpoint.cycle_count}")
        
        try:
            # Step 1: Identify knowledge gaps
            gaps = self._identify_knowledge_gaps(prompt=prompt)
            self.checkpoint.gaps_identified.extend(gaps)
            self.logger.info(f"Identified {len(gaps)} knowledge gaps")
            
            cycle_results = {
                "cycle_number": self.checkpoint.cycle_count,
                "gaps_found": len(gaps),
                "files_created": 0,
                "errors": []
            }
            
            # Step 2: Gather information for each gap
            for gap in gaps:
                try:
                    information = self._gather_information(gap)
                    filepath = self._write_knowledge_file(information)
                    self.checkpoint.knowledge_files_created.append(filepath)
                    cycle_results["files_created"] += 1
                except Exception as e:
                    error_msg = f"Failed to process gap '{gap}': {e}"
                    self.logger.error(error_msg)
                    cycle_results["errors"].append(error_msg)
            
            # Step 3: Update checkpoint
            self.checkpoint.status = "stopped"
            self._save_checkpoint()
            
            cycle_duration = time.time() - cycle_start
            cycle_results["duration_seconds"] = round(cycle_duration, 2)
            
            self.logger.info(
                f"Cycle {self.checkpoint.cycle_count} completed: "
                f"created {cycle_results['files_created']} files in "
                f"{cycle_results['duration_seconds']}s"
            )
            
            return cycle_results
            
        except Exception as e:
            self.checkpoint.status = "error"
            self._save_checkpoint()
            self.logger.error(f"Cycle {self.checkpoint.cycle_count} failed: {e}")
            raise
    
    def run(self, cycles: int = 1, delay: float = 0.0, prompt: str = "Identify key knowledge gaps about MCP servers") -> List[Dict[str, Any]]:
        """
        Run the agent for specified number of cycles.
        
        Args:
            cycles: Number of cycles to run
            delay: Delay between cycles in seconds
            prompt: Prompt to guide knowledge gap identification
            
        Returns:
            List of cycle results
        """
        self.logger.info(f"Starting agent run: {cycles} cycles with {delay}s delay")
        
        results = []
        
        try:
            for i in range(cycles):
                if i > 0 and delay > 0:
                    self.logger.info(f"Waiting {delay}s before next cycle...")
                    time.sleep(delay)
                
                cycle_result = self.run_cycle(prompt=prompt)
                results.append(cycle_result)
                
        except KeyboardInterrupt:
            self.logger.info("Agent run interrupted by user")
            self.checkpoint.status = "interrupted"
            self._save_checkpoint()
        except Exception as e:
            self.logger.error(f"Agent run failed: {e}")
            self.checkpoint.status = "error"
            self._save_checkpoint()
            raise
        
        self.logger.info(f"Agent run completed: {len(results)} cycles executed")
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "status": self.checkpoint.status,
            "cycle_count": self.checkpoint.cycle_count,
            "last_run_time": self.checkpoint.last_run_time,
            "files_created": len(self.checkpoint.knowledge_files_created),
            "gaps_identified": len(self.checkpoint.gaps_identified),
            "created_at": self.checkpoint.created_at,
            "updated_at": self.checkpoint.updated_at
        }
    
    def reset(self) -> None:
        """Reset agent state (use with caution)."""
        self.logger.warning("Resetting agent state")
        now = datetime.now().isoformat()
        self.checkpoint = AgentCheckpoint(
            created_at=now,
            updated_at=now
        )
        self._save_checkpoint()
        self.logger.info("Agent state reset completed")