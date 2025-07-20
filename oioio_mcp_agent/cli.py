"""
Command-line interface for the OIOIO MCP Agent.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from dotenv import load_dotenv
from prefect import get_client
from prefect.client.schemas import FlowRun
from prefect.deployments import run_deployment
from prefect.states import Completed, Failed

from oioio_mcp_agent.config import Config, ConfigLoader
from oioio_mcp_agent.core import AgentManager, discover_plugins


@click.group()
@click.option(
    "--config",
    "-c",
    default="config.yaml",
    help="Path to configuration file",
)
@click.option(
    "--env-file",
    "-e",
    default=".env",
    help="Path to environment file",
)
@click.option(
    "--env",
    default=lambda: os.environ.get("MCP_ENV", "dev"),
    help="Environment name (dev, prod, etc.) for loading specific config",
)
@click.option(
    "--config-dir",
    default="configs",
    help="Directory containing configuration files",
)
@click.option(
    "--log-level",
    default=lambda: os.environ.get("MCP_LOG_LEVEL", "INFO"),
    help="Logging level",
)
@click.pass_context
def cli(
    ctx: click.Context,
    config: str,
    env_file: str,
    env: str,
    config_dir: str,
    log_level: str,
) -> None:
    """OIOIO MCP Agent - Autonomous MCP Server Knowledge Accumulation."""
    ctx.ensure_object(dict)
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    logger = logging.getLogger("cli")
    logger.info(f"Starting CLI with environment: {env}")
    
    # Create config directory if it doesn't exist
    Path(config_dir).mkdir(exist_ok=True)
    
    # Load environment variables
    env_path = Path(env_file)
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}")
    else:
        logger.warning(f"Environment file {env_path} not found, continuing without it")
    
    # Load configuration
    try:
        # Use configuration loader for YAML-based config
        config_loader = ConfigLoader(config_dir=config_dir)
        loaded_config = config_loader.load_config(config_name=config, env_name=env)
        ctx.obj["config"] = loaded_config
        logger.info(f"Loaded configuration from {config_dir}/{config}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        if not Path(f"{config_dir}/{config}").exists():
            logger.error(f"Configuration file {config_dir}/{config} not found")
            logger.info("Run 'init' command to create a default configuration file")
        raise click.Abort()
    
    # Discover plugins
    discover_plugins("oioio_mcp_agent.plugins")


@cli.command()
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force overwrite existing configuration",
)
@click.pass_context
def init(ctx: click.Context, force: bool) -> None:
    """Initialize default configuration."""
    config_dir = Path("configs")
    config_path = config_dir / "config.yaml"
    env_path = Path(".env.example")
    
    if config_path.exists() and not force:
        click.echo(f"Configuration file already exists: {config_path}")
        click.echo("Use --force to overwrite")
        return
    
    # Create config directory
    config_dir.mkdir(exist_ok=True)
    
    # Create default configuration
    default_config = {
        "version": "1.0",
        "core": {
            "knowledge_dir": "knowledge",
            "checkpoint_dir": ".prefect",
            "log_level": "INFO"
        },
        "docker": {
            "compose_file": "docker-compose.yml",
            "services": [
                {
                    "name": "brave-search",
                    "image": "mcp/brave-search",
                    "port": 8080
                }
            ]
        },
        "llm": {
            "provider": "openrouter",
            "model": "gemini-2.0-flash-lite",
            "temperature": 0.7,
            "max_tokens": 500
        },
        "agents": [
            {
                "name": "mcp-knowledge-agent",
                "enabled": True,
                "flows": [
                    {
                        "name": "knowledge_flow",
                        "schedule": "interval:3600",
                        "params": {
                            "max_gaps_to_process": 3,
                            "prompt": "Identify key knowledge gaps about MCP servers"
                        }
                    }
                ]
            }
        ],
        "flows": {
            "knowledge_flow": {
                "tasks": [
                    "identify_gaps",
                    "generate_search_terms",
                    "perform_web_search",
                    "compile_knowledge",
                    "write_knowledge_file"
                ]
            }
        },
        "tasks": {
            "identify_gaps": {
                "plugin": "llm_gap_identifier",
                "params": {
                    "max_gaps": 5
                }
            },
            "generate_search_terms": {
                "plugin": "llm_search_term_generator"
            },
            "perform_web_search": {
                "plugin": "mcp_brave_search"
            },
            "compile_knowledge": {
                "plugin": "llm_knowledge_compiler"
            },
            "write_knowledge_file": {
                "plugin": "markdown_writer",
                "params": {
                    "add_timestamp": True
                }
            }
        }
    }
    
    # Write config file
    import yaml
    with open(config_path, "w") as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
    
    click.echo(f"Created default configuration file: {config_path}")
    
    # Create dev and prod config files
    for env in ["dev", "prod"]:
        env_config_path = config_dir / f"config.{env}.yaml"
        if not env_config_path.exists() or force:
            with open(env_config_path, "w") as f:
                yaml.dump({
                    "version": "1.0",
                    "core": {
                        "log_level": "DEBUG" if env == "dev" else "INFO"
                    }
                }, f, default_flow_style=False, sort_keys=False)
            click.echo(f"Created {env} configuration file: {env_config_path}")
    
    # Create example .env file
    if not env_path.exists() or force:
        with open(env_path, "w") as f:
            f.write("# Environment variables for OIOIO MCP Agent\n")
            f.write("MCP_ENV=dev\n")
            f.write("MCP_LOG_LEVEL=INFO\n")
            f.write("\n# LLM API keys\n")
            f.write("OPENROUTER_API_KEY=\n")
            f.write("\n# Docker configuration\n")
            f.write("MCP_PORT=8080\n")
            f.write("MCP_DATA_DIR=./mcp_data\n")
            f.write("\n# Prefect configuration\n")
            f.write("PREFECT_API_URL=http://localhost:4200/api\n")
        
        click.echo(f"Created example environment file: {env_path}")
        click.echo("Copy .env.example to .env and fill in your API keys")


@cli.command()
@click.option(
    "--agents",
    "-a",
    help="Comma-separated list of agents to start (default: all)",
)
@click.option(
    "--start-docker",
    is_flag=True,
    help="Start Docker services before starting agents",
)
@click.pass_context
def start(ctx: click.Context, agents: Optional[str], start_docker: bool) -> None:
    """Start agents based on configuration."""
    config = ctx.obj["config"]
    agent_names = agents.split(",") if agents else None
    
    # Start Docker services if requested
    if start_docker:
        _start_docker_services(config)
    
    click.echo("Starting agents...")
    
    # Create agent manager
    agent_manager = AgentManager()
    
    # Filter agents if specified
    agent_configs = config.agents
    if agent_names:
        agent_configs = [a for a in config.agents if a.name in agent_names]
        if not agent_configs:
            click.echo(f"No agents found with names: {agents}")
            return
    
    # Load agents from configuration
    agent_manager.load_agents_from_config(agent_configs)
    
    # Start all agents
    try:
        asyncio.run(agent_manager.start_all_agents())
        click.echo(f"Started {len(agent_configs)} agents")
    except Exception as e:
        click.echo(f"Error starting agents: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option(
    "--services",
    "-s",
    help="Comma-separated list of services to start (default: all)",
)
@click.pass_context
def docker(ctx: click.Context, services: Optional[str]) -> None:
    """Start Docker services."""
    config = ctx.obj["config"]
    service_names = services.split(",") if services else None
    
    _start_docker_services(config, service_names)


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show agent status."""
    config = ctx.obj["config"]
    
    click.echo("=== OIOIO MCP Agent Status ===")
    
    # Show configuration info
    click.echo(f"Configuration:")
    click.echo(f"  Environment: {os.environ.get('MCP_ENV', 'dev')}")
    click.echo(f"  Knowledge directory: {config.core.knowledge_dir}")
    click.echo(f"  Log level: {config.core.log_level}")
    
    # Show agent info
    click.echo(f"\nAgents ({len(config.agents)}):")
    for agent in config.agents:
        click.echo(f"  - {agent.name}: {'Enabled' if agent.enabled else 'Disabled'}")
        for flow in agent.flows:
            flow_name = flow.get("name", "unknown")
            schedule = flow.get("schedule", "manual")
            click.echo(f"    - Flow: {flow_name} (Schedule: {schedule})")
    
    # Check Docker services
    _check_docker_services(config)
    
    # Get recent flow runs
    try:
        recent_runs = asyncio.run(_get_recent_flow_runs())
        if recent_runs:
            click.echo("\nRecent flow runs:")
            for run in recent_runs[:5]:  # Show 5 most recent
                status = run.state.name if run.state else "Unknown"
                start_time = run.start_time.strftime("%Y-%m-%d %H:%M:%S") if run.start_time else "Not started"
                click.echo(f"  - {run.name} ({status}) - Started: {start_time}")
        else:
            click.echo("\nNo recent flow runs found.")
    except Exception as e:
        click.echo(f"Error fetching flow runs: {e}")


@cli.command()
@click.option(
    "--agent",
    "-a",
    required=True,
    help="Agent name",
)
@click.option(
    "--flow",
    "-f",
    required=True,
    help="Flow name",
)
@click.option(
    "--wait",
    is_flag=True,
    help="Wait for flow run to complete",
)
@click.pass_context
def run(ctx: click.Context, agent: str, flow: str, wait: bool) -> None:
    """Run a flow manually."""
    config = ctx.obj["config"]
    
    # Find agent config
    agent_config = None
    for a in config.agents:
        if a.name == agent:
            agent_config = a
            break
    
    if not agent_config:
        click.echo(f"Agent '{agent}' not found")
        return
    
    # Find flow config
    flow_config = None
    for f in agent_config.flows:
        if f.get("name") == flow:
            flow_config = f
            break
    
    if not flow_config:
        click.echo(f"Flow '{flow}' not found in agent '{agent}'")
        return
    
    # Run the flow
    deployment_name = f"{agent}-{flow}"
    click.echo(f"Running flow '{flow}' from agent '{agent}'...")
    
    try:
        flow_run = asyncio.run(_run_flow(deployment_name, flow_config.get("params", {}), wait))
        click.echo(f"Flow run started with ID: {flow_run}")
    except Exception as e:
        click.echo(f"Error running flow: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option(
    "--type",
    "-t",
    "plugin_type",
    required=True,
    help="Plugin type to list",
)
@click.pass_context
def list_plugins(ctx: click.Context, plugin_type: str) -> None:
    """List available plugins."""
    from oioio_mcp_agent.core.plugin import get_registry
    
    try:
        registry = get_registry(plugin_type)
        plugins = registry.list_plugins()
        
        if not plugins:
            click.echo(f"No plugins found for type '{plugin_type}'")
            return
        
        click.echo(f"=== Plugins for type '{plugin_type}' ===")
        for plugin_name in plugins:
            click.echo(f"  - {plugin_name}")
    
    except Exception as e:
        click.echo(f"Error listing plugins: {e}", err=True)


def _start_docker_services(config: Config, service_names: Optional[List[str]] = None) -> None:
    """Start Docker services."""
    compose_file = config.docker.compose_file
    services = config.docker.services
    
    if not services:
        click.echo("No Docker services configured")
        return
    
    # Filter services if specified
    if service_names:
        services = [s for s in services if s.name in service_names]
        if not services:
            click.echo(f"No services found with names: {service_names}")
            return
    
    click.echo(f"Starting {len(services)} Docker services...")
    
    for service in services:
        try:
            click.echo(f"Starting service '{service.name}'...")
            result = subprocess.run(
                ["docker-compose", "-f", compose_file, "up", "-d", service.name],
                capture_output=True,
                text=True,
                check=True,
            )
            click.echo(f"Service '{service.name}' started successfully")
        except subprocess.CalledProcessError as e:
            click.echo(f"Error starting service '{service.name}': {e}", err=True)
            if e.stderr:
                click.echo(f"Error details: {e.stderr}", err=True)
        except FileNotFoundError:
            click.echo("Docker Compose not found. Please install Docker Compose.", err=True)
            break


def _check_docker_services(config: Config) -> None:
    """Check status of Docker services."""
    compose_file = config.docker.compose_file
    services = config.docker.services
    
    if not services:
        return
    
    click.echo("\nDocker services:")
    
    try:
        for service in services:
            result = subprocess.run(
                ["docker-compose", "-f", compose_file, "ps", service.name],
                capture_output=True,
                text=True
            )
            
            if "Up" in result.stdout:
                status = "Running"
            elif "Exit" in result.stdout:
                status = "Stopped"
            else:
                status = "Unknown"
                
            click.echo(f"  - {service.name}: {status}")
    
    except subprocess.CalledProcessError as e:
        click.echo(f"Error checking Docker services: {e}", err=True)
    except FileNotFoundError:
        click.echo("Docker Compose not found", err=True)


async def _get_recent_flow_runs() -> List[FlowRun]:
    """Get recent flow runs."""
    async with get_client() as client:
        flow_runs = await client.read_flow_runs(
            sort="-start_time",
            limit=10,
        )
    return flow_runs


async def _run_flow(deployment_name: str, parameters: Dict[str, Any], wait: bool) -> str:
    """Run a flow deployment."""
    flow_run = await run_deployment(
        name=deployment_name,
        parameters=parameters,
    )
    
    run_id = flow_run.id
    
    if wait:
        # Wait for flow run to complete
        async with get_client() as client:
            while True:
                flow_run = await client.read_flow_run(run_id)
                state = flow_run.state
                
                if state.is_completed():
                    print(f"Flow run completed successfully!")
                    break
                    
                if state.is_failed():
                    print(f"Flow run failed: {state.message}")
                    break
                    
                # Still running
                print(f"Flow run status: {state.name}")
                await asyncio.sleep(2)
    
    return run_id


def main() -> None:
    """Run the CLI."""
    cli(obj={})


@click.group()
@click.option(
    "--knowledge-dir",
    default=lambda: os.environ.get("MCP_KNOWLEDGE_DIR", "knowledge"),
    help="Directory to store knowledge files",
)
@click.option(
    "--openrouter-api-key",
    default=lambda: os.environ.get("OPENROUTER_API_KEY"),
    help="OpenRouter API key (or set OPENROUTER_API_KEY env var)",
)
@click.option(
    "--mcp-server-url",
    default=lambda: os.environ.get("MCP_SERVER_URL", "http://localhost:8080"),
    help="URL for the MCP Brave Search server",
)
@click.pass_context
def cli(
    ctx: click.Context,
    knowledge_dir: str,
    openrouter_api_key: Optional[str],
    mcp_server_url: str,
) -> None:
    """MCP Knowledge Agent - Autonomous MCP Server Knowledge Accumulation."""
    ctx.ensure_object(dict)
    
    ctx.obj["config"] = AgentConfig(
        knowledge_dir=Path(knowledge_dir),
        openrouter_api_key=openrouter_api_key,
        mcp_server_url=mcp_server_url,
    )


@cli.command()
@click.option(
    "--cycles",
    "-c",
    default=1,
    type=int,
    help="Number of cycles to run",
)
@click.option(
    "--delay",
    "-d",
    default=0,
    type=int,
    help="Delay between cycles in seconds",
)
@click.option(
    "--prompt",
    "-p",
    default="Identify key knowledge gaps about MCP servers",
    help="Prompt for knowledge gap identification",
)
@click.option(
    "--start-docker",
    is_flag=True,
    help="Start the MCP Brave Search server with Docker Compose before running",
)
@click.pass_context
def run(
    ctx: click.Context,
    cycles: int,
    delay: int,
    prompt: str,
    start_docker: bool,
) -> None:
    """Run the knowledge agent for specified cycles."""
    config = ctx.obj["config"]
    
    if start_docker:
        click.echo("Starting MCP Brave Search server with Docker Compose...")
        try:
            result = subprocess.run(
                ["docker-compose", "up", "-d", "brave-search"],
                capture_output=True,
                text=True,
                check=True,
            )
            click.echo("Docker container started successfully.")
        except subprocess.CalledProcessError as e:
            click.echo(f"Error starting Docker container: {e}", err=True)
            click.echo(f"Error output: {e.stderr}", err=True)
            if not click.confirm("Continue without MCP Brave Search server?"):
                return
        except FileNotFoundError:
            click.echo("Docker Compose not found. Please install Docker Compose.")
            if not click.confirm("Continue without MCP Brave Search server?"):
                return

    click.echo(f"Starting knowledge agent: {cycles} cycles with {delay}s delay")
    click.echo(f"Using prompt: '{prompt}'")
    
    run_results = []
    
    try:
        for i in range(cycles):
            if i > 0 and delay > 0:
                click.echo(f"Waiting {delay}s before next cycle...")
                time.sleep(delay)
            
            click.echo(f"Running cycle {i+1}/{cycles}...")
            result = knowledge_agent_flow(
                config=config,
                prompt=prompt,
                max_gaps_to_process=3,  # Limit to 3 gaps per cycle
            )
            run_results.append(result)
            
            # Print cycle summary
            click.echo(f"Cycle {i+1} completed:")
            click.echo(f"  - Gaps found: {result.get('gaps_found', 0)}")
            click.echo(f"  - Files created: {result.get('files_created', 0)}")
            click.echo(f"  - Search results found: {result.get('search_results_found', 0)}")

        click.echo("\n=== Agent Run Summary ===")
        total_files = sum(r.get("files_created", 0) for r in run_results)
        total_gaps = sum(r.get("gaps_found", 0) for r in run_results)
        total_errors = sum(len(r.get("errors", [])) for r in run_results)
        
        click.echo(f"Cycles completed: {len(run_results)}")
        click.echo(f"Total files created: {total_files}")
        click.echo(f"Total gaps identified: {total_gaps}")
        click.echo(f"Total errors: {total_errors}")
        
        if total_errors > 0:
            click.echo("\nErrors encountered:")
            for result in run_results:
                for error in result.get("errors", []):
                    click.echo(f"  - {error}")
    
    except KeyboardInterrupt:
        click.echo("\nAgent interrupted by user")
    except Exception as e:
        click.echo(f"Agent run failed: {e}", err=True)
        raise click.Abort()


@cli.command("status")
@click.pass_context
def show_status(ctx: click.Context) -> None:
    """Show status of knowledge files and recent runs."""
    config = ctx.obj["config"]
    knowledge_dir = config.knowledge_dir
    
    click.echo("=== Knowledge Agent Status ===")
    
    # Check knowledge directory
    if not knowledge_dir.exists():
        click.echo(f"Knowledge directory '{knowledge_dir}' does not exist")
    else:
        md_files = list(knowledge_dir.glob("*.md"))
        click.echo(f"Knowledge files: {len(md_files)}")
    
    # Get recent flow runs
    try:
        recent_runs = _get_recent_flow_runs()
        if recent_runs:
            click.echo("\nRecent flow runs:")
            for run in recent_runs[:5]:  # Show 5 most recent
                status = run.state.name if run.state else "Unknown"
                start_time = run.start_time.strftime("%Y-%m-%d %H:%M:%S") if run.start_time else "Not started"
                click.echo(f"  - {run.name} ({status}) - Started: {start_time}")
        else:
            click.echo("\nNo recent flow runs found.")
    except Exception as e:
        click.echo(f"Error fetching flow runs: {e}")
    
    # Check if MCP server is reachable
    _check_mcp_server(config.mcp_server_url)


@cli.command("deploy")
@click.option(
    "--name",
    default="mcp-knowledge-agent",
    help="Name for the deployment",
)
@click.option(
    "--schedule",
    type=int,
    help="Schedule interval in seconds (optional)",
)
@click.pass_context
def create_agent_deployment(
    ctx: click.Context,
    name: str,
    schedule: Optional[int],
) -> None:
    """Deploy the agent as a Prefect deployment."""
    config = ctx.obj["config"]
    
    click.echo(f"Creating deployment '{name}'...")
    
    try:
        # Create and apply deployment
        deployment = create_deployment(
            name=name,
            schedule_interval_seconds=schedule,
            config=config,
        )
        deployment_id = deployment.apply()
        
        click.echo(f"Deployment created successfully with ID: {deployment_id}")
        click.echo("You can run this deployment with:")
        click.echo(f"  prefect deployment run {name}")
        
        if schedule:
            click.echo(f"Scheduled to run every {schedule} seconds")
        else:
            click.echo("No schedule set. Run manually or add a schedule later.")
    
    except Exception as e:
        click.echo(f"Error creating deployment: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option(
    "--deployment",
    "-d",
    default="mcp-knowledge-agent/mcp-knowledge-agent-flow",
    help="Deployment to run",
)
@click.option(
    "--wait",
    is_flag=True,
    help="Wait for flow run to complete",
)
@click.pass_context
def start(
    ctx: click.Context,
    deployment: str,
    wait: bool,
) -> None:
    """Start a flow run from deployment."""
    click.echo(f"Starting flow run from deployment '{deployment}'...")
    
    try:
        config = ctx.obj["config"]
        
        # Run deployment
        flow_run = run_deployment(
            name=deployment,
            parameters={
                "config": config.model_dump(),
            },
        )
        
        click.echo(f"Flow run '{flow_run.id}' started")
        
        # Wait for completion if requested
        if wait:
            click.echo("Waiting for flow run to complete...")
            _wait_for_flow_run(flow_run.id)
    
    except Exception as e:
        click.echo(f"Error starting flow run: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.pass_context
def list_files(ctx: click.Context) -> None:
    """List all knowledge files."""
    knowledge_dir = ctx.obj["config"].knowledge_dir
    
    if not knowledge_dir.exists():
        click.echo(f"Knowledge directory '{knowledge_dir}' does not exist")
        return
    
    md_files = list(knowledge_dir.glob("*.md"))
    
    if not md_files:
        click.echo("No knowledge files found")
        return
    
    click.echo(f"=== Knowledge Files ({len(md_files)} total) ===")
    for file_path in sorted(md_files):
        # Get file size and modification time
        stat = file_path.stat()
        size_kb = stat.st_size / 1024
        mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_path.stat().st_mtime))
        
        click.echo(f"{file_path.name:40} {size_kb:>6.1f}KB  {mtime}")


@cli.command()
@click.argument("filename")
@click.pass_context
def show(ctx: click.Context, filename: str) -> None:
    """Show contents of a specific knowledge file."""
    knowledge_dir = ctx.obj["config"].knowledge_dir
    file_path = knowledge_dir / filename
    
    if not file_path.exists():
        click.echo(f"File '{filename}' not found in {knowledge_dir}")
        return
    
    try:
        with open(file_path, "r") as f:
            content = f.read()
        
        click.echo(f"=== {filename} ===")
        click.echo(content)
    
    except Exception as e:
        click.echo(f"Error reading file: {e}", err=True)


@cli.command()
@click.argument("action", type=click.Choice(["start", "stop", "restart", "status"]))
@click.pass_context
def docker(ctx: click.Context, action: str) -> None:
    """Manage the MCP Brave Search Docker container."""
    try:
        if action == "start":
            click.echo("Starting MCP Brave Search server...")
            result = subprocess.run(["docker-compose", "up", "-d", "brave-search"], check=True)
            click.echo("Container started successfully")
        
        elif action == "stop":
            click.echo("Stopping MCP Brave Search server...")
            result = subprocess.run(["docker-compose", "stop", "brave-search"], check=True)
            click.echo("Container stopped successfully")
        
        elif action == "restart":
            click.echo("Restarting MCP Brave Search server...")
            result = subprocess.run(["docker-compose", "restart", "brave-search"], check=True)
            click.echo("Container restarted successfully")
        
        elif action == "status":
            result = subprocess.run(
                ["docker-compose", "ps", "brave-search"],
                capture_output=True,
                text=True
            )
            click.echo("MCP Brave Search server status:")
            click.echo(result.stdout)
    
    except subprocess.CalledProcessError as e:
        click.echo(f"Error: {e}", err=True)
        if e.stderr:
            click.echo(f"Error details: {e.stderr}", err=True)
    except FileNotFoundError:
        click.echo("Docker Compose not found. Please install Docker Compose.", err=True)


async def _get_recent_flow_runs() -> List[FlowRun]:
    """Get recent flow runs for the MCP knowledge agent flow."""
    async with get_client() as client:
        flow_runs = await client.read_flow_runs(
            flow_filter={"name": {"any_": ["mcp_knowledge_agent_flow"]}},
            sort="-start_time",
            limit=10,
        )
    return flow_runs


def _check_mcp_server(server_url: str) -> None:
    """Check if MCP server is reachable."""
    import requests
    
    click.echo("\nChecking MCP Brave Search server...")
    try:
        response = requests.post(
            f"{server_url}/handshake", 
            json={
                "client_name": "cli_check",
                "client_version": "1.0.0",
            },
            timeout=2
        )
        
        if response.status_code == 200:
            click.echo("MCP Brave Search server: Connected")
        else:
            click.echo(f"MCP Brave Search server: Not reachable (status code: {response.status_code})")
    except requests.exceptions.ConnectionError:
        click.echo("MCP Brave Search server: Connection refused")
    except Exception as e:
        click.echo(f"MCP Brave Search server: Error - {e}")


async def _wait_for_flow_run(flow_run_id: str) -> None:
    """Wait for a flow run to complete."""
    async with get_client() as client:
        while True:
            flow_run = await client.read_flow_run(flow_run_id)
            state = flow_run.state
            
            if isinstance(state, Completed):
                click.echo(f"Flow run completed successfully!")
                break
                
            elif isinstance(state, Failed):
                click.echo(f"Flow run failed: {state.message}")
                raise click.Abort()
                
            else:
                # Still running
                click.echo(f"Flow run status: {state.name}")
                time.sleep(2)


@cli.command()
@click.option(
    "--host",
    default=None,
    help="API server host (default: from config or 0.0.0.0)",
)
@click.option(
    "--port",
    default=None,
    type=int,
    help="API server port (default: from config or 8000)",
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload for development",
)
@click.option(
    "--workers",
    default=1,
    type=int,
    help="Number of worker processes",
)
@click.pass_context
def serve(ctx: click.Context, host: Optional[str], port: Optional[int], reload: bool, workers: int) -> None:
    """Start the API server."""
    config = ctx.obj["config"]
    api_config = getattr(config, "api", {})
    
    # Import optional dependencies
    try:
        import uvicorn
    except ImportError:
        click.echo("Error: API server dependencies not installed.")
        click.echo("Install with: pip install fastapi uvicorn")
        raise click.Abort()
    
    # Get configuration
    host = host or api_config.get("host", "0.0.0.0")
    port = port or int(api_config.get("port", 8000))
    
    click.echo(f"Starting API server at http://{host}:{port}")
    click.echo(f"API documentation available at http://{host}:{port}/api/docs")
    
    # Start server
    uvicorn.run(
        "oioio_mcp_agent.api.app:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
    )


@cli.command()
@click.argument("command", type=click.Choice(["init", "upgrade", "revision"]))
@click.option("--message", "-m", help="Migration message (for revision)")
@click.pass_context
def db(ctx: click.Context, command: str, message: Optional[str]) -> None:
    """Manage database migrations."""
    try:
        from alembic import config as alembic_config
    except ImportError:
        click.echo("Error: Database migration dependencies not installed.")
        click.echo("Install with: pip install alembic sqlalchemy")
        raise click.Abort()
    
    # Get configuration
    config = ctx.obj["config"]
    api_config = getattr(config, "api", {})
    
    # Set environment variables for Alembic
    os.environ["DATABASE_URL"] = api_config.get("database_url", "sqlite:///./oioio_mcp_agent.db")
    
    alembic_args = ["-c", "alembic.ini"]
    
    if command == "init":
        click.echo("Initializing database...")
        alembic_args.extend(["revision", "--autogenerate", "-m", "Initial migration"])
        alembic_args.extend(["upgrade", "head"])
    elif command == "upgrade":
        click.echo("Upgrading database...")
        alembic_args.extend(["upgrade", "head"])
    elif command == "revision":
        if not message:
            click.echo("Error: Message required for revision")
            raise click.Abort()
        click.echo(f"Creating migration: {message}")
        alembic_args.extend(["revision", "--autogenerate", "-m", message])
    
    alembic_config.main(argv=alembic_args)
    click.echo("Database operation completed successfully.")


def main() -> None:
    """Run the CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()