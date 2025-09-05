"""
Context selector for LLM optimization.

This module selects the most relevant context based on token budget
and user intent to maximize the value of information provided to LLMs.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SelectionStrategy(Enum):
    """Context selection strategies."""

    BREADTH_FIRST = "breadth_first"  # Show many files with less detail
    DEPTH_FIRST = "depth_first"  # Show few files with more detail
    HYBRID = "hybrid"  # Balance breadth and depth
    CENTRALITY_BASED = "centrality_based"  # Prioritize by dependency centrality


@dataclass
class ContextSelection:
    """Result of context selection process."""

    selected_symbols: List[Dict[str, Any]]
    total_tokens: int
    strategy_used: SelectionStrategy
    coverage_percentage: float
    priority_breakdown: Dict[str, int]


class ContextSelector:
    """Selects optimal context based on token budget and user intent."""

    def __init__(self, dependency_graph=None, context_manager=None):
        self.dependency_graph = dependency_graph
        self.context_manager = context_manager
        self.default_strategy = SelectionStrategy.HYBRID

    def select_optimal_context(
        self,
        all_symbols: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]] = None,
        token_budget: int = 1024,
        strategy: Optional[SelectionStrategy] = None,
    ) -> ContextSelection:
        """Select optimal symbols to include given token budget.

        Args:
            all_symbols: List of all available symbols
            user_context: User context and intent information
            token_budget: Available token budget
            strategy: Selection strategy to use

        Returns:
            ContextSelection with selected symbols and metadata
        """
        if not all_symbols:
            return ContextSelection(
                selected_symbols=[],
                total_tokens=0,
                strategy_used=strategy or self.default_strategy,
                coverage_percentage=0.0,
                priority_breakdown={},
            )

        # Determine strategy
        if strategy is None:
            strategy = self._determine_optimal_strategy(
                all_symbols, user_context, token_budget
            )

        # Apply selection strategy
        if strategy == SelectionStrategy.BREADTH_FIRST:
            selected_symbols = self._breadth_first_selection(all_symbols, token_budget)
        elif strategy == SelectionStrategy.DEPTH_FIRST:
            selected_symbols = self._depth_first_selection(all_symbols, token_budget)
        elif strategy == SelectionStrategy.CENTRALITY_BASED:
            selected_symbols = self._centrality_based_selection(
                all_symbols, token_budget
            )
        else:  # HYBRID
            selected_symbols = self._hybrid_selection(all_symbols, token_budget)

        # Calculate metrics
        total_tokens = self._estimate_selection_tokens(selected_symbols)
        coverage_percentage = len(selected_symbols) / len(all_symbols) * 100
        priority_breakdown = self._calculate_priority_breakdown(selected_symbols)

        return ContextSelection(
            selected_symbols=selected_symbols,
            total_tokens=total_tokens,
            strategy_used=strategy,
            coverage_percentage=coverage_percentage,
            priority_breakdown=priority_breakdown,
        )

    def balance_breadth_vs_depth(
        self, symbols: List[Dict[str, Any]], budget: int
    ) -> List[Dict[str, Any]]:
        """Balance showing many files vs detailed information.

        Args:
            symbols: List of symbols to balance
            budget: Token budget available

        Returns:
            Balanced list of symbols
        """
        if not symbols:
            return []

        # Calculate optimal balance based on budget
        if budget < 512:
            # Small budget: prioritize breadth
            return self._breadth_first_selection(symbols, budget)
        elif budget > 2048:
            # Large budget: can afford depth
            return self._depth_first_selection(symbols, budget)
        else:
            # Medium budget: hybrid approach
            return self._hybrid_selection(symbols, budget)

    def _determine_optimal_strategy(
        self,
        symbols: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]],
        token_budget: int,
    ) -> SelectionStrategy:
        """Determine optimal selection strategy based on context."""

        # Strategy based on budget size
        if token_budget < 512:
            return SelectionStrategy.BREADTH_FIRST
        elif token_budget > 2048:
            return SelectionStrategy.DEPTH_FIRST

        # Strategy based on user context
        if user_context:
            intent = user_context.get("intent", "").lower()

            if any(word in intent for word in ["overview", "summary", "list", "files"]):
                return SelectionStrategy.BREADTH_FIRST
            elif any(
                word in intent
                for word in ["detail", "implementation", "code", "function"]
            ):
                return SelectionStrategy.DEPTH_FIRST
            elif any(
                word in intent for word in ["dependency", "impact", "relationship"]
            ):
                return SelectionStrategy.CENTRALITY_BASED

        # Strategy based on symbol characteristics
        high_centrality_count = sum(
            1 for s in symbols if s.get("centrality_score", 0) > 0.8
        )

        if high_centrality_count > len(symbols) * 0.3:
            # Many important symbols: prioritize breadth
            return SelectionStrategy.BREADTH_FIRST
        elif high_centrality_count < len(symbols) * 0.1:
            # Few important symbols: prioritize depth
            return SelectionStrategy.DEPTH_FIRST
        else:
            # Mixed importance: use hybrid
            return SelectionStrategy.HYBRID

    def _breadth_first_selection(
        self, symbols: List[Dict[str, Any]], token_budget: int
    ) -> List[Dict[str, Any]]:
        """Select many symbols with less detail per symbol."""
        # Sort by importance (centrality, impact, etc.)
        sorted_symbols = sorted(
            symbols,
            key=lambda s: (
                s.get("centrality_score", 0),
                s.get("impact_risk", 0),
                s.get("complexity_score", 0),
            ),
            reverse=True,
        )

        selected = []
        current_tokens = 0
        tokens_per_symbol = token_budget // min(
            len(symbols), 20
        )  # Aim for at least 20 symbols

        for symbol in sorted_symbols:
            symbol_tokens = self._estimate_symbol_tokens(symbol, detail_level="minimal")

            if current_tokens + symbol_tokens <= token_budget:
                # Add symbol with minimal detail
                minimal_symbol = self._create_minimal_symbol(symbol)
                selected.append(minimal_symbol)
                current_tokens += symbol_tokens
            else:
                break

        return selected

    def _depth_first_selection(
        self, symbols: List[Dict[str, Any]], token_budget: int
    ) -> List[Dict[str, Any]]:
        """Select fewer symbols with more detail per symbol."""
        # Sort by importance
        sorted_symbols = sorted(
            symbols,
            key=lambda s: (
                s.get("centrality_score", 0),
                s.get("impact_risk", 0),
                s.get("complexity_score", 0),
            ),
            reverse=True,
        )

        selected = []
        current_tokens = 0

        # Focus on top symbols with full detail
        for symbol in sorted_symbols[:10]:  # Limit to top 10
            symbol_tokens = self._estimate_symbol_tokens(symbol, detail_level="full")

            if current_tokens + symbol_tokens <= token_budget:
                # Add symbol with full detail
                detailed_symbol = self._create_detailed_symbol(symbol)
                selected.append(detailed_symbol)
                current_tokens += symbol_tokens
            else:
                # Try with medium detail
                medium_symbol = self._create_medium_symbol(symbol)
                medium_tokens = self._estimate_symbol_tokens(
                    medium_symbol, detail_level="medium"
                )

                if current_tokens + medium_tokens <= token_budget:
                    selected.append(medium_symbol)
                    current_tokens += medium_tokens
                else:
                    break

        return selected

    def _centrality_based_selection(
        self, symbols: List[Dict[str, Any]], token_budget: int
    ) -> List[Dict[str, Any]]:
        """Select symbols based on dependency centrality."""
        if not self.dependency_graph:
            # Fall back to hybrid if no dependency graph
            return self._hybrid_selection(symbols, token_budget)

        # Sort by centrality score
        sorted_symbols = sorted(
            symbols, key=lambda s: s.get("centrality_score", 0), reverse=True
        )

        selected = []
        current_tokens = 0

        # Select high-centrality symbols first
        high_centrality = [
            s for s in sorted_symbols if s.get("centrality_score", 0) > 0.7
        ]
        medium_centrality = [
            s for s in sorted_symbols if 0.4 <= s.get("centrality_score", 0) <= 0.7
        ]
        low_centrality = [
            s for s in sorted_symbols if s.get("centrality_score", 0) < 0.4
        ]

        # Allocate budget: 60% high, 30% medium, 10% low
        high_budget = int(token_budget * 0.6)
        medium_budget = int(token_budget * 0.3)
        low_budget = token_budget - high_budget - medium_budget

        # Select from each category
        selected.extend(
            self._select_within_budget(high_centrality, high_budget, "full")
        )
        selected.extend(
            self._select_within_budget(medium_centrality, medium_budget, "medium")
        )
        selected.extend(
            self._select_within_budget(low_centrality, low_budget, "minimal")
        )

        return selected

    def _hybrid_selection(
        self, symbols: List[Dict[str, Any]], token_budget: int
    ) -> List[Dict[str, Any]]:
        """Hybrid approach balancing breadth and depth."""
        # Start with breadth-first to get overview
        breadth_budget = int(token_budget * 0.7)
        depth_budget = token_budget - breadth_budget

        # Get breadth selection
        breadth_symbols = self._breadth_first_selection(symbols, breadth_budget)

        # Use remaining budget for depth on top symbols
        if depth_budget > 0:
            top_symbols = [s for s in symbols if s.get("centrality_score", 0) > 0.8][:3]
            depth_symbols = self._depth_first_selection(top_symbols, depth_budget)

            # Merge selections, prioritizing depth for top symbols
            merged = []
            depth_symbol_names = {s.get("name") for s in depth_symbols}

            for symbol in breadth_symbols:
                if symbol.get("name") in depth_symbol_names:
                    # Use detailed version
                    detailed = next(
                        s for s in depth_symbols if s.get("name") == symbol.get("name")
                    )
                    merged.append(detailed)
                else:
                    merged.append(symbol)

            return merged

        return breadth_symbols

    def _select_within_budget(
        self, symbols: List[Dict[str, Any]], budget: int, detail_level: str
    ) -> List[Dict[str, Any]]:
        """Select symbols within a specific budget with given detail level."""
        selected = []
        current_tokens = 0

        for symbol in symbols:
            symbol_tokens = self._estimate_symbol_tokens(symbol, detail_level)

            if current_tokens + symbol_tokens <= budget:
                if detail_level == "full":
                    selected_symbol = self._create_detailed_symbol(symbol)
                elif detail_level == "medium":
                    selected_symbol = self._create_medium_symbol(symbol)
                else:
                    selected_symbol = self._create_minimal_symbol(symbol)

                selected.append(selected_symbol)
                current_tokens += symbol_tokens
            else:
                break

        return selected

    def _create_minimal_symbol(self, symbol: Dict[str, Any]) -> Dict[str, Any]:
        """Create minimal detail version of symbol."""
        return {
            "name": symbol.get("name", ""),
            "file_path": symbol.get("file_path", ""),
            "line_number": symbol.get("line_number", 0),
            "symbol_type": symbol.get("symbol_type", ""),
            "centrality_score": symbol.get("centrality_score", 0),
            "impact_risk": symbol.get("impact_risk", 0),
            # Minimal implementation details
            "critical_lines": (
                symbol.get("critical_lines", [])[:1]
                if symbol.get("critical_lines")
                else []
            ),
            "signature": symbol.get("signature", ""),
            "dependencies": (
                symbol.get("dependencies", [])[:2] if symbol.get("dependencies") else []
            ),
        }

    def _create_medium_symbol(self, symbol: Dict[str, Any]) -> Dict[str, Any]:
        """Create medium detail version of symbol."""
        return {
            "name": symbol.get("name", ""),
            "file_path": symbol.get("file_path", ""),
            "line_number": symbol.get("line_number", 0),
            "symbol_type": symbol.get("symbol_type", ""),
            "centrality_score": symbol.get("centrality_score", 0),
            "impact_risk": symbol.get("impact_risk", 0),
            # Medium implementation details
            "critical_lines": (
                symbol.get("critical_lines", [])[:2]
                if symbol.get("critical_lines")
                else []
            ),
            "signature": symbol.get("signature", ""),
            "dependencies": (
                symbol.get("dependencies", [])[:3] if symbol.get("dependencies") else []
            ),
            "usage_examples": (
                symbol.get("usage_examples", [])[:1]
                if symbol.get("usage_examples")
                else []
            ),
        }

    def _create_detailed_symbol(self, symbol: Dict[str, Any]) -> Dict[str, Any]:
        """Create full detail version of symbol."""
        return {
            "name": symbol.get("name", ""),
            "file_path": symbol.get("file_path", ""),
            "line_number": symbol.get("line_number", 0),
            "symbol_type": symbol.get("symbol_type", ""),
            "centrality_score": symbol.get("centrality_score", 0),
            "impact_risk": symbol.get("impact_risk", 0),
            # Full implementation details
            "critical_lines": (
                symbol.get("critical_lines", [])[:3]
                if symbol.get("critical_lines")
                else []
            ),
            "signature": symbol.get("signature", ""),
            "dependencies": (
                symbol.get("dependencies", [])[:5] if symbol.get("dependencies") else []
            ),
            "usage_examples": (
                symbol.get("usage_examples", [])[:2]
                if symbol.get("usage_examples")
                else []
            ),
            "error_cases": (
                symbol.get("error_cases", [])[:2] if symbol.get("error_cases") else []
            ),
            "complexity_score": symbol.get("complexity_score", 0),
        }

    def _estimate_symbol_tokens(
        self, symbol: Dict[str, Any], detail_level: str = "medium"
    ) -> int:
        """Estimate token count for a symbol at given detail level."""
        base_tokens = 50  # Base tokens for symbol metadata

        # Add tokens for critical lines
        critical_lines = symbol.get("critical_lines", [])
        if detail_level == "minimal":
            critical_tokens = len(critical_lines[:1]) * 20
        elif detail_level == "medium":
            critical_tokens = len(critical_lines[:2]) * 20
        else:  # full
            critical_tokens = len(critical_lines[:3]) * 20

        # Add tokens for dependencies
        dependencies = symbol.get("dependencies", [])
        if detail_level == "minimal":
            dep_tokens = len(dependencies[:2]) * 10
        elif detail_level == "medium":
            dep_tokens = len(dependencies[:3]) * 10
        else:  # full
            dep_tokens = len(dependencies[:5]) * 10

        # Add tokens for usage examples
        usage_examples = symbol.get("usage_examples", [])
        if detail_level == "minimal":
            usage_tokens = 0
        elif detail_level == "medium":
            usage_tokens = len(usage_examples[:1]) * 30
        else:  # full
            usage_tokens = len(usage_examples[:2]) * 30

        return base_tokens + critical_tokens + dep_tokens + usage_tokens

    def _estimate_selection_tokens(self, symbols: List[Dict[str, Any]]) -> int:
        """Estimate total token count for selected symbols."""
        total_tokens = 0

        for symbol in symbols:
            # Determine detail level based on content
            if len(symbol.get("critical_lines", [])) > 2:
                detail_level = "full"
            elif len(symbol.get("critical_lines", [])) > 1:
                detail_level = "medium"
            else:
                detail_level = "minimal"

            total_tokens += self._estimate_symbol_tokens(symbol, detail_level)

        return total_tokens

    def _calculate_priority_breakdown(
        self, symbols: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate breakdown of symbols by priority level."""
        breakdown = {
            "high_priority": 0,  # centrality > 0.8
            "medium_priority": 0,  # 0.4 <= centrality <= 0.8
            "low_priority": 0,  # centrality < 0.4
        }

        for symbol in symbols:
            centrality = symbol.get("centrality_score", 0)
            if centrality > 0.8:
                breakdown["high_priority"] += 1
            elif centrality >= 0.4:
                breakdown["medium_priority"] += 1
            else:
                breakdown["low_priority"] += 1

        return breakdown
