#!/usr/bin/env python3
"""
Parallel Processing Demo for repomap-tool.

This script demonstrates the professional parallel processing capabilities
with progress tracking, error handling, and performance monitoring.
"""

import sys
import time
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from repomap_tool.core.parallel_processor import ParallelTagExtractor
from repomap_tool.core.repo_map import DockerRepoMap
from repomap_tool.models import RepoMapConfig
from rich.console import Console
from rich.panel import Panel

console = Console()


def demo_parallel_processing():
    """Demonstrate parallel processing capabilities."""
    
    console.print(Panel.fit(
        "[bold blue]Parallel Processing Demo[/bold blue]\n"
        "Professional tag extraction with progress tracking and monitoring",
        border_style="blue"
    ))
    
    # Initialize configuration
    config = RepoMapConfig(
        project_root=".",
        verbose=True,
        fuzzy_match={"enabled": True, "threshold": 70},
        semantic_match={"enabled": True, "threshold": 50}
    )
    
    # Initialize RepoMap
    console.print("🔧 [yellow]Initializing RepoMap...[/yellow]")
    repomap = DockerRepoMap(config)
    
    # Get project files
    console.print("📁 [yellow]Scanning project files...[/yellow]")
    project_files = repomap._get_project_files()
    console.print(f"Found [green]{len(project_files)}[/green] files to process")
    
    # Initialize parallel processor
    console.print("⚡ [yellow]Setting up parallel processor...[/yellow]")
    parallel_processor = ParallelTagExtractor(
        max_workers=4,
        enable_progress=True,
        console=console
    )
    
    # Process files in parallel
    console.print("\n🚀 [bold green]Starting parallel processing...[/bold green]")
    start_time = time.time()
    
    identifiers, stats = parallel_processor.extract_tags_parallel(
        files=project_files,
        project_root=str(config.project_root),
        repo_map=repomap.repo_map,
        progress_callback=lambda file_path, count: console.print(
            f"  ✅ {file_path}: {count} identifiers", style="dim"
        )
    )
    
    total_time = time.time() - start_time
    
    # Display results
    console.print("\n" + "="*60)
    console.print("[bold green]🎉 Processing Complete![/bold green]")
    console.print("="*60)
    
    # Performance summary
    console.print(Panel(
        f"[bold]Performance Summary[/bold]\n\n"
        f"📊 Files Processed: [green]{stats.processed_files}/{stats.total_files}[/green]\n"
        f"✅ Success Rate: [green]{stats.success_rate:.1f}%[/green]\n"
        f"🔍 Identifiers Found: [green]{stats.total_identifiers}[/green]\n"
        f"⏱️  Total Time: [green]{total_time:.2f}s[/green]\n"
        f"🚀 Files/Second: [green]{stats.files_per_second:.1f}[/green]\n"
        f"👥 Workers Used: [green]{parallel_processor.max_workers}[/green]",
        title="📈 Results",
        border_style="green"
    ))
    
    # Detailed metrics
    metrics = parallel_processor.get_performance_metrics()
    
    console.print(Panel(
        f"[bold]Detailed Metrics[/bold]\n\n"
        f"📁 File Size Stats:\n"
        f"  • Total Size: {metrics['file_size_stats'].get('total_size_mb', 0):.1f} MB\n"
        f"  • Average Size: {metrics['file_size_stats'].get('avg_size_kb', 0):.1f} KB\n"
        f"  • Largest File: {metrics['file_size_stats'].get('largest_file_kb', 0):.1f} KB\n\n"
        f"👥 Worker Performance:\n",
        title="🔍 Detailed Analysis",
        border_style="blue"
    ))
    
    # Show worker performance
    for worker_id, worker_stats in metrics['worker_performance'].items():
        console.print(
            f"  • {worker_id}: {worker_stats['files_processed']} files "
            f"({worker_stats['avg_time']:.3f}s avg)",
            style="dim"
        )
    
    # Show sample identifiers
    if identifiers:
        console.print(Panel(
            f"[bold]Sample Identifiers Found[/bold]\n\n"
            f"{chr(10).join('• ' + ident for ident in sorted(identifiers)[:20])}\n"
            f"{'...' if len(identifiers) > 20 else ''}",
            title="🏷️  Identifiers",
            border_style="yellow"
        ))
    
    # Error summary if any
    if stats.errors:
        console.print(Panel(
            f"[bold red]Errors Encountered[/bold red]\n\n"
            f"{chr(10).join(f'• {file}: {error}' for file, error in stats.errors[:5])}\n"
            f"{'...' if len(stats.errors) > 5 else ''}",
            title="⚠️  Errors",
            border_style="red"
        ))
    
    console.print("\n[bold green]✨ Demo complete![/bold green]")


def compare_sequential_vs_parallel():
    """Compare sequential vs parallel processing performance."""
    
    console.print(Panel.fit(
        "[bold blue]Performance Comparison[/bold blue]\n"
        "Sequential vs Parallel Processing",
        border_style="blue"
    ))
    
    # Initialize
    config = RepoMapConfig(project_root=".", verbose=False)
    repomap = DockerRepoMap(config)
    project_files = repomap._get_project_files()
    
    # Sequential processing
    console.print("🐌 [yellow]Running sequential processing...[/yellow]")
    start_time = time.time()
    
    identifiers_seq = []
    for file_path in project_files:
        try:
            abs_path = str(Path(config.project_root) / file_path)
            tags = repomap.repo_map.get_tags(abs_path, file_path)
            for tag in tags:
                if hasattr(tag, "name") and tag.name:
                    identifiers_seq.append(tag.name)
        except Exception as e:
            console.print(f"  ❌ Error processing {file_path}: {e}", style="red")
    
    sequential_time = time.time() - start_time
    
    # Parallel processing
    console.print("⚡ [yellow]Running parallel processing...[/yellow]")
    parallel_processor = ParallelTagExtractor(max_workers=4, enable_progress=False)
    
    start_time = time.time()
    identifiers_par, stats = parallel_processor.extract_tags_parallel(
        files=project_files,
        project_root=str(config.project_root),
        repo_map=repomap.repo_map
    )
    parallel_time = time.time() - start_time
    
    # Comparison
    speedup = sequential_time / parallel_time if parallel_time > 0 else 0
    
    console.print(Panel(
        f"[bold]Performance Comparison[/bold]\n\n"
        f"🐌 Sequential: [red]{sequential_time:.2f}s[/red]\n"
        f"⚡ Parallel: [green]{parallel_time:.2f}s[/green]\n"
        f"🚀 Speedup: [bold green]{speedup:.1f}x[/bold green]\n\n"
        f"📊 Identifiers Found:\n"
        f"  • Sequential: {len(identifiers_seq)}\n"
        f"  • Parallel: {len(identifiers_par)}\n"
        f"  • Match: {'✅' if len(identifiers_seq) == len(identifiers_par) else '❌'}",
        title="📈 Comparison Results",
        border_style="green"
    ))


if __name__ == "__main__":
    try:
        # Run the main demo
        demo_parallel_processing()
        
        console.print("\n" + "="*60)
        
        # Run performance comparison
        compare_sequential_vs_parallel()
        
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)
