#!/usr/bin/env python3

from repomap_tool.cli import create_search_config
from repomap_tool.core import DockerRepoMap


def test_search_config_creation():
    """Test that search config is created correctly."""
    config = create_search_config(".", "fuzzy", True)

    assert config.fuzzy_match.enabled is True
    assert config.semantic_match.enabled is False


def test_fuzzy_matcher_initialization():
    """Test that fuzzy matcher is initialized correctly."""
    config = create_search_config(".", "fuzzy", True)
    dm = DockerRepoMap(config)

    assert dm.fuzzy_matcher is not None


def test_fuzzy_matcher_functionality():
    """Test that fuzzy matcher works correctly."""
    config = create_search_config(".", "fuzzy", True)
    dm = DockerRepoMap(config)

    if dm.fuzzy_matcher:
        test_identifiers = {"DockerRepoMap", "parse_gitignore", "should_ignore_file"}
        matches = dm.fuzzy_matcher.match_identifiers("DockerRepoMap", test_identifiers)

        # Should find exact match
        assert len(matches) > 0
        assert any(
            identifier == "DockerRepoMap" and score == 100
            for identifier, score in matches
        )
