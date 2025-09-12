"""
Output formatting utilities for RepoMap-Tool CLI.

This module contains functions for displaying project information and search results
in various formats (JSON, table, text, markdown).
"""

from typing import Optional, Literal, Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ...models import ProjectInfo, SearchResponse

# Create console instance for this module
console = Console()


def display_project_info(
    project_info: ProjectInfo,
    output_format: Literal["json", "text", "markdown", "table"],
    template_config: Optional[Dict[str, Any]] = None,
) -> None:
    """Display project analysis results."""

    if output_format == "json":
        console.print(project_info.model_dump_json(indent=2))
        return

    # Handle text and markdown formats
    if output_format in ["markdown", "text"]:
        use_emojis = not (template_config and template_config.get("no_emojis", False))
        
        if output_format == "markdown":
            # Markdown format
            lines = []
            lines.append("# 📊 Project Analysis Results" if use_emojis else "# Project Analysis Results")
            lines.append("")
            lines.append(f"**Project Root:** {project_info.project_root}")
            lines.append(f"**Total Files:** {project_info.total_files}")
            lines.append(f"**Total Identifiers:** {project_info.total_identifiers}")
            lines.append(f"**Analysis Time:** {project_info.analysis_time_ms:.2f}ms")
            lines.append("")
            
            if project_info.file_types:
                lines.append("## File Types")
                for ext, count in project_info.file_types.items():
                    lines.append(f"- **{ext}:** {count}")
                lines.append("")
            
            if project_info.identifier_types:
                lines.append("## Identifier Types")
                for id_type, count in project_info.identifier_types.items():
                    lines.append(f"- **{id_type}:** {count}")
                lines.append("")
            
            if project_info.cache_stats:
                lines.append("## Cache Statistics")
                for key, value in project_info.cache_stats.items():
                    lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
                    
            output = "\n".join(lines)
        else:  # text
            # Text format
            lines = []
            lines.append("📊 Project Analysis Results" if use_emojis else "Project Analysis Results")
            lines.append("=" * 30)
            lines.append(f"Project Root: {project_info.project_root}")
            lines.append(f"Total Files: {project_info.total_files}")
            lines.append(f"Total Identifiers: {project_info.total_identifiers}")
            lines.append(f"Analysis Time: {project_info.analysis_time_ms:.2f}ms")
            lines.append("")
            
            if project_info.file_types:
                lines.append("File Types:")
                for ext, count in project_info.file_types.items():
                    lines.append(f"  {ext}: {count}")
                lines.append("")
            
            if project_info.identifier_types:
                lines.append("Identifier Types:")
                for id_type, count in project_info.identifier_types.items():
                    lines.append(f"  {id_type}: {count}")
                lines.append("")
            
            if project_info.cache_stats:
                lines.append("Cache Statistics:")
                for key, value in project_info.cache_stats.items():
                    lines.append(f"  {key.replace('_', ' ').title()}: {value}")
                    
            output = "\n".join(lines)

        console.print(output)
        return

    # Table format
    if output_format == "table":
        table = Table(title="📊 Project Analysis Results")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")

        table.add_row("Project Root", str(project_info.project_root))
        table.add_row("Total Files", str(project_info.total_files))
        table.add_row("Total Identifiers", str(project_info.total_identifiers))

        # File types
        if project_info.file_types:
            file_types_str = ", ".join(
                [f"{ext}: {count}" for ext, count in project_info.file_types.items()]
            )
            table.add_row("File Types", file_types_str)

        # Identifier types
        if project_info.identifier_types:
            id_types_str = ", ".join(
                [
                    f"{id_type}: {count}"
                    for id_type, count in project_info.identifier_types.items()
                ]
            )
            table.add_row("Identifier Types", id_types_str)

        # Cache stats
        if project_info.cache_stats:
            cache_str = ", ".join(
                [f"{key}: {value}" for key, value in project_info.cache_stats.items()]
            )
            table.add_row("Cache Stats", cache_str)

        console.print(table)


def display_search_results(
    search_response: SearchResponse,
    output_format: Literal["json", "text", "table"],
    template_config: Optional[Dict[str, Any]] = None,
) -> None:
    """Display search results."""

    if output_format == "json":
        console.print(search_response.model_dump_json(indent=2))
        return

    if not search_response.results:
        console.print(
            Panel("No results found.", title="Search Results", style="yellow")
        )
        return

    if output_format == "table":
        table = Table(title=f"🔍 Search Results ({len(search_response.results)} found)")
        table.add_column("Rank", justify="right", style="cyan", no_wrap=True)
        table.add_column("Identifier", style="green")
        table.add_column("Score", justify="right", style="magenta")
        table.add_column("Type", style="blue")

        for i, result in enumerate(search_response.results, 1):
            table.add_row(
                str(i),
                result.identifier,
                f"{result.score:.3f}",
                result.match_type or "unknown",
            )

        console.print(table)

        # Show performance metrics if available
        if search_response.performance_metrics:
            metrics_table = Table(title="⚡ Performance Metrics")
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Value", style="yellow")

            for key, value in search_response.performance_metrics.items():
                if isinstance(value, float):
                    formatted_value = f"{value:.3f}"
                else:
                    formatted_value = str(value)
                metrics_table.add_row(key.replace("_", " ").title(), formatted_value)

            console.print(metrics_table)

    elif output_format == "text":
        console.print(f"\n🔍 Search Results ({len(search_response.results)} found)\n")

        for i, result in enumerate(search_response.results, 1):
            console.print(
                f"{i:2d}. [green]{result.identifier}[/green] "
                f"(score: [magenta]{result.score:.3f}[/magenta], "
                f"type: [blue]{result.match_type or 'unknown'}[/blue])"
            )

        # Show performance metrics
        if search_response.performance_metrics:
            console.print("\n⚡ Performance Metrics:")
            for key, value in search_response.performance_metrics.items():
                if isinstance(value, float):
                    formatted_value = f"{value:.3f}"
                else:
                    formatted_value = str(value)
                console.print(f"  {key.replace('_', ' ').title()}: {formatted_value}")


def display_dependency_results(
    results: Dict[str, Any],
    output_format: Literal["json", "text", "table"],
) -> None:
    """Display dependency analysis results."""

    if output_format == "json":
        import json

        console.print(json.dumps(results, indent=2, default=str))
        return

    if output_format == "table":
        # Create summary table
        table = Table(title="📊 Dependency Analysis Results")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")

        table.add_row("Total Files", str(results.get("total_files", 0)))
        table.add_row("Total Dependencies", str(results.get("total_dependencies", 0)))
        table.add_row(
            "Circular Dependencies", str(results.get("circular_dependencies", 0))
        )

        console.print(table)

    elif output_format == "text":
        console.print(f"\n📊 Dependency Analysis Results\n")
        console.print(f"Total Files: {results.get('total_files', 0)}")
        console.print(f"Total Dependencies: {results.get('total_dependencies', 0)}")
        console.print(
            f"Circular Dependencies: {results.get('circular_dependencies', 0)}"
        )


def display_cycles_results(
    cycles: List[List[str]],
    output_format: Literal["json", "text", "table"],
) -> None:
    """Display circular dependency results."""

    if output_format == "json":
        import json

        console.print(json.dumps({"cycles": cycles}, indent=2))
        return

    if not cycles:
        console.print(
            Panel(
                "No circular dependencies found! 🎉",
                title="Cycle Detection",
                style="green",
            )
        )
        return

    if output_format == "table":
        table = Table(title=f"🔄 Circular Dependencies ({len(cycles)} found)")
        table.add_column("Cycle #", justify="right", style="cyan", no_wrap=True)
        table.add_column("Dependencies", style="red")

        for i, cycle in enumerate(cycles, 1):
            cycle_str = " → ".join(cycle + [cycle[0]])  # Close the cycle
            table.add_row(str(i), cycle_str)

        console.print(table)

    elif output_format == "text":
        console.print(f"\n🔄 Circular Dependencies ({len(cycles)} found)\n")

        for i, cycle in enumerate(cycles, 1):
            cycle_str = " → ".join(cycle + [cycle[0]])  # Close the cycle
            console.print(f"{i:2d}. [red]{cycle_str}[/red]")
