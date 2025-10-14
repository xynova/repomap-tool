#!/usr/bin/env python3

from repomap_tool.cli.config.loader import load_or_create_config
from repomap_tool.core import RepoMapService


def test_search_config_creation():
    """Test that search config is created correctly."""
    config, was_created = load_or_create_config(
        project_path=".",
        config_file=None,
        create_if_missing=False,
        verbose=True,
    )

    # Fuzzy matching should be enabled by default
    assert config.fuzzy_match.enabled is True


def test_fuzzy_matcher_initialization(session_container, session_test_repo_path):
    """Test that fuzzy matcher is initialized correctly."""
    config, was_created = load_or_create_config(
        project_path=str(session_test_repo_path),
        config_file=None,
        create_if_missing=False,
        verbose=True,
    )
    from tests.conftest import create_repomap_service_from_session_container

    dm = create_repomap_service_from_session_container(session_container, config)

    assert dm.fuzzy_matcher is not None


def test_fuzzy_matcher_functionality(session_container, session_test_repo_path):
    """Test that fuzzy matcher works correctly."""
    config, was_created = load_or_create_config(
        project_path=str(session_test_repo_path),
        config_file=None,
        create_if_missing=False,
        verbose=True,
    )
    from tests.conftest import create_repomap_service_from_session_container

    dm = create_repomap_service_from_session_container(session_container, config)

    if dm.fuzzy_matcher:
        test_identifiers = {"RepoMapService", "parse_gitignore", "should_ignore_file"}
        matches = dm.fuzzy_matcher.match_identifiers("RepoMapService", test_identifiers)

        # Should find exact match
        assert len(matches) > 0
        assert any(
            identifier == "RepoMapService" and score == 100
            for identifier, score in matches
        )
