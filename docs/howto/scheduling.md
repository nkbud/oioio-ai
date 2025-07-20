# Scheduling Guide

This guide explains how to configure and manage schedules for flows in the OIOIO MCP Agent system.

## Schedule Types

The system supports three types of schedules:

1. **Interval-based**: Run a flow at regular intervals (e.g., every 3600 seconds)
2. **Cron-based**: Run a flow according to a cron expression (e.g., "0 * * * *" for once per hour)
3. **One-time**: Run a flow once after a delay

## Configuring Schedules

Schedules are configured in the agent section of your `config.yaml` file:

```yaml
agents:
  - name: mcp-knowledge-agent
    flows:
      - name: knowledge_flow
        schedule: "interval:3600"  # Run every hour
```

### Schedule Format

The schedule specification follows this format:

- Interval schedule: `interval:<seconds>`
- Cron schedule: `cron:<cron_expression>`
- One-time schedule: `once:<delay_seconds>`

Examples:
- `interval:3600`: Run every 3600 seconds (1 hour)
- `cron:0 0 * * *`: Run at midnight every day
- `once:30`: Run once after a 30-second delay

## Environment-Specific Scheduling

You can override schedules for different environments:

```yaml
# config.dev.yaml
agents:
  - name: mcp-knowledge-agent
    flows:
      - name: knowledge_flow
        schedule: "interval:7200"  # Every 2 hours in dev
```

```yaml
# config.prod.yaml
agents:
  - name: mcp-knowledge-agent
    flows:
      - name: knowledge_flow
        schedule: "interval:3600"  # Every hour in production
```

## Disabling Schedules

To disable scheduling for a flow:

```yaml
agents:
  - name: mcp-knowledge-agent
    flows:
      - name: knowledge_flow
        schedule: null  # No schedule
        enabled: false  # Explicitly disable
```

## Running Flows Manually

You can run flows manually with the CLI:

```bash
python -m oioio_mcp_agent run --agent mcp-knowledge-agent --flow knowledge_flow
```

Add `--wait` to wait for the flow to complete:

```bash
python -m oioio_mcp_agent run --agent mcp-knowledge-agent --flow knowledge_flow --wait
```

## Managing Schedules

The agent manager automatically creates and applies schedules when the agent starts:

```bash
python -m oioio_mcp_agent start
```

## Schedule Persistence

Schedules are stored in the Prefect backend and persist across restarts. To update a schedule:

1. Modify the schedule in your configuration file
2. Restart the agent:
   ```bash
   python -m oioio_mcp_agent start
   ```

## Common Cron Expressions

- `0 * * * *`: Every hour at minute 0
- `0 0 * * *`: Every day at midnight
- `0 0 * * MON`: Every Monday at midnight
- `0 12 * * *`: Every day at noon
- `0 0 1 * *`: First day of each month
- `*/15 * * * *`: Every 15 minutes

## Best Practices

1. **Development vs. Production**: Use less frequent schedules in development
2. **Resource Consideration**: Consider system resources when setting schedules
3. **Overlapping Runs**: Set intervals longer than typical flow execution time
4. **Time Zones**: Cron schedules are evaluated in the server's time zone
5. **Monitoring**: Regularly check flow run history to ensure schedules are working