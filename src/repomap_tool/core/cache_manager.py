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
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List, Set
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

        # File timestamp tracking: {file_path: cached_timestamp}
        self._file_timestamps: Dict[str, float] = {}

        # File-based cache keys: {file_path: set_of_cache_keys}
        self._file_cache_keys: Dict[str, Set[str]] = {}

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0
        self._invalidations = 0

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

    def set(self, key: str, value: Any, file_path: Optional[str] = None) -> None:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            file_path: Optional file path for timestamp tracking
        """
        # If max_size is 0, caching is disabled
        if self.max_size == 0:
            return

        current_time = time.time()

        # If key already exists, update it
        if key in self._cache:
            self._cache[key] = (value, current_time)
            self._access_times[key] = current_time
            if file_path:
                self._track_file_cache(key, file_path)
            return

        # Check if we need to evict before adding
        if len(self._cache) >= self.max_size:
            self._evict_lru()

        # Add new entry
        self._cache[key] = (value, current_time)
        self._access_times[key] = current_time

        # Track file association if provided
        if file_path:
            self._track_file_cache(key, file_path)

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
            "invalidations": self._invalidations,
            "total_requests": total_requests,
            "tracked_files": len(self._file_timestamps),
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

    def _track_file_cache(self, cache_key: str, file_path: str) -> None:
        """
        Track association between cache key and file.

        Args:
            cache_key: Cache key to associate with file
            file_path: File path to track
        """
        # Normalize file path
        normalized_path = str(Path(file_path).resolve())

        # Track file timestamp when caching
        try:
            self._file_timestamps[normalized_path] = os.path.getmtime(normalized_path)
        except OSError:
            # File doesn't exist or can't access - don't track
            return

        # Associate cache key with file
        if normalized_path not in self._file_cache_keys:
            self._file_cache_keys[normalized_path] = set()
        self._file_cache_keys[normalized_path].add(cache_key)

        logger.debug(f"Tracking cache key '{cache_key}' for file '{normalized_path}'")

    def is_file_cache_valid(self, file_path: str) -> bool:
        """
        Check if cached data for a file is still valid based on modification time.

        Args:
            file_path: File path to check

        Returns:
            True if cache is valid, False if file has been modified
        """
        normalized_path = str(Path(file_path).resolve())

        # If we don't have timestamp data, consider cache invalid
        if normalized_path not in self._file_timestamps:
            return False

        try:
            current_mtime = os.path.getmtime(normalized_path)
            cached_mtime = self._file_timestamps[normalized_path]

            # Cache is valid if file hasn't been modified since caching
            return current_mtime <= cached_mtime
        except OSError:
            # File doesn't exist anymore - cache is invalid
            return False

    def invalidate_file_cache(self, file_path: str) -> int:
        """
        Invalidate all cache entries associated with a specific file.

        Args:
            file_path: File path whose cache entries should be invalidated

        Returns:
            Number of cache entries invalidated
        """
        normalized_path = str(Path(file_path).resolve())
        invalidated_count = 0

        # Get all cache keys associated with this file
        if normalized_path in self._file_cache_keys:
            cache_keys = self._file_cache_keys[normalized_path].copy()

            for cache_key in cache_keys:
                if cache_key in self._cache:
                    self._evict(cache_key)
                    invalidated_count += 1
                    self._invalidations += 1

            # Clean up file tracking
            del self._file_cache_keys[normalized_path]
            if normalized_path in self._file_timestamps:
                del self._file_timestamps[normalized_path]

            logger.debug(
                f"Invalidated {invalidated_count} cache entries for file '{normalized_path}'"
            )

        return invalidated_count

    def invalidate_stale_files(self, project_files: List[str]) -> int:
        """
        Check all tracked files and invalidate caches for any that have been modified.

        Args:
            project_files: List of project file paths to check

        Returns:
            Number of files whose caches were invalidated
        """
        invalidated_files = 0

        for file_path in project_files:
            normalized_path = str(Path(file_path).resolve())

            # Only check files we're actually tracking
            if normalized_path in self._file_timestamps:
                if not self.is_file_cache_valid(file_path):
                    cache_count = self.invalidate_file_cache(file_path)
                    if cache_count > 0:
                        invalidated_files += 1
                        logger.info(f"Invalidated cache for modified file: {file_path}")

        if invalidated_files > 0:
            logger.info(f"Invalidated caches for {invalidated_files} modified files")

        return invalidated_files

    def get_tracked_files(self) -> List[str]:
        """
        Get list of files currently being tracked for cache invalidation.

        Returns:
            List of file paths being tracked
        """
        return list(self._file_timestamps.keys())
