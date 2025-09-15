"""
Configuration factory for creating RepoMap configurations with proper defaults.

This module provides factory methods for creating configuration objects
to avoid direct instantiation and ensure consistent configuration patterns.
"""

import logging
from typing import Optional, List
from pathlib import Path

from repomap_tool.models import (
    RepoMapConfig,
    DependencyConfig,
    FuzzyMatchConfig,
    SemanticMatchConfig,
    PerformanceConfig,
)

logger = logging.getLogger(__name__)


class ConfigFactory:
    """Factory for creating RepoMap configuration objects."""

    @staticmethod
    def create_dependency_config(
        max_graph_size: int = 1000,
        enable_call_graph: bool = True,
        enable_impact_analysis: bool = True,
    ) -> DependencyConfig:
        """Create a DependencyConfig with specified parameters.

        Args:
            max_graph_size: Maximum size of dependency graph
            enable_call_graph: Enable function call graph analysis
            enable_impact_analysis: Enable change impact analysis

        Returns:
            Configured DependencyConfig instance
        """
        return DependencyConfig(
            max_graph_size=max_graph_size,
            enable_call_graph=enable_call_graph,
            enable_impact_analysis=enable_impact_analysis,
        )

    @staticmethod
    def create_fuzzy_match_config(
        threshold: int = 70,
        strategies: Optional[List[str]] = None,
        cache_results: bool = True,
    ) -> FuzzyMatchConfig:
        """Create a FuzzyMatchConfig with specified parameters.

        Args:
            threshold: Match threshold (0-100)
            strategies: List of matching strategies
            cache_results: Enable result caching

        Returns:
            Configured FuzzyMatchConfig instance
        """
        if strategies is None:
            strategies = ["prefix", "substring", "levenshtein"]

        return FuzzyMatchConfig(
            threshold=threshold,
            strategies=strategies,
            cache_results=cache_results,
        )

    @staticmethod
    def create_semantic_match_config(
        threshold: float = 0.6,
        enabled: bool = False,
    ) -> SemanticMatchConfig:
        """Create a SemanticMatchConfig with specified parameters.

        Args:
            threshold: Semantic match threshold (0.0-1.0)
            enabled: Enable semantic matching

        Returns:
            Configured SemanticMatchConfig instance
        """
        return SemanticMatchConfig(
            threshold=threshold,
            enabled=enabled,
        )

    @staticmethod
    def create_performance_config(
        max_workers: int = 4,
        enable_progress: bool = True,
    ) -> PerformanceConfig:
        """Create a PerformanceConfig with specified parameters.

        Args:
            max_workers: Maximum worker threads
            enable_progress: Enable progress bars

        Returns:
            Configured PerformanceConfig instance
        """
        return PerformanceConfig(
            max_workers=max_workers,
            enable_progress=enable_progress,
        )

    @staticmethod
    def create_repomap_config(
        project_root: str,
        dependencies: Optional[DependencyConfig] = None,
        fuzzy_match: Optional[FuzzyMatchConfig] = None,
        semantic_match: Optional[SemanticMatchConfig] = None,
        performance: Optional[PerformanceConfig] = None,
        verbose: bool = False,
        **kwargs,
    ) -> RepoMapConfig:
        """Create a RepoMapConfig with specified parameters.

        Args:
            project_root: Project root path
            dependencies: Dependency configuration
            fuzzy_match: Fuzzy matching configuration
            semantic_match: Semantic matching configuration
            performance: Performance configuration
            verbose: Enable verbose output
            **kwargs: Additional configuration parameters

        Returns:
            Configured RepoMapConfig instance
        """
        # Use defaults if not provided
        if dependencies is None:
            dependencies = ConfigFactory.create_dependency_config()
        if fuzzy_match is None:
            fuzzy_match = ConfigFactory.create_fuzzy_match_config()
        if semantic_match is None:
            semantic_match = ConfigFactory.create_semantic_match_config()
        if performance is None:
            performance = ConfigFactory.create_performance_config()

        return RepoMapConfig(
            project_root=project_root,
            dependencies=dependencies,
            fuzzy_match=fuzzy_match,
            semantic_match=semantic_match,
            performance=performance,
            verbose=verbose,
            **kwargs,
        )

    @staticmethod
    def create_basic_config(project_root: str, verbose: bool = False) -> RepoMapConfig:
        """Create a basic RepoMapConfig with default settings.

        Args:
            project_root: Project root path
            verbose: Enable verbose output

        Returns:
            Basic RepoMapConfig instance
        """
        return ConfigFactory.create_repomap_config(
            project_root=project_root,
            verbose=verbose,
        )

    @staticmethod
    def create_analysis_config(
        project_root: str,
        enable_impact_analysis: bool = True,
        max_graph_size: int = 1000,
        verbose: bool = False,
    ) -> RepoMapConfig:
        """Create a RepoMapConfig optimized for analysis operations.

        Args:
            project_root: Project root path
            enable_impact_analysis: Enable impact analysis
            max_graph_size: Maximum size of dependency graph
            verbose: Enable verbose output

        Returns:
            Analysis-optimized RepoMapConfig instance
        """
        dependencies = ConfigFactory.create_dependency_config(
            max_graph_size=max_graph_size,
            enable_impact_analysis=enable_impact_analysis,
        )

        return ConfigFactory.create_repomap_config(
            project_root=project_root,
            dependencies=dependencies,
            verbose=verbose,
        )

    @staticmethod
    def create_search_config(
        project_root: str,
        fuzzy_threshold: int = 70,
        semantic_enabled: bool = False,
        verbose: bool = False,
    ) -> RepoMapConfig:
        """Create a RepoMapConfig optimized for search operations.

        Args:
            project_root: Project root path
            fuzzy_threshold: Fuzzy matching threshold (0-100)
            semantic_enabled: Enable semantic matching
            verbose: Enable verbose output

        Returns:
            Search-optimized RepoMapConfig instance
        """
        fuzzy_match = ConfigFactory.create_fuzzy_match_config(
            threshold=fuzzy_threshold,
        )

        semantic_match = ConfigFactory.create_semantic_match_config(
            enabled=semantic_enabled,
        )

        return ConfigFactory.create_repomap_config(
            project_root=project_root,
            fuzzy_match=fuzzy_match,
            semantic_match=semantic_match,
            verbose=verbose,
        )


# Global config factory instance
_config_factory: Optional[ConfigFactory] = None


def get_config_factory() -> ConfigFactory:
    """Get the global config factory instance.

    Returns:
        ConfigFactory instance
    """
    global _config_factory
    if _config_factory is None:
        _config_factory = ConfigFactory()
    return _config_factory
