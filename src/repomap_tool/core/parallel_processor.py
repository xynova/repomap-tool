"""
Parallel processing module for repomap-tool.

This module provides sophisticated parallel processing capabilities with
progress tracking, error handling, and performance monitoring.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import logging

from .config_service import get_config
from .logging_service import get_logger

from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)
from rich.console import Console

from ..exceptions import ParallelProcessingError


@dataclass
class ProcessingStats:
    """Statistics for parallel processing operations."""

    total_files: int = 0
    processed_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    total_identifiers: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    errors: List[Tuple[str, str]] = field(
        default_factory=list
    )  # (file_path, error_message)

    @property
    def processing_time(self) -> float:
        """Get total processing time in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.successful_files / self.total_files) * 100

    @property
    def files_per_second(self) -> float:
        """Get files processed per second."""
        if self.processing_time == 0:
            return 0.0
        return self.processed_files / self.processing_time

    def add_error(self, file_path: str, error_message: str) -> None:
        """Add an error to the statistics."""
        self.errors.append((file_path, error_message))
        self.failed_files += 1

    def add_success(self, identifiers_count: int) -> None:
        """Add a successful file processing."""
        self.successful_files += 1
        self.total_identifiers += identifiers_count

    def finalize(self) -> None:
        """Finalize the statistics."""
        self.end_time = time.time()


class ParallelTagExtractor:
    """
    Professional parallel tag extraction with progress tracking and error handling.

    This class provides sophisticated parallel processing capabilities for
    extracting identifiers from project files with comprehensive monitoring
    and error handling.
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        enable_progress: bool = True,
        console: Optional[Console] = None,
    ):
        """
        Initialize the parallel tag extractor.

        Args:
            max_workers: Maximum number of worker threads (default: from config)
            enable_progress: Whether to show progress bars
            console: Rich console for progress display
        """
        # Use config default if not provided
        if max_workers is None:
            max_workers = get_config("MAX_WORKERS", 4)
        self.max_workers = max_workers
        self.enable_progress = enable_progress
        if console is None:
            raise ValueError("Console must be injected - no fallback allowed")
        self.console = console
        self.logger = get_logger(__name__)

        # Thread safety
        self._lock = threading.Lock()
        self._stats = ProcessingStats()

        # Performance tracking
        self._worker_times: Dict[int, List[float]] = {}
        self._file_sizes: Dict[str, int] = {}

    def extract_tags_parallel(
        self,
        files: List[str],
        project_root: str,
        repo_map: Any,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> Tuple[List[str], ProcessingStats]:
        """
        Extract tags from files in parallel with comprehensive monitoring.

        Args:
            files: List of file paths to process
            project_root: Root directory of the project
            repo_map: Repository map object for tag extraction
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (identifiers, processing_stats)
        """
        self._stats = ProcessingStats(total_files=len(files))
        all_identifiers: List[str] = []

        if not files:
            self._stats.finalize()
            return all_identifiers, self._stats

        # Create progress bar if enabled
        progress_context = (
            self._create_progress_context() if self.enable_progress else nullcontext()
        )

        with progress_context as progress:
            task_id = None
            if progress:
                task_id = progress.add_task(
                    f"Processing {len(files)} files with {self.max_workers} workers...",
                    total=len(files),
                )

            # Process files in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all file processing tasks
                future_to_file = {
                    executor.submit(
                        self._process_file_with_monitoring,
                        file_path,
                        project_root,
                        repo_map,
                    ): file_path
                    for file_path in files
                }

                # Collect results as they complete
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    worker_id = threading.current_thread().ident or 0

                    try:
                        start_time = time.time()
                        identifiers = future.result()
                        processing_time = time.time() - start_time

                        # Update statistics
                        with self._lock:
                            all_identifiers.extend(identifiers)
                            self._stats.add_success(len(identifiers))
                            self._stats.processed_files += 1

                            # Track worker performance
                            if worker_id not in self._worker_times:
                                self._worker_times[worker_id] = []
                            self._worker_times[worker_id].append(processing_time)

                        # Update progress
                        if progress and task_id:
                            progress.update(task_id, advance=1)

                        # Call progress callback
                        if progress_callback:
                            progress_callback(file_path, len(identifiers))

                        # Log successful processing
                        self.logger.debug(
                            f"Processed {file_path}: {len(identifiers)} identifiers "
                            f"({processing_time:.3f}s)"
                        )

                    except Exception as e:
                        error_msg = str(e)
                        with self._lock:
                            self._stats.add_error(file_path, error_msg)
                            self._stats.processed_files += 1

                        # Log error
                        self.logger.warning(
                            f"Failed to process {file_path}: {error_msg}"
                        )

                        # Update progress even for failures
                        if progress and task_id:
                            progress.update(task_id, advance=1)

        # Finalize statistics
        self._stats.finalize()

        # Log final statistics
        self._log_processing_summary()

        return all_identifiers, self._stats

    def _process_file_with_monitoring(
        self, file_path: str, project_root: str, repo_map: Any
    ) -> List[str]:
        """
        Process a single file with comprehensive monitoring.

        Args:
            file_path: Path to the file to process
            project_root: Root directory of the project
            repo_map: Repository map object

        Returns:
            List of identifiers extracted from the file
        """
        try:
            # Track file size for performance analysis
            abs_path = Path(project_root) / file_path
            if abs_path.exists():
                self._file_sizes[file_path] = abs_path.stat().st_size

            # Extract tags using the repository map
            if repo_map is not None:
                abs_path_str = str(abs_path)
                tags = repo_map.get_tags(abs_path_str, file_path)

                # Extract identifier names
                identifiers = []
                for tag in tags:
                    if hasattr(tag, "name") and tag.name:
                        identifiers.append(tag.name)

                return identifiers
            else:
                self.logger.warning(f"Repository map is None for {file_path}")
                return []

        except Exception as e:
            # Re-raise with context for better error handling
            raise ParallelProcessingError(
                f"Failed to process file {file_path}: {str(e)}"
            ) from e

    def _create_progress_context(self) -> Progress:
        """Create a progress bar context."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TextColumn("[progress.completed]{task.completed}/{task.total}"),
            TextColumn("•"),
            TimeElapsedColumn(),
            console=self.console,
            transient=False,
        )

    def _log_processing_summary(self) -> None:
        """Log a comprehensive processing summary."""
        stats = self._stats

        # Calculate performance metrics
        avg_worker_time = 0.0
        if self._worker_times:
            all_times = [t for times in self._worker_times.values() for t in times]
            avg_worker_time = sum(all_times) / len(all_times) if all_times else 0.0

        # Log summary
        self.logger.info(
            f"Parallel processing complete:\n"
            f"  Files: {stats.processed_files}/{stats.total_files} "
            f"({stats.success_rate:.1f}% success rate)\n"
            f"  Identifiers: {stats.total_identifiers} total\n"
            f"  Time: {stats.processing_time:.2f}s ({stats.files_per_second:.1f} files/s)\n"
            f"  Workers: {self.max_workers} (avg {avg_worker_time:.3f}s per file)\n"
            f"  Errors: {stats.failed_files} files failed"
        )

        # Log detailed errors if any
        if stats.errors:
            self.logger.warning("Processing errors:")
            for file_path, error in stats.errors[:5]:  # Show first 5 errors
                self.logger.warning(f"  {file_path}: {error}")
            if len(stats.errors) > 5:
                self.logger.warning(f"  ... and {len(stats.errors) - 5} more errors")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics."""
        stats = self._stats

        # Calculate worker performance
        worker_stats = {}
        for worker_id, times in self._worker_times.items():
            worker_stats[f"worker_{worker_id}"] = {
                "files_processed": len(times),
                "avg_time": sum(times) / len(times) if times else 0.0,
                "total_time": sum(times),
            }

        # Calculate file size statistics
        file_sizes = list(self._file_sizes.values())
        size_stats = {}
        if file_sizes:
            size_stats = {
                "total_size_mb": sum(file_sizes) / (1024 * 1024),
                "avg_size_kb": sum(file_sizes) / len(file_sizes) / 1024,
                "largest_file_kb": max(file_sizes) / 1024,
                "smallest_file_kb": min(file_sizes) / 1024,
            }

        return {
            "processing_stats": {
                "total_files": stats.total_files,
                "processed_files": stats.processed_files,
                "successful_files": stats.successful_files,
                "failed_files": stats.failed_files,
                "success_rate": stats.success_rate,
                "total_identifiers": stats.total_identifiers,
                "processing_time": stats.processing_time,
                "files_per_second": stats.files_per_second,
            },
            "worker_performance": worker_stats,
            "file_size_stats": size_stats,
            "configuration": {
                "max_workers": self.max_workers,
                "enable_progress": self.enable_progress,
            },
        }


class nullcontext:
    """Null context manager for when progress is disabled."""

    def __enter__(self) -> None:
        return None

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass
