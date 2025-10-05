"""
Code Search Module

This module provides intelligent code search and discovery capabilities using multiple strategies:
- Fuzzy matching for approximate string matching
- Semantic matching using domain-specific dictionaries
- Hybrid matching combining fuzzy and semantic approaches
- Adaptive semantic matching using TF-IDF
"""

from .fuzzy_matcher import FuzzyMatcher
from .semantic_matcher import DomainSemanticMatcher
from .hybrid_matcher import HybridMatcher
from .adaptive_semantic_matcher import AdaptiveSemanticMatcher

__all__ = [
    "FuzzyMatcher",
    "DomainSemanticMatcher",
    "HybridMatcher",
    "AdaptiveSemanticMatcher",
]
