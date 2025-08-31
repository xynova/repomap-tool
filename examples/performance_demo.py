#!/usr/bin/env python3
"""
Performance Improvements Demo

This script demonstrates the performance improvements implemented in the repomap-tool,
including parallel processing, progress tracking, and performance monitoring.
"""

import os
import sys
import time
import tempfile
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from repomap_tool.models import RepoMapConfig, PerformanceConfig
from repomap_tool.core.repo_map import DockerRepoMap
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def create_test_project(base_dir: Path, num_files: int = 50) -> Path:
    """Create a test project with the specified number of files."""
    project_dir = base_dir / f"test_project_{num_files}_files"
    project_dir.mkdir(exist_ok=True)

    # Create subdirectories
    (project_dir / "src").mkdir(exist_ok=True)
    (project_dir / "tests").mkdir(exist_ok=True)
    (project_dir / "docs").mkdir(exist_ok=True)

    # Create Python files with identifiers
    for i in range(num_files):
        if i < num_files // 3:
            # Source files
            file_path = project_dir / "src" / f"module_{i}.py"
        elif i < 2 * num_files // 3:
            # Test files
            file_path = project_dir / "tests" / f"test_module_{i}.py"
        else:
            # Documentation
            file_path = project_dir / "docs" / f"doc_{i}.md"

        # Create file content with identifiers
        if file_path.suffix == ".py":
            content = f'''"""
Module {i} - Test module for performance demonstration.
"""

class TestClass{i}:
    """Test class {i}."""
    
    def __init__(self):
        self.value = {i}
    
    def get_value(self):
        """Get the value."""
        return self.value
    
    def set_value(self, new_value):
        """Set the value."""
        self.value = new_value

def test_function_{i}():
    """Test function {i}."""
    return f"function_{i}"

CONSTANT_{i} = {i}
'''
        else:
            content = f"# Documentation {i}\n\nThis is documentation file {i}."

        file_path.write_text(content)

    return project_dir


def benchmark_analysis(project_path: Path, config: RepoMapConfig, label: str) -> dict:
    """Benchmark project analysis with given configuration."""
    console.print(f"\n[bold blue]Benchmarking: {label}[/bold blue]")

    start_time = time.time()

    try:
        # Initialize RepoMap
        repomap = DockerRepoMap(config)

        # Analyze project
        if config.performance.enable_progress:
            project_info = repomap.analyze_project_with_progress()
        else:
            project_info = repomap.analyze_project()

        # Get performance metrics
        metrics = repomap.get_performance_metrics()

        end_time = time.time()
        total_time = end_time - start_time

        return {
            "label": label,
            "total_time": total_time,
            "project_info": project_info,
            "metrics": metrics,
            "success": True,
        }

    except Exception as e:
        console.print(f"[red]Error in {label}: {e}[/red]")
        return {
            "label": label,
            "total_time": time.time() - start_time,
            "error": str(e),
            "success": False,
        }


def display_results(results: list):
    """Display benchmark results in a table."""
    console.print("\n[bold green]Benchmark Results[/bold green]")

    table = Table(title="Performance Comparison")
    table.add_column("Configuration", style="cyan")
    table.add_column("Total Files", style="green")
    table.add_column("Total Identifiers", style="green")
    table.add_column("Processing Time", style="yellow")
    table.add_column("Files/Second", style="blue")
    table.add_column("Success Rate", style="magenta")

    for result in results:
        if not result["success"]:
            table.add_row(
                result["label"],
                "ERROR",
                "ERROR",
                f"{result['total_time']:.2f}s",
                "ERROR",
                "ERROR",
            )
            continue

        project_info = result["project_info"]
        metrics = result["metrics"]

        # Extract metrics
        processing_stats = metrics.get("processing_stats", {})
        files_per_second = processing_stats.get("files_per_second", 0)
        success_rate = processing_stats.get("success_rate", 0)

        table.add_row(
            result["label"],
            str(project_info.total_files),
            str(project_info.total_identifiers),
            f"{result['total_time']:.2f}s",
            f"{files_per_second:.1f}",
            f"{success_rate:.1f}%",
        )

    console.print(table)


def display_detailed_metrics(results: list):
    """Display detailed performance metrics."""
    console.print("\n[bold green]Detailed Performance Metrics[/bold green]")

    for result in results:
        if not result["success"]:
            continue

        console.print(f"\n[bold cyan]{result['label']}[/bold cyan]")

        metrics = result["metrics"]
        config = metrics.get("configuration", {})
        processing_stats = metrics.get("processing_stats", {})

        # Configuration details
        config_table = Table(title="Configuration")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="green")

        config_table.add_row("Max Workers", str(config.get("max_workers", "N/A")))
        config_table.add_row(
            "Parallel Threshold", str(config.get("parallel_threshold", "N/A"))
        )
        config_table.add_row(
            "Progress Enabled", str(config.get("enable_progress", "N/A"))
        )
        config_table.add_row(
            "Monitoring Enabled", str(config.get("enable_monitoring", "N/A"))
        )

        console.print(config_table)

        # Processing statistics
        if processing_stats:
            stats_table = Table(title="Processing Statistics")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="green")

            stats_table.add_row(
                "Total Files", str(processing_stats.get("total_files", 0))
            )
            stats_table.add_row(
                "Successful Files", str(processing_stats.get("successful_files", 0))
            )
            stats_table.add_row(
                "Failed Files", str(processing_stats.get("failed_files", 0))
            )
            stats_table.add_row(
                "Success Rate", f"{processing_stats.get('success_rate', 0):.1f}%"
            )
            stats_table.add_row(
                "Total Identifiers", str(processing_stats.get("total_identifiers", 0))
            )
            stats_table.add_row(
                "Processing Time", f"{processing_stats.get('processing_time', 0):.2f}s"
            )
            stats_table.add_row(
                "Files per Second", f"{processing_stats.get('files_per_second', 0):.1f}"
            )

            console.print(stats_table)


def main():
    """Main demonstration function."""
    console.print(
        Panel.fit(
            "[bold blue]RepoMap Performance Improvements Demo[/bold blue]\n"
            "This demo shows the performance improvements including:\n"
            "• Parallel processing for large projects\n"
            "• Progress tracking with Rich\n"
            "• Performance monitoring and metrics\n"
            "• Development-focused error handling (fail fast)",
            border_style="blue",
        )
    )

    # Create temporary directory for test projects
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Test with different project sizes
        project_sizes = [10, 50, 100]
        results = []

        for size in project_sizes:
            console.print(
                f"\n[bold yellow]Creating test project with {size} files...[/bold yellow]"
            )
            project_path = create_test_project(temp_path, size)

            # Test 1: Sequential processing (no parallel)
            config_sequential = RepoMapConfig(
                project_root=str(project_path),
                performance=PerformanceConfig(
                    max_workers=1,
                    parallel_threshold=1000,  # Won't trigger parallel
                    enable_progress=False,
                    enable_monitoring=True,
                    allow_fallback=False,  # Fail fast
                ),
            )

            result_sequential = benchmark_analysis(
                project_path, config_sequential, f"Sequential ({size} files)"
            )
            results.append(result_sequential)

            # Test 2: Parallel processing
            config_parallel = RepoMapConfig(
                project_root=str(project_path),
                performance=PerformanceConfig(
                    max_workers=4,
                    parallel_threshold=5,  # Will trigger parallel
                    enable_progress=True,
                    enable_monitoring=True,
                    allow_fallback=False,  # Fail fast
                ),
            )

            result_parallel = benchmark_analysis(
                project_path, config_parallel, f"Parallel ({size} files)"
            )
            results.append(result_parallel)

        # Display results
        display_results(results)
        display_detailed_metrics(results)

        # Performance improvement summary
        console.print("\n[bold green]Performance Improvement Summary[/bold green]")

        for i in range(0, len(results), 2):
            if i + 1 < len(results):
                sequential = results[i]
                parallel = results[i + 1]

                if sequential["success"] and parallel["success"]:
                    improvement = (
                        (sequential["total_time"] / parallel["total_time"])
                        if parallel["total_time"] > 0
                        else 0
                    )
                    console.print(
                        f"• {sequential['label']} vs {parallel['label']}: {improvement:.1f}x faster"
                    )

        console.print("\n[bold green]Demo completed![/bold green]")


if __name__ == "__main__":
    main()
