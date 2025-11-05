from __future__ import annotations

from typing import Any, Optional
from dataclasses import dataclass

from repomap_tool.core.logging_service import get_logger

logger = get_logger(__name__)


@dataclass
class ContextSelection:
    """Context selection result (kept for compatibility)."""

    data: Any
    tokens_used: int = 0


class SelectionStrategy:
    """Selection strategy enum (kept for compatibility)."""

    CENTRALITY_BASED = "centrality_based"
    BREADTH_FIRST = "breadth_first"
    DEPTH_FIRST = "depth_first"
    HYBRID = "hybrid"


class ContextSelector:
    """Selects and optimizes context for LLM consumption (simplified - no longer uses TokenOptimizer)."""

    def __init__(self, max_tokens: int = 8000):
        """Initialize ContextSelector.

        Args:
            max_tokens: Maximum tokens for context (kept for compatibility, not enforced)
        """
        self.max_tokens = max_tokens
        logger.info(f"ContextSelector initialized with max_tokens: {max_tokens}")

    def select_context(
        self,
        data: Any,
        max_tokens: Optional[int] = None,
        strategy: Any = None,  # Strategy no longer used
    ) -> ContextSelection:
        """Select optimal context (simplified - returns data as-is).

        Args:
            data: Data to return
            max_tokens: Maximum tokens (kept for compatibility, not enforced)
            strategy: Selection strategy (kept for compatibility, not used)

        Returns:
            ContextSelection with data as-is
        """
        logger.debug(
            f"ContextSelector.select_context called (no-op, returns data as-is)"
        )
        return ContextSelection(data=data, tokens_used=0)
