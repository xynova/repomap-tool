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
