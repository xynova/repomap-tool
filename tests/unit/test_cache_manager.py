"""
Unit tests for CacheManager class.

Tests LRU eviction, TTL expiration, memory monitoring, and statistics.
"""

import time
import pytest
from repomap_tool.core.cache_manager import CacheManager
from repomap_tool.exceptions import CacheError


class TestCacheManager:
    """Test cases for CacheManager functionality."""

    def test_basic_get_set(self):
        """Test basic get and set operations."""
        cache = CacheManager(max_size=10, ttl=3600)

        # Set and get a value
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Get non-existent key
        assert cache.get("nonexistent") is None

    def test_lru_eviction(self):
        """Test LRU eviction when cache reaches max size."""
        cache = CacheManager(max_size=3, ttl=3600)

        # Fill cache to capacity
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # All keys should be present
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

        # Add one more key - should evict the least recently used (key1)
        cache.set("key4", "value4")

        # key1 should be evicted
        assert cache.get("key1") is None
        # Other keys should still be present
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_ttl_expiration(self):
        """Test TTL expiration of cache entries."""
        cache = CacheManager(max_size=10, ttl=1)  # 1 second TTL

        # Set a value
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # Value should be expired
        assert cache.get("key1") is None

    def test_cache_statistics(self):
        """Test cache statistics tracking."""
        cache = CacheManager(max_size=10, ttl=3600)

        # Initial stats
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["cache_size"] == 0
        assert stats["hit_rate_percent"] == 0.0

        # Set and get a value
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["cache_size"] == 1
        assert stats["hit_rate_percent"] == 50.0

    def test_eviction_statistics(self):
        """Test eviction statistics tracking."""
        cache = CacheManager(max_size=2, ttl=3600)

        # Fill cache and trigger eviction
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Should evict key1

        stats = cache.get_stats()
        assert stats["evictions"] == 1
        assert stats["cache_size"] == 2

    def test_expiration_statistics(self):
        """Test expiration statistics tracking."""
        cache = CacheManager(max_size=10, ttl=1)  # 1 second TTL

        cache.set("key1", "value1")
        time.sleep(1.1)
        cache.get("key1")  # Should trigger expiration

        stats = cache.get_stats()
        assert stats["expirations"] == 1

    def test_memory_monitoring(self):
        """Test memory usage estimation."""
        cache = CacheManager(max_size=10, ttl=3600, enable_memory_monitoring=True)

        # Add some data
        cache.set("key1", "value1")
        cache.set("key2", ["item1", "item2", "item3"])

        stats = cache.get_stats()
        assert "estimated_memory_mb" in stats
        assert stats["estimated_memory_mb"] > 0

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        cache = CacheManager(max_size=10, ttl=3600)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get_stats()["cache_size"] == 0

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = CacheManager(max_size=10, ttl=1)  # 1 second TTL

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        time.sleep(1.1)  # Wait for expiration

        # Cleanup should remove expired entries
        expired_count = cache.cleanup_expired()
        assert expired_count == 2
        assert cache.get_stats()["cache_size"] == 0

    def test_resize_cache(self):
        """Test cache resizing functionality."""
        cache = CacheManager(max_size=5, ttl=3600)

        # Fill cache
        for i in range(5):
            cache.set(f"key{i}", f"value{i}")

        assert cache.get_stats()["cache_size"] == 5

        # Resize to smaller size
        cache.resize(3)

        # Should have evicted oldest entries
        assert cache.get_stats()["cache_size"] == 3
        assert cache.get_stats()["max_size"] == 3

    def test_warm_cache(self):
        """Test cache warming functionality."""
        cache = CacheManager(max_size=10, ttl=3600)

        warmup_data = {"key1": "value1", "key2": "value2", "key3": "value3"}

        cache.warm_cache(warmup_data)

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get_stats()["cache_size"] == 3

    def test_disable_caching(self):
        """Test behavior when caching is disabled."""
        cache = CacheManager(max_size=0, ttl=3600)  # Disable caching

        cache.set("key1", "value1")
        assert cache.get("key1") is None  # Should not cache anything

    def test_invalid_resize(self):
        """Test error handling for invalid resize."""
        cache = CacheManager(max_size=10, ttl=3600)

        with pytest.raises(CacheError):
            cache.resize(-1)  # Invalid negative size

    def test_file_timestamp_tracking(self):
        """Test file timestamp tracking functionality."""
        cache = CacheManager(max_size=10, ttl=3600)
        
        # Create a temporary file for testing
        import tempfile
        import os
        from pathlib import Path
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_function(): pass")
            temp_file = f.name
        
        try:
            # Set cache with file association
            cache.set("test_key", "test_value", temp_file)
            
            # Check that file is being tracked
            tracked_files = cache.get_tracked_files()
            assert len(tracked_files) == 1
            assert Path(temp_file).resolve() in [Path(f).resolve() for f in tracked_files]
            
            # Check cache validity
            assert cache.is_file_cache_valid(temp_file) == True
            
        finally:
            # Cleanup
            os.unlink(temp_file)

    def test_file_cache_invalidation(self):
        """Test cache invalidation when files are modified."""
        cache = CacheManager(max_size=10, ttl=3600)
        
        import tempfile
        import os
        import time
        from pathlib import Path
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_function(): pass")
            temp_file = f.name
        
        try:
            # Set cache with file association
            cache.set("test_key", "test_value", temp_file)
            cache.set("another_key", "another_value", temp_file)
            
            # Verify cache is working
            assert cache.get("test_key") == "test_value"
            assert cache.get("another_key") == "another_value"
            
            # Wait a bit to ensure different timestamp
            time.sleep(0.1)
            
            # Modify the file
            with open(temp_file, 'w') as f:
                f.write("def test_function_modified(): pass")
            
            # Check that cache is now invalid
            assert cache.is_file_cache_valid(temp_file) == False
            
            # Invalidate stale files
            invalidated_count = cache.invalidate_stale_files([temp_file])
            assert invalidated_count == 1
            
            # Check that cache entries are gone
            assert cache.get("test_key") is None
            assert cache.get("another_key") is None
            
            # Check that file is no longer tracked
            tracked_files = cache.get_tracked_files()
            assert len(tracked_files) == 0
            
        finally:
            # Cleanup
            os.unlink(temp_file)

    def test_multiple_file_tracking(self):
        """Test tracking multiple files independently."""
        cache = CacheManager(max_size=10, ttl=3600)
        
        import tempfile
        import os
        import time
        from pathlib import Path
        
        # Create two temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f1:
            f1.write("def file1_function(): pass")
            temp_file1 = f1.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f2:
            f2.write("def file2_function(): pass")
            temp_file2 = f2.name
        
        try:
            # Set cache entries for different files
            cache.set("key1", "value1", temp_file1)
            cache.set("key2", "value2", temp_file2)
            
            # Check both files are tracked
            tracked_files = cache.get_tracked_files()
            assert len(tracked_files) == 2
            
            # Modify only one file
            time.sleep(0.1)
            with open(temp_file1, 'w') as f:
                f.write("def file1_function_modified(): pass")
            
            # Invalidate stale files
            invalidated_count = cache.invalidate_stale_files([temp_file1, temp_file2])
            assert invalidated_count == 1
            
            # Only key1 should be invalidated, key2 should remain
            assert cache.get("key1") is None
            assert cache.get("key2") == "value2"
            
            # Only file1 should be removed from tracking
            tracked_files = cache.get_tracked_files()
            assert len(tracked_files) == 1
            assert Path(temp_file2).resolve() in [Path(f).resolve() for f in tracked_files]
            
        finally:
            # Cleanup
            os.unlink(temp_file1)
            os.unlink(temp_file2)

    def test_file_cache_invalidation_statistics(self):
        """Test that file cache invalidation is properly tracked in statistics."""
        cache = CacheManager(max_size=10, ttl=3600)
        
        import tempfile
        import os
        import time
        from pathlib import Path
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_function(): pass")
            temp_file = f.name
        
        try:
            # Set multiple cache entries
            cache.set("key1", "value1", temp_file)
            cache.set("key2", "value2", temp_file)
            cache.set("key3", "value3", temp_file)
            
            # Check initial stats
            stats = cache.get_stats()
            assert stats["invalidations"] == 0
            assert stats["tracked_files"] == 1
            
            # Modify file and invalidate
            time.sleep(0.1)
            with open(temp_file, 'w') as f:
                f.write("def test_function_modified(): pass")
            
            invalidated_count = cache.invalidate_stale_files([temp_file])
            assert invalidated_count == 1
            
            # Check final stats
            stats = cache.get_stats()
            assert stats["invalidations"] == 3  # 3 keys were invalidated
            assert stats["tracked_files"] == 0  # No files tracked anymore
            
        finally:
            # Cleanup
            os.unlink(temp_file)

    def test_file_cache_invalidation_edge_cases(self):
        """Test edge cases for file cache invalidation."""
        cache = CacheManager(max_size=10, ttl=3600)
        
        # Test with non-existent file
        assert cache.is_file_cache_valid("/nonexistent/file.py") == False
        
        # Test with None file path
        cache.set("key1", "value1", None)
        assert cache.get("key1") == "value1"  # Should still work
        
        # Test invalidate_stale_files with empty list
        invalidated_count = cache.invalidate_stale_files([])
        assert invalidated_count == 0
        
        # Test invalidate_stale_files with non-existent files
        invalidated_count = cache.invalidate_stale_files(["/nonexistent/file.py"])
        assert invalidated_count == 0

    def test_file_path_normalization(self):
        """Test that file paths are properly normalized for tracking."""
        cache = CacheManager(max_size=10, ttl=3600)
        
        import tempfile
        import os
        from pathlib import Path
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_function(): pass")
            temp_file = f.name
        
        try:
            # Get absolute path
            abs_path = str(Path(temp_file).resolve())
            
            # Set cache with relative path (should be normalized)
            cache.set("test_key", "test_value", temp_file)
            
            # Check that absolute path is tracked
            tracked_files = cache.get_tracked_files()
            assert len(tracked_files) == 1
            assert abs_path in tracked_files
            
            # Check validity with different path representations
            assert cache.is_file_cache_valid(temp_file) == True
            assert cache.is_file_cache_valid(abs_path) == True
            
        finally:
            # Cleanup
            os.unlink(temp_file)

    def test_file_cache_invalidation_with_errors(self):
        """Test file cache invalidation handles file access errors gracefully."""
        cache = CacheManager(max_size=10, ttl=3600)
        
        import tempfile
        import os
        import time
        from pathlib import Path
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_function(): pass")
            temp_file = f.name
        
        try:
            # Set cache with file association
            cache.set("test_key", "test_value", temp_file)
            
            # Verify file is tracked
            assert len(cache.get_tracked_files()) == 1
            
            # Delete the file (simulate file access error)
            os.unlink(temp_file)
            
            # Check that cache is considered invalid for deleted file
            assert cache.is_file_cache_valid(temp_file) == False
            
            # Invalidation should handle this gracefully
            invalidated_count = cache.invalidate_stale_files([temp_file])
            assert invalidated_count == 1
            
        except Exception:
            # Cleanup in case of error
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            raise
