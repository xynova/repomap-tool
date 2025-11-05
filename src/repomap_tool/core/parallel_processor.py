"""
Parallel processing module for repomap-tool.

This module provides sophisticated parallel processing capabilities with
progress tracking, error handling, and performance monitoring.
"""

import logging
from typing import Any, Optional

from .config_service import get_config
from .logging_service import get_logger


# Removed ProcessingStats dataclass


# Removed ParallelTagExtractor class


class nullcontext:
    """Null context manager for when progress is disabled."""

    def __enter__(self) -> None:
        return None

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass
