"""
Centralized configuration service for RepoMap-Tool.

This service provides a single source of truth for all configuration values,
eliminating hardcoded constants scattered across the codebase.
"""

import logging
from .logging_service import get_logger
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = get_logger(__name__)


@dataclass(frozen=True)
class ConfigDefaults:
    """Centralized configuration defaults for RepoMap-Tool."""

    # === MATCHING CONFIGURATION ===
    FUZZY_THRESHOLD: float = 0.7
    SEMANTIC_THRESHOLD: float = 0.3
    HYBRID_THRESHOLD: float = 0.3
    HYBRID_FUZZY_WEIGHT: float = 0.55
    HYBRID_SEMANTIC_WEIGHT: float = 0.45

    # === PERFORMANCE CONFIGURATION ===
    MAX_WORKERS: int = 4
    PARALLEL_THRESHOLD: int = 10
    CACHE_SIZE: int = 1000
    CACHE_TTL: int = 3600
    MAX_MEMORY_MB: int = 100

    # === LLM CONFIGURATION ===
    MAX_TOKENS: int = 4000
    MIN_TOKENS: int = 1000
    MAX_TOKENS_LIMIT: int = 8000
    ANALYSIS_TIMEOUT: int = 30
    MIN_TIMEOUT: int = 5
    MAX_TIMEOUT: int = 120

    # === OUTPUT CONFIGURATION ===
    DEFAULT_LIMIT: int = 5
    MAX_LIMIT: int = 10
    MAX_RESULTS: int = 50
    MAX_CRITICAL_LINES: int = 3
    MAX_DEPENDENCIES: int = 3

    # === TREE EXPLORATION CONFIGURATION ===
    MAX_DEPTH: int = 3
    MIN_DEPTH: int = 1
    MAX_DEPTH_LIMIT: int = 10
    MAX_TREES_PER_SESSION: int = 5
    ENTRYPOINT_THRESHOLD: float = 0.6

    # === DEPENDENCY ANALYSIS CONFIGURATION ===
    MAX_GRAPH_SIZE: int = 1000
    MAX_DEPENDENCY_DEPTH: int = 10
    MAX_TRANSITIVE_DEPTH: int = 20

    # === CENTRALITY ANALYSIS CONFIGURATION ===
    PAGERANK_ALPHA: float = 0.85
    PAGERANK_MAX_ITER: int = 100
    EIGENVECTOR_MAX_ITER: int = 1000

    # === SESSION MANAGEMENT CONFIGURATION ===
    MAX_SESSION_AGE_HOURS: int = 24
    CLEANUP_INTERVAL_HOURS: int = 6

    # === FILE PROCESSING CONFIGURATION ===
    MAX_FILE_WIDTH: int = 50
    SNIPPET_MAX_LINES: int = 10
    MIN_SNIPPET_LINES: int = 5
    MAX_SNIPPET_LINES: int = 20
    MAX_SNIPPETS_PER_FILE: int = 3
    MIN_SNIPPETS_PER_FILE: int = 1
    MAX_SNIPPETS_LIMIT: int = 10

    # === SEARCH CONFIGURATION ===
    SEARCH_LIMIT: int = 50
    MAX_SEARCH_RESULTS: int = 100
    MIN_SEARCH_RESULTS: int = 1

    # === VALIDATION CONFIGURATION ===
    MIN_IDENTIFIERS: int = 10
    MIN_PYTHON_FILES: int = 5
    MIN_CONTEXT_LENGTH: int = 10
    MAX_SEARCH_TIME: float = 5.0

    # === SCORE THRESHOLDS ===
    FUZZY_SCORE_THRESHOLD: float = 0.7
    SEMANTIC_SCORE_THRESHOLD: float = 0.1
    HYBRID_SCORE_THRESHOLD: float = 0.1

    # === COMPRESSION LEVELS ===
    COMPRESSION_LEVELS: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if self.COMPRESSION_LEVELS is None:
            object.__setattr__(self, "COMPRESSION_LEVELS", ["low", "medium", "high"])


class ConfigService:
    """Centralized configuration service for RepoMap-Tool."""

    def __init__(self) -> None:
        """Initialize the configuration service."""
        self.defaults = ConfigDefaults()
        self._overrides: Dict[str, Any] = {}
        logger.info("ConfigService initialized with centralized defaults")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (e.g., 'FUZZY_THRESHOLD')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        # Check overrides first
        if key in self._overrides:
            return self._overrides[key]

        # Check defaults
        if hasattr(self.defaults, key):
            return getattr(self.defaults, key)

        # Return provided default
        return default

    def set(self, key: str, value: Any) -> None:
        """Set a configuration override.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self._overrides[key] = value
        logger.debug(f"Configuration override set: {key} = {value}")

    def reset(self, key: Optional[str] = None) -> None:
        """Reset configuration overrides.

        Args:
            key: Specific key to reset, or None to reset all
        """
        if key is None:
            self._overrides.clear()
            logger.debug("All configuration overrides reset")
        else:
            self._overrides.pop(key, None)
            logger.debug(f"Configuration override reset: {key}")

    def get_all_defaults(self) -> Dict[str, Any]:
        """Get all default configuration values.

        Returns:
            Dictionary of all default configuration values
        """
        return {
            key: value
            for key, value in self.defaults.__dict__.items()
            if not key.startswith("_")
        }

    def get_all_overrides(self) -> Dict[str, Any]:
        """Get all configuration overrides.

        Returns:
            Dictionary of all configuration overrides
        """
        return self._overrides.copy()

    def get_effective_config(self) -> Dict[str, Any]:
        """Get effective configuration (defaults + overrides).

        Returns:
            Dictionary of effective configuration values
        """
        config = self.get_all_defaults()
        config.update(self._overrides)
        return config

    # === CONVENIENCE METHODS ===

    def get_fuzzy_threshold(self) -> float:
        """Get fuzzy matching threshold."""
        return float(self.get("FUZZY_THRESHOLD"))

    def get_semantic_threshold(self) -> float:
        """Get semantic matching threshold."""
        return float(self.get("SEMANTIC_THRESHOLD"))

    def get_hybrid_threshold(self) -> float:
        """Get hybrid matching threshold."""
        return float(self.get("HYBRID_THRESHOLD"))

    def get_max_workers(self) -> int:
        """Get maximum worker threads."""
        return int(self.get("MAX_WORKERS"))

    def get_max_tokens(self) -> int:
        """Get maximum tokens for LLM output."""
        return int(self.get("MAX_TOKENS"))

    def get_analysis_timeout(self) -> int:
        """Get analysis timeout in seconds."""
        return int(self.get("ANALYSIS_TIMEOUT"))

    def get_default_limit(self) -> int:
        """Get default result limit."""
        return int(self.get("DEFAULT_LIMIT"))

    def get_max_depth(self) -> int:
        """Get maximum tree depth."""
        return int(self.get("MAX_DEPTH"))

    def get_cache_size(self) -> int:
        """Get cache size."""
        return int(self.get("CACHE_SIZE"))

    def get_cache_ttl(self) -> int:
        """Get cache TTL in seconds."""
        return int(self.get("CACHE_TTL"))

    def get_compression_levels(self) -> List[str]:
        """Get available compression levels."""
        return list(self.get("COMPRESSION_LEVELS"))

    def validate_compression_level(self, level: str) -> bool:
        """Validate compression level.

        Args:
            level: Compression level to validate

        Returns:
            True if valid, False otherwise
        """
        return level in self.get_compression_levels()

    def validate_max_tokens(self, tokens: int) -> bool:
        """Validate max tokens value.

        Args:
            tokens: Number of tokens to validate

        Returns:
            True if valid, False otherwise
        """
        min_tokens = int(self.get("MIN_TOKENS"))
        max_tokens = int(self.get("MAX_TOKENS_LIMIT"))
        return min_tokens <= tokens <= max_tokens

    def validate_timeout(self, timeout: int) -> bool:
        """Validate timeout value.

        Args:
            timeout: Timeout in seconds to validate

        Returns:
            True if valid, False otherwise
        """
        min_timeout = int(self.get("MIN_TIMEOUT"))
        max_timeout = int(self.get("MAX_TIMEOUT"))
        return min_timeout <= timeout <= max_timeout


# Global configuration service instance
_config_service: Optional[ConfigService] = None


def get_config_service() -> ConfigService:
    """Get the global configuration service instance.

    Returns:
        ConfigService instance
    """
    global _config_service
    if _config_service is None:
        _config_service = ConfigService()
    return _config_service


def set_config_service(service: ConfigService) -> None:
    """Set the global configuration service instance.

    Args:
        service: ConfigService instance
    """
    global _config_service
    _config_service = service


# Convenience functions for backward compatibility
def get_config(key: str, default: Any = None) -> Any:
    """Get a configuration value.

    Args:
        key: Configuration key
        default: Default value if key not found

    Returns:
        Configuration value
    """
    return get_config_service().get(key, default)


def set_config(key: str, value: Any) -> None:
    """Set a configuration override.

    Args:
        key: Configuration key
        value: Configuration value
    """
    get_config_service().set(key, value)


def reset_config(key: Optional[str] = None) -> None:
    """Reset configuration overrides.

    Args:
        key: Specific key to reset, or None to reset all
    """
    get_config_service().reset(key)
