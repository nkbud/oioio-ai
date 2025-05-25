"""
Command-line interface for the MCP Knowledge Agent.
"""

import os
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

import click
from prefect import get_client
from prefect.client.schemas import FlowRun
from prefect.deployments import run_deployment
from prefect.states import Completed, Failed

from oioio_mcp_agent.config import AgentConfig
from oioio_mcp_agent.deploy import create_deployment, deploy
from oioio_mcp_agent.flows.knowledge_flow import knowledge_agent_flow


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


def main() -> None:
    """Run the CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()