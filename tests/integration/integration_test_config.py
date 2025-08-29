#!/usr/bin/env python3
"""
Test Configuration for Self-Integration Tests

This module defines configuration parameters, expected results, and test data
for the repomap-tool self-integration tests.
"""

from typing import Dict, List, Any
from pathlib import Path

# Test configuration
TEST_CONFIG = {
    "project_root": Path(__file__).parent.parent.parent,
    "src_dir": Path(__file__).parent.parent.parent / "src" / "repomap_tool",
    "test_timeout": 30,  # seconds
    "max_results": 20,
    "performance_threshold": {
        "fuzzy_search": 10.0,    # seconds
        "semantic_search": 10.0, # seconds
        "hybrid_search": 15.0,   # seconds
    }
}

# Expected Python files in the project
EXPECTED_PYTHON_FILES = [
    "core.py",
    "cli.py", 
    "models.py",
    "__init__.py"
]

# Expected matcher files
EXPECTED_MATCHER_FILES = [
    "fuzzy_matcher.py",
    "semantic_matcher.py", 
    "adaptive_semantic_matcher.py",
    "hybrid_matcher.py"
]

# Expected classes in the codebase
EXPECTED_CLASSES = [
    "DockerRepoMap",
    "RepoMapConfig", 
    "FuzzyMatchConfig",
    "SemanticMatchConfig",
    "SearchRequest",
    "SearchResponse",
    "ProjectInfo",
    "FuzzyMatcher",
    "SemanticMatcher",
    "AdaptiveSemanticMatcher",
    "HybridMatcher"
]

# Expected functions in the codebase
EXPECTED_FUNCTIONS = [
    "analyze_project",
    "search_identifiers",
    "parse_gitignore",
    "should_ignore_file",
    "extract_identifiers_from_file",
    "extract_identifiers_from_ast"
]

# Test queries for fuzzy search
FUZZY_TEST_QUERIES = [
    "RepoMap",      # Should find DockerRepoMap, RepoMapConfig, etc.
    "matcher",      # Should find FuzzyMatcher, SemanticMatcher, etc.
    "config",       # Should find RepoMapConfig, FuzzyMatchConfig, etc.
    "search",       # Should find search_identifiers, etc.
    "analyze",      # Should find analyze_project, etc.
    "fuzzy",        # Should find FuzzyMatcher, fuzzy matching functions
    "semantic",     # Should find SemanticMatcher, semantic matching functions
    "hybrid"        # Should find HybridMatcher, hybrid matching functions
]

# Test queries for semantic search
SEMANTIC_TEST_QUERIES = [
    "code analysis",           # Should find analyze_project, etc.
    "matching algorithms",     # Should find matchers, etc.
    "configuration management", # Should find config classes, etc.
    "file processing",         # Should find file-related functions, etc.
    "search functionality",    # Should find search methods, etc.
    "text similarity",         # Should find similarity functions, etc.
    "pattern matching",        # Should find pattern matching functions, etc.
    "data structures"          # Should find data structure classes, etc.
]

# Test queries for hybrid search
HYBRID_TEST_QUERIES = [
    "RepoMap",              # Should find both exact and semantic matches
    "matcher",              # Should find matcher classes and related concepts
    "configuration",        # Should find config classes and related concepts
    "search",               # Should find search methods and related concepts
    "analysis"              # Should find analysis functions and related concepts
]

# Specific identifiers to test for
SPECIFIC_IDENTIFIERS = [
    "DockerRepoMap",        # Main class
    "RepoMapConfig",        # Configuration class
    "analyze_project",      # Core function
    "search_identifiers",   # Search function
    "FuzzyMatcher",         # Matcher class
    "SemanticMatcher",      # Matcher class
    "HybridMatcher",        # Matcher class
    "parse_gitignore",      # Utility function
    "extract_identifiers_from_file",  # Core function
    "should_ignore_file"    # Utility function
]

# Performance test queries
PERFORMANCE_TEST_QUERIES = [
    "RepoMap",
    "matcher", 
    "config",
    "search",
    "analyze"
]

# Fuzzy matching configuration
FUZZY_CONFIG = {
    "enabled": True,
    "threshold": 70,
    "strategies": ["prefix", "substring", "levenshtein"],
    "cache_results": True
}

# Semantic matching configuration
SEMANTIC_CONFIG = {
    "enabled": True,
    "threshold": 0.1,
    "use_tfidf": True,
    "min_word_length": 3,
    "cache_results": True
}

# Hybrid configuration (both fuzzy and semantic)
HYBRID_CONFIG = {
    "fuzzy_match": FUZZY_CONFIG,
    "semantic_match": SEMANTIC_CONFIG
}

# Test assertions and validations
VALIDATIONS = {
    "min_identifiers": 10,           # Minimum number of identifiers to find
    "min_python_files": 5,           # Minimum number of Python files to find
    "min_search_results": 1,         # Minimum search results per query
    "max_search_time": 5.0,          # Maximum time per search operation (seconds)
    "context_min_length": 10,        # Minimum context length
    "score_thresholds": {
        "fuzzy": 0.7,               # Fuzzy search score threshold
        "semantic": 0.1,            # Semantic search score threshold
        "hybrid": 0.1               # Hybrid search score threshold
    }
}

# Error test cases
ERROR_TEST_CASES = [
    {
        "name": "empty_query",
        "query": "",
        "expected_behavior": "graceful_handling"
    },
    {
        "name": "short_query", 
        "query": "a",
        "expected_behavior": "graceful_handling"
    },
    {
        "name": "very_long_query",
        "query": "a" * 1000,
        "expected_behavior": "graceful_handling"
    },
    {
        "name": "special_characters",
        "query": "!@#$%^&*()",
        "expected_behavior": "graceful_handling"
    }
]

# Performance benchmarks
PERFORMANCE_BENCHMARKS = {
    "fuzzy_only": {
        "max_time": 10.0,
        "description": "Fuzzy search only mode"
    },
    "semantic_only": {
        "max_time": 10.0, 
        "description": "Semantic search only mode"
    },
    "hybrid": {
        "max_time": 15.0,
        "description": "Hybrid search mode"
    }
}

def get_test_config() -> Dict[str, Any]:
    """Get the complete test configuration."""
    return {
        "config": TEST_CONFIG,
        "expected_files": EXPECTED_PYTHON_FILES + EXPECTED_MATCHER_FILES,
        "expected_classes": EXPECTED_CLASSES,
        "expected_functions": EXPECTED_FUNCTIONS,
        "fuzzy_queries": FUZZY_TEST_QUERIES,
        "semantic_queries": SEMANTIC_TEST_QUERIES,
        "hybrid_queries": HYBRID_TEST_QUERIES,
        "specific_identifiers": SPECIFIC_IDENTIFIERS,
        "performance_queries": PERFORMANCE_TEST_QUERIES,
        "fuzzy_config": FUZZY_CONFIG,
        "semantic_config": SEMANTIC_CONFIG,
        "hybrid_config": HYBRID_CONFIG,
        "validations": VALIDATIONS,
        "error_cases": ERROR_TEST_CASES,
        "performance_benchmarks": PERFORMANCE_BENCHMARKS
    }
