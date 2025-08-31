"""
Cache management with LRU eviction and memory limits.

This module provides a CacheManager class that implements:
- LRU (Least Recently Used) eviction policy
- TTL (Time To Live) expiration
- Memory usage monitoring
- Cache hit/miss metrics
"""

import time
import logging
from typing import Any, Dict, Optional, Tuple
from ..exceptions import CacheError

logger = logging.getLogger(__name__)


class CacheManager:
    """
    A cache manager with LRU eviction, TTL expiration, and memory monitoring.

    Features:
    - LRU eviction when cache reaches max_size
    - TTL expiration for cache entries
    - Memory usage tracking
    - Cache hit/miss statistics
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl: int = 3600,
        enable_memory_monitoring: bool = True,
    ):
        """
        Initialize the cache manager.

        Args:
            max_size: Maximum number of cache entries
            ttl: Time to live in seconds for cache entries
            enable_memory_monitoring: Whether to track memory usage
        """
        self.max_size = max_size
        self.ttl = ttl
        self.enable_memory_monitoring = enable_memory_monitoring

        # Cache storage: {key: (value, timestamp)}
        self._cache: Dict[str, Tuple[Any, float]] = {}

        # Access times for LRU tracking: {key: last_access_time}
        self._access_times: Dict[str, float] = {}

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0

        logger.debug(f"CacheManager initialized with max_size={max_size}, ttl={ttl}")

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        if key not in self._cache:
            self._misses += 1
            return None

        value, timestamp = self._cache[key]
        current_time = time.time()

        # Check if entry has expired
        if current_time - timestamp > self.ttl:
            self._expirations += 1
            self._evict(key)
            return None

        # Update access time for LRU
        self._access_times[key] = current_time
        self._hits += 1

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        # If max_size is 0, caching is disabled
        if self.max_size == 0:
            return

        current_time = time.time()

        # If key already exists, update it
        if key in self._cache:
            self._cache[key] = (value, current_time)
            self._access_times[key] = current_time
            return

        # Check if we need to evict before adding
        if len(self._cache) >= self.max_size:
            self._evict_lru()

        # Add new entry
        self._cache[key] = (value, current_time)
        self._access_times[key] = current_time

        logger.debug(f"Added key '{key}' to cache (size: {len(self._cache)})")

    def _evict(self, key: str) -> None:
        """
        Remove a specific key from cache.

        Args:
            key: Key to remove
        """
        if key in self._cache:
            del self._cache[key]
        if key in self._access_times:
            del self._access_times[key]

    def _evict_lru(self) -> None:
        """Remove the least recently used item from cache."""
        if not self._access_times:
            return

        # Find the oldest accessed item
        oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])

        self._evict(oldest_key)
        self._evictions += 1

        logger.debug(f"Evicted LRU key '{oldest_key}' from cache")

    def clear(self) -> None:
        """Clear all cache entries."""
        cache_size = len(self._cache)
        self._cache.clear()
        self._access_times.clear()

        logger.info(f"Cache cleared ({cache_size} entries removed)")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        stats = {
            "cache_size": len(self._cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
            "evictions": self._evictions,
            "expirations": self._expirations,
            "total_requests": total_requests,
        }

        if self.enable_memory_monitoring:
            stats["estimated_memory_mb"] = self._estimate_memory_usage()

        return stats

    def _estimate_memory_usage(self) -> float:
        """
        Estimate memory usage of cache in MB.

        Returns:
            Estimated memory usage in MB
        """
        total_size = 0

        # Estimate size of cache entries
        for key, (value, timestamp) in self._cache.items():
            # Key size
            total_size += len(key.encode("utf-8"))

            # Value size (rough estimate)
            if isinstance(value, (list, tuple)):
                total_size += sum(len(str(item).encode("utf-8")) for item in value)
            elif isinstance(value, dict):
                total_size += sum(
                    len(str(k).encode("utf-8")) + len(str(v).encode("utf-8"))
                    for k, v in value.items()
                )
            else:
                total_size += len(str(value).encode("utf-8"))

            # Timestamp (float)
            total_size += 8

        # Access times
        total_size += len(self._access_times) * 8  # float per entry

        # Add some overhead for dictionary structures
        total_size += len(self._cache) * 50  # Rough overhead per entry

        return round(total_size / (1024 * 1024), 4)  # More precision for small values

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of expired entries removed
        """
        current_time = time.time()
        expired_keys = []

        for key, (value, timestamp) in self._cache.items():
            if current_time - timestamp > self.ttl:
                expired_keys.append(key)

        for key in expired_keys:
            self._evict(key)
            self._expirations += 1

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def resize(self, new_max_size: int) -> None:
        """
        Resize the cache to a new maximum size.

        Args:
            new_max_size: New maximum cache size
        """
        if new_max_size < 0:
            raise CacheError(
                "Cache size must be non-negative", {"new_max_size": new_max_size}
            )

        old_max_size = self.max_size
        self.max_size = new_max_size

        # If new size is smaller, evict excess items
        while len(self._cache) > self.max_size:
            self._evict_lru()

        logger.info(f"Cache resized from {old_max_size} to {new_max_size} entries")

    def warm_cache(self, warmup_data: Dict[str, Any]) -> None:
        """
        Pre-populate cache with warmup data.

        Args:
            warmup_data: Dictionary of key-value pairs to pre-load
        """
        for key, value in warmup_data.items():
            if len(self._cache) < self.max_size:
                self.set(key, value)

        logger.info(f"Cache warmed with {len(warmup_data)} entries")
