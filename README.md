# oioio-ai

This repository contains the code and resources for the oioio-ai project.

## Knowledge Agent

A durable background agent for autonomously accumulating knowledge about MCP (Model Context Protocol) servers.

### Features

- **Durable Execution**: Start, stop, and resume execution with checkpoint-based state persistence
- **Knowledge Gap Detection**: Automatically identifies gaps in the current knowledge base
- **Information Gathering**: Placeholder system for gathering new information (extensible for real web search/APIs)
- **Markdown Documentation**: Each piece of knowledge is stored as a separate markdown file
- **CLI Interface**: Easy-to-use command-line interface for agent management
- **Progress Tracking**: Comprehensive logging and checkpoint system for recovery

### Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the agent for 3 cycles with 1-second delay:
   ```bash
   python agent_cli.py run --cycles 3 --delay 1
   ```

3. Check agent status:
   ```bash
   python agent_cli.py status
   ```

4. List created knowledge files:
   ```bash
   python agent_cli.py list-files
   ```

5. Resume from last checkpoint:
   ```bash
   python agent_cli.py resume
   ```

### CLI Commands

- `run` - Run the agent for specified cycles
- `status` - Show current agent status and progress
- `resume` - Resume agent from last checkpoint
- `list-files` - List all knowledge files created
- `show <filename>` - Display contents of a knowledge file
- `checkpoint` - Show detailed checkpoint information
- `reset` - Reset agent state (removes all progress)

### Architecture

- `agent/knowledge_agent.py` - Core agent implementation
- `agent_cli.py` - Command-line interface
- `knowledge/` - Directory containing generated markdown files
- `.agent_checkpoint.json` - Checkpoint file for state persistence

## GitHub Pages Demo

This repository is set up with GitHub Pages to provide a demonstration site. You can visit the demo site at [https://nkbud.github.io/oioio-ai](https://nkbud.github.io/oioio-ai).