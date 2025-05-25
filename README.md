# oioio-ai

This repository contains the code and resources for the oioio-ai project.

## Knowledge Agent

A durable background agent for autonomously accumulating knowledge about MCP (Model Context Protocol) servers with web search capabilities.

### Features

- **Durable Execution**: Start, stop, and resume execution with checkpoint-based state persistence
- **Knowledge Gap Detection**: Uses LLM to identify gaps in the current knowledge base
- **Web Search Integration**: Uses MCP Brave Search server for real-time web search
- **RAG Implementation**: Three-step RAG process for knowledge accumulation with citations
- **Markdown Documentation**: Each piece of knowledge is stored as a separate markdown file with citations
- **CLI Interface**: Easy-to-use command-line interface for agent management
- **Progress Tracking**: Comprehensive logging and checkpoint system for recovery

### Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the MCP Brave Search server:
   ```bash
   python agent_cli.py docker start
   ```

3. Run the agent with web search capabilities:
   ```bash
   export OPENROUTER_API_KEY="your_api_key_here"
   python agent_cli.py run --cycles 3 --delay 1 --start-docker
   ```

4. Check agent status:
   ```bash
   python agent_cli.py status
   ```

5. List created knowledge files:
   ```bash
   python agent_cli.py list-files
   ```

6. Resume from last checkpoint:
   ```bash
   python agent_cli.py resume
   ```

### CLI Commands

- `run` - Run the agent for specified cycles
- `status` - Show current agent status, progress, and Docker status
- `resume` - Resume agent from last checkpoint
- `list-files` - List all knowledge files created
- `show <filename>` - Display contents of a knowledge file
- `checkpoint` - Show detailed checkpoint information
- `reset` - Reset agent state (removes all progress)
- `docker <action>` - Manage the MCP Brave Search Docker container (start, stop, restart, status)

### Architecture

- `agent/knowledge_agent.py` - Core agent implementation
- `agent/mcp_client.py` - Client for MCP Brave Search server
- `agent_cli.py` - Command-line interface
- `knowledge/` - Directory containing generated markdown files
- `docker-compose.yml` - Docker Compose configuration for MCP Brave Search
- `.agent_checkpoint.json` - Checkpoint file for state persistence

### RAG Implementation

The agent uses a three-step RAG process for knowledge accumulation:

1. **Generate Search Terms**: Uses LLM to generate effective search terms for a knowledge gap
2. **Perform Web Searches**: Queries the MCP Brave Search server for relevant information
3. **Compile Knowledge**: Uses LLM to synthesize the search results into comprehensive knowledge documents with citations

### OpenRouter Integration

The agent uses OpenRouter to access LLM capabilities, with Gemini 2.0 Flash Lite as the default model:

```bash
# Set your OpenRouter API key
export OPENROUTER_API_KEY="your_key_here"
```

## GitHub Pages Demo

This repository is set up with GitHub Pages to provide a demonstration site. You can visit the demo site at [https://nkbud.github.io/oioio-ai](https://nkbud.github.io/oioio-ai).