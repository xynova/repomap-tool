"""
Search engine functionality.

This module handles different types of search operations (fuzzy, semantic, hybrid).
"""

import logging
from .config_service import get_config
from typing import List, Optional
from ..protocols import MatcherProtocol
from ..models import MatchResult

# Exception imports removed since we're using graceful degradation instead of raising exceptions


class SearchEngine:
    """Search engine service for handling different types of search operations."""

    def __init__(
        self,
        fuzzy_matcher: Optional[MatcherProtocol] = None,
        semantic_matcher: Optional[MatcherProtocol] = None,
        hybrid_matcher: Optional[MatcherProtocol] = None,
    ):
        """Initialize the search engine.

        Args:
            fuzzy_matcher: Fuzzy matching service
            semantic_matcher: Semantic matching service
            hybrid_matcher: Hybrid matching service
        """
        self.fuzzy_matcher = fuzzy_matcher
        self.semantic_matcher = semantic_matcher
        self.hybrid_matcher = hybrid_matcher

    def search(
        self,
        query: str,
        identifiers: List[str],
        search_type: str = "fuzzy",
        limit: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> List[MatchResult]:
        """Perform search based on the specified type.

        Args:
            query: Search query
            identifiers: List of identifiers to search in
            search_type: Type of search (fuzzy, semantic, hybrid)
            limit: Maximum number of results
            threshold: Threshold for hybrid search

        Returns:
            List of match results
        """
        if limit is None:
            limit = get_config("MAX_LIMIT", 10)
        if threshold is None:
            threshold = get_config("HYBRID_THRESHOLD", 0.3)

        if search_type == "fuzzy":
            if self.fuzzy_matcher is None:
                raise ValueError("Fuzzy matcher is not available")
            return fuzzy_search(query, identifiers, self.fuzzy_matcher, limit)
        elif search_type == "semantic":
            if self.semantic_matcher is None:
                raise ValueError("Semantic matcher is not available")
            return semantic_search(query, identifiers, self.semantic_matcher, limit)
        elif search_type == "hybrid":
            if self.hybrid_matcher is None:
                raise ValueError("Hybrid matcher is not available")
            return hybrid_search(
                query, identifiers, self.hybrid_matcher, limit, threshold
            )
        else:
            # Default to basic search
            return basic_search(query, identifiers, limit)


def fuzzy_search(
    query: str,
    identifiers: List[str],
    fuzzy_matcher: MatcherProtocol,
    limit: int = get_config("MAX_LIMIT", 10),
) -> List[MatchResult]:
    """Perform fuzzy search on identifiers."""
    # Input validation
    if not query or not identifiers:
        logging.warning("Empty query or identifiers provided")
        return []

    if not fuzzy_matcher:
        logging.warning("Fuzzy matcher not available")
        return []

    try:
        results = fuzzy_matcher.match_identifiers(query, set(identifiers))

        # Validate results and process
        match_results = []
        if results is not None and isinstance(results, (list, tuple)):
            # Convert to MatchResult format and limit results
            for identifier, score in results[:limit]:
                match_results.append(
                    MatchResult(
                        identifier=identifier,
                        score=score / 100.0,  # Convert percentage to 0-1 scale
                        strategy="fuzzy_match",
                        match_type="fuzzy",
                        context=f"Found in identifiers: {identifier}",
                    )
                )
        return match_results
    except Exception as e:
        logging.error(f"Fuzzy search failed: {e}")
        # Return empty list instead of raising for graceful degradation
        return []


def semantic_search(
    query: str,
    identifiers: List[str],
    semantic_matcher: MatcherProtocol,
    limit: int = get_config("MAX_LIMIT", 10),
) -> List[MatchResult]:
    """Perform semantic search on identifiers."""
    # Input validation
    if not query or not identifiers:
        logging.warning("Empty query or identifiers provided")
        return []

    if not semantic_matcher:
        logging.warning("Semantic matcher not available")
        return []

    try:
        # Use match_identifiers method from protocol instead of find_semantic_matches
        results = semantic_matcher.match_identifiers(query, set(identifiers))

        # Validate results and process
        match_results = []
        if results is not None and isinstance(results, (list, tuple)):
            # Convert to MatchResult format and limit results
            for identifier, score in results[:limit]:
                match_results.append(
                    MatchResult(
                        identifier=identifier,
                        score=score / 100.0,  # Convert percentage to 0-1 scale
                        strategy="semantic_match",
                        match_type="semantic",
                        context=f"Found in identifiers: {identifier}",
                    )
                )
        # If no semantic results found, fall back to basic search
        if not match_results:
            logging.info(
                f"No semantic results found for '{query}', falling back to basic search"
            )
            basic_results = basic_search(query, identifiers, limit)
            # Convert basic search results to semantic match type for consistency
            semantic_results = []
            for result in basic_results:
                semantic_results.append(
                    MatchResult(
                        identifier=result.identifier,
                        score=result.score,
                        strategy="semantic_fallback",
                        match_type="semantic",  # Keep semantic match type
                        context=result.context,
                    )
                )
            return semantic_results
        return match_results
    except Exception as e:
        logging.error(f"Semantic search failed: {e}")
        # Fall back to basic search if semantic search fails
        basic_results = basic_search(query, identifiers, limit)
        # Convert basic search results to semantic match type for consistency
        semantic_results = []
        for result in basic_results:
            semantic_results.append(
                MatchResult(
                    identifier=result.identifier,
                    score=result.score,
                    strategy="semantic_fallback",
                    match_type="semantic",  # Keep semantic match type
                    context=result.context,
                )
            )
        return semantic_results


def hybrid_search(
    query: str,
    identifiers: List[str],
    hybrid_matcher: MatcherProtocol,
    limit: int = get_config("MAX_LIMIT", 10),
    threshold: float = get_config("HYBRID_THRESHOLD", 0.3),
) -> List[MatchResult]:
    """Perform hybrid search on identifiers."""
    # Input validation
    if not query or not identifiers:
        logging.warning("Empty query or identifiers provided")
        return []

    if not hybrid_matcher:
        logging.warning("Hybrid matcher not available")
        return []

    try:
        # Ensure TF-IDF model is built for hybrid matcher
        if hasattr(hybrid_matcher, "build_tfidf_model") and identifiers:
            # Convert list to set for the build_tfidf_model method
            identifier_set = set(identifiers)
            hybrid_matcher.build_tfidf_model(identifier_set)

        results = hybrid_matcher.match_identifiers(query, set(identifiers), threshold)

        # Validate results and process
        match_results = []
        if results is not None and isinstance(results, (list, tuple)):
            # Convert to MatchResult format and limit results
            for identifier, score in results[:limit]:
                match_results.append(
                    MatchResult(
                        identifier=identifier,
                        score=score / 100.0,  # Convert percentage to 0-1 scale
                        strategy="hybrid_match",
                        match_type="hybrid",
                        context=f"Found in identifiers: {identifier}",
                    )
                )
        return match_results
    except Exception as e:
        logging.error(f"Hybrid search failed: {e}")
        # Return empty list instead of raising for graceful degradation
        return []


def basic_search(
    query: Optional[str],
    identifiers: Optional[List[str]],
    limit: int = get_config("MAX_LIMIT", 10),
) -> List[MatchResult]:
    """Perform basic string search on identifiers."""
    # Handle None inputs gracefully
    if query is None:
        logging.warning("Basic search received None query, returning empty results")
        return []

    if identifiers is None:
        logging.warning(
            "Basic search received None identifiers, returning empty results"
        )
        return []

    try:
        query_lower = query.lower()
    except AttributeError:
        logging.warning(
            f"Basic search received non-string query: {type(query)}, returning empty results"
        )
        return []

    results = []

    for identifier in identifiers:
        try:
            if query_lower in identifier.lower():
                # Simple scoring based on position and length
                score = 0.8  # Base score for substring matches
                if identifier.lower().startswith(query_lower):
                    score = 1.0  # Higher score for prefix matches (max allowed)

                results.append(
                    MatchResult(
                        identifier=identifier,
                        score=score,  # Let the model's validator handle normalization
                        strategy="basic_string_match",
                        match_type="fuzzy",  # Use fuzzy as the closest match type
                        context=f"Found in identifier: {identifier}",
                    )
                )
        except (AttributeError, TypeError):
            # Skip invalid identifiers
            continue

    # Sort by score (descending) and limit results
    results.sort(key=lambda x: x.score, reverse=True)
    return results[:limit]
