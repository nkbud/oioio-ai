# OIOIO MCP Knowledge Agent

A declarative, scalable, and schedulable system for autonomously accumulating knowledge about MCP (Model Context Protocol) servers with web search capabilities.

## Features

- **Declarative Configuration**: YAML-based configuration with environment variable support
- **Pluggable Architecture**: Extensible plugin system for all core components
- **Scalable Design**: Support for multiple agents, flows, and tasks
- **Scheduler Integration**: Declaratively define schedules for automated execution
- **Docker Integration**: Built-in Docker Compose management for services
- **Modern Python**: Built with uv and distributable via PyPI

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
uvx oioio-mcp-agent run --agent mcp-knowledge-agent --flow knowledge_flow
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/nkbud/oioio-ai
cd oioio-ai

# Install in development mode with uv
uv pip install -e .

# Create initial configuration
python -m oioio_mcp_agent init
```

## Quick Start

1. Initialize the configuration (first time only):
   ```bash
   python -m oioio_mcp_agent init
   ```

2. Copy the example environment file and add your API keys:
   ```bash
   cp .env.example .env
   # Edit .env to add your API keys
   ```

3. Start the MCP Brave Search server:
   ```bash
   python -m oioio_mcp_agent docker
   ```

4. Run a flow manually:
   ```bash
   python -m oioio_mcp_agent run --agent mcp-knowledge-agent --flow knowledge_flow
   ```

5. Check agent status:
   ```bash
   python -m oioio_mcp_agent status
   ```

## Configuration

The system uses a hierarchical configuration system:

1. `configs/config.yaml` - Base configuration
2. `configs/config.<env>.yaml` - Environment-specific overrides
3. `.env` file - Secret keys and additional overrides
4. Command-line arguments - Runtime overrides

Example configuration:

```yaml
version: "1.0"

# Core configuration
core:
  knowledge_dir: knowledge
  log_level: INFO

# Agent configuration
agents:
  - name: mcp-knowledge-agent
    flows:
      - name: knowledge_flow
        schedule: "interval:3600"  # Run every hour
```

See the [Configuration Guide](docs/howto/configuration.md) for more details.

## CLI Commands

- `init` - Create initial configuration files
- `start` - Start agents based on configuration
- `docker` - Manage Docker services
- `status` - Show status of agents, flows, and services
- `run` - Run a specific flow manually
- `list-plugins` - List available plugins by type

## Extending the System

### Creating Custom Plugins

The system supports four main types of plugins:

1. Gap Identifier Plugins
2. Search Plugins
3. LLM Plugins
4. Document Writer Plugins

Example plugin:

```python
from oioio_mcp_agent.core import SearchPlugin, register_plugin

@register_plugin
class CustomSearchPlugin(SearchPlugin):
    plugin_name = "custom_search"
    plugin_type = "search"
    
    def search(self, query, max_results=10):
        # Custom search implementation
        pass
```

See the [Plugin Development Guide](docs/howto/plugins.md) for more details.

## Environment Variables

Secret keys and configuration overrides can be specified in a `.env` file:

```
# Secret keys
OPENROUTER_API_KEY=your_api_key_here

# Configuration overrides
MCP_ENV=dev
MCP_CORE__LOG_LEVEL=DEBUG
```

## Documentation

- [Configuration Guide](docs/howto/configuration.md)
- [Plugin Development Guide](docs/howto/plugins.md)
- [Scheduling Guide](docs/howto/scheduling.md)

## GitHub Pages Demo

Visit the demo site at [https://nkbud.github.io/oioio-ai](https://nkbud.github.io/oioio-ai)