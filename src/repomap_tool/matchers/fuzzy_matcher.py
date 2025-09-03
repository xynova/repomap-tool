#!/usr/bin/env python3
"""
fuzzy_matcher.py - Core fuzzy matching functionality for docker-repomap

This module provides intelligent identifier discovery using multiple fuzzy matching strategies.
"""

import re
import logging
from typing import List, Set, Tuple, Dict, Optional, Any
from fuzzywuzzy import fuzz
from ..core.cache_manager import CacheManager


# Configure logging
logger = logging.getLogger(__name__)


class FuzzyMatcher:
    """
    A fuzzy matching engine for discovering related identifiers in codebases.

    Supports multiple matching strategies:
    - prefix: Matches identifiers that start with the query
    - suffix: Matches identifiers that end with the query
    - substring: Matches identifiers containing the query
    - levenshtein: Matches based on edit distance
    - word: Matches based on word overlap
    """

    def __init__(
        self,
        threshold: int = 70,
        strategies: Optional[List[str]] = None,
        cache_results: bool = True,
        verbose: bool = True,
        cache_max_size: int = 1000,
        cache_ttl: int = 3600,
    ):
        """
        Initialize the fuzzy matcher.

        Args:
            threshold: Similarity threshold (0-100, default: 70)
            strategies: List of matching strategies to use
            cache_results: Whether to cache match results
            verbose: Whether to log matching details
            cache_max_size: Maximum number of cache entries
            cache_ttl: Time to live for cache entries in seconds
        """
        self.threshold = max(0, min(100, threshold))  # Clamp to 0-100
        self.strategies = strategies or ["prefix", "substring", "levenshtein"]
        self.cache_results = cache_results
        self.verbose = verbose
        self.enabled = True  # Add enabled attribute for compatibility

        # Initialize cache manager with bounded memory
        self.cache_manager: Optional[CacheManager]
        if self.cache_results:
            self.cache_manager = CacheManager(
                max_size=cache_max_size, ttl=cache_ttl, enable_memory_monitoring=True
            )
        else:
            self.cache_manager = None

        # Validate strategies
        valid_strategies = {"prefix", "suffix", "substring", "levenshtein", "word"}
        invalid_strategies = set(self.strategies) - valid_strategies
        if invalid_strategies:
            raise ValueError(
                f"Invalid strategies: {invalid_strategies}. Valid: {valid_strategies}"
            )

        if self.verbose:
            logger.info(
                f"FuzzyMatcher initialized with threshold={self.threshold}, strategies={self.strategies}, cache_max_size={cache_max_size}"
            )

    def match_identifiers(
        self, query: str, all_identifiers: Set[str]
    ) -> List[Tuple[str, int]]:
        """
        Match a query against all identifiers using multiple strategies.

        Args:
            query: The identifier to search for
            all_identifiers: Set of all available identifiers

        Returns:
            List of (identifier, score) tuples, sorted by score (highest first)
        """
        if not query or not all_identifiers:
            return []

        # Check cache first
        cache_key = f"{query}_{self.threshold}_{','.join(sorted(self.strategies))}"
        if self.cache_results and self.cache_manager:
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                if self.verbose:
                    logger.debug(f"Cache hit for query: {query}")
                return cached_result  # type: ignore

        matches = []
        query_lower = query.lower()

        for ident in all_identifiers:
            ident_lower = ident.lower()
            best_score = 0

            # Strategy 1: Exact match (highest priority)
            if query_lower == ident_lower:
                matches.append((ident, 100))
                continue

            # Strategy 2: Prefix matching
            if "prefix" in self.strategies and ident_lower.startswith(query_lower):
                # Score based on query length and position
                score = min(95, 70 + len(query_lower) * 2)
                best_score = max(best_score, score)

            # Strategy 3: Suffix matching
            if "suffix" in self.strategies and ident_lower.endswith(query_lower):
                # Slightly lower score than prefix
                score = min(90, 65 + len(query_lower) * 2)
                best_score = max(best_score, score)

            # Strategy 4: Substring matching
            if "substring" in self.strategies and query_lower in ident_lower:
                # Score based on query length and position
                position = ident_lower.find(query_lower)
                position_bonus = max(0, 10 - position)  # Bonus for early position
                score = min(85, 60 + len(query_lower) * 2 + position_bonus)
                best_score = max(best_score, score)

            # Strategy 5: Levenshtein distance
            if "levenshtein" in self.strategies:
                # Use multiple fuzzy matching algorithms
                ratio = fuzz.ratio(query_lower, ident_lower)
                partial_ratio = fuzz.partial_ratio(query_lower, ident_lower)
                token_sort_ratio = fuzz.token_sort_ratio(query_lower, ident_lower)
                token_set_ratio = fuzz.token_set_ratio(query_lower, ident_lower)

                # Take the best score from all algorithms
                score = max(ratio, partial_ratio, token_sort_ratio, token_set_ratio)
                if score >= self.threshold:
                    best_score = max(best_score, score)

            # Strategy 6: Word-based matching
            if "word" in self.strategies:
                query_words = set(re.split(r"[_\-\s]+", query_lower))
                ident_words = set(re.split(r"[_\-\s]+", ident_lower))

                if query_words.intersection(ident_words):
                    common_words = len(query_words.intersection(ident_words))
                    total_words = len(query_words.union(ident_words))
                    score = int((common_words / total_words) * 100)
                    if score >= self.threshold:
                        best_score = max(best_score, score)

            if best_score >= self.threshold:
                matches.append((ident, best_score))

        # Sort by score (highest first), then by identifier name for consistency
        matches.sort(key=lambda x: (-x[1], x[0]))

        # Cache the result
        if self.cache_results and self.cache_manager:
            self.cache_manager.set(cache_key, matches)

        if self.verbose:
            logger.debug(f"Query '{query}' matched {len(matches)} identifiers")

        return matches

    def batch_match_identifiers(
        self, queries: List[str], all_identifiers: Set[str]
    ) -> Dict[str, List[Tuple[str, int]]]:
        """
        Match multiple queries against all identifiers.

        Args:
            queries: List of identifiers to search for
            all_identifiers: Set of all available identifiers

        Returns:
            Dictionary mapping queries to their match results
        """
        results = {}
        for query in queries:
            results[query] = self.match_identifiers(query, all_identifiers)
        return results

    def get_match_summary(
        self, query: str, all_identifiers: Set[str], max_matches: int = 5
    ) -> str:
        """
        Get a human-readable summary of matches for a query.

        Args:
            query: The identifier to search for
            all_identifiers: Set of all available identifiers
            max_matches: Maximum number of matches to include in summary

        Returns:
            Formatted string summary of matches
        """
        matches = self.match_identifiers(query, all_identifiers)

        if not matches:
            return f"No matches found for '{query}' (threshold: {self.threshold}%)"

        summary = f"Fuzzy matches for '{query}' (threshold: {self.threshold}%):\n"
        for i, (ident, score) in enumerate(matches[:max_matches], 1):
            summary += f"  {i}. {ident} (similarity: {score}%)\n"

        if len(matches) > max_matches:
            summary += f"  ... and {len(matches) - max_matches} more matches\n"

        return summary

    def clear_cache(self) -> None:
        """Clear the match cache."""
        if self.cache_manager:
            self.cache_manager.clear()
        if self.verbose:
            logger.debug("Fuzzy matching cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if self.cache_manager:
            return self.cache_manager.get_stats()
        else:
            return {
                "cache_size": 0,
                "max_size": 0,
                "ttl": 0,
                "hits": 0,
                "misses": 0,
                "hit_rate_percent": 0.0,
                "evictions": 0,
                "expirations": 0,
                "total_requests": 0,
                "estimated_memory_mb": 0.0,
            }
