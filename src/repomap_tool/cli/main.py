#!/usr/bin/env python3
"""
Main CLI entry point for RepoMap-Tool.

This module provides the main CLI group and orchestrates all command groups.
"""

import click
from rich.console import Console

# Import command groups
from .commands.system import system
from .commands.index import index
from .commands.search import search
from .commands.explore import explore
from .commands.analyze import analyze

console = Console()


@click.group()
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.pass_context
def cli(ctx: click.Context, no_color: bool) -> None:
    """RepoMap-Tool: Intelligent code repository mapping and analysis."""
    ctx.ensure_object(dict)
    ctx.obj["no_color"] = no_color
    
    if no_color:
        console.no_color = True


# Register command groups
cli.add_command(system)
cli.add_command(index)
cli.add_command(search)
cli.add_command(explore)
cli.add_command(analyze)


if __name__ == "__main__":
    cli()
