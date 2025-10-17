#!/usr/bin/env python3

import pytest
from repomap_tool.core import RepoMapService
from repomap_tool.models import RepoMapConfig


def test_identifier_extraction(session_identifiers):
    """Test that identifiers are extracted correctly from the test fixture."""
    # Should have extracted some identifiers from our test fixture
    assert len(session_identifiers) > 0
    # Check for identifiers from our test fixture files
    assert "User" in session_identifiers
    assert "UserRole" in session_identifiers
    assert "sync_function" in session_identifiers


def test_fuzzy_search_with_real_identifiers(session_identifiers, session_container):
    """Test fuzzy search with real identifiers from the test fixture."""
    # Get fuzzy matcher from session container
    fuzzy_matcher = session_container.fuzzy_matcher()

    # Test fuzzy matcher
    if fuzzy_matcher:
        # Test User search
        matches = fuzzy_matcher.match_identifiers("User", session_identifiers)
        assert len(matches) > 0
        assert any(identifier == "User" for identifier, score in matches)

        # Test function search
        matches = fuzzy_matcher.match_identifiers("sync_function", session_identifiers)
        assert len(matches) > 0
        assert any(identifier == "sync_function" for identifier, score in matches)

        # Test partial match
        matches = fuzzy_matcher.match_identifiers("UserR", session_identifiers)
        assert len(matches) > 0
        # Should find UserRole
        assert any("UserRole" in identifier for identifier, score in matches)
    else:
        pytest.skip("Fuzzy matcher not available")


def test_fuzzy_search_with_test_fixture_identifiers(
    session_identifiers, session_container
):
    """Test fuzzy search with specific test fixture identifiers."""
    fuzzy_matcher = session_container.fuzzy_matcher()

    if fuzzy_matcher:
        # Test class search
        matches = fuzzy_matcher.match_identifiers("BaseModel", session_identifiers)
        assert len(matches) > 0
        assert any(identifier == "BaseModel" for identifier, score in matches)

        # Test enum search
        matches = fuzzy_matcher.match_identifiers("UserRole", session_identifiers)
        assert len(matches) > 0
        assert any(identifier == "UserRole" for identifier, score in matches)

        # Test method search
        matches = fuzzy_matcher.match_identifiers(
            "authenticate_user", session_identifiers
        )
        assert len(matches) > 0
        assert any(identifier == "authenticate_user" for identifier, score in matches)
    else:
        pytest.skip("Fuzzy matcher not available")
