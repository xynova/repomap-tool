#!/usr/bin/env python3
"""
cli.py - Command Line Interface for Docker RepoMap

This module provides a CLI interface using Click and Pydantic models
for argument validation and structured output.
"""

import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .models import (
    RepoMapConfig, FuzzyMatchConfig, SemanticMatchConfig,
    SearchRequest, create_error_response
)
from .core import DockerRepoMap

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Docker RepoMap - Intelligent code analysis and identifier matching."""
    pass


@cli.command()
@click.argument('project_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file (JSON/YAML)')
@click.option('--fuzzy/--no-fuzzy', default=False, help='Enable fuzzy matching')
@click.option('--semantic/--no-semantic', default=False, help='Enable semantic matching')
@click.option('--threshold', '-t', type=float, default=0.7, help='Match threshold (0.0-1.0)')
@click.option('--max-results', '-m', type=int, default=50, help='Maximum results to return')
@click.option('--output', '-o', type=click.Choice(['json', 'text', 'markdown']), default='json', help='Output format')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def analyze(project_path: str, config: Optional[str], fuzzy: bool, semantic: bool, 
           threshold: float, max_results: int, output: str, verbose: bool):
    """Analyze a project and generate a code map."""
    
    try:
        # Load configuration
        if config:
            config_obj = load_config_file(config)
        else:
            config_obj = create_default_config(project_path, fuzzy, semantic, threshold, max_results, output, verbose)
        
        # Initialize RepoMap
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing RepoMap...", total=None)
            
            repomap = DockerRepoMap(config_obj)
            progress.update(task, description="Analyzing project...")
            
            # Analyze project
            project_info = repomap.analyze_project()
            
            progress.update(task, description="Analysis complete!")
        
        # Display results
        display_project_info(project_info, output)
        
    except Exception as e:
        error_response = create_error_response(str(e), "AnalysisError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('project_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('query', type=str)
@click.option('--match-type', type=click.Choice(['fuzzy', 'semantic', 'hybrid']), default='hybrid', help='Matching strategy')
@click.option('--threshold', '-t', type=float, default=0.7, help='Match threshold (0.0-1.0)')
@click.option('--max-results', '-m', type=int, default=10, help='Maximum results to return')
@click.option('--strategies', '-s', multiple=True, help='Specific matching strategies')
@click.option('--output', '-o', type=click.Choice(['json', 'text', 'table']), default='table', help='Output format')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def search(project_path: str, query: str, match_type: str, threshold: float, 
          max_results: int, strategies: tuple, output: str, verbose: bool):
    """Search for identifiers in a project."""
    
    try:
        # Create configuration
        config = create_search_config(project_path, match_type, verbose)
        
        # Create search request
        request = SearchRequest(
            query=query,
            match_type=match_type,
            threshold=threshold,
            max_results=max_results,
            strategies=list(strategies) if strategies else None
        )
        
        # Initialize RepoMap
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing RepoMap...", total=None)
            
            repomap = DockerRepoMap(config)
            progress.update(task, description="Searching identifiers...")
            
            # Perform search
            response = repomap.search_identifiers(request)
            
            progress.update(task, description="Search complete!")
        
        # Display results
        display_search_results(response, output)
        
    except Exception as e:
        error_response = create_error_response(str(e), "SearchError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('project_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--output', '-o', type=click.Path(), help='Output file for configuration')
def config(project_path: str, output: Optional[str]):
    """Generate a configuration file for the project."""
    
    try:
        # Create default configuration
        config_obj = create_default_config(project_path, fuzzy=True, semantic=True, threshold=0.7, max_results=50, output='json', verbose=True)
        
        # Convert to dictionary
        config_dict = config_obj.model_dump(indent=2)
        
        if output:
            # Write to file
            with open(output, 'w') as f:
                json.dump(config_dict, f, indent=2)
            console.print(f"[green]Configuration saved to: {output}[/green]")
        else:
            # Display configuration
            console.print(Panel(
                json.dumps(config_dict, indent=2),
                title="Generated Configuration",
                border_style="blue"
            ))
        
    except Exception as e:
        error_response = create_error_response(str(e), "ConfigError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


@cli.command()
def version():
    """Show version information."""
    console.print(Panel(
        "[bold blue]Docker RepoMap[/bold blue]\n"
        "Version: 0.1.0\n"
        "A portable code analysis tool using aider libraries\n"
        "with fuzzy and semantic matching capabilities.",
        title="Version Info",
        border_style="green"
    ))


def load_config_file(config_path: str) -> RepoMapConfig:
    """Load configuration from file."""
    try:
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        return RepoMapConfig(**config_dict)
    except Exception as e:
        raise ValueError(f"Failed to load configuration file: {e}")


def create_default_config(project_path: str, fuzzy: bool, semantic: bool, 
                         threshold: float, max_results: int, output: str, verbose: bool) -> RepoMapConfig:
    """Create default configuration."""
    
    # Create fuzzy match config
    fuzzy_config = FuzzyMatchConfig(
        enabled=fuzzy,
        threshold=int(threshold * 100),  # Convert to percentage
        strategies=['prefix', 'substring', 'levenshtein']
    )
    
    # Create semantic match config
    semantic_config = SemanticMatchConfig(
        enabled=semantic,
        threshold=threshold,
        use_tfidf=True
    )
    
    # Create main config
    config = RepoMapConfig(
        project_root=project_path,
        fuzzy_match=fuzzy_config,
        semantic_match=semantic_config,
        max_results=max_results,
        output_format=output,
        verbose=verbose
    )
    
    return config


def create_search_config(project_path: str, match_type: str, verbose: bool) -> RepoMapConfig:
    """Create configuration for search operations."""
    
    # Enable appropriate matchers based on match type
    fuzzy_enabled = match_type in ['fuzzy', 'hybrid']
    semantic_enabled = match_type in ['semantic', 'hybrid']
    
    fuzzy_config = FuzzyMatchConfig(enabled=fuzzy_enabled)
    semantic_config = SemanticMatchConfig(enabled=semantic_enabled)
    
    config = RepoMapConfig(
        project_root=project_path,
        fuzzy_match=fuzzy_config,
        semantic_match=semantic_config,
        verbose=verbose
    )
    
    return config


def display_project_info(project_info, output_format: str):
    """Display project analysis results."""
    
    if output_format == 'json':
        console.print(json.dumps(project_info.model_dump(), indent=2))
        return
    
    # Create rich table for display
    table = Table(title="Project Analysis Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Project Root", str(project_info.project_root))
    table.add_row("Total Files", str(project_info.total_files))
    table.add_row("Total Identifiers", str(project_info.total_identifiers))
    table.add_row("Analysis Time", f"{project_info.analysis_time_ms:.2f}ms")
    table.add_row("Last Updated", project_info.last_updated.strftime("%Y-%m-%d %H:%M:%S"))
    
    if project_info.cache_size_bytes:
        table.add_row("Cache Size", f"{project_info.cache_size_bytes / 1024:.1f}KB")
    
    console.print(table)
    
    # Display file types
    if project_info.file_types:
        file_table = Table(title="File Types")
        file_table.add_column("Extension", style="cyan")
        file_table.add_column("Count", style="green")
        
        for ext, count in sorted(project_info.file_types.items(), key=lambda x: x[1], reverse=True):
            file_table.add_row(ext, str(count))
        
        console.print(file_table)
    
    # Display identifier types
    if project_info.identifier_types:
        id_table = Table(title="Identifier Types")
        id_table.add_column("Type", style="cyan")
        id_table.add_column("Count", style="green")
        
        for id_type, count in sorted(project_info.identifier_types.items(), key=lambda x: x[1], reverse=True):
            id_table.add_row(id_type, str(count))
        
        console.print(id_table)


def display_search_results(response, output_format: str):
    """Display search results."""
    
    if output_format == 'json':
        console.print(json.dumps(response.model_dump(), indent=2))
        return
    
    # Create rich table for results
    table = Table(title=f"Search Results for '{response.query}'")
    table.add_column("Identifier", style="cyan")
    table.add_column("Score", style="green")
    table.add_column("Strategy", style="yellow")
    table.add_column("Type", style="magenta")
    
    for result in response.results:
        score_str = f"{result.score:.3f}"
        table.add_row(
            result.identifier,
            score_str,
            result.strategy,
            result.match_type
        )
    
    console.print(table)
    
    # Display summary
    summary = Panel(
        f"Found {response.total_results} results in {response.search_time_ms:.2f}ms\n"
        f"Match type: {response.match_type}\n"
        f"Threshold: {response.threshold}",
        title="Search Summary",
        border_style="blue"
    )
    console.print(summary)


if __name__ == '__main__':
    cli()
