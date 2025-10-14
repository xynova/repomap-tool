"""
Unit tests for TreeSitterTagCache.

Tests cache storage, retrieval, invalidation, and statistics.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from repomap_tool.core.tag_cache import TreeSitterTagCache
from repomap_tool.code_analysis.models import CodeTag


class TestTreeSitterTagCache:
    """Test TreeSitterTagCache functionality."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def cache(self, temp_cache_dir):
        """Create cache instance with temporary directory."""
        return TreeSitterTagCache(cache_dir=temp_cache_dir)

    @pytest.fixture
    def sample_tags(self, temp_cache_dir):
        """Create sample CodeTag objects for testing."""
        # Create a real test file
        test_file = temp_cache_dir / "test_file.py"
        test_file.write_text(
            """
class TestClass:
    def test_function(self):
        pass
"""
        )

        return [
            CodeTag(
                name="TestClass",
                kind="class.name",
                file=str(test_file),
                line=2,
                column=0,
                end_line=4,
                end_column=0,
            ),
            CodeTag(
                name="test_function",
                kind="name.definition.function",
                file=str(test_file),
                line=3,
                column=4,
                end_line=4,
                end_column=0,
            ),
        ]

    def test_cache_initialization(self, cache):
        """Test cache initialization creates database."""
        assert cache.db_path.exists()
        assert cache.db_path.is_file()

    def test_set_and_get_tags(self, cache, sample_tags):
        """Test storing and retrieving tags."""
        file_path = "/test/file.py"

        # Set tags
        cache.set_tags(file_path, sample_tags)

        # Get tags
        retrieved_tags = cache.get_tags(file_path)

        assert retrieved_tags is not None
        assert len(retrieved_tags) == 2
        assert retrieved_tags[0].name == "TestClass"
        assert retrieved_tags[1].name == "test_function"

    def test_cache_invalidation_on_file_change(
        self, cache, sample_tags, temp_cache_dir
    ):
        """Test cache invalidation when file is modified."""
        # Create a test file
        test_file = temp_cache_dir / "test_file.py"
        test_file.write_text("def test(): pass")

        # Cache tags for the file
        cache.set_tags(str(test_file), sample_tags)

        # Verify cache is valid
        assert cache.get_tags(str(test_file)) is not None

        # Modify the file
        test_file.write_text("def test(): pass\n# Modified")

        # Cache should be invalid now
        assert cache.get_tags(str(test_file)) is None

    def test_cache_invalidation_on_file_deletion(
        self, cache, sample_tags, temp_cache_dir
    ):
        """Test cache invalidation when file is deleted."""
        # Create a test file
        test_file = temp_cache_dir / "test_file.py"
        test_file.write_text("def test(): pass")

        # Cache tags for the file
        cache.set_tags(str(test_file), sample_tags)

        # Verify cache is valid
        assert cache.get_tags(str(test_file)) is not None

        # Delete the file
        test_file.unlink()

        # Cache should be invalid now
        assert cache.get_tags(str(test_file)) is None

    def test_invalidate_file(self, cache, sample_tags):
        """Test manual file invalidation."""
        # Use the first tag's file path
        file_path = sample_tags[0].file

        # Set tags
        cache.set_tags(file_path, sample_tags)

        # Verify cache is valid
        assert cache.get_tags(file_path) is not None

        # Invalidate file
        cache.invalidate_file(file_path)

        # Cache should be invalid now
        assert cache.get_tags(file_path) is None

    def test_clear_cache(self, cache, sample_tags):
        """Test clearing entire cache."""
        # Use the first tag's file path
        file_path = sample_tags[0].file

        # Set tags
        cache.set_tags(file_path, sample_tags)

        # Verify cache has data
        assert cache.get_tags(file_path) is not None

        # Clear cache
        cache.clear()

        # Cache should be empty
        assert cache.get_tags(file_path) is None

    def test_cache_stats(self, cache, sample_tags):
        """Test cache statistics."""
        # Use the first tag's file path
        file_path = sample_tags[0].file

        # Initially empty
        stats = cache.get_cache_stats()
        assert stats["cached_files"] == 0
        assert stats["total_tags"] == 0

        # Add tags
        cache.set_tags(file_path, sample_tags)

        # Check stats
        stats = cache.get_cache_stats()
        assert stats["cached_files"] == 1
        assert stats["total_tags"] == 2
        assert "cache_location" in stats
        assert "approx_size_bytes" in stats

    def test_multiple_files(self, cache, sample_tags, temp_cache_dir):
        """Test caching multiple files."""
        # Create two separate test files
        file1 = temp_cache_dir / "file1.py"
        file1.write_text("class TestClass:\n    pass")

        file2 = temp_cache_dir / "file2.py"
        file2.write_text("def test_function():\n    pass")

        # Cache different tags for each file
        tags1 = [sample_tags[0]]  # Just the class
        tags2 = [sample_tags[1]]  # Just the function

        cache.set_tags(str(file1), tags1)
        cache.set_tags(str(file2), tags2)

        # Verify each file has correct tags
        retrieved1 = cache.get_tags(str(file1))
        retrieved2 = cache.get_tags(str(file2))

        assert len(retrieved1) == 1
        assert retrieved1[0].name == "TestClass"

        assert len(retrieved2) == 1
        assert retrieved2[0].name == "test_function"

        # Check stats
        stats = cache.get_cache_stats()
        assert stats["cached_files"] == 2
        assert stats["total_tags"] == 2

    def test_empty_tags_list(self, cache, temp_cache_dir):
        """Test caching empty tags list."""
        # Create a real empty file
        file_path = temp_cache_dir / "empty.py"
        file_path.write_text("")

        # Cache empty list
        cache.set_tags(str(file_path), [])

        # Should return empty list, not None
        retrieved = cache.get_tags(str(file_path))
        assert retrieved is not None
        assert len(retrieved) == 0

    def test_nonexistent_file(self, cache):
        """Test getting tags for nonexistent file."""
        file_path = "/nonexistent/file.py"

        # Should return None for nonexistent file
        assert cache.get_tags(file_path) is None
