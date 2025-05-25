# Plugin Development Guide

This guide explains how to create custom plugins for the OIOIO MCP Agent system.

## Plugin Types

The system supports four main types of plugins:

1. **Gap Identifier Plugins**: Identify knowledge gaps in the system
2. **Search Plugins**: Execute searches to gather information
3. **LLM Plugins**: Interact with large language models
4. **Document Writer Plugins**: Write content to knowledge files

## Creating a Plugin

To create a plugin:

1. Create a new file in the appropriate directory:
   - `oioio_mcp_agent/plugins/gaps/` for gap identifier plugins
   - `oioio_mcp_agent/plugins/search/` for search plugins
   - `oioio_mcp_agent/plugins/llm/` for LLM plugins
   - `oioio_mcp_agent/plugins/writers/` for document writer plugins

2. Define a plugin class that inherits from the appropriate base class
3. Use the `@register_plugin` decorator to register your plugin

## Plugin Base Classes

Choose the appropriate base class for your plugin:

- `GapIdentifierPlugin`: For plugins that identify knowledge gaps
- `SearchPlugin`: For plugins that execute searches
- `LLMPlugin`: For plugins that interact with language models
- `DocumentWriterPlugin`: For plugins that write knowledge files

## Example Plugins

### LLM Plugin Example

```python
from oioio_mcp_agent.core import LLMPlugin, register_plugin

@register_plugin
class OpenRouterPlugin(LLMPlugin):
    """OpenRouter LLM plugin."""
    
    plugin_name = "openrouter"
    plugin_type = "llm"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = kwargs.get("api_key")
        self.model = kwargs.get("model", "gemini-2.0-flash-lite")
        
    def generate(self, 
                system_message: str, 
                user_message: str, 
                temperature: float = 0.7,
                max_tokens: int = 500) -> str:
        """Generate text using OpenRouter."""
        # Implementation code here
        pass
```

### Search Plugin Example

```python
from typing import Dict, Any, List
from oioio_mcp_agent.core import SearchPlugin, register_plugin

@register_plugin
class BraveSearchPlugin(SearchPlugin):
    """Brave Search plugin using MCP."""
    
    plugin_name = "brave_search"
    plugin_type = "search"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.server_url = kwargs.get("server_url", "http://localhost:8080")
        
    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Perform a search using Brave Search."""
        # Implementation code here
        pass
```

### Document Writer Plugin Example

```python
import os
import time
from pathlib import Path
from oioio_mcp_agent.core import DocumentWriterPlugin, register_plugin

@register_plugin
class MarkdownWriterPlugin(DocumentWriterPlugin):
    """Markdown writer plugin."""
    
    plugin_name = "markdown_writer"
    plugin_type = "document_writer"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_timestamp = kwargs.get("add_timestamp", True)
        
    def write(self, content: str, filename: str, directory: str) -> str:
        """Write content to a markdown file."""
        # Implementation code here
        pass
```

## Configuring Plugins

Configure your plugins in the `config.yaml` file:

```yaml
tasks:
  search_task:
    plugin: brave_search
    params:
      server_url: http://localhost:8080
      
  generate_content:
    plugin: openrouter
    params:
      model: gpt-4
      temperature: 0.8
```

## Discovering Plugins

The system automatically discovers plugins in the `oioio_mcp_agent.plugins` package. To list available plugins:

```bash
python -m oioio_mcp_agent list-plugins --type search
```

## Plugin Registration

Plugins are registered using the `register_plugin` decorator:

```python
from oioio_mcp_agent.core import register_plugin, SearchPlugin

@register_plugin
class MySearchPlugin(SearchPlugin):
    plugin_name = "my_search"
    plugin_type = "search"
    
    # Plugin implementation
```

## Best Practices

1. **Error Handling**: Add robust error handling to your plugins
2. **Logging**: Use the Python logging module to provide helpful debug information
3. **Configuration**: Make plugins configurable via parameters
4. **Documentation**: Add docstrings and type hints
5. **Testing**: Write unit tests for your plugins