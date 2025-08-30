"""
Search engine functionality.

This module handles different types of search operations (fuzzy, semantic, hybrid).
"""

import logging
from typing import List, Any, Optional
from ..models import MatchResult


def fuzzy_search(
    query: str,
    identifiers: List[str],
    fuzzy_matcher: Any,
    limit: int = 10,
) -> List[MatchResult]:
    """Perform fuzzy search on identifiers."""
    if not fuzzy_matcher:
        logging.warning("Fuzzy matcher not available")
        return []

    try:
        results = fuzzy_matcher.match_identifiers(query, identifiers)
        # Convert to MatchResult format and limit results
        match_results = []
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
        return []


def semantic_search(
    query: str,
    identifiers: List[str],
    semantic_matcher: Any,
    limit: int = 10,
) -> List[MatchResult]:
    """Perform semantic search on identifiers."""
    if not semantic_matcher:
        logging.warning("Semantic matcher not available")
        return []

    try:
        results = semantic_matcher.find_semantic_matches(query, identifiers)
        # Convert to MatchResult format and limit results
        match_results = []
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
    hybrid_matcher: Any,
    limit: int = 10,
) -> List[MatchResult]:
    """Perform hybrid search on identifiers."""
    if not hybrid_matcher:
        logging.warning("Hybrid matcher not available")
        return []

    try:
        # Ensure TF-IDF model is built for hybrid matcher
        if hasattr(hybrid_matcher, "build_tfidf_model") and identifiers:
            # Convert list to set for the build_tfidf_model method
            identifier_set = set(identifiers)
            hybrid_matcher.build_tfidf_model(identifier_set)

        results = hybrid_matcher.match_identifiers(query, set(identifiers))
        # Convert to MatchResult format and limit results
        match_results = []
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
        return []


def basic_search(
    query: Optional[str],
    identifiers: Optional[List[str]],
    limit: int = 10,
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
