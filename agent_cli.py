#!/usr/bin/env python3
"""
CLI interface for the Knowledge Agent.

Provides command-line access to start, stop, resume, and monitor
the durable background agent for MCP server knowledge accumulation.
"""

import click
import json
from pathlib import Path

from agent.knowledge_agent import KnowledgeAgent


@click.group()
@click.option('--knowledge-dir', default='knowledge', 
              help='Directory to store knowledge files')
@click.option('--checkpoint-file', default='.agent_checkpoint.json',
              help='Checkpoint file path')
@click.pass_context
def cli(ctx, knowledge_dir, checkpoint_file):
    """Knowledge Agent CLI - Autonomous MCP Server Knowledge Accumulation."""
    ctx.ensure_object(dict)
    ctx.obj['knowledge_dir'] = knowledge_dir
    ctx.obj['checkpoint_file'] = checkpoint_file


@cli.command()
@click.option('--cycles', '-c', default=1, type=int,
              help='Number of cycles to run')
@click.option('--delay', '-d', default=0.0, type=float,
              help='Delay between cycles in seconds')
@click.pass_context
def run(ctx, cycles, delay):
    """Run the knowledge agent for specified cycles."""
    agent = KnowledgeAgent(
        knowledge_dir=ctx.obj['knowledge_dir'],
        checkpoint_file=ctx.obj['checkpoint_file']
    )
    
    click.echo(f"Starting knowledge agent: {cycles} cycles with {delay}s delay")
    
    try:
        results = agent.run(cycles=cycles, delay=delay)
        
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
        checkpoint_file=ctx.obj['checkpoint_file']
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


@cli.command()
@click.pass_context 
def resume(ctx):
    """Resume agent from last checkpoint (alias for run with 1 cycle)."""
    ctx.invoke(run, cycles=1, delay=0.0)


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
        checkpoint_file=ctx.obj['checkpoint_file']
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


if __name__ == '__main__':
    cli()