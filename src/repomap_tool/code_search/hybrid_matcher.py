#!/usr/bin/env python3
"""
hybrid_matcher.py - Enhanced hybrid matching combining fuzzy and semantic approaches

This module provides a comprehensive approach by using:
1. Fuzzy matching (existing)
2. TF-IDF vectorization for semantic similarity
3. Domain semantic matching (programming knowledge)
4. ML embedding matching (CodeRankEmbed)
5. Context-aware scoring
"""

import re
import logging
from ..core.config_service import get_config
from ..core.logging_service import get_logger
from typing import Dict, List, Set, Tuple, Any, Optional
from collections import Counter
import math
from .embedding_matcher import EmbeddingMatcher
from .semantic_matcher import DomainSemanticMatcher

# Import our existing fuzzy matcher
from .fuzzy_matcher import FuzzyMatcher

logger = get_logger(__name__)


class HybridMatcher:
    """
    Enhanced hybrid matcher that combines multiple semantic approaches.

    This approach provides comprehensive semantic matching by combining:
    1. Fuzzy matching (string similarity)
    2. TF-IDF vectorization (statistical similarity)
    3. Domain semantic matching (programming knowledge)
    4. ML embedding matching (CodeRankEmbed contextual understanding)
    """

    def __init__(
        self,
        fuzzy_matcher: FuzzyMatcher,
        embedding_matcher: Optional[EmbeddingMatcher] = None,
        domain_semantic_matcher: Optional[DomainSemanticMatcher] = None,
        semantic_threshold: float = get_config("SEMANTIC_THRESHOLD", 0.3),
        use_word_embeddings: bool = False,
        verbose: bool = True,
    ):
        """
        Initialize the enhanced hybrid matcher.

        Args:
            fuzzy_matcher: Injected FuzzyMatcher instance
            embedding_matcher: Injected EmbeddingMatcher instance (optional)
            domain_semantic_matcher: Injected DomainSemanticMatcher instance (optional)
            semantic_threshold: Threshold for semantic similarity (0.0-1.0)
            use_word_embeddings: Whether to use word embeddings (requires more dependencies)
            verbose: Whether to log matching details
        """
        self.fuzzy_matcher = fuzzy_matcher
        self.embedding_matcher = embedding_matcher
        self.domain_semantic_matcher = domain_semantic_matcher

        # Debug logging
        if self.embedding_matcher:
            logger.debug(
                f"HybridMatcher received embedding_matcher: {type(self.embedding_matcher).__name__}"
            )
            logger.debug(
                f"Embedding matcher enabled: {getattr(self.embedding_matcher, 'enabled', False)}"
            )
        else:
            logger.debug("HybridMatcher did NOT receive embedding_matcher")

        if self.domain_semantic_matcher:
            logger.debug(
                f"HybridMatcher received domain_semantic_matcher: {type(self.domain_semantic_matcher).__name__}"
            )
            logger.debug(
                f"Domain semantic matcher enabled: {getattr(self.domain_semantic_matcher, 'enabled', True)}"
            )
        else:
            logger.debug("HybridMatcher did NOT receive domain_semantic_matcher")

        self.fuzzy_threshold = fuzzy_matcher.threshold
        self.semantic_threshold = semantic_threshold
        self.use_word_embeddings = use_word_embeddings
        self.verbose = verbose
        self.enabled = True

        # TF-IDF components
        self.word_frequencies: Counter[str] = Counter()
        self.total_identifiers = 0
        self.idf_cache: Dict[str, float] = {}

        # Word embeddings (optional)
        self.word_vectors: Dict[str, List[float]] = {}
        if use_word_embeddings:
            self._initialize_word_embeddings()

        if self.verbose:
            logger.info(
                f"Initialized Enhanced HybridMatcher (fuzzy: {self.fuzzy_threshold}, semantic: {semantic_threshold})"
            )
            logger.info(
                f"  - Embedding matcher: {'enabled' if self.embedding_matcher and getattr(self.embedding_matcher, 'enabled', False) else 'disabled'}"
            )
            logger.info(
                f"  - Domain semantic matcher: {'enabled' if self.domain_semantic_matcher else 'disabled'}"
            )

    def _initialize_word_embeddings(self) -> None:
        """Initialize lightweight word embeddings for common programming terms."""
        # Simple word vectors for common programming concepts
        # This is a lightweight alternative to full word embeddings
        programming_vectors = {
            # Data types
            "string": [1, 0, 0, 0, 0],
            "int": [1, 0, 0, 0, 0],
            "float": [1, 0, 0, 0, 0],
            "list": [1, 0, 0, 0, 0],
            "dict": [1, 0, 0, 0, 0],
            "set_collection": [1, 0, 0, 0, 0],
            # Operations
            "get": [0, 1, 0, 0, 0],
            "set_operation": [0, 1, 0, 0, 0],
            "add": [0, 1, 0, 0, 0],
            "remove": [0, 1, 0, 0, 0],
            "update": [0, 1, 0, 0, 0],
            "delete": [0, 1, 0, 0, 0],
            # Actions
            "create": [0, 0, 1, 0, 0],
            "build": [0, 0, 1, 0, 0],
            "generate": [0, 0, 1, 0, 0],
            "process": [0, 0, 1, 0, 0],
            "transform": [0, 0, 1, 0, 0],
            "convert": [0, 0, 1, 0, 0],
            # States
            "active": [0, 0, 0, 1, 0],
            "inactive": [0, 0, 0, 1, 0],
            "enabled": [0, 0, 0, 1, 0],
            "disabled": [0, 0, 0, 1, 0],
            "valid": [0, 0, 0, 1, 0],
            "invalid": [0, 0, 0, 1, 0],
            # Qualifiers
            "max": [0, 0, 0, 0, 1],
            "min": [0, 0, 0, 0, 1],
            "total": [0, 0, 0, 0, 1],
            "count": [0, 0, 0, 0, 1],
            "size": [0, 0, 0, 0, 1],
            "length": [0, 0, 0, 0, 1],
        }

        self.word_vectors = programming_vectors  # type: ignore

    def split_identifier(self, identifier: str) -> List[str]:
        """Split an identifier into words (same as fuzzy matcher)."""
        if not identifier:
            return []

        # Split by underscores and hyphens first
        parts = re.split(r"[_-]", identifier)

        # Then split camelCase and PascalCase
        words = []
        for part in parts:
            if part:
                camel_parts = re.findall(
                    r"[A-Z]?[a-z]+|[A-Z]{2,}(?=[A-Z][a-z]|\b|\d)|\d+", part
                )
                words.extend(camel_parts)

        return [word.lower() for word in words if word]

    def build_tfidf_model(self, all_identifiers: Set[str]) -> None:
        """
        Build TF-IDF model from all identifiers in the codebase.

        Args:
            all_identifiers: Set of all identifiers in the codebase
        """
        self.total_identifiers = len(all_identifiers)

        # Count word frequencies across all identifiers
        for identifier in all_identifiers:
            words = self.split_identifier(identifier)
            for word in set(words):  # Count unique words per identifier
                self.word_frequencies[word] += 1

        # Calculate IDF for each word
        for word, freq in self.word_frequencies.items():
            self.idf_cache[word] = math.log(self.total_identifiers / freq)

        if self.verbose:
            logger.info(
                f"Built TF-IDF model with {len(self.word_frequencies)} unique words"
            )

    def calculate_tfidf_similarity(self, query: str, identifier: str) -> float:
        """
        Calculate TF-IDF similarity between query and identifier.

        Args:
            query: The search query
            identifier: The identifier to compare against

        Returns:
            Similarity score between 0.0 and 1.0
        """
        query_words = set(self.split_identifier(query))
        identifier_words = set(self.split_identifier(identifier))

        if not query_words or not identifier_words:
            return 0.0

        # Calculate TF-IDF vectors
        query_vector = {}
        identifier_vector = {}

        # Query vector (TF = 1 for each word, IDF from cache)
        for word in query_words:
            if word in self.idf_cache:
                query_vector[word] = self.idf_cache[word]

        # Identifier vector (TF = 1 for each word, IDF from cache)
        for word in identifier_words:
            if word in self.idf_cache:
                identifier_vector[word] = self.idf_cache[word]

        # Calculate cosine similarity
        common_words = set(query_vector.keys()) & set(identifier_vector.keys())

        if not common_words:
            return 0.0

        # Numerator: sum of products
        numerator = sum(
            query_vector[word] * identifier_vector[word] for word in common_words
        )

        # Denominator: product of magnitudes
        query_magnitude = math.sqrt(sum(score**2 for score in query_vector.values()))
        identifier_magnitude = math.sqrt(
            sum(score**2 for score in identifier_vector.values())
        )

        if query_magnitude == 0 or identifier_magnitude == 0:
            return 0.0

        similarity = numerator / (query_magnitude * identifier_magnitude)
        return similarity

    def calculate_word_vector_similarity(self, query: str, identifier: str) -> float:
        """
        Calculate similarity using word vectors (if available).

        Args:
            query: The search query
            identifier: The identifier to compare against

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not self.word_vectors:
            return 0.0

        query_words = self.split_identifier(query)
        identifier_words = self.split_identifier(identifier)

        # Find words that have vectors
        query_vectors = [
            self.word_vectors.get(word)
            for word in query_words
            if word in self.word_vectors
        ]
        identifier_vectors = [
            self.word_vectors.get(word)
            for word in identifier_words
            if word in self.word_vectors
        ]

        if not query_vectors or not identifier_vectors:
            return 0.0

        # Calculate average similarity between all vector pairs
        total_similarity = 0.0
        count = 0

        for q_vec in query_vectors:
            for i_vec in identifier_vectors:
                if q_vec is not None and i_vec is not None:
                    # Simple cosine similarity for small vectors
                    dot_product = sum(a * b for a, b in zip(q_vec, i_vec))
                    q_magnitude = math.sqrt(sum(a * a for a in q_vec))
                    i_magnitude = math.sqrt(sum(a * a for a in i_vec))

                if q_magnitude > 0 and i_magnitude > 0:
                    similarity = dot_product / (q_magnitude * i_magnitude)
                    total_similarity += similarity
                    count += 1

        return total_similarity / count if count > 0 else 0.0

    def calculate_context_similarity(self, query: str, identifier: str) -> float:
        """
        Calculate context-based similarity using word co-occurrence patterns.

        Args:
            query: The search query
            identifier: The identifier to compare against

        Returns:
            Similarity score between 0.0 and 1.0
        """
        query_words = set(self.split_identifier(query))
        identifier_words = set(self.split_identifier(identifier))

        if not query_words or not identifier_words:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(query_words.intersection(identifier_words))
        union = len(query_words.union(identifier_words))

        if union == 0:
            return 0.0

        return intersection / union

    def hybrid_similarity(
        self, query: str, identifier: str
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate hybrid similarity combining multiple approaches.

        Args:
            query: The search query
            identifier: The identifier to compare against

        Returns:
            Tuple of (overall_score, component_scores)
        """
        # Get fuzzy similarity
        fuzzy_matches = self.fuzzy_matcher.match_identifiers(query, {identifier})
        fuzzy_score = fuzzy_matches[0][1] / 100.0 if fuzzy_matches else 0.0

        # Get TF-IDF similarity
        tfidf_score = self.calculate_tfidf_similarity(query, identifier)

        # Get word vector similarity
        vector_score = self.calculate_word_vector_similarity(query, identifier)

        # Get context similarity
        context_score = self.calculate_context_similarity(query, identifier)

        # Get domain semantic similarity (programming knowledge)
        domain_semantic_score = 0.0
        if self.domain_semantic_matcher:
            try:
                domain_semantic_score = (
                    self.domain_semantic_matcher.semantic_similarity(query, identifier)
                )
            except Exception as e:
                if self.verbose:
                    logger.debug(f"Domain semantic similarity failed: {e}")
                domain_semantic_score = 0.0

        # Get embedding similarity (CodeRankEmbed) - only for multi-word queries
        embedding_score = 0.0
        if (
            self.embedding_matcher
            and hasattr(self.embedding_matcher, "enabled")
            and self.embedding_matcher.enabled
            and len(query.split()) > 1
        ):  # Only use embeddings for multi-word queries
            try:
                from sklearn.metrics.pairwise import cosine_similarity

                query_emb = self.embedding_matcher.get_embedding(query)
                identifier_emb = self.embedding_matcher.get_embedding(identifier)
                if query_emb is not None and identifier_emb is not None:
                    embedding_score = cosine_similarity(
                        query_emb.reshape(1, -1), identifier_emb.reshape(1, -1)
                    )[0][0]
                    # Ensure score is in [0, 1]
                    embedding_score = max(0.0, min(1.0, float(embedding_score)))
            except Exception as e:
                if self.verbose:
                    logger.debug(f"Embedding similarity failed: {e}")
                embedding_score = 0.0

        # Intelligent weighting based on available matchers
        if (
            self.embedding_matcher
            and hasattr(self.embedding_matcher, "enabled")
            and self.embedding_matcher.enabled
            and self.domain_semantic_matcher
        ):
            # Full semantic stack: fuzzy + domain + ML embeddings
            weights = {
                "fuzzy": 0.25,  # 25% - string similarity
                "tfidf": 0.20,  # 20% - statistical similarity
                "domain_semantic": 0.30,  # 30% - programming domain knowledge
                "embedding": 0.25,  # 25% - ML semantic understanding
            }
            overall_score = (
                fuzzy_score * weights["fuzzy"]
                + tfidf_score * weights["tfidf"]
                + domain_semantic_score * weights["domain_semantic"]
                + embedding_score * weights["embedding"]
            )
        elif self.domain_semantic_matcher:
            # Domain knowledge + fuzzy (no ML embeddings)
            weights = {
                "fuzzy": 0.40,  # 40% - string similarity
                "tfidf": 0.30,  # 30% - statistical similarity
                "domain_semantic": 0.30,  # 30% - programming domain knowledge
            }
            overall_score = (
                fuzzy_score * weights["fuzzy"]
                + tfidf_score * weights["tfidf"]
                + domain_semantic_score * weights["domain_semantic"]
            )
        elif (
            self.embedding_matcher
            and hasattr(self.embedding_matcher, "enabled")
            and self.embedding_matcher.enabled
        ):
            # ML embeddings + fuzzy (no domain knowledge)
            weights = {
                "fuzzy": 0.35,  # 35% - string similarity
                "tfidf": 0.25,  # 25% - statistical similarity
                "embedding": 0.40,  # 40% - ML semantic understanding
            }
            overall_score = (
                fuzzy_score * weights["fuzzy"]
                + tfidf_score * weights["tfidf"]
                + embedding_score * weights["embedding"]
            )
        else:
            # Fallback: fuzzy + TF-IDF only
            weights = {
                "fuzzy": 0.60,  # 60% - string similarity
                "tfidf": 0.40,  # 40% - statistical similarity
            }
            overall_score = (
                fuzzy_score * weights["fuzzy"] + tfidf_score * weights["tfidf"]
            )

        component_scores: Dict[str, float] = {
            "fuzzy": fuzzy_score,
            "tfidf": tfidf_score,
            "vector": vector_score,
            "context": context_score,
            "domain_semantic": domain_semantic_score,
            "embedding": embedding_score,
            "overall": overall_score,
            "weights": weights,  # type: ignore[dict-item]
        }

        return overall_score, component_scores

    def find_hybrid_matches(
        self,
        query: str,
        all_identifiers: Set[str],
        threshold: float = get_config("SEMANTIC_THRESHOLD", 0.3),
    ) -> List[Tuple[str, float, Dict[str, float]]]:
        """
        Find hybrid matches for a query among all identifiers.

        Args:
            query: The search query
            all_identifiers: Set of all available identifiers
            threshold: Minimum similarity threshold (0.0 to 1.0)

        Returns:
            List of (identifier, overall_score, component_scores) tuples, sorted by score
        """
        # Debug logging (only shows with --verbose)
        logger.debug(
            f"find_hybrid_matches: query='{query}', identifiers={len(all_identifiers)}, threshold={threshold}"
        )

        matches: List[Tuple[str, float, Dict[str, float]]] = []

        for identifier in all_identifiers:
            overall_score, component_scores = self.hybrid_similarity(query, identifier)

            # Log first few scores
            if len(matches) < 5:
                logger.debug(
                    f"Similarity for '{identifier}': overall={overall_score:.3f}, components={component_scores}"
                )

            if overall_score >= threshold:
                matches.append((identifier, overall_score, component_scores))

        # Log filtering results
        logger.debug(f"Before filtering: {len(all_identifiers)} identifiers")
        logger.debug(f"After threshold {threshold}: {len(matches)} matches")

        # Sort by overall score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)

        if self.verbose:
            logger.debug(
                f"Enhanced hybrid matches for '{query}' (threshold: {threshold}):"
            )
            for identifier, score, components in matches[:5]:
                logger.debug(
                    f"  - {identifier} (overall: {score:.2f}, fuzzy: {components['fuzzy']:.2f}, "
                    f"domain: {components['domain_semantic']:.2f}, embedding: {components['embedding']:.2f})"
                )

        return matches

    def match_identifiers(
        self, query: str, all_identifiers: Set[str], threshold: Optional[float] = None
    ) -> List[Tuple[str, int]]:
        """
        Match a query against all identifiers using hybrid approach.

        This method provides a consistent interface with FuzzyMatcher.match_identifiers
        by returning (identifier, score) tuples where score is an integer (0-100).

        Args:
            query: The identifier to search for
            all_identifiers: Set of all available identifiers

        Returns:
            List of (identifier, score) tuples, sorted by score (highest first)
        """
        # Debug logging (only shows with --verbose)
        logger.debug(
            f"Enhanced HybridMatcher.match_identifiers: query='{query}', identifiers={len(all_identifiers)}"
        )
        logger.debug(
            f"Embedding matcher: {self.embedding_matcher is not None}, enabled={getattr(self.embedding_matcher, 'enabled', False) if self.embedding_matcher else False}"
        )
        logger.debug(
            f"Domain semantic matcher: {self.domain_semantic_matcher is not None}"
        )

        # Use passed threshold or fallback to config default
        if threshold is None:
            threshold = get_config("HYBRID_THRESHOLD", 0.1)
        logger.debug(f"Using threshold: {threshold}")

        # Get hybrid matches
        hybrid_matches = self.find_hybrid_matches(query, all_identifiers, threshold)

        # Log match count
        logger.debug(f"Found {len(hybrid_matches)} hybrid matches")

        # Convert to the expected format: (identifier, score) where score is 0-100
        matches = []
        for identifier, overall_score, component_scores in hybrid_matches:
            # Convert float score (0.0-1.0) to integer score (0-100)
            score = int(overall_score * 100)
            matches.append((identifier, score))
            # Log first few matches
            if len(matches) <= 5:
                logger.debug(
                    f"Match: {identifier} = {score}% (fuzzy: {component_scores['fuzzy']:.2f}, "
                    f"domain: {component_scores['domain_semantic']:.2f}, "
                    f"embedding: {component_scores['embedding']:.2f})"
                )

        return matches

    def get_match_analysis(
        self, query: str, all_identifiers: Set[str], max_matches: int = 10
    ) -> Dict[str, Any]:
        """
        Get detailed analysis of matches for a query.

        Args:
            query: The search query
            all_identifiers: Set of all available identifiers
            max_matches: Maximum number of matches to analyze

        Returns:
            Dictionary with match analysis
        """
        matches = self.find_hybrid_matches(
            query, all_identifiers, threshold=get_config("HYBRID_THRESHOLD", 0.1)
        )

        analysis: Dict[str, Any] = {
            "query": query,
            "total_matches": len(matches),
            "top_matches": matches[:max_matches],
            "component_averages": {
                "fuzzy": 0.0,
                "tfidf": 0.0,
                "vector": 0.0,
                "context": 0.0,
            },
        }

        if matches:
            # Calculate component averages
            for component in ["fuzzy", "tfidf", "vector", "context"]:
                avg_score = sum(
                    match[2][component] for match in matches[:max_matches]
                ) / len(matches[:max_matches])
                analysis["component_averages"][component] = avg_score

        return analysis

    def suggest_queries(self, identifier: str) -> List[str]:
        """
        Suggest alternative queries based on an identifier.

        Args:
            identifier: The identifier to suggest queries for

        Returns:
            List of suggested queries
        """
        words = self.split_identifier(identifier)
        suggestions = []

        # Single word suggestions
        suggestions.extend(words)

        # Two-word combinations
        for i in range(len(words)):
            for j in range(i + 1, len(words)):
                suggestions.append(f"{words[i]}_{words[j]}")
                suggestions.append(f"{words[i]}{words[j]}")

        return suggestions[:10]  # Limit to 10 suggestions

    def clear_cache(self) -> None:
        """Clear the cache for both fuzzy and semantic matchers."""
        if self.fuzzy_matcher and hasattr(self.fuzzy_matcher, "clear_cache"):
            self.fuzzy_matcher.clear_cache()
        if self.domain_semantic_matcher and hasattr(
            self.domain_semantic_matcher, "clear_cache"
        ):
            self.domain_semantic_matcher.clear_cache()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics from both matchers."""
        stats = {}
        if self.fuzzy_matcher and hasattr(self.fuzzy_matcher, "get_cache_stats"):
            stats["fuzzy"] = self.fuzzy_matcher.get_cache_stats()
        if self.domain_semantic_matcher and hasattr(
            self.domain_semantic_matcher, "get_cache_stats"
        ):
            stats["semantic"] = self.domain_semantic_matcher.get_cache_stats()
        return stats
