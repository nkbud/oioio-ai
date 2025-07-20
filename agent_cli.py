#!/usr/bin/env python3
"""
CLI interface for the Knowledge Agent.

Provides command-line access to start, stop, resume, and monitor
the durable background agent for MCP server knowledge accumulation.
"""

import click
import json
import os
from pathlib import Path

from agent.knowledge_agent import KnowledgeAgent


@click.group()
@click.option('--knowledge-dir', default='knowledge', 
              help='Directory to store knowledge files')
@click.option('--checkpoint-file', default='.agent_checkpoint.json',
              help='Checkpoint file path')
@click.option('--openrouter-api-key', 
              default=lambda: os.environ.get("OPENROUTER_API_KEY"), 
              help='OpenRouter API key (or set OPENROUTER_API_KEY env var)')
@click.option('--mcp-server-url', default='http://localhost:8080',
              help='URL for the MCP Brave Search server')
@click.pass_context
def cli(ctx, knowledge_dir, checkpoint_file, openrouter_api_key, mcp_server_url):
    """Knowledge Agent CLI - Autonomous MCP Server Knowledge Accumulation."""
    ctx.ensure_object(dict)
    ctx.obj['knowledge_dir'] = knowledge_dir
    ctx.obj['checkpoint_file'] = checkpoint_file
    ctx.obj['openrouter_api_key'] = openrouter_api_key
    ctx.obj['mcp_server_url'] = mcp_server_url


@cli.command()
@click.option('--cycles', '-c', default=1, type=int,
              help='Number of cycles to run')
@click.option('--delay', '-d', default=0.0, type=float,
              help='Delay between cycles in seconds')
@click.option('--prompt', '-p', 
              default="Identify key knowledge gaps about MCP servers",
              help='Prompt for knowledge gap identification')
@click.option('--start-docker', is_flag=True,
              help='Start the MCP Brave Search server with Docker Compose before running')
@click.pass_context
def run(ctx, cycles, delay, prompt, start_docker):
    """Run the knowledge agent for specified cycles."""
    if start_docker:
        click.echo("Starting MCP Brave Search server with Docker Compose...")
        # This imports the subprocess module only when needed
        import subprocess
        try:
            result = subprocess.run(
                ['docker-compose', 'up', '-d', 'brave-search'],
                capture_output=True,
                text=True,
                check=True
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
    
    agent = KnowledgeAgent(
        knowledge_dir=ctx.obj['knowledge_dir'],
        checkpoint_file=ctx.obj['checkpoint_file'],
        openrouter_api_key=ctx.obj['openrouter_api_key'],
        mcp_server_url=ctx.obj['mcp_server_url']
    )
    
    click.echo(f"Starting knowledge agent: {cycles} cycles with {delay}s delay")
    click.echo(f"Using prompt: '{prompt}'")
    
    try:
        results = agent.run(cycles=cycles, delay=delay, prompt=prompt)
        
        click.echo("\n=== Agent Run Summary ===")
        total_files = sum(r.get('files_created', 0) for r in results)
        total_gaps = sum(r.get('gaps_found', 0) for r in results)
        total_errors = sum(len(r.get('errors', [])) for r in results)
        
        click.echo(f"Cycles completed: {len(results)}")
        click.echo(f"Total files created: {total_files}")
        click.echo(f"Total gaps identified: {total_gaps}")
        click.echo(f"Total errors: {total_errors}")
        
        if total_errors > 0:
            click.echo("\nErrors encountered:")
            for result in results:
                for error in result.get('errors', []):
                    click.echo(f"  - {error}")
        
    except KeyboardInterrupt:
        click.echo("\nAgent interrupted by user")
    except Exception as e:
        click.echo(f"Agent run failed: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.pass_context
def status(ctx):
    """Show current agent status."""
    agent = KnowledgeAgent(
        knowledge_dir=ctx.obj['knowledge_dir'],
        checkpoint_file=ctx.obj['checkpoint_file'],
        openrouter_api_key=ctx.obj['openrouter_api_key'],
        mcp_server_url=ctx.obj['mcp_server_url']
    )
    
    status_info = agent.get_status()
    
    click.echo("=== Knowledge Agent Status ===")
    click.echo(f"Status: {status_info['status']}")
    click.echo(f"Cycle count: {status_info['cycle_count']}")
    click.echo(f"Files created: {status_info['files_created']}")
    click.echo(f"Gaps identified: {status_info['gaps_identified']}")
    click.echo(f"Last run: {status_info['last_run_time'] or 'Never'}")
    click.echo(f"Created: {status_info['created_at']}")
    click.echo(f"Updated: {status_info['updated_at']}")
    
    # Check if MCP server is reachable
    try:
        if agent.mcp_client.connect():
            click.echo("\nMCP Brave Search server: Connected")
            agent.mcp_client.close()
        else:
            click.echo("\nMCP Brave Search server: Not reachable")
    except Exception:
        click.echo("\nMCP Brave Search server: Error connecting")
    
    # Docker status
    import subprocess
    try:
        result = subprocess.run(
            ['docker-compose', 'ps'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            click.echo("\nDocker Compose Status:")
            click.echo(result.stdout)
    except Exception:
        pass


@cli.command()
@click.option('--prompt', '-p', 
              default="Identify key knowledge gaps about MCP servers",
              help='Prompt for knowledge gap identification')
@click.option('--start-docker', is_flag=True,
              help='Start the MCP Brave Search server with Docker Compose before running')
@click.pass_context 
def resume(ctx, prompt, start_docker):
    """Resume agent from last checkpoint (alias for run with 1 cycle)."""
    ctx.invoke(run, cycles=1, delay=0.0, prompt=prompt, start_docker=start_docker)


@cli.command()
@click.option('--confirm', is_flag=True, 
              help='Confirm reset without prompt')
@click.pass_context
def reset(ctx, confirm):
    """Reset agent state (removes all progress)."""
    if not confirm:
        if not click.confirm('This will reset all agent progress. Continue?'):
            click.echo("Reset cancelled")
            return
    
    agent = KnowledgeAgent(
        knowledge_dir=ctx.obj['knowledge_dir'],
        checkpoint_file=ctx.obj['checkpoint_file'],
        openrouter_api_key=ctx.obj['openrouter_api_key'],
        mcp_server_url=ctx.obj['mcp_server_url']
    )
    
    agent.reset()
    click.echo("Agent state reset successfully")


@cli.command()
@click.pass_context
def list_files(ctx):
    """List all knowledge files created by the agent."""
    knowledge_dir = Path(ctx.obj['knowledge_dir'])
    
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
        mtime = Path(file_path).stat().st_mtime
        
        click.echo(f"{file_path.name:40} {size_kb:>6.1f}KB")


@cli.command()
@click.argument('filename')
@click.pass_context
def show(ctx, filename):
    """Show contents of a specific knowledge file."""
    knowledge_dir = Path(ctx.obj['knowledge_dir'])
    file_path = knowledge_dir / filename
    
    if not file_path.exists():
        click.echo(f"File '{filename}' not found in {knowledge_dir}")
        return
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        click.echo(f"=== {filename} ===")
        click.echo(content)
        
    except Exception as e:
        click.echo(f"Error reading file: {e}", err=True)


@cli.command()
@click.pass_context
def checkpoint(ctx):
    """Show detailed checkpoint information."""
    checkpoint_file = Path(ctx.obj['checkpoint_file'])
    
    if not checkpoint_file.exists():
        click.echo("No checkpoint file found")
        return
    
    try:
        with open(checkpoint_file, 'r') as f:
            checkpoint_data = json.load(f)
        
        click.echo("=== Agent Checkpoint ===")
        click.echo(json.dumps(checkpoint_data, indent=2))
        
    except Exception as e:
        click.echo(f"Error reading checkpoint: {e}", err=True)


@cli.command()
@click.argument('action', type=click.Choice(['start', 'stop', 'restart', 'status']))
@click.pass_context
def docker(ctx, action):
    """Manage the MCP Brave Search Docker container."""
    import subprocess
    
    try:
        if action == 'start':
            click.echo("Starting MCP Brave Search server...")
            result = subprocess.run(['docker-compose', 'up', '-d', 'brave-search'], check=True)
            click.echo("Container started successfully")
        
        elif action == 'stop':
            click.echo("Stopping MCP Brave Search server...")
            result = subprocess.run(['docker-compose', 'stop', 'brave-search'], check=True)
            click.echo("Container stopped successfully")
        
        elif action == 'restart':
            click.echo("Restarting MCP Brave Search server...")
            result = subprocess.run(['docker-compose', 'restart', 'brave-search'], check=True)
            click.echo("Container restarted successfully")
        
        elif action == 'status':
            result = subprocess.run(['docker-compose', 'ps', 'brave-search'], capture_output=True, text=True)
            click.echo("MCP Brave Search server status:")
            click.echo(result.stdout)
    
    except subprocess.CalledProcessError as e:
        click.echo(f"Error: {e}", err=True)
        if e.stderr:
            click.echo(f"Error details: {e.stderr}", err=True)
    except FileNotFoundError:
        click.echo("Docker Compose not found. Please install Docker Compose.", err=True)


if __name__ == '__main__':
    cli()