"""
System commands for RepoMap-Tool CLI.

This module contains system-level commands like version info and configuration.
"""

import json
import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel

from ...models import RepoMapConfig, create_error_response
from ..config.loader import resolve_project_path, create_default_config

console = Console()


@click.group()
def system() -> None:
    """System information commands."""
    pass


@system.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=False,
)
@click.option(
    "--output", "-o", type=click.Path(), help="Output configuration file path"
)
@click.option("--fuzzy/--no-fuzzy", default=True, help="Enable fuzzy matching")
@click.option("--semantic/--no-semantic", default=True, help="Enable semantic matching")
@click.option(
    "--threshold", "-t", default=0.7, type=float, help="Matching threshold (0.0-1.0)"
)
@click.option(
    "--cache-size", default=1000, type=int, help="Cache size for results"
)
def config(
    project_path: Optional[str],
    output: Optional[str],
    fuzzy: bool,
    semantic: bool,
    threshold: float,
    cache_size: int,
) -> None:
    """Generate a configuration file for the project."""

    try:
        # Resolve project path from argument or discovery
        project_path = resolve_project_path(project_path, None)
        # Create default configuration
        config_obj = create_default_config(
            project_path,
            fuzzy=fuzzy,
            semantic=semantic,
            threshold=threshold,
            max_results=50,
            output="json",
            verbose=True,
            cache_size=cache_size,
        )

        # Convert to dictionary with proper serialization
        config_dict = config_obj.model_dump(mode="json")

        if output:
            # Write to file
            with open(output, "w") as f:
                json.dump(config_dict, f, indent=2)
            console.print(f"[green]Configuration saved to: {output}[/green]")
        else:
            # Display configuration
            console.print(
                Panel(
                    json.dumps(config_dict, indent=2),
                    title="Generated Configuration",
                    border_style="blue",
                )
            )

    except Exception as e:
        error_response = create_error_response(str(e), "ConfigError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


@system.command()
def version() -> None:
    """Show version information."""
    console.print(
        Panel(
            "[bold blue]RepoMap-Tool[/bold blue]\n"
            "Version: 0.1.0\n"
            "A portable code analysis tool using aider libraries\n"
            "with fuzzy and semantic matching capabilities.",
            title="Version Info",
            border_style="green",
        )
    )
