#!/usr/bin/env python3
"""
Advanced parallel processing demo for repomap-tool.

This script demonstrates how to use the parallel processing capabilities
for efficient tag extraction from a large number of files.
"""

import os
import time
import logging
from pathlib import Path
from typing import List, Tuple, Any

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)

from repomap_tool.core.config_service import get_config
from repomap_tool.core.logging_service import get_logger
from repomap_tool.core.file_scanner import get_project_files
from repomap_tool.code_analysis.tree_sitter_parser import TreeSitterParser
from repomap_tool.core.tag_cache import TreeSitterTagCache
from repomap_tool.models import RepoMapConfig

# Removed ParallelTagExtractor import


logger = get_logger(__name__)


def process_file_and_extract_tags(
    file_path: str, project_root: str, tree_sitter_parser: TreeSitterParser
) -> List[str]:
    """Process a single file and extract tags using the provided parser."""
    try:
        tags = tree_sitter_parser.get_tags(file_path)
        return [tag.name for tag in tags if tag.name]
    except Exception as e:
        logger.warning(f"Error processing {file_path}: {e}")
        return []


def main():
    console = Console()
    console.print("[bold green]🚀 Starting Parallel Processing Demo[/bold green]")

    # Setup a dummy project directory
    temp_dir = Path("./temp_demo_project")
    temp_dir.mkdir(exist_ok=True, parents=True)
    console.print(f"Created temporary project directory: {temp_dir}")

    # Create a large number of dummy Python files
    num_files = 100
    for i in range(num_files):
        file_content = f"""
# This is a dummy Python file number {i}

def func_{i}(arg1, arg2):
    # Some comment
    variable_{i} = arg1 + arg2
    return variable_{i}

class Class_{i}:
    def method_{i}(self):
        pass
"""
        (temp_dir / f"file_{i}.py").write_text(file_content)
    console.print(f"Created {num_files} dummy Python files.")

    # Configure RepoMapConfig for the demo
    config = RepoMapConfig(project_root=str(temp_dir), verbose=False)

    # Initialize TreeSitterParser and TagCache
    cache_dir = Path.home() / ".repomap-tool" / "cache_demo"
    cache_dir.mkdir(parents=True, exist_ok=True)
    tag_cache = TreeSitterTagCache(cache_dir=cache_dir)
    tree_sitter_parser = TreeSitterParser(project_root=str(temp_dir), cache=tag_cache)

    # Get all project files
    console.print("[bold yellow]Scanning project files...[/bold yellow]")
    project_files = get_project_files(str(temp_dir), config.verbose)
    console.print(f"Found {len(project_files)} files.")

    # Start parallel processing
    console.print("[bold yellow]Starting parallel tag extraction...[/bold yellow]")
    start_time = time.time()

    all_extracted_tags: List[str] = []
    successful_files = 0
    failed_files = 0
    total_identifiers = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task_id = progress.add_task(
            f"Processing {len(project_files)} files...", total=len(project_files)
        )

        from concurrent.futures import ThreadPoolExecutor, as_completed

        max_workers = get_config("MAX_WORKERS", 4)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(
                    process_file_and_extract_tags,
                    file_path,
                    str(temp_dir),
                    tree_sitter_parser,
                ): file_path
                for file_path in project_files
            }

            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    identifiers = future.result()
                    all_extracted_tags.extend(identifiers)
                    successful_files += 1
                    total_identifiers += len(identifiers)
                except Exception as e:
                    failed_files += 1
                    logger.error(f"Failed to process {file_path}: {e}")
                finally:
                    progress.update(task_id, advance=1)

    end_time = time.time()
    duration = end_time - start_time
    console.print("[bold green]✅ Parallel Processing Complete[/bold green]")
    console.print(f"Total files processed: {num_files}")
    console.print(f"Successful files: {successful_files}")
    console.print(f"Failed files: {failed_files}")
    console.print(f"Total identifiers extracted: {total_identifiers}")
    console.print(f"Time taken: {duration:.2f} seconds")

    # Cleanup
    console.print(
        "[bold yellow]Cleaning up temporary project directory...[/bold yellow]"
    )
    import shutil

    shutil.rmtree(temp_dir)
    console.print("[bold green]Cleanup complete.[/bold green]")


if __name__ == "__main__":
    main()
