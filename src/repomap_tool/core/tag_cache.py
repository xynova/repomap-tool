"""
Tree-sitter tag caching system for persistent tag storage.

This module provides TreeSitterTagCache class that implements:
- SQLite backend for persistent tag caching
- File hash + mtime validation for cache invalidation
- CodeTag dataclass integration
- Cache statistics and management
"""

import os
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..core.logging_service import get_logger
from ..code_analysis.models import CodeTag

logger = get_logger(__name__)


class TreeSitterTagCache:
    """Generic tag caching system for tree-sitter parsing results using CodeTag"""

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize cache with SQLite backend

        Args:
            cache_dir: Directory for cache storage. Defaults to ~/.repomap-tool/cache
        """
        self.cache_dir = cache_dir or Path.home() / ".repomap-tool" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "tags.db"

        # Check if cache is disabled via environment variable
        if os.getenv("REPOMAP_DISABLE_CACHE", "0").lower() in ("1", "true", "yes"):
            self._cache_disabled = True
        else:
            self._cache_disabled = False
            # Initialize database file if it doesn't exist
            if not self.db_path.exists():
                self._get_db_connection().close()

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get a database connection, initializing the schema if the DB is new or table is missing."""
        db_exists = self.db_path.exists()
        conn = sqlite3.connect(str(self.db_path))

        # Check if the file_cache table exists
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(file_cache)")
        table_info = cursor.fetchall()
        table_exists = len(table_info) > 0

        if not db_exists or not table_exists:
            if not db_exists:
                logger.info(f"Initializing new tag cache database at {self.db_path}")
            elif not table_exists:
                logger.warning(
                    f"Table 'file_cache' missing in existing database at {self.db_path}. Re-initializing schema."
                )
            self._init_db(conn)  # Pass the connection to init_db
        return conn

    def _init_db(self, conn: sqlite3.Connection) -> None:
        """Initialize SQLite database schema"""
        cursor = conn.cursor()

        # File cache table - tracks file metadata
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS file_cache (
                file_path TEXT PRIMARY KEY,
                file_hash TEXT NOT NULL,
                mtime REAL NOT NULL,
                cached_at REAL NOT NULL
            )
        """
        )

        # Tags table - stores CodeTag data
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                name TEXT NOT NULL,
                kind TEXT NOT NULL,
                file TEXT NOT NULL,
                line INTEGER NOT NULL,
                column INTEGER NOT NULL,
                end_line INTEGER,
                end_column INTEGER,
                rel_fname TEXT,
                FOREIGN KEY (file_path) REFERENCES file_cache(file_path)
                    ON DELETE CASCADE
            )
        """
        )

        # Indices for fast lookups
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tags_file
            ON tags(file_path)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tags_kind
            ON tags(kind)
        """
        )

        conn.commit()
        # conn.close() # Remove this line - connection should remain open

    def get_tags(self, file_path: str) -> Optional[List[CodeTag]]:
        """Get cached tags for a file if valid - returns CodeTag objects

        Args:
            file_path: Path to the file to get cached tags for

        Returns:
            List of CodeTag objects if cache is valid, None otherwise
        """
        if self._cache_disabled:
            return None

        if not self._is_cache_valid(file_path):
            return None

        conn = self._get_db_connection()  # Use the new method
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT name, kind, file, line, column, end_line, end_column, rel_fname
            FROM tags WHERE file_path = ?
        """,
            (file_path,),
        )

        rows = cursor.fetchall()
        conn.close()

        # If cache is valid for the file but there are no tag rows, return an empty list
        # This distinguishes between "no cached entry" (handled by _is_cache_valid -> None)
        # and "cached entry with zero tags" (valid empty result for empty files)
        if not rows:
            return []

        tags = []
        for row in rows:
            name, kind, file, line, column, end_line, end_column, rel_fname = row
            tag = CodeTag(
                name=name,
                kind=kind,
                file=file,
                line=line,
                column=column,
                end_line=end_line,
                end_column=end_column,
                rel_fname=rel_fname,
            )
            tags.append(tag)

        return tags

    def set_tags(self, file_path: str, tags: List[CodeTag]) -> None:
        """Cache tags for a file - accepts CodeTag objects

        Args:
            file_path: Path to the file being cached
            tags: List of CodeTag objects to cache
        """
        if self._cache_disabled:
            return

        file_hash = self._compute_file_hash(file_path)
        mtime = Path(file_path).stat().st_mtime

        conn = self._get_db_connection()  # Use the new method
        cursor = conn.cursor()

        # Delete old entry if exists
        cursor.execute("DELETE FROM file_cache WHERE file_path = ?", (file_path,))
        cursor.execute("DELETE FROM tags WHERE file_path = ?", (file_path,))

        # Insert file cache entry
        cursor.execute(
            """
            INSERT INTO file_cache (file_path, file_hash, mtime, cached_at)
            VALUES (?, ?, ?, ?)
        """,
            (file_path, file_hash, mtime, datetime.now().timestamp()),
        )

        # Insert tags
        for tag in tags:
            cursor.execute(
                """
                INSERT INTO tags (file_path, name, kind, file, line, column, end_line, end_column, rel_fname)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    file_path,
                    tag.name,
                    tag.kind,
                    tag.file,
                    tag.line,
                    tag.column,
                    tag.end_line,
                    tag.end_column,
                    tag.rel_fname,
                ),
            )

        conn.commit()
        conn.close()

        logger.debug(f"Cached {len(tags)} tags for {file_path}")

    def invalidate_file(self, file_path: str) -> None:
        """Invalidate cache for a file

        Args:
            file_path: Path to the file to invalidate
        """
        if self._cache_disabled:
            return

        conn = self._get_db_connection()  # Use the new method
        cursor = conn.cursor()
        cursor.execute("DELETE FROM file_cache WHERE file_path = ?", (file_path,))
        cursor.execute("DELETE FROM tags WHERE file_path = ?", (file_path,))
        conn.commit()
        conn.close()

        logger.debug(f"Invalidated cache for {file_path}")

    def clear(self) -> None:
        """Clear entire cache"""
        if self._cache_disabled:
            return

        conn = self._get_db_connection()  # Use the new method
        cursor = conn.cursor()
        cursor.execute("DELETE FROM file_cache")
        cursor.execute("DELETE FROM tags")
        conn.commit()
        conn.close()

        logger.info("Tag cache cleared")

    def _is_cache_valid(self, file_path: str) -> bool:
        """Check if cached data is still valid (mtime + hash)

        Args:
            file_path: Path to the file to check

        Returns:
            True if cache is valid, False otherwise
        """
        if self._cache_disabled:
            return False

        if not Path(file_path).exists():
            return False

        conn = self._get_db_connection()  # Use the new method
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT file_hash, mtime FROM file_cache WHERE file_path = ?
        """,
            (file_path,),
        )

        result = cursor.fetchone()
        conn.close()

        if not result:
            return False

        cached_hash, cached_mtime = result
        if cached_hash is None or cached_mtime is None:
            return False

        current_mtime = Path(file_path).stat().st_mtime

        # Check if file modified
        if current_mtime > cached_mtime:
            return False

        # Check if content changed
        current_hash = self._compute_file_hash(file_path)
        return bool(current_hash == cached_hash)

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file content

        Args:
            file_path: Path to the file

        Returns:
            SHA256 hash as hex string
        """
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        conn = self._get_db_connection()  # Use the new method
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM file_cache")
        file_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tags")
        tag_count = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(LENGTH(name) + LENGTH(kind)) FROM tags")
        approx_size = cursor.fetchone()[0] or 0

        conn.close()

        return {
            "cached_files": file_count,
            "total_tags": tag_count,
            "approx_size_bytes": approx_size,
            "cache_location": str(self.db_path),
        }
