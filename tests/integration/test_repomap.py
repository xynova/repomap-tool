#!/usr/bin/env python3

from aider.repomap import RepoMap
from aider.io import InputOutput
from aider.models import Model, DEFAULT_MODEL_NAME


def test_repomap_creation():
    """Test that RepoMap can be created with real components."""
    io = InputOutput()
    model = Model(DEFAULT_MODEL_NAME)
    rm = RepoMap(root=".", io=io, main_model=model)
    assert rm is not None


def test_get_ranked_tags_map():
    """Test that get_ranked_tags_map returns expected format."""
    io = InputOutput()
    model = Model(DEFAULT_MODEL_NAME)
    rm = RepoMap(root=".", io=io, main_model=model)

    test_file = "src/repomap_tool/core/repo_map.py"
    result = rm.get_ranked_tags_map([test_file], max_map_tokens=1024)

    # Can return None or string (as we discovered)
    assert result is None or isinstance(result, str)


def test_get_tags():
    """Test that get_tags returns tag objects."""
    io = InputOutput()
    model = Model(DEFAULT_MODEL_NAME)
    rm = RepoMap(root=".", io=io, main_model=model)

    test_file = "src/repomap_tool/core/repo_map.py"
    tags = list(rm.get_tags(test_file, test_file))

    # Should find some tags
    assert len(tags) > 0

    # Tags should have name and kind attributes
    for tag in tags[:5]:  # Check first 5 tags
        assert hasattr(tag, "name")
        assert hasattr(tag, "kind")
        assert tag.name is not None
