#!/usr/bin/env python3
"""
hybrid_matcher.py - Hybrid matching combining fuzzy and semantic approaches

This module provides a more flexible approach than rigid dictionaries by using:
1. Fuzzy matching (existing)
2. TF-IDF vectorization for semantic similarity
3. Word embeddings (optional, lightweight)
4. Context-aware scoring
"""

import re
import logging
from typing import Dict, List, Set, Tuple, Optional
from collections import Counter
import math

# Import our existing fuzzy matcher
from fuzzy_matcher import FuzzyMatcher

logger = logging.getLogger(__name__)

class HybridMatcher:
    """
    A hybrid matcher that combines fuzzy matching with lightweight semantic analysis.
    
    This approach is more flexible than rigid dictionaries and adapts to the
    actual codebase content.
    """
    
    def __init__(self, fuzzy_threshold: int = 70, semantic_threshold: float = 0.3,
                 use_word_embeddings: bool = False, verbose: bool = True):
        """
        Initialize the hybrid matcher.
        
        Args:
            fuzzy_threshold: Threshold for fuzzy matching (0-100)
            semantic_threshold: Threshold for semantic similarity (0.0-1.0)
            use_word_embeddings: Whether to use word embeddings (requires more dependencies)
            verbose: Whether to log matching details
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.semantic_threshold = semantic_threshold
        self.use_word_embeddings = use_word_embeddings
        self.verbose = verbose
        
        # Initialize fuzzy matcher
        self.fuzzy_matcher = FuzzyMatcher(
            threshold=fuzzy_threshold,
            strategies=['prefix', 'substring', 'levenshtein'],
            verbose=verbose
        )
        
        # TF-IDF components
        self.word_frequencies = Counter()
        self.total_identifiers = 0
        self.idf_cache = {}
        
        # Word embeddings (optional)
        self.word_vectors = {}
        if use_word_embeddings:
            self._initialize_word_embeddings()
        
        if self.verbose:
            logger.info(f"Initialized HybridMatcher (fuzzy: {fuzzy_threshold}, semantic: {semantic_threshold})")
    
    def _initialize_word_embeddings(self):
        """Initialize lightweight word embeddings for common programming terms."""
        # Simple word vectors for common programming concepts
        # This is a lightweight alternative to full word embeddings
        programming_vectors = {
            # Data types
            'string': [1, 0, 0, 0, 0], 'int': [1, 0, 0, 0, 0], 'float': [1, 0, 0, 0, 0],
            'list': [1, 0, 0, 0, 0], 'dict': [1, 0, 0, 0, 0], 'set': [1, 0, 0, 0, 0],
            
            # Operations
            'get': [0, 1, 0, 0, 0], 'set': [0, 1, 0, 0, 0], 'add': [0, 1, 0, 0, 0],
            'remove': [0, 1, 0, 0, 0], 'update': [0, 1, 0, 0, 0], 'delete': [0, 1, 0, 0, 0],
            
            # Actions
            'create': [0, 0, 1, 0, 0], 'build': [0, 0, 1, 0, 0], 'generate': [0, 0, 1, 0, 0],
            'process': [0, 0, 1, 0, 0], 'transform': [0, 0, 1, 0, 0], 'convert': [0, 0, 1, 0, 0],
            
            # States
            'active': [0, 0, 0, 1, 0], 'inactive': [0, 0, 0, 1, 0], 'enabled': [0, 0, 0, 1, 0],
            'disabled': [0, 0, 0, 1, 0], 'valid': [0, 0, 0, 1, 0], 'invalid': [0, 0, 0, 1, 0],
            
            # Qualifiers
            'max': [0, 0, 0, 0, 1], 'min': [0, 0, 0, 0, 1], 'total': [0, 0, 0, 0, 1],
            'count': [0, 0, 0, 0, 1], 'size': [0, 0, 0, 0, 1], 'length': [0, 0, 0, 0, 1],
        }
        
        self.word_vectors = programming_vectors
    
    def split_identifier(self, identifier: str) -> List[str]:
        """Split an identifier into words (same as fuzzy matcher)."""
        if not identifier:
            return []
        
        # Split by underscores and hyphens first
        parts = re.split(r'[_-]', identifier)
        
        # Then split camelCase and PascalCase
        words = []
        for part in parts:
            if part:
                camel_parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]{2,}(?=[A-Z][a-z]|\b|\d)|\d+', part)
                words.extend(camel_parts)
        
        return [word.lower() for word in words if word]
    
    def build_tfidf_model(self, all_identifiers: Set[str]):
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
            logger.info(f"Built TF-IDF model with {len(self.word_frequencies)} unique words")
    
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
        numerator = sum(query_vector[word] * identifier_vector[word] for word in common_words)
        
        # Denominator: product of magnitudes
        query_magnitude = math.sqrt(sum(score ** 2 for score in query_vector.values()))
        identifier_magnitude = math.sqrt(sum(score ** 2 for score in identifier_vector.values()))
        
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
        query_vectors = [self.word_vectors.get(word) for word in query_words if word in self.word_vectors]
        identifier_vectors = [self.word_vectors.get(word) for word in identifier_words if word in self.word_vectors]
        
        if not query_vectors or not identifier_vectors:
            return 0.0
        
        # Calculate average similarity between all vector pairs
        total_similarity = 0.0
        count = 0
        
        for q_vec in query_vectors:
            for i_vec in identifier_vectors:
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
    
    def hybrid_similarity(self, query: str, identifier: str) -> Tuple[float, Dict[str, float]]:
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
        
        # Weighted combination
        weights = {
            'fuzzy': 0.4,
            'tfidf': 0.3,
            'vector': 0.2,
            'context': 0.1
        }
        
        overall_score = (
            fuzzy_score * weights['fuzzy'] +
            tfidf_score * weights['tfidf'] +
            vector_score * weights['vector'] +
            context_score * weights['context']
        )
        
        component_scores = {
            'fuzzy': fuzzy_score,
            'tfidf': tfidf_score,
            'vector': vector_score,
            'context': context_score,
            'overall': overall_score
        }
        
        return overall_score, component_scores
    
    def find_hybrid_matches(self, query: str, all_identifiers: Set[str], 
                           threshold: float = 0.3) -> List[Tuple[str, float, Dict[str, float]]]:
        """
        Find hybrid matches for a query among all identifiers.
        
        Args:
            query: The search query
            all_identifiers: Set of all available identifiers
            threshold: Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            List of (identifier, overall_score, component_scores) tuples, sorted by score
        """
        matches = []
        
        for identifier in all_identifiers:
            overall_score, component_scores = self.hybrid_similarity(query, identifier)
            
            if overall_score >= threshold:
                matches.append((identifier, overall_score, component_scores))
        
        # Sort by overall score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        if self.verbose:
            logger.debug(f"Hybrid matches for '{query}' (threshold: {threshold}):")
            for identifier, score, components in matches[:5]:
                logger.debug(f"  - {identifier} (overall: {score:.2f}, fuzzy: {components['fuzzy']:.2f}, tfidf: {components['tfidf']:.2f})")
        
        return matches
    
    def get_match_analysis(self, query: str, all_identifiers: Set[str], 
                          max_matches: int = 10) -> Dict:
        """
        Get detailed analysis of matches for a query.
        
        Args:
            query: The search query
            all_identifiers: Set of all available identifiers
            max_matches: Maximum number of matches to analyze
            
        Returns:
            Dictionary with match analysis
        """
        matches = self.find_hybrid_matches(query, all_identifiers, threshold=0.1)
        
        analysis = {
            'query': query,
            'total_matches': len(matches),
            'top_matches': matches[:max_matches],
            'component_averages': {
                'fuzzy': 0.0,
                'tfidf': 0.0,
                'vector': 0.0,
                'context': 0.0
            }
        }
        
        if matches:
            # Calculate component averages
            for component in ['fuzzy', 'tfidf', 'vector', 'context']:
                avg_score = sum(match[2][component] for match in matches[:max_matches]) / len(matches[:max_matches])
                analysis['component_averages'][component] = avg_score
        
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
