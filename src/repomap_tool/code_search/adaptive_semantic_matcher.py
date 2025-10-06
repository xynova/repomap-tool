#!/usr/bin/env python3
"""
adaptive_semantic_matcher.py - Adaptive semantic matching using TF-IDF

This matcher learns from the actual codebase content rather than using
predefined categories. It's much more flexible and adaptive.
"""

import re
import logging
from ..core.config_service import get_config
from ..core.logging_service import get_logger
from typing import Dict, List, Set, Tuple
from collections import Counter
import math

logger = get_logger(__name__)


class AdaptiveSemanticMatcher:
    """
    An adaptive semantic matcher that learns from the actual codebase.

    This approach uses TF-IDF to understand the semantic patterns in your
    specific codebase, making it much more flexible than rigid dictionaries.
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize the adaptive semantic matcher.

        Args:
            verbose: Whether to log matching details
        """
        self.verbose = verbose
        self.enabled = True  # Add enabled attribute for compatibility

        # TF-IDF components
        self.word_frequencies: Counter[str] = Counter()
        self.total_identifiers = 0
        self.idf_cache: Dict[str, float] = {}

        # Identifier analysis
        self.identifier_words: Dict[str, Set[str]] = {}  # identifier -> set of words
        self.word_to_identifiers: Dict[str, Set[str]] = (
            {}
        )  # word -> set of identifiers containing it

        # Similarity cache
        self.similarity_cache: Dict[str, float] = {}

        if self.verbose:
            logger.info("Initialized AdaptiveSemanticMatcher")

    def split_identifier(self, identifier: str) -> List[str]:
        """
        Split an identifier into words (camelCase, snake_case, kebab-case, etc.).

        Args:
            identifier: The identifier to split

        Returns:
            List of words from the identifier
        """
        if not identifier:
            return []

        # Handle different naming conventions
        # camelCase -> ['camel', 'Case']
        # snake_case -> ['snake', 'case']
        # kebab-case -> ['kebab', 'case']
        # PascalCase -> ['Pascal', 'Case']

        # Split by underscores and hyphens first
        parts = re.split(r"[_-]", identifier)

        # Then split camelCase and PascalCase
        words = []
        for part in parts:
            if part:
                # Split camelCase: "camelCase" -> ["camel", "Case"]
                camel_parts = re.findall(
                    r"[A-Z]?[a-z]+|[A-Z]{2,}(?=[A-Z][a-z]|\b|\d)|\d+", part
                )
                words.extend(camel_parts)

        return [word.lower() for word in words if word]

    def learn_from_identifiers(self, all_identifiers: Set[str]) -> None:
        """
        Learn semantic patterns from all identifiers in the codebase.

        Args:
            all_identifiers: Set of all identifiers in the codebase
        """
        self.total_identifiers = len(all_identifiers)

        # Clear previous learning
        self.word_frequencies.clear()
        self.idf_cache.clear()
        self.identifier_words.clear()
        self.word_to_identifiers.clear()
        self.similarity_cache.clear()

        # Analyze each identifier
        for identifier in all_identifiers:
            words = set(self.split_identifier(identifier))
            self.identifier_words[identifier] = words

            # Count word frequencies
            for word in words:
                self.word_frequencies[word] += 1
                if word not in self.word_to_identifiers:
                    self.word_to_identifiers[word] = set()
                self.word_to_identifiers[word].add(identifier)

        # Calculate IDF for each word
        for word, freq in self.word_frequencies.items():
            self.idf_cache[word] = math.log(self.total_identifiers / freq)

        if self.verbose:
            logger.info(
                f"Learned from {self.total_identifiers} identifiers with {len(self.word_frequencies)} unique words"
            )

    def get_identifier_vector(self, identifier: str) -> Dict[str, float]:
        """
        Get TF-IDF vector for an identifier.

        Args:
            identifier: The identifier to vectorize

        Returns:
            Dictionary mapping words to their TF-IDF scores
        """
        words = self.identifier_words.get(identifier, set())
        vector = {}

        for word in words:
            if word in self.idf_cache:
                # TF = 1 (each word appears once in the identifier)
                # IDF = pre-calculated
                vector[word] = self.idf_cache[word]

        return vector

    def get_query_vector(self, query: str) -> Dict[str, float]:
        """
        Get TF-IDF vector for a query.

        Args:
            query: The search query

        Returns:
            Dictionary mapping words to their TF-IDF scores
        """
        words = set(self.split_identifier(query))
        vector = {}

        for word in words:
            if word in self.idf_cache:
                # TF = 1 (each word appears once in the query)
                # IDF = pre-calculated
                vector[word] = self.idf_cache[word]

        return vector

    def cosine_similarity(
        self, vector1: Dict[str, float], vector2: Dict[str, float]
    ) -> float:
        """
        Calculate cosine similarity between two TF-IDF vectors.

        Args:
            vector1: First TF-IDF vector
            vector2: Second TF-IDF vector

        Returns:
            Cosine similarity score between 0.0 and 1.0
        """
        # Get all unique words
        all_words = set(vector1.keys()) | set(vector2.keys())

        if not all_words:
            return 0.0

        # Calculate dot product and magnitudes
        dot_product = 0.0
        magnitude1 = 0.0
        magnitude2 = 0.0

        for word in all_words:
            val1 = vector1.get(word, 0.0)
            val2 = vector2.get(word, 0.0)

            dot_product += val1 * val2
            magnitude1 += val1 * val1
            magnitude2 += val2 * val2

        magnitude1 = math.sqrt(magnitude1)
        magnitude2 = math.sqrt(magnitude2)

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def semantic_similarity(self, query: str, identifier: str) -> float:
        """
        Calculate semantic similarity between query and identifier.

        Args:
            query: The search query
            identifier: The identifier to compare against

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Check cache first
        cache_key = f"{query}_{identifier}"
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]

        # Get vectors
        query_vector = self.get_query_vector(query)
        identifier_vector = self.get_identifier_vector(identifier)

        # Calculate similarity
        similarity = self.cosine_similarity(query_vector, identifier_vector)

        # Cache result
        self.similarity_cache[cache_key] = similarity

        return similarity

    def find_semantic_matches(
        self,
        query: str,
        all_identifiers: Set[str],
        threshold: float = get_config("HYBRID_THRESHOLD", 0.1),
    ) -> List[Tuple[str, float]]:
        """
        Find semantic matches for a query among all identifiers.

        Args:
            query: The search query
            all_identifiers: Set of all available identifiers
            threshold: Minimum similarity threshold (0.0 to 1.0)

        Returns:
            List of (identifier, similarity_score) tuples, sorted by score
        """
        matches = []

        for identifier in all_identifiers:
            similarity = self.semantic_similarity(query, identifier)

            if similarity >= threshold:
                matches.append((identifier, similarity))

        # Sort by similarity score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)

        if self.verbose:
            logger.debug(f"Semantic matches for '{query}' (threshold: {threshold}):")
            for identifier, score in matches[:5]:
                logger.debug(f"  - {identifier} (similarity: {score:.3f})")

        return matches

    def get_related_identifiers(
        self, identifier: str, max_results: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Find identifiers semantically related to a given identifier.

        Args:
            identifier: The identifier to find related ones for
            max_results: Maximum number of results to return

        Returns:
            List of (related_identifier, similarity_score) tuples
        """
        if identifier not in self.identifier_words:
            return []

        related = []
        identifier_vector = self.get_identifier_vector(identifier)

        for other_identifier in self.identifier_words.keys():
            if other_identifier != identifier:
                similarity = self.cosine_similarity(
                    identifier_vector, self.get_identifier_vector(other_identifier)
                )
                if similarity > 0.1:  # Low threshold to get more results
                    related.append((other_identifier, similarity))

        # Sort and limit results
        related.sort(key=lambda x: x[1], reverse=True)
        return related[:max_results]

    def get_word_importance(self, word: str) -> float:
        """
        Get the importance (IDF) of a word in the codebase.

        Args:
            word: The word to check

        Returns:
            IDF score (higher = more distinctive/important)
        """
        return self.idf_cache.get(word.lower(), 0.0)

    def get_most_important_words(self, top_n: int = 20) -> List[Tuple[str, float]]:
        """
        Get the most important (distinctive) words in the codebase.

        Args:
            top_n: Number of top words to return

        Returns:
            List of (word, idf_score) tuples, sorted by IDF
        """
        important_words = [(word, idf) for word, idf in self.idf_cache.items()]
        important_words.sort(key=lambda x: x[1], reverse=True)
        return important_words[:top_n]

    def get_common_words(self, top_n: int = 20) -> List[Tuple[str, int]]:
        """
        Get the most common words in the codebase.

        Args:
            top_n: Number of top words to return

        Returns:
            List of (word, frequency) tuples, sorted by frequency
        """
        common_words = [(word, freq) for word, freq in self.word_frequencies.items()]
        common_words.sort(key=lambda x: x[1], reverse=True)
        return common_words[:top_n]

    def suggest_queries(self, identifier: str) -> List[str]:
        """
        Suggest alternative queries based on an identifier.

        Args:
            identifier: The identifier to suggest queries for

        Returns:
            List of suggested queries
        """
        words = list(self.identifier_words.get(identifier, set()))
        suggestions = []

        # Single word suggestions
        suggestions.extend(words)

        # Two-word combinations
        for i in range(len(words)):
            for j in range(i + 1, len(words)):
                suggestions.append(f"{words[i]}_{words[j]}")
                suggestions.append(f"{words[i]}{words[j]}")

        # Add related words based on co-occurrence
        for word in words:
            if word in self.word_to_identifiers:
                # Find other words that often appear with this word
                related_identifiers = self.word_to_identifiers[word]
                for related_id in related_identifiers:
                    if related_id != identifier:
                        related_words = self.identifier_words[related_id]
                        for related_word in related_words:
                            if related_word not in words and len(suggestions) < 20:
                                suggestions.append(related_word)

        return suggestions[:20]  # Limit to 20 suggestions

    def get_semantic_clusters(
        self,
        all_identifiers: Set[str],
        similarity_threshold: float = get_config("SEMANTIC_THRESHOLD", 0.3),
    ) -> List[Set[str]]:
        """
        Group identifiers into semantic clusters.

        Args:
            all_identifiers: Set of all identifiers
            similarity_threshold: Minimum similarity for clustering

        Returns:
            List of identifier clusters
        """
        clusters = []
        processed = set()

        for identifier in all_identifiers:
            if identifier in processed:
                continue

            # Start a new cluster
            cluster = {identifier}
            processed.add(identifier)

            # Find similar identifiers
            for other_identifier in all_identifiers:
                if other_identifier not in processed:
                    similarity = self.semantic_similarity(identifier, other_identifier)
                    if similarity >= similarity_threshold:
                        cluster.add(other_identifier)
                        processed.add(other_identifier)

            if len(cluster) > 1:  # Only keep clusters with multiple items
                clusters.append(cluster)

        return clusters

    def match_identifiers(
        self, query: str, all_identifiers: Set[str]
    ) -> List[Tuple[str, int]]:
        """
        Match a query against all identifiers using semantic similarity.

        This method provides a consistent interface with other matchers
        by returning (identifier, score) tuples where score is an integer (0-100).

        Args:
            query: The search query
            all_identifiers: Set of all available identifiers

        Returns:
            List of (identifier, score) tuples, sorted by score (highest first)
        """
        # Use a lower threshold for match_identifiers to be more inclusive
        threshold = get_config("HYBRID_THRESHOLD", 0.1)

        # Get semantic matches
        semantic_matches = self.find_semantic_matches(query, all_identifiers, threshold)

        # Convert to the expected format: (identifier, score) where score is 0-100
        matches = []
        for identifier, similarity_score in semantic_matches:
            # Convert float score (0.0-1.0) to integer score (0-100)
            score = int(similarity_score * 100)
            matches.append((identifier, score))

        return matches

    def clear_cache(self) -> None:
        """Clear the similarity cache."""
        self.similarity_cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "cache_size": len(self.similarity_cache),
            "total_identifiers": self.total_identifiers,
            "unique_words": len(self.word_frequencies),
        }
