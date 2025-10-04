"""
Output formatting utilities for RepoMap-Tool CLI.

This module contains functions for displaying project information and search results
in various formats (JSON, table, text, markdown).
"""

from typing import Optional, Literal, Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from tabulate import tabulate

from ...models import ProjectInfo, SearchResponse

# Note: console should be obtained via get_console(ctx) in functions that need it
from ..utils.console import get_console
import click


def display_project_info(
    project_info: ProjectInfo,
    output_format: Literal["text", "json"],
    template_config: Optional[Dict[str, Any]] = None,
) -> None:
    """Display project analysis results."""
    # Get console from Click context
    ctx = click.get_current_context(silent=True)
    console = get_console(ctx)

    if output_format == "json":
        console.print(project_info.model_dump_json(indent=2))
        return

    # Handle text format (rich, hierarchical, LLM-optimized)
    if output_format == "text":
        use_emojis = not (template_config and template_config.get("no_emojis", False))

        # Rich hierarchical format for LLM consumption
        lines = []
        lines.append(
            "🧠 LLM-Optimized Project Analysis" if use_emojis else "Project Analysis"
        )
        lines.append("=" * 60)
        lines.append("")

        # Summary section
        lines.append("📊 SUMMARY:")
        lines.append(f"├── Project Root: {project_info.project_root}")
        lines.append(f"├── Total Files: {project_info.total_files}")
        lines.append(f"├── Total Identifiers: {project_info.total_identifiers}")
        lines.append(f"└── Analysis Time: {project_info.analysis_time_ms:.2f}ms")
        lines.append("")

        # File types breakdown
        if project_info.file_types:
            lines.append("📁 FILE TYPES:")
            for ext, count in project_info.file_types.items():
                lines.append(f"├── {ext}: {count} files")
            lines.append("")

        # Identifier types breakdown
        if project_info.identifier_types:
            lines.append("🏷️ IDENTIFIER TYPES:")
            for id_type, count in project_info.identifier_types.items():
                lines.append(f"├── {id_type}: {count} identifiers")
            lines.append("")

        # Cache statistics
        if project_info.cache_stats:
            lines.append("💾 CACHE STATISTICS:")
            for key, value in project_info.cache_stats.items():
                lines.append(f"├── {key.replace('_', ' ').title()}: {value}")
            lines.append("")

        console.print("\n".join(lines))
        return


def display_search_results(
    search_response: SearchResponse,
    output_format: Literal["json", "text"],
    template_config: Optional[Dict[str, Any]] = None,
) -> None:
    """Display search results."""
    # Get console from Click context
    ctx = click.get_current_context(silent=True)
    console = get_console(ctx)

    if output_format == "json":
        console.print(search_response.model_dump_json(indent=2))
        return

    if not search_response.results:
        console.print(
            Panel("No results found.", title="Search Results", style="yellow")
        )
        return

    # For 'text' format, use clean ASCII table (LLM-friendly, no ANSI codes)
    if output_format == "text":
        # Prepare table data
        table_data = []
        for i, result in enumerate(search_response.results, 1):
            # Format file path - show full path for LLM consumption
            file_display = result.file_path if result.file_path else "N/A"

            # Format line number
            line_display = str(result.line_number) if result.line_number else "N/A"

            table_data.append(
                [
                    str(i),
                    result.identifier,
                    file_display,
                    line_display,
                    f"{result.score:.3f}",
                    result.strategy,
                ]
            )

        # Create clean ASCII table
        headers = ["Rank", "Identifier", "File Path", "Line", "Score", "Strategy"]
        table_str = tabulate(table_data, headers=headers, tablefmt="grid")

        # Print with title
        console.print(f"🔍 Search Results ({len(search_response.results)} found)")
        console.print(table_str)

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


def display_dependency_results(
    results: Dict[str, Any],
    output_format: Literal["json", "text"],
) -> None:
    """Display dependency analysis results."""
    # Get console from Click context
    ctx = click.get_current_context(silent=True)
    console = get_console(ctx)

    if output_format == "json":
        import json

        console.print(json.dumps(results, indent=2, default=str))
        return

    # For 'text' format, use clean ASCII table (LLM-friendly, no ANSI codes)
    if output_format == "text":
        # Prepare table data
        table_data = [
            ["Total Files", str(results.get("total_files", 0))],
            ["Total Dependencies", str(results.get("total_dependencies", 0))],
            ["Circular Dependencies", str(results.get("circular_dependencies", 0))],
        ]

        # Create clean ASCII table
        headers = ["Metric", "Value"]
        table_str = tabulate(table_data, headers=headers, tablefmt="grid")

        # Print with title
        console.print("📊 Dependency Analysis Results")
        console.print(table_str)


def display_cycles_results(
    cycles: List[List[str]],
    output_format: Literal["json", "text"],
) -> None:
    """Display circular dependency results."""
    # Get console from Click context
    ctx = click.get_current_context(silent=True)
    console = get_console(ctx)

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

    # For 'text' format, use clean ASCII table (LLM-friendly, no ANSI codes)
    if output_format == "text":
        # Prepare table data
        table_data = []
        for i, cycle in enumerate(cycles, 1):
            cycle_str = " → ".join(cycle + [cycle[0]])  # Close the cycle
            table_data.append([str(i), cycle_str])

        # Create clean ASCII table
        headers = ["Cycle #", "Dependencies"]
        table_str = tabulate(table_data, headers=headers, tablefmt="grid")

        # Print with title
        console.print(f"🔄 Circular Dependencies ({len(cycles)} found)")
        console.print(table_str)
