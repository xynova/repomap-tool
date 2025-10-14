"""
Search Controller for CLI.

This controller orchestrates search operations,
coordinating between code_search, code_analysis, and core services.
"""

from __future__ import annotations

import logging
from repomap_tool.core.config_service import get_config
from repomap_tool.core.logging_service import get_logger
from typing import List, Dict, Any, Optional

from ...models import SearchRequest, SearchResponse, MatchResult
from .base_controller import BaseController
from .view_models import (
    SearchViewModel,
    SymbolViewModel,
    ControllerConfig,
    AnalysisType,
)


logger = get_logger(__name__)


class SearchController(BaseController):
    """Controller for search operations.

    This controller orchestrates the search of identifiers in a project,
    coordinating between different domain services to provide
    LLM-optimized search results.
    """

    def __init__(
        self,
        repomap_service: Optional[Any] = None,
        search_engine: Optional[Any] = None,
        fuzzy_matcher: Optional[Any] = None,
        semantic_matcher: Optional[Any] = None,
        config: Optional[ControllerConfig] = None,
    ):
        """Initialize the SearchController.

        Args:
            repomap_service: Main RepoMap service for search operations
            search_engine: Search engine service
            fuzzy_matcher: Fuzzy matching service
            semantic_matcher: Semantic matching service
            config: Controller configuration
        """
        super().__init__(config)

        # All dependencies must be injected - no fallback allowed
        if fuzzy_matcher is None:
            raise ValueError("FuzzyMatcher must be injected - no fallback allowed")
        # repomap_service is injected after creation in explore commands
        # semantic_matcher is optional - only needed for semantic/hybrid matching

        self.repomap_service = repomap_service
        self.search_engine = search_engine
        self.fuzzy_matcher = fuzzy_matcher
        self.semantic_matcher = semantic_matcher

    def execute(self, search_request: SearchRequest) -> SearchViewModel:
        """Execute search operation and return ViewModel.

        Args:
            search_request: Search request parameters

        Returns:
            SearchViewModel with search results and metadata
        """
        if self.config is None:
            raise ValueError("ControllerConfig must be set before executing")

        self._log_operation(
            "search",
            {
                "query": search_request.query,
                "match_type": search_request.match_type,
                "threshold": search_request.threshold,
                "max_results": search_request.max_results,
            },
        )

        try:
            # Perform search using RepoMap service
            if not self.repomap_service:
                raise ValueError("RepoMap service not available")
            search_response = self.repomap_service.search_identifiers(search_request)

            # Convert SearchResponse to SearchViewModel
            view_model = self._build_search_view_model(search_response, search_request)

            self._log_operation(
                "search_complete",
                {
                    "total_results": view_model.total_results,
                    "execution_time": view_model.execution_time,
                    "token_count": view_model.token_count,
                },
            )

            return view_model

        except Exception as e:
            self.logger.error(f"Search operation failed: {e}")
            raise

    def _build_search_view_model(
        self, search_response: SearchResponse, search_request: SearchRequest
    ) -> SearchViewModel:
        """Build SearchViewModel from SearchResponse.

        Args:
            search_response: Raw search response from service
            search_request: Original search request

        Returns:
            SearchViewModel with structured data
        """
        # Convert MatchResult objects to SymbolViewModel objects
        symbol_view_models = []
        for result in search_response.results:
            symbol_view_model = SymbolViewModel(
                name=result.identifier,
                file_path=result.file_path or "Unknown",
                line_number=result.line_number or 0,
                symbol_type="identifier",  # Default type for search results
                signature=None,
                critical_lines=None,
                dependencies=None,
                centrality_score=None,
                impact_risk=None,
                importance_score=result.score,
                is_critical=result.score >= 0.8,  # High score = critical
            )
            symbol_view_models.append(symbol_view_model)

        # Estimate token count for the results
        token_count = self._estimate_tokens(search_response)

        # Determine compression level based on token count vs max tokens
        compression_level = self._determine_compression_level(token_count)

        return SearchViewModel(
            query=search_response.query,
            results=symbol_view_models,
            total_results=search_response.total_results,
            search_strategy=search_response.match_type,
            execution_time=search_response.search_time_ms
            / 1000.0,  # Convert to seconds
            token_count=token_count,
            max_tokens=self.config.max_tokens if self.config else 4000,
            compression_level=compression_level,
            threshold=search_response.threshold,
            match_type=search_response.match_type,
            search_time_ms=search_response.search_time_ms,
            cache_hit=search_response.cache_hit,
            spellcheck_suggestions=search_response.spellcheck_suggestions,
            metadata=search_response.metadata,
            performance_metrics=search_response.performance_metrics,
        )

    def _determine_compression_level(self, token_count: int) -> str:
        """Determine compression level based on token count.

        Args:
            token_count: Estimated token count

        Returns:
            Compression level string
        """
        if self.config is None:
            return "medium"

        ratio = token_count / self.config.max_tokens

        if ratio <= 0.5:
            return "low"
        elif ratio <= 0.8:
            return "medium"
        else:
            return "high"

    def _estimate_tokens(self, search_response: SearchResponse) -> int:
        """Estimate token count for search response.

        Args:
            search_response: Search response to estimate tokens for

        Returns:
            Estimated token count
        """
        # Base tokens for query and metadata
        base_tokens = 50

        # Tokens for each result
        result_tokens = 0.0
        for result in search_response.results:
            # Identifier name
            result_tokens += len(result.identifier.split()) * 1.3
            # File path
            if result.file_path:
                result_tokens += len(result.file_path.split()) * 1.3
            # Context if available
            if result.context:
                result_tokens += len(result.context.split()) * 1.3
            # Metadata
            result_tokens += 10  # Fixed overhead per result

        return int(base_tokens + result_tokens)
