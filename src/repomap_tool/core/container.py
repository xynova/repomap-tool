"""
Dependency injection container for RepoMap services.

This module provides a centralized container for managing dependencies
and ensuring proper lifecycle management of services.
"""

import logging
from .logging_service import get_logger
from typing import TYPE_CHECKING, Any, Optional, cast

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

if TYPE_CHECKING:
    from repomap_tool.code_analysis.advanced_dependency_graph import (
        AdvancedDependencyGraph,
    )
    from repomap_tool.code_analysis.ast_file_analyzer import ASTFileAnalyzer
    from repomap_tool.code_analysis.centrality_analysis_engine import (
        CentralityAnalysisEngine,
    )
    from repomap_tool.code_analysis.centrality_calculator import CentralityCalculator
    from repomap_tool.code_analysis.impact_analysis_engine import ImpactAnalysisEngine
    from repomap_tool.code_analysis.impact_analyzer import ImpactAnalyzer
    from repomap_tool.code_analysis.path_resolver import PathResolver
    from repomap_tool.code_analysis.import_analyzer import ImportAnalyzer
    from repomap_tool.code_analysis.call_graph_builder import CallGraphBuilder
    from repomap_tool.utils.path_normalizer import PathNormalizer
    from repomap_tool.code_search.fuzzy_matcher import FuzzyMatcher
    from repomap_tool.code_search.adaptive_semantic_matcher import (
        AdaptiveSemanticMatcher,
    )
    from repomap_tool.code_search.hybrid_matcher import HybridMatcher
    from repomap_tool.core.cache_manager import CacheManager
    from repomap_tool.core.parallel_processor import ParallelTagExtractor
    from repomap_tool.code_exploration.session_manager import (
        SessionManager,
        SessionStore,
    )
    from repomap_tool.code_exploration.tree_mapper import TreeMapper
    from repomap_tool.code_exploration.tree_clusters import TreeClusterer
    from repomap_tool.code_exploration.discovery_engine import EntrypointDiscoverer
    from repomap_tool.code_exploration.tree_builder import TreeBuilder
    from repomap_tool.core.tag_cache import TreeSitterTagCache
    from repomap_tool.cli.controllers.centrality_controller import CentralityController
    from repomap_tool.cli.controllers.impact_controller import ImpactController
    from repomap_tool.cli.controllers.search_controller import SearchController
    from repomap_tool.cli.controllers.exploration_controller import (
        ExplorationController,
    )
    from rich.console import Console

# Legacy factory functions removed - using DI container instead
from ..models import RepoMapConfig

logger = get_logger(__name__)


class Container(containers.DeclarativeContainer):
    """Dependency injection container for RepoMap services."""

    # Configuration
    config = providers.Configuration()

    # Tag cache for tree-sitter parsing results (conditionally created)
    tag_cache: "providers.Singleton[TreeSitterTagCache]" = cast(
        "providers.Singleton[TreeSitterTagCache]",
        providers.Singleton(
            "repomap_tool.core.tag_cache.TreeSitterTagCache",
            cache_dir=config.cache_dir,
        ),
    )

    # Core dependency graph
    dependency_graph: "providers.Singleton[AdvancedDependencyGraph]" = cast(
        "providers.Singleton[AdvancedDependencyGraph]",
        providers.Singleton(
            "repomap_tool.code_analysis.advanced_dependency_graph.AdvancedDependencyGraph",
        ),
    )

    # Path normalizer
    path_normalizer: "providers.Singleton[PathNormalizer]" = cast(
        "providers.Singleton[PathNormalizer]",
        providers.Singleton(
            "repomap_tool.utils.path_normalizer.PathNormalizer",
            project_root=config.project_root,
        ),
    )

    # AST analyzer (needed by centrality engine)
    ast_analyzer: "providers.Singleton[ASTFileAnalyzer]" = cast(
        "providers.Singleton[ASTFileAnalyzer]",
        providers.Singleton(
            "repomap_tool.code_analysis.ast_file_analyzer.ASTFileAnalyzer",
            project_root=config.project_root,
        ),
    )

    # Centrality analysis services
    centrality_calculator: "providers.Singleton[CentralityCalculator]" = cast(
        "providers.Singleton[CentralityCalculator]",
        providers.Singleton(
            "repomap_tool.code_analysis.centrality_calculator.CentralityCalculator",
            dependency_graph=dependency_graph,
        ),
    )

    centrality_analysis_engine: "providers.Factory[CentralityAnalysisEngine]" = cast(
        "providers.Factory[CentralityAnalysisEngine]",
        providers.Factory(
            "repomap_tool.code_analysis.centrality_analysis_engine.CentralityAnalysisEngine",
            ast_analyzer=ast_analyzer,
            centrality_calculator=centrality_calculator,
            dependency_graph=dependency_graph,
            path_normalizer=path_normalizer,
        ),
    )

    # Impact analysis services
    impact_analyzer: "providers.Singleton[ImpactAnalyzer]" = cast(
        "providers.Singleton[ImpactAnalyzer]",
        providers.Singleton(
            "repomap_tool.code_analysis.impact_analyzer.ImpactAnalyzer",
            dependency_graph=dependency_graph,
        ),
    )

    impact_analysis_engine: "providers.Factory[ImpactAnalysisEngine]" = cast(
        "providers.Factory[ImpactAnalysisEngine]",
        providers.Factory(
            "repomap_tool.code_analysis.impact_analysis_engine.ImpactAnalysisEngine",
            ast_analyzer=ast_analyzer,
            dependency_graph=dependency_graph,
            path_normalizer=path_normalizer,
        ),
    )

    path_resolver: "providers.Singleton[PathResolver]" = cast(
        "providers.Singleton[PathResolver]",
        providers.Singleton(
            "repomap_tool.code_analysis.path_resolver.PathResolver",
            project_root=config.project_root,
        ),
    )

    # Import analyzer
    import_analyzer: "providers.Singleton[ImportAnalyzer]" = cast(
        "providers.Singleton[ImportAnalyzer]",
        providers.Singleton(
            "repomap_tool.code_analysis.import_analyzer.ImportAnalyzer",
            project_root=config.project_root,
            tree_sitter_parser=providers.Singleton(
                "repomap_tool.code_analysis.tree_sitter_parser.TreeSitterParser",
                project_root=config.project_root,
                cache=tag_cache,
            ),
        ),
    )

    # Session manager
    session_manager: "providers.Singleton[SessionManager]" = cast(
        "providers.Singleton[SessionManager]",
        providers.Singleton(
            "repomap_tool.code_exploration.session_manager.SessionManager",
        ),
    )

    # Core services
    console: "providers.Singleton[Console]" = cast(
        "providers.Singleton[Console]",
        providers.Singleton("rich.console.Console"),
    )

    cache_manager: "providers.Singleton[CacheManager]" = cast(
        "providers.Singleton[CacheManager]",
        providers.Singleton(
            "repomap_tool.core.cache_manager.CacheManager",
        ),
    )

    # Spell checker service
    spellchecker_service: "providers.Singleton[Any]" = providers.Singleton(
        "repomap_tool.core.spellchecker_service.SpellCheckerService",
        custom_dictionary=set(),
    )

    parallel_tag_extractor: "providers.Factory[ParallelTagExtractor]" = cast(
        "providers.Factory[ParallelTagExtractor]",
        providers.Factory(
            "repomap_tool.core.parallel_processor.ParallelTagExtractor",
            max_workers=config.performance.max_workers,
            enable_progress=config.performance.enable_progress,
            console=console,
        ),
    )

    # Matchers with proper dependency injection
    fuzzy_matcher: "providers.Factory[FuzzyMatcher]" = cast(
        "providers.Factory[FuzzyMatcher]",
        providers.Factory(
            "repomap_tool.code_search.fuzzy_matcher.FuzzyMatcher",
            threshold=config.fuzzy_match.threshold,
            strategies=config.fuzzy_match.strategies,
            cache_results=config.fuzzy_match.cache_results,
            verbose=config.verbose,
        ),
    )

    # Embedding matcher with persistent caching
    embedding_matcher: "providers.Singleton[Any]" = providers.Singleton(
        "repomap_tool.code_search.embedding_matcher.EmbeddingMatcher",
        model_name="nomic-ai/CodeRankEmbed",  # FIXED: Use hardcoded value instead of config
        cache_manager=cache_manager,
        cache_dir=config.embedding.cache_dir,
    )

    adaptive_semantic_matcher: "providers.Factory[AdaptiveSemanticMatcher]" = cast(
        "providers.Factory[AdaptiveSemanticMatcher]",
        providers.Factory(
            "repomap_tool.code_search.adaptive_semantic_matcher.AdaptiveSemanticMatcher",
            verbose=config.verbose,
        ),
    )

    # Domain semantic matcher for programming knowledge
    domain_semantic_matcher: "providers.Singleton[Any]" = providers.Singleton(
        "repomap_tool.code_search.semantic_matcher.DomainSemanticMatcher",
        verbose=config.verbose,
    )

    hybrid_matcher: "providers.Factory[HybridMatcher]" = providers.Factory(
        "repomap_tool.code_search.hybrid_matcher.HybridMatcher",
        fuzzy_matcher=fuzzy_matcher,
        embedding_matcher=embedding_matcher,
        domain_semantic_matcher=domain_semantic_matcher,
        semantic_threshold=config.semantic_match.threshold,
        verbose=config.verbose,
    )

    # Additional services for trees and dependencies
    session_store: "providers.Singleton[SessionStore]" = cast(
        "providers.Singleton[SessionStore]",
        providers.Singleton(
            "repomap_tool.code_exploration.session_manager.SessionStore",
        ),
    )

    tree_mapper: "providers.Factory[TreeMapper]" = cast(
        "providers.Factory[TreeMapper]",
        providers.Factory(
            "repomap_tool.code_exploration.tree_mapper.TreeMapper",
        ),
    )

    tree_clusterer: "providers.Factory[TreeClusterer]" = cast(
        "providers.Factory[TreeClusterer]",
        providers.Factory(
            "repomap_tool.code_exploration.tree_clusters.TreeClusterer",
        ),
    )

    # Dependency analysis services
    call_analyzer: "providers.Singleton[CallGraphBuilder]" = cast(
        "providers.Singleton[CallGraphBuilder]",
        providers.Singleton(
            "repomap_tool.code_analysis.call_graph_builder.CallGraphBuilder",
            project_root=config.project_root,
            tree_sitter_parser=providers.Singleton(
                "repomap_tool.code_analysis.tree_sitter_parser.TreeSitterParser",
                project_root=config.project_root,
                cache=tag_cache,
            ),
        ),
    )

    # Controllers
    centrality_controller: "providers.Factory[CentralityController]" = cast(
        "providers.Factory[CentralityController]",
        providers.Factory(
            "repomap_tool.cli.controllers.centrality_controller.CentralityController",
            dependency_graph=dependency_graph,
            centrality_calculator=centrality_calculator,
            centrality_engine=centrality_analysis_engine,
            ast_analyzer=ast_analyzer,
            path_resolver=path_resolver,
        ),
    )

    impact_controller: "providers.Factory[ImpactController]" = cast(
        "providers.Factory[ImpactController]",
        providers.Factory(
            "repomap_tool.cli.controllers.impact_controller.ImpactController",
            dependency_graph=dependency_graph,
            impact_analyzer=impact_analyzer,
            impact_engine=impact_analysis_engine,
            ast_analyzer=ast_analyzer,
            path_resolver=path_resolver,
        ),
    )

    # Entrypoint discoverer for exploration
    entrypoint_discoverer: "providers.Factory[EntrypointDiscoverer]" = cast(
        "providers.Factory[EntrypointDiscoverer]",
        providers.Factory(
            "repomap_tool.code_exploration.discovery_engine.EntrypointDiscoverer",
            repo_map=None,  # Will be injected from context
            import_analyzer=import_analyzer,
            dependency_graph=dependency_graph,
            centrality_calculator=centrality_calculator,
            impact_analyzer=impact_analyzer,
        ),
    )

    # Tree builder for exploration
    tree_builder: "providers.Factory[TreeBuilder]" = cast(
        "providers.Factory[TreeBuilder]",
        providers.Factory(
            "repomap_tool.code_exploration.tree_builder.TreeBuilder",
            repo_map=None,  # Will be injected from context
            entrypoint_discoverer=entrypoint_discoverer,
        ),
    )

    # Search controller for exploration
    search_controller: "providers.Factory[SearchController]" = cast(
        "providers.Factory[SearchController]",
        providers.Factory(
            "repomap_tool.cli.controllers.search_controller.SearchController",
            repomap_service=None,  # Will be injected from context
            search_engine=None,  # Optional
            fuzzy_matcher=fuzzy_matcher,
            semantic_matcher=adaptive_semantic_matcher,
        ),
    )

    # Exploration controller
    exploration_controller: "providers.Factory[ExplorationController]" = cast(
        "providers.Factory[ExplorationController]",
        providers.Factory(
            "repomap_tool.cli.controllers.exploration_controller.ExplorationController",
            search_controller=search_controller,
            session_manager=session_manager,
            tree_builder=tree_builder,
        ),
    )


def create_container(config: RepoMapConfig) -> Container:
    """Create and configure the dependency injection container.

    Args:
        config: RepoMap configuration

    Returns:
        Configured container instance
    """
    container = Container()

    # Configure the container with the provided config
    try:
        container.config.from_dict(
            {
                "project_root": str(config.project_root),
                "dependencies": {
                    "enable_impact_analysis": (
                        config.dependencies.enable_impact_analysis
                        if config.dependencies
                        else False
                    ),
                },
                "fuzzy_match": {
                    "threshold": config.fuzzy_match.threshold,
                    "strategies": config.fuzzy_match.strategies,
                    "cache_results": config.fuzzy_match.cache_results,
                },
                "semantic_match": {
                    "threshold": config.semantic_match.threshold,
                },
                "performance": {
                    "max_workers": config.performance.max_workers,
                    "enable_progress": config.performance.enable_progress,
                },
                "verbose": config.verbose,
            }
        )
        logger.debug("Dependency injection container created and configured")
    except Exception as e:
        logger.error(f"Error configuring container: {e}")
        raise

    return container


def get_container() -> Optional[Container]:
    """Get the current container instance.

    Returns:
        Container instance if available, None otherwise
    """
    return Container.instance if hasattr(Container, "instance") else None
