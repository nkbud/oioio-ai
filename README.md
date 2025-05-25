# MCP Knowledge Agent

A durable background agent for autonomously accumulating knowledge about MCP (Model Context Protocol) servers with web search capabilities.

## Features

- **Prefect Integration**: Uses Prefect workflows for robust task orchestration and monitoring
- **Durable Execution**: Start, stop, and resume execution with full state persistence
- **Knowledge Gap Detection**: Uses LLM to identify gaps in the knowledge base
- **Web Search Integration**: Uses MCP Brave Search server for real-time web search
- **RAG Implementation**: Three-step RAG process for knowledge accumulation with citations
- **Markdown Documentation**: Each knowledge piece stored as a separate markdown file
- **Modern Python Packaging**: Built with uv and distributable via PyPI

## Installation

### Using uv (recommended)

```bash
# Install uv if you don't have it
pip install uv

# Install the package
uv pip install oioio-mcp-agent
```

### Using uvx for quick runs

```bash
# Run directly without installing
uvx oioio-mcp-agent run --cycles 1
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/nkbud/oioio-ai
cd oioio-ai

# Install in development mode with uv
uv pip install -e .
```

## Quick Start

1. Start the MCP Brave Search server:
   ```bash
   mcp-agent docker start
   ```

2. Run the agent with web search capabilities:
   ```bash
   export OPENROUTER_API_KEY="your_api_key_here"
   mcp-agent run --cycles 3 --delay 1 --start-docker
   ```

3. Check agent status:
   ```bash
   mcp-agent status
   ```

4. List created knowledge files:
   ```bash
   mcp-agent list-files
   ```

5. Deploy as a scheduled Prefect flow:
   ```bash
   mcp-agent deploy --schedule 3600  # Run every hour
   ```

## CLI Commands

- `run` - Run the agent for specified cycles
- `status` - Show current agent status and files
- `deploy` - Create a Prefect deployment for the agent
- `start` - Start a flow run from a deployment
- `list-files` - List all knowledge files created
- `show <filename>` - Display contents of a knowledge file
- `docker <action>` - Manage the MCP Brave Search Docker container

## Architecture

Built with Prefect's controlflow framework, the system consists of:

- **Tasks**: Modular units for specific operations
  - Knowledge gap identification
  - Search term generation
  - Web search integration
  - Knowledge compilation
  - File writing

- **Flows**: Orchestrated workflows that combine tasks
  - Main knowledge agent flow

- **Deployments**: Scheduled or on-demand executions
  - Support for recurring knowledge updates

## Docker Compose Integration

The project includes a Docker Compose configuration that supports:

- MCP Brave Search server
- Agent container with proper environment
- Optional Prefect server for local development

```bash
# Run with Prefect server
docker-compose --profile prefect up

# Run the agent in a container
docker-compose --profile agent up
```

## RAG Implementation

The agent uses a three-step RAG process for knowledge accumulation:

1. **Generate Search Terms**: Uses LLM to generate effective search terms for a knowledge gap
2. **Perform Web Searches**: Queries the MCP Brave Search server for relevant information
3. **Compile Knowledge**: Uses LLM to synthesize search results into knowledge documents with citations

## Environment Variables

- `OPENROUTER_API_KEY`: API key for OpenRouter
- `MCP_SERVER_URL`: URL for the MCP Brave Search server
- `MCP_KNOWLEDGE_DIR`: Directory to store knowledge files
- `MCP_LLM_MODEL`: LLM model to use with OpenRouter (default: gemini-2.0-flash-lite)

## GitHub Pages Demo

This repository is set up with GitHub Pages to provide a demonstration site. You can visit the demo site at [https://nkbud.github.io/oioio-ai](https://nkbud.github.io/oioio-ai).