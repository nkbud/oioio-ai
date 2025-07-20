# Configuration Guide

This document explains how to configure the OIOIO MCP Agent system using YAML configuration files and environment variables.

## Configuration Files

The system uses YAML-based configuration files stored in the `configs/` directory:

- `config.yaml`: Base configuration with default values
- `config.dev.yaml`: Development-specific overrides
- `config.prod.yaml`: Production-specific overrides
- Other environment-specific configs: `config.<env>.yaml`

When you start the agent with a specific environment, it loads the base configuration and then overrides it with environment-specific values.

## Creating a Configuration

To create a default configuration:

```bash
python -m oioio_mcp_agent init
```

This will create:
- `configs/config.yaml`: Default configuration
- `configs/config.dev.yaml`: Development configuration
- `configs/config.prod.yaml`: Production configuration
- `.env.example`: Example environment variables file

## Configuration Structure

The main configuration file is organized into sections:

### Core Configuration

```yaml
core:
  knowledge_dir: knowledge
  checkpoint_dir: .prefect
  log_level: INFO
```

### Docker Configuration

```yaml
docker:
  compose_file: docker-compose.yml
  services:
    - name: brave-search
      image: mcp/brave-search
      port: 8080
```

### LLM Configuration

```yaml
llm:
  provider: openrouter
  model: gemini-2.0-flash-lite
  temperature: 0.7
  max_tokens: 500
```

### Agent Configuration

Each agent can have multiple flows:

```yaml
agents:
  - name: mcp-knowledge-agent
    enabled: true
    flows:
      - name: knowledge_flow
        schedule: "interval:3600"  # Run every hour
        params:
          max_gaps_to_process: 3
```

### Flow Definitions

```yaml
flows:
  knowledge_flow:
    tasks:
      - identify_gaps
      - generate_search_terms
      - perform_web_search
      - compile_knowledge
      - write_knowledge_file
```

### Task Definitions

```yaml
tasks:
  identify_gaps:
    plugin: llm_gap_identifier
    params:
      max_gaps: 5
```

## Environment Variables

You can override configuration values using environment variables. The system follows this pattern:

```
MCP_SECTION__KEY=value
```

For example:
- `MCP_CORE__KNOWLEDGE_DIR=/path/to/knowledge` overrides the knowledge directory path
- `MCP_LLM__MODEL=gpt-4` overrides the LLM model

Environment variables can be loaded from a `.env` file. Copy `.env.example` to `.env` and customize the values.

## Scheduling

The system supports two types of schedule specifications:

1. Interval-based: `interval:3600` (run every 3600 seconds)
2. Cron-based: `cron:0 * * * *` (run at the start of every hour)

Configure schedules in the agent flow configuration:

```yaml
agents:
  - name: my-agent
    flows:
      - name: my_flow
        schedule: "interval:3600"
```

## Multi-Environment Setup

For different environments:

1. Create a `config.<env>.yaml` file with environment-specific overrides
2. Set the `MCP_ENV` environment variable to the environment name
3. Run the agent with `python -m oioio_mcp_agent --env <env> start`

## Examples

### Development Setup

```yaml
# config.dev.yaml
core:
  log_level: DEBUG

llm:
  model: gemini-2.0-flash-lite
```

### Production Setup

```yaml
# config.prod.yaml
core:
  knowledge_dir: /data/knowledge
  log_level: INFO

llm:
  model: gemini-2.0-pro
  timeout: 60
```