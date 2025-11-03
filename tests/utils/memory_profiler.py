"""Memory profiling utilities for tests."""

import os
import gc
import psutil
import tracemalloc
from contextlib import contextmanager
from typing import Dict, Any, Optional


@contextmanager
def memory_profile(threshold_mb: float = 10.0, always_show: bool = False):
    """Context manager to profile memory usage.

    Args:
        threshold_mb: Only report if memory increase exceeds this threshold (MB)
        always_show: If True, always show output regardless of threshold
    """
    process = psutil.Process(os.getpid())

    # Get baseline memory
    gc.collect()
    start_memory = process.memory_info().rss / 1024 / 1024

    tracemalloc.start()

    try:
        yield
    finally:
        # Get final memory
        gc.collect()
        end_memory = process.memory_info().rss / 1024 / 1024
        memory_diff = end_memory - start_memory

        # Get traced allocations
        current, peak = tracemalloc.get_traced_memory()
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")

        if always_show or memory_diff > threshold_mb:
            print(f"\n{'='*60}")
            print(f"📊 MEMORY PROFILE")
            print(f"{'='*60}")
            print(f"Start:     {start_memory:.1f} MB")
            print(f"End:       {end_memory:.1f} MB")
            print(
                f"Increase:  {memory_diff:.1f} MB {'⚠️' if memory_diff > threshold_mb else ''}"
            )
            print(f"Traced:    {current / 1024 / 1024:.1f} MB")
            print(f"Peak:      {peak / 1024 / 1024:.1f} MB")

            if top_stats:
                print(f"\nTop 10 allocations:")
                for stat in top_stats[:10]:
                    # Format the stat nicely
                    size_mb = stat.size / 1024 / 1024
                    count = stat.count
                    traceback = stat.traceback
                    if traceback:
                        filename = traceback[0].filename if traceback else "unknown"
                        lineno = traceback[0].lineno if traceback else 0
                        print(
                            f"  {filename}:{lineno}: {size_mb:.2f} MB ({count} allocations)"
                        )

            print(f"{'='*60}\n")

        tracemalloc.stop()


def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage statistics.

    Returns:
        Dictionary with memory statistics:
        - rss_mb: Resident Set Size in MB
        - vms_mb: Virtual Memory Size in MB
        - percent: Memory usage percentage
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()

    return {
        "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size
        "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size
        "percent": process.memory_percent(),
    }


def get_all_pytest_processes() -> list[Dict[str, Any]]:
    """Get all pytest processes and their memory usage.

    Returns:
        List of dictionaries with process information
    """
    processes = []
    for proc in psutil.process_iter(["pid", "name", "memory_info", "cmdline"]):
        try:
            cmdline = proc.info["cmdline"]
            if cmdline and any("pytest" in arg for arg in cmdline):
                memory_mb = proc.info["memory_info"].rss / 1024 / 1024
                processes.append(
                    {
                        "pid": proc.info["pid"],
                        "name": proc.info["name"],
                        "memory_mb": memory_mb,
                        "cmdline": " ".join(cmdline[:3]),  # First 3 args for brevity
                    }
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return processes
