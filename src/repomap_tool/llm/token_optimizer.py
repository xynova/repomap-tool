from __future__ import annotations

import logging
from typing import Any, Optional
from enum import Enum
from dataclasses import dataclass

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

from repomap_tool.core.logging_service import get_logger

logger = get_logger(__name__)


class SelectionStrategy(str, Enum):
    CENTRALITY_BASED = "centrality_based"
    BREADTH_FIRST = "breadth_first"
    DEPTH_FIRST = "depth_first"
    HYBRID = "hybrid"


@dataclass
class ContextSelection:
    data: Any
    tokens_used: int


class TokenEstimator:
    """Token estimation using tiktoken for accurate token counting."""

    def __init__(self, model: str = "gpt-4"):
        """Initialize token estimator with model encoding.

        Args:
            model: Model name to use for tokenization (default: gpt-4)
        """
        self.model = model
        self._encoding = None
        if TIKTOKEN_AVAILABLE:
            try:
                self._encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                # Fallback to cl100k_base (GPT-4 encoding) if model not found
                logger.warning(
                    f"Model {model} not found in tiktoken, using cl100k_base encoding"
                )
                self._encoding = tiktoken.get_encoding("cl100k_base")
        else:
            logger.warning("tiktoken not available, using rough estimate")

    def estimate_tokens(self, data: Any) -> int:
        """Estimate token usage for a given data structure.

        Args:
            data: Data structure to estimate tokens for (string, dict, list, etc.)

        Returns:
            Estimated number of tokens
        """
        if self._encoding is None:
            # Fallback: rough estimate if tiktoken not available
            return len(str(data)) // 4

        # Convert data to string representation
        text = self._data_to_text(data)

        # Count tokens using tiktoken
        try:
            tokens = self._encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.warning(f"Error encoding text with tiktoken: {e}, using fallback")
            return len(text) // 4  # Fallback estimate

    def _data_to_text(self, data: Any) -> str:
        """Convert data structure to text for token counting.

        Args:
            data: Data structure to convert

        Returns:
            String representation of the data
        """
        if isinstance(data, str):
            return data
        elif isinstance(data, (dict, list)):
            import json

            try:
                return json.dumps(data, indent=2)
            except (TypeError, ValueError):
                return str(data)
        else:
            return str(data)


class TokenOptimizer:
    """Token budget management and context selection for LLM optimization."""

    def __init__(self, max_tokens: int = 8000, model: str = "gpt-4"):
        """Initialize token optimizer.

        Args:
            max_tokens: Maximum token budget for context
            model: Model name for tokenization (default: gpt-4)
        """
        self.max_tokens = max_tokens
        self.model = model
        self.token_estimator = TokenEstimator(model=model)
        logger.info(
            f"TokenOptimizer initialized with max_tokens: {max_tokens}, model: {model}"
        )

    def optimize_for_token_budget(
        self, content: str, max_tokens: int, model: str = "gpt-4"
    ) -> str:
        """Optimize content for token budget (compatibility with TokenOptimizerProtocol)."""
        # Use the existing optimize_context method
        context_selection = self.optimize_context(content)

        # If the content fits within the token budget, return it as-is
        if context_selection.tokens_used <= max_tokens:
            return content

        # Otherwise, return the optimized content
        return str(context_selection.data)

    def optimize_context(
        self,
        data: Any,
        strategy: SelectionStrategy = SelectionStrategy.CENTRALITY_BASED,
    ) -> ContextSelection:
        """Optimize context based on token budget and selection strategy."""
        estimated_tokens = self.token_estimator.estimate_tokens(data)

        if estimated_tokens <= self.max_tokens:
            logger.debug(f"Context fits within token budget: {estimated_tokens} tokens")
            return ContextSelection(data=data, tokens_used=estimated_tokens)

        logger.info(
            f"Context too large ({estimated_tokens} tokens), applying optimization strategy: {strategy}"
        )

        if strategy == SelectionStrategy.CENTRALITY_BASED:
            return self._select_by_centrality(data)
        elif strategy == SelectionStrategy.BREADTH_FIRST:
            return self._select_breadth_first(data)
        else:
            logger.warning(
                f"Unsupported context selection strategy: {strategy}, returning original data (truncated if too large)"
            )
            # Fallback: simple truncation using token-aware truncation
            return self._truncate_by_tokens(data, self.max_tokens)

    def _select_by_centrality(self, data: Any) -> ContextSelection:
        """Placeholder for centrality-based context selection."""
        logger.debug("Applying centrality-based context selection (placeholder)")
        # In a real implementation, this would involve more sophisticated graph analysis
        # For now, it's a simple placeholder.
        return ContextSelection(
            data=data, tokens_used=self.token_estimator.estimate_tokens(data) // 2
        )  # Arbitrary reduction

    def _select_breadth_first(self, data: Any) -> ContextSelection:
        """Placeholder for breadth-first context selection."""
        logger.debug("Applying breadth-first context selection (placeholder)")
        # In a real implementation, this would involve traversing a tree/graph breadth-first
        # For now, it's a simple placeholder.
        return ContextSelection(
            data=data, tokens_used=self.token_estimator.estimate_tokens(data) // 2
        )  # Arbitrary reduction

    def _truncate_by_tokens(self, data: Any, max_tokens: int) -> ContextSelection:
        """Truncate data to fit within token budget.

        Args:
            data: Data to truncate
            max_tokens: Maximum number of tokens

        Returns:
            ContextSelection with truncated data
        """
        text = self.token_estimator._data_to_text(data)

        if self.token_estimator._encoding is None:
            # Fallback: character-based truncation
            max_chars = max_tokens * 4  # Rough: 1 token ≈ 4 chars
            truncated = text[:max_chars]
            return ContextSelection(data=truncated, tokens_used=len(truncated) // 4)

        # Token-aware truncation
        try:
            tokens = self.token_estimator._encoding.encode(text)
            if len(tokens) <= max_tokens:
                return ContextSelection(data=data, tokens_used=len(tokens))

            # Truncate tokens and decode back to text
            truncated_tokens = tokens[:max_tokens]
            truncated_text = self.token_estimator._encoding.decode(truncated_tokens)

            # Try to preserve data structure if possible
            if isinstance(data, str):
                truncated_data = truncated_text
            else:
                # For complex structures, just use truncated text
                truncated_data = truncated_text

            return ContextSelection(data=truncated_data, tokens_used=max_tokens)
        except Exception as e:
            logger.warning(f"Error in token-aware truncation: {e}, using fallback")
            max_chars = max_tokens * 4
            truncated = text[:max_chars]
            return ContextSelection(data=truncated, tokens_used=len(truncated) // 4)
