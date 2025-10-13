import pytest
from repomap_tool.code_search.fuzzy_matcher import FuzzyMatcher


def test_fuzzy_matcher_basic():
    """Test fuzzy matcher with simple identifiers."""
    matcher = FuzzyMatcher(threshold=30)
    
    identifiers = {
        "FuzzyMatcher", "fuzzy_search", "test_fuzzy", 
        "HybridMatcher", "SemanticMatcher", "test_function"
    }
    
    # Test 1: Exact match
    results = matcher.match_identifiers("test", identifiers)
    print(f"Query 'test': {len(results)} results")
    for id, score in results[:5]:
        print(f"  {id}: {score}%")
    
    # Test 2: Fuzzy match
    results = matcher.match_identifiers("fuzzy", identifiers)
    print(f"Query 'fuzzy': {len(results)} results")
    for id, score in results[:5]:
        print(f"  {id}: {score}%")
    
    assert len(results) > 0, "Should find fuzzy-related identifiers"

