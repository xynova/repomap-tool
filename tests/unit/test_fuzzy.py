#!/usr/bin/env python3

import pytest
from repomap_tool.core import DockerRepoMap
from repomap_tool.models import RepoMapConfig


def test_identifier_extraction():
    """Test that identifiers are extracted correctly from the project."""
    config = RepoMapConfig(project_root=".", verbose=True)
    dm = DockerRepoMap(config)

    # Get identifiers
    project_files = dm._get_project_files()
    all_tags = []
    for file_path in project_files:
        # file_path is already relative to project root
        try:
            tags = dm.repo_map.get_tags(file_path, file_path)
            if tags:
                all_tags.extend(tags)
        except Exception as e:
            pytest.fail(f"Failed to get tags for {file_path}: {e}")

    identifiers = set()
    for tag in all_tags:
        if hasattr(tag, "name") and tag.name:
            identifiers.add(tag.name)

    # Should have extracted some identifiers
    assert len(identifiers) > 0
    assert "DockerRepoMap" in identifiers
    assert "parse_gitignore" in identifiers


def test_fuzzy_search_with_real_identifiers():
    """Test fuzzy search with real identifiers from the project."""
    config = RepoMapConfig(project_root=".", verbose=True)
    dm = DockerRepoMap(config)

    # Get identifiers
    project_files = dm._get_project_files()
    all_tags = []
    for file_path in project_files:
        # file_path is already relative to project root
        try:
            tags = dm.repo_map.get_tags(file_path, file_path)
            if tags:
                all_tags.extend(tags)
        except Exception as e:
            pytest.fail(f"Failed to get tags for {file_path}: {e}")

    identifiers = set()
    for tag in all_tags:
        if hasattr(tag, "name") and tag.name:
            identifiers.add(tag.name)

    # Test fuzzy matcher
    if dm.fuzzy_matcher:
        # Test DockerRepoMap search
        matches = dm.fuzzy_matcher.match_identifiers("DockerRepoMap", identifiers)
        assert len(matches) > 0
        assert any(identifier == "DockerRepoMap" for identifier, score in matches)

        # Test parse_gitignore search
        matches = dm.fuzzy_matcher.match_identifiers("parse_gitignore", identifiers)
        assert len(matches) > 0
        assert any(identifier == "parse_gitignore" for identifier, score in matches)
    else:
        pytest.skip("Fuzzy matcher not available")
