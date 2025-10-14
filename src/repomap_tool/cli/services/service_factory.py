"""
Service factory for CLI commands with dependency injection.

This module provides a centralized way to create services for CLI commands
using the dependency injection container.
"""

import logging
from repomap_tool.core.logging_service import get_logger
from typing import Optional, Any
from pathlib import Path

from repomap_tool.models import RepoMapConfig
from repomap_tool.core.container import create_container
from repomap_tool.core.repo_map import RepoMapService
from repomap_tool.code_exploration.discovery_engine import EntrypointDiscoverer
from repomap_tool.code_exploration.tree_builder import TreeBuilder
from repomap_tool.code_exploration.tree_manager import TreeManager
from repomap_tool.code_exploration.session_manager import SessionManager
from repomap_tool.code_analysis.advanced_dependency_graph import AdvancedDependencyGraph
from repomap_tool.core.parallel_processor import ParallelTagExtractor
from repomap_tool.code_search.fuzzy_matcher import FuzzyMatcher
from rich.console import Console

logger = get_logger(__name__)


class ServiceFactory:
    """Factory for creating services with dependency injection."""

    def __init__(self) -> None:
        """Initialize the service factory."""
        self._containers: dict[str, Any] = {}
        self._services: dict[str, Any] = {}

    def create_repomap_service(self, config: RepoMapConfig) -> RepoMapService:
        """Create a RepoMapService with all dependencies injected.

        Args:
            config: RepoMap configuration

        Returns:
            RepoMapService instance with injected dependencies
        """
        cache_key = f"repomap_{config.project_root}"

        if cache_key in self._services:
            return self._services[cache_key]  # type: ignore
        # Create DI container
        container = create_container(config)
        self._containers[cache_key] = container

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
        """Create an EntrypointDiscoverer with injected dependencies.

        Args:
            repo_map_service: RepoMapService instance
            config: RepoMap configuration

        Returns:
            EntrypointDiscoverer instance with injected dependencies
        """
        cache_key = f"discoverer_{config.project_root}"

        if cache_key in self._services:
            return self._services[cache_key]  # type: ignore

        # Get container (reuse existing one for this project)
        container = self._containers.get(f"repomap_{config.project_root}")
        if container is None:
            container = create_container(config)
            self._containers[f"repomap_{config.project_root}"] = container

        # Get dependencies from container
        import_analyzer = container.import_analyzer()
        dependency_graph: AdvancedDependencyGraph = container.dependency_graph()
        centrality_calculator = container.centrality_calculator()
        impact_analyzer = None
        if config.dependencies.enable_impact_analysis:
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
        """Create a TreeBuilder with injected dependencies.

        Args:
            repo_map_service: RepoMapService instance
            config: RepoMap configuration

        Returns:
            TreeBuilder instance with injected dependencies
        """
        cache_key = f"tree_builder_{config.project_root}"

        if cache_key in self._services:
            return self._services[cache_key]  # type: ignore

        # Create entrypoint discoverer
        entrypoint_discoverer: EntrypointDiscoverer = self.create_entrypoint_discoverer(
            repo_map_service, config
        )

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
        """Create a TreeManager with injected dependencies.

        Args:
            repo_map_service: RepoMapService instance
            config: RepoMap configuration

        Returns:
            TreeManager instance with injected dependencies
        """
        cache_key = f"tree_manager_{config.project_root}"

        if cache_key in self._services:
            return self._services[cache_key]  # type: ignore

        # Get container (reuse existing one for this project)
        container = self._containers.get(f"repomap_{config.project_root}")
        if container is None:
            container = create_container(config)
            self._containers[f"repomap_{config.project_root}"] = container

        # Get dependencies from container
        session_manager = container.session_manager()
        tree_builder: TreeBuilder = self.create_tree_builder(repo_map_service, config)

        # Create TreeManager with injected dependencies
        tree_manager = TreeManager(
            repo_map=repo_map_service,
            session_manager=session_manager,
            tree_builder=tree_builder,
        )

        self._services[cache_key] = tree_manager
        logger.debug(f"Created TreeManager for {config.project_root}")
        return tree_manager

    def get_llm_analyzer(self, config: RepoMapConfig) -> Any:
        """Get LLM analyzer from container.

        Args:
            config: RepoMap configuration

        Returns:
            LLM analyzer instance
        """
        cache_key = f"llm_analyzer_{config.project_root}"

        if cache_key in self._services:
            return self._services[cache_key]

        # Get container (reuse existing one for this project)
        container = self._containers.get(f"repomap_{config.project_root}")
        if container is None:
            container = create_container(config)
            self._containers[f"repomap_{config.project_root}"] = container

        # Get LLM analyzer from container
        llm_analyzer = container.llm_file_analyzer()
        self._services[cache_key] = llm_analyzer
        logger.debug(f"Created LLM analyzer for {config.project_root}")
        return llm_analyzer

    def clear_cache(self, project_root: Optional[str] = None) -> None:
        """Clear service cache.

        Args:
            project_root: Specific project root to clear, or None to clear all
        """
        if project_root is None:
            self._containers.clear()
            self._services.clear()
            logger.debug("Cleared all service caches")
        else:
            keys_to_remove = [k for k in self._containers.keys() if project_root in k]
            for key in keys_to_remove:
                self._containers.pop(key, None)
                self._services.pop(key, None)
            logger.debug(f"Cleared service cache for {project_root}")


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
