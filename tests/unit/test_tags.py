#!/usr/bin/env python3

from aider.repomap import RepoMap
from aider.io import InputOutput
from aider.models import Model, DEFAULT_MODEL_NAME


def test_tag_extraction():
    """Test that tags are extracted correctly from core/repo_map.py."""
    # Initialize RepoMap
    rm = RepoMap(root=".", main_model=Model(DEFAULT_MODEL_NAME), io=InputOutput())

    # Get tags from core/repo_map.py
    tags = rm.get_tags(
        "src/repomap_tool/core/repo_map.py", "src/repomap_tool/core/repo_map.py"
    )

    # Should find some tags
    assert len(tags) > 0

    # Check available kinds
    kinds = set(tag.kind for tag in tags)
    assert "def" in kinds
    assert "ref" in kinds


def test_dockerrepomap_tag():
    """Test that RepoMapService tag is found."""
    # Initialize RepoMap
    rm = RepoMap(root=".", main_model=Model(DEFAULT_MODEL_NAME), io=InputOutput())

    # Get tags from core/repo_map.py
    tags = rm.get_tags(
        "src/repomap_tool/core/repo_map.py", "src/repomap_tool/core/repo_map.py"
    )

    # Look for RepoMapService specifically
    docker_tags = [tag for tag in tags if "RepoMapService" in tag.name]

    # Should find RepoMapService
    assert len(docker_tags) > 0
    assert any(tag.name == "RepoMapService" for tag in docker_tags)


def test_definition_tags():
    """Test that definition tags are found."""
    # Initialize RepoMap
    rm = RepoMap(root=".", main_model=Model(DEFAULT_MODEL_NAME), io=InputOutput())

    # Get tags from core/repo_map.py
    tags = rm.get_tags(
        "src/repomap_tool/core/repo_map.py", "src/repomap_tool/core/repo_map.py"
    )

    # Look for all 'def' kind tags
    def_tags = [tag for tag in tags if tag.kind == "def"]

    # Should find some definition tags
    assert len(def_tags) > 0
