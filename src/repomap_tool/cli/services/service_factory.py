"""
Service factory for CLI commands with dependency injection.

This module provides a centralized way to create services for CLI commands
using the dependency injection container.
"""

from __future__ import annotations

import logging
from repomap_tool.core.logging_service import get_logger
from typing import Optional, Any, TYPE_CHECKING, Union, cast
from pathlib import Path

from repomap_tool.models import RepoMapConfig
# Revert Container and create_container to TYPE_CHECKING / local import
# from repomap_tool.core.container import Container, create_container # REMOVED
from repomap_tool.core.repo_map import RepoMapService
from repomap_tool.code_exploration.discovery_engine import EntrypointDiscoverer

# from repomap_tool.code_exploration.tree_builder import TreeBuilder # Moved import
# from repomap_tool.code_exploration.tree_manager import TreeManager # Moved import
from repomap_tool.code_exploration.session_manager import SessionManager
from repomap_tool.code_analysis.advanced_dependency_graph import AdvancedDependencyGraph
from repomap_tool.core.parallel_processor import ParallelTagExtractor
from repomap_tool.code_search.fuzzy_matcher import FuzzyMatcher
from rich.console import Console

# from repomap_tool.core.container import Container # Removed top-level import

if TYPE_CHECKING:
    from repomap_tool.code_exploration.tree_builder import TreeBuilder
    from repomap_tool.code_exploration.tree_manager import TreeManager
    # Use string literal for Container type hint in TYPE_CHECKING
    from repomap_tool.core.container import Container # REMOVED, now only string literal used

logger = get_logger(__name__)


class ServiceFactory:
    """Factory for creating services with dependency injection."""

    def __init__(self) -> None:
        """Initialize the service factory."""
        self._containers: dict[str, Any] = {}
        self._services: dict[str, Any] = {}

    def create_repomap_service(self, config: RepoMapConfig) -> RepoMapService:
        """Create a RepoMapService with all dependencies injected."""
        cache_key = f"repomap_{config.project_root}"

        if cache_key in self._services:
            return self._services[cache_key]  # type: ignore
        # Ensure the container is created and cached via the helper method
        container = self._get_or_create_container(config)

        # Get all dependencies from container
        console: Console = container.console()
        parallel_extractor: ParallelTagExtractor = container.parallel_tag_extractor()
        fuzzy_matcher: FuzzyMatcher = container.fuzzy_matcher()
        embedding_matcher = container.embedding_matcher()
        semantic_matcher = None
        hybrid_matcher = None
        if config.semantic_match.enabled:
            semantic_matcher = container.adaptive_semantic_matcher()
            hybrid_matcher = container.hybrid_matcher()

        dependency_graph: AdvancedDependencyGraph = container.dependency_graph()
        impact_analyzer = None
        if config.dependencies.enable_impact_analysis:
            impact_analyzer = container.impact_analyzer()
        centrality_calculator = container.centrality_calculator()
        spellchecker_service = container.spellchecker_service()

        # Create RepoMapService with injected dependencies
        service = RepoMapService(
            config=config,
            console=console,
            parallel_extractor=parallel_extractor,
            fuzzy_matcher=fuzzy_matcher,
            semantic_matcher=semantic_matcher,
            embedding_matcher=embedding_matcher,
            hybrid_matcher=hybrid_matcher,
            dependency_graph=dependency_graph,
            impact_analyzer=impact_analyzer,
            centrality_calculator=centrality_calculator,
            spellchecker_service=spellchecker_service,
        )

        self._services[cache_key] = service
        logger.debug(f"Created RepoMapService for {config.project_root}")
        return service

    def create_entrypoint_discoverer(
        self, repo_map_service: RepoMapService, config: RepoMapConfig
    ) -> EntrypointDiscoverer:
        """Create an EntrypointDiscoverer with injected dependencies."""
        cache_key = f"discoverer_{config.project_root}"

        if cache_key in self._services:
            return self._services[cache_key]  # type: ignore

        # Ensure the container is created and cached via the helper method
        container = self._get_or_create_container(config)

        import_analyzer = container.import_analyzer()
        dependency_graph = container.dependency_graph()
        centrality_calculator = container.centrality_calculator()
        impact_analyzer = container.impact_analyzer()

        # Create EntrypointDiscoverer with injected dependencies
        discoverer = EntrypointDiscoverer(
            repo_map=repo_map_service,
            import_analyzer=import_analyzer,
            dependency_graph=dependency_graph,
            centrality_calculator=centrality_calculator,
            impact_analyzer=impact_analyzer,
        )

        self._services[cache_key] = discoverer
        logger.debug(f"Created EntrypointDiscoverer for {config.project_root}")
        return discoverer

    def create_tree_builder(
        self, repo_map_service: RepoMapService, config: RepoMapConfig
    ) -> TreeBuilder:
        """Create a TreeBuilder with injected dependencies."""
        cache_key = f"tree_builder_{config.project_root}"

        if cache_key in self._services:
            return self._services[cache_key]  # type: ignore

        # Ensure the container is created and cached via the helper method
        container = self._get_or_create_container(config)

        entrypoint_discoverer = container.entrypoint_discoverer()

        from repomap_tool.code_exploration.tree_builder import (
            TreeBuilder,
        )  # Moved import

        # Create TreeBuilder with injected dependencies
        tree_builder = TreeBuilder(
            repo_map=repo_map_service,
            entrypoint_discoverer=entrypoint_discoverer,
        )

        self._services[cache_key] = tree_builder
        logger.debug(f"Created TreeBuilder for {config.project_root}")
        return tree_builder

    def create_tree_manager(
        self, repo_map_service: RepoMapService, config: RepoMapConfig
    ) -> TreeManager:
        """Create a TreeManager with injected dependencies."""
        cache_key = f"tree_manager_{config.project_root}"

        if cache_key in self._services:
            return self._services[cache_key]  # type: ignore

        # Ensure the container is created and cached via the helper method
        container = self._get_or_create_container(config)

        session_manager = container.session_manager()
        tree_builder: TreeBuilder = self.create_tree_builder(repo_map_service, config)

        from repomap_tool.code_exploration.tree_manager import (
            TreeManager,
        )  # Moved import

        # Create TreeManager with injected dependencies
        # The TreeManager constructor expects repo_map_service
        tree_manager = TreeManager(
            session_manager=session_manager,
            tree_builder=tree_builder,
            repo_map=repo_map_service,  # Add missing repo_map argument
        )
        self._services["tree_manager_" + str(config.project_root)] = (
            tree_manager  # Explicitly cast to str
        )
        logger.debug(f"Created and cached TreeManager for {config.project_root}")
        return tree_manager

    def create_fuzzy_matcher(self, config: RepoMapConfig) -> FuzzyMatcher:
        """Create a FuzzyMatcher with all dependencies injected."""
        cache_key = f"fuzzy_matcher_{config.project_root}"

        if cache_key in self._services:
            return self._services[cache_key]  # type: ignore

        # Use the helper method to get or create container
        container = self._get_or_create_container(config)

        # Get fuzzy matcher from container
        fuzzy_matcher = container.fuzzy_matcher()
        self._services[cache_key] = fuzzy_matcher
        logger.debug(f"Created FuzzyMatcher for {config.project_root}")
        return fuzzy_matcher

    def get_llm_analyzer(self, config: RepoMapConfig) -> Any:
        """Get LLM analyzer from container."""
        cache_key = f"llm_analyzer_{config.project_root}"

        if cache_key in self._services:
            return self._services[cache_key]

        # Use the helper method to get or create container
        container = self._get_or_create_container(config)

        # Get LLM analyzer from container
        llm_analyzer = container.llm_file_analyzer()
        self._services[cache_key] = llm_analyzer
        logger.debug(f"Created LLM analyzer for {config.project_root}")
        return llm_analyzer

    def _get_or_create_container(self, config: RepoMapConfig) -> 'Container': # Use string literal for return type
        """Get or create a container for a given project root, with caching.

        Args:
            config: The RepoMapConfig for the project.

        Returns:
            The Dependency Injector container.
        """
        container_key = f"repomap_{str(config.project_root)}"  # Explicitly cast to str
        if container_key not in self._containers:
            # Dynamically import create_container only when needed for initial creation
            import importlib
            container_module = importlib.import_module("repomap_tool.core.container")
            create_container_func = getattr(container_module, "create_container")

            container = create_container_func(config)
            self._containers[container_key] = container
            logger.debug(f"Created and cached new container for {config.project_root}")
        else:
            logger.debug(f"Using cached container for {config.project_root}")
        # No longer casting directly to Container, as it's a dynamic import
        return self._containers[container_key] # Return type handled by string literal hint

    def clear_cache(self, project_root: Optional[Union[str, Path]] = None) -> None:
        """Clear cached services and containers.

        Args:
            project_root: If provided, only clear cache for this specific project root.
        """
        if project_root:
            project_root_str = str(project_root)  # Convert Path to string
            # Clear specific services
            keys_to_remove = [k for k in self._services.keys() if project_root_str in k]
            for k in keys_to_remove:
                del self._services[k]

            # Clear specific containers
            keys_to_remove = [
                k for k in self._containers.keys() if project_root_str in k
            ]
            for k in keys_to_remove:
                del self._containers[k]

            logger.info(f"Cache cleared for project root: {project_root_str}")


# Global service factory instance
_service_factory: Optional[ServiceFactory] = None


def get_service_factory() -> ServiceFactory:
    """Get the global service factory instance.

    Returns:
        ServiceFactory instance
    """
    global _service_factory
    if _service_factory is None:
        _service_factory = ServiceFactory()
    return _service_factory


def clear_service_cache(project_root: Optional[str] = None) -> None:
    """Clear the service cache.

    Args:
        project_root: Specific project root to clear, or None to clear all
    """
    factory = get_service_factory()
    factory.clear_cache(project_root)
