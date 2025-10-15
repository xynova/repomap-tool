from __future__ import annotations

import logging
from typing import Any, List, Optional

from repomap_tool.core.logging_service import get_logger
from .token_optimizer import SelectionStrategy, ContextSelection, TokenOptimizer

logger = get_logger(__name__)


class ContextSelector:
    """Selects and optimizes context for LLM consumption based on various strategies."""

    def __init__(self, token_optimizer: TokenOptimizer, max_tokens: int = 8000):
        if token_optimizer is None:
            raise ValueError("TokenOptimizer must be injected - no fallback allowed")

        self.token_optimizer = token_optimizer
        self.max_tokens = max_tokens
        logger.info(f"ContextSelector initialized with max_tokens: {max_tokens}")

    def select_context(
        self,
        data: Any,
        max_tokens: Optional[int] = None,
        strategy: SelectionStrategy = SelectionStrategy.CENTRALITY_BASED,
    ) -> ContextSelection:
        """Select optimal context based on token budget and strategy."""
        effective_max_tokens = max_tokens if max_tokens is not None else self.max_tokens
        logger.debug(
            f"Selecting context with strategy: {strategy}, effective_max_tokens: {effective_max_tokens}"
        )
        return self.token_optimizer.optimize_context(data, strategy)
