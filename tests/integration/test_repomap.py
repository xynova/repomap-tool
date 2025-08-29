#!/usr/bin/env python3

from aider.repomap import RepoMap
import os


class SimpleIO:
    def read_text(self, fname):
        if os.path.exists(fname):
            with open(fname, "r") as f:
                content = f.read()
            return content
        else:
            return "def test(): pass"

    def tool_warning(self, msg):
        pass


class SimpleModel:
    def token_count(self, text):
        return len(text.split())


def test_repomap_creation():
    """Test that RepoMap can be created with simple components."""
    rm = RepoMap(root=".", io=SimpleIO(), main_model=SimpleModel())
    assert rm is not None


def test_get_ranked_tags_map():
    """Test that get_ranked_tags_map returns expected format."""
    rm = RepoMap(root=".", io=SimpleIO(), main_model=SimpleModel())

    test_file = "src/repomap_tool/core.py"
    result = rm.get_ranked_tags_map([test_file], max_map_tokens=1024)

    # Can return None or string (as we discovered)
    assert result is None or isinstance(result, str)


def test_get_tags():
    """Test that get_tags returns tag objects."""
    rm = RepoMap(root=".", io=SimpleIO(), main_model=SimpleModel())

    test_file = "src/repomap_tool/core.py"
    tags = list(rm.get_tags(test_file, test_file))

    # Should find some tags
    assert len(tags) > 0

    # Tags should have name and kind attributes
    for tag in tags[:5]:  # Check first 5 tags
        assert hasattr(tag, "name")
        assert hasattr(tag, "kind")
        assert tag.name is not None
