import pytest
from repomap_tool.code_search.fuzzy_matcher import FuzzyMatcher


def test_fuzzy_matcher_basic(session_container, session_test_repo_path):
    """Test fuzzy matcher with simple identifiers."""
    from repomap_tool.models import RepoMapConfig
    from tests.conftest import create_repomap_service_from_session_container

    # Create config and get service from session container
    config = RepoMapConfig(project_root=str(session_test_repo_path))
    repomap_service = create_repomap_service_from_session_container(
        session_container, config
    )
    matcher = repomap_service.fuzzy_matcher

    identifiers = {
        "FuzzyMatcher",
        "fuzzy_search",
        "test_fuzzy",
        "HybridMatcher",
        "SemanticMatcher",
        "test_function",
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
