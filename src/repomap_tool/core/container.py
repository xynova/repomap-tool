"""
Dependency injection container for RepoMap services.

This module provides a centralized container for managing dependencies
and ensuring proper lifecycle management of services.
"""

import logging
from .logging_service import get_logger
from typing import Any, Optional, cast

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

# All imports that were previously inside if TYPE_CHECKING:
from repomap_tool.code_analysis.advanced_dependency_graph import AdvancedDependencyGraph
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
from repomap_tool.code_analysis.file_discovery_service import FileDiscoveryService
from repomap_tool.utils.path_normalizer import PathNormalizer
from repomap_tool.code_search.fuzzy_matcher import FuzzyMatcher
from repomap_tool.code_search.adaptive_semantic_matcher import AdaptiveSemanticMatcher
from repomap_tool.code_search.hybrid_matcher import HybridMatcher
from repomap_tool.core.cache_manager import CacheManager
from repomap_tool.code_exploration.session_manager import SessionManager, SessionStore
from repomap_tool.code_exploration.tree_mapper import TreeMapper
from repomap_tool.code_exploration.tree_clusters import TreeClusterer
from repomap_tool.code_exploration.discovery_engine import EntrypointDiscoverer
from repomap_tool.code_exploration.tree_builder import TreeBuilder
from repomap_tool.core.tag_cache import TreeSitterTagCache
from repomap_tool.cli.controllers.centrality_controller import CentralityController
from repomap_tool.cli.controllers.impact_controller import ImpactController
from repomap_tool.cli.controllers.search_controller import SearchController
from repomap_tool.cli.controllers.exploration_controller import ExplorationController
from repomap_tool.cli.controllers.density_controller import DensityController
from rich.console import Console
from repomap_tool.protocols import (
    OutputManagerProtocol,
    TemplateRegistryProtocol,
    CacheManagerProtocol,
    QueryLoaderProtocol,
    TagCacheProtocol,
    ConsoleManagerProtocol,  # Import ConsoleManagerProtocol from central protocols.py
)
from repomap_tool.code_analysis.query_loader import FileQueryLoader
from repomap_tool.code_analysis.tree_sitter_parser import TreeSitterParser
from repomap_tool.core.repo_map import RepoMapService
from repomap_tool.code_analysis.call_graph_builder import (
    PythonCallAnalyzer,
    JavaScriptCallAnalyzer,
)
from repomap_tool.cli.output.manager import OutputManager
from repomap_tool.cli.output.console_manager import (
    DefaultConsoleManager,
    ConsoleProvider,
)  # Import DefaultConsoleManager and ConsoleProvider
from repomap_tool.cli.utils.console import (
    RichConsoleFactory,
)  # Import RichConsoleFactory
from repomap_tool.cli.output.templates.engine import (
    TemplateEngine,
)  # Import TemplateEngine
from repomap_tool.cli.output.templates.registry import DefaultTemplateRegistry
from repomap_tool.cli.output.templates.config import (
    TemplateConfig,
)  # Import TemplateConfig
from repomap_tool.cli.output.standard_formatters import (
    FormatterRegistry,
    ProjectInfoFormatter,
    DictFormatter,
    ListFormatter,
    StringFormatter,
    ErrorResponseFormatter,
    SuccessResponseFormatter,
    SearchResponseFormatter,
)  # Import FormatterRegistry and get_formatter_registry, ErrorResponseFormatter and SuccessResponseFormatter
from repomap_tool.cli.output.controller_formatters import (
    CentralityViewModelFormatter,
    ImpactViewModelFormatter,
    SearchViewModelFormatter,
    DensityAnalysisFormatter,
)
from repomap_tool.cli.output.exploration_formatters import (
    TreeClusterViewModelFormatter,
    TreeFocusViewModelFormatter,
    TreeExpansionViewModelFormatter,
    TreePruningViewModelFormatter,
    TreeMappingViewModelFormatter,
    TreeListingViewModelFormatter,
    SessionStatusViewModelFormatter,
    ExplorationViewModelFormatter,
)
from repomap_tool.cli.controllers.view_models import (
    CentralityViewModel,
    ImpactViewModel,
    SearchViewModel,
    DensityAnalysisViewModel,
    TreeClusterViewModel,
    TreeFocusViewModel,
    TreeExpansionViewModel,
    TreePruningViewModel,
    TreeMappingViewModel,
    TreeListingViewModel,
    SessionStatusViewModel,
    ExplorationViewModel,
)
from repomap_tool.core.spellchecker_service import SpellCheckerService

# Legacy factory functions removed - using DI container instead
from ..models import RepoMapConfig, SearchResponse
from ..code_analysis.density_analyzer import DensityAnalyzer
from repomap_tool.models import (
    ProjectInfo,
    ErrorResponse,
    SuccessResponse,
)  # Import ErrorResponse and SuccessResponse

logger = get_logger(__name__)


class Container(containers.DeclarativeContainer):
    """Dependency injection container for RepoMap services."""

    # Configuration
    config = providers.Configuration()

    # Console Provider
    console_provider: "providers.Singleton[ConsoleProvider]" = providers.Singleton(
        ConsoleProvider,
        factory=providers.Singleton(RichConsoleFactory),
    )

    # Console Manager
    console_manager: "providers.Singleton[ConsoleManagerProtocol]" = cast(
        "providers.Singleton[ConsoleManagerProtocol]",
        providers.Singleton(
            "repomap_tool.cli.output.console_manager.DefaultConsoleManager",  # Use concrete class
            provider=console_provider(),  # Pass the resolved ConsoleProvider instance
        ),
    )

    # Console (callable to get console instance)
    console: "providers.Callable[Console]" = cast(
        "providers.Callable[Console]",
        providers.Callable(console_manager().get_console),
    )

    # Template Engine and Registry
    template_config: providers.Singleton[TemplateConfig] = providers.Singleton(
        TemplateConfig,  # Default template config
    )

    template_registry: providers.Singleton[TemplateRegistryProtocol] = (
        providers.Singleton(
            DefaultTemplateRegistry,  # Use the concrete implementation
            template_loader=providers.Singleton(
                "repomap_tool.cli.output.templates.loader.FileTemplateLoader"
            ),  # Pass template_loader to registry
            default_config=template_config,  # Pass default config to registry
        )
    )

    template_engine: providers.Singleton[TemplateEngine] = providers.Singleton(
        TemplateEngine,
        template_registry=template_registry,
        template_loader=providers.Singleton(
            "repomap_tool.cli.output.templates.loader.FileTemplateLoader"
        ),
        enable_logging=config.verbose,
    )

    # Formatter Registry
    formatter_registry: "providers.Singleton[FormatterRegistry]" = cast(
        "providers.Singleton[FormatterRegistry]",
        providers.Singleton(
            FormatterRegistry,
            template_engine=template_engine,
            template_registry=template_registry,
            console_manager=console_manager,
        ),
    )
    # Output Manager (uses the injected console manager, template engine, and formatter registry)
    output_manager: "providers.Singleton[OutputManager]" = cast(
        "providers.Singleton[OutputManager]",
        providers.Singleton(
            "repomap_tool.cli.output.manager.OutputManager",
            console_manager=console_manager(),
            formatter_registry=formatter_registry(),
            template_engine=template_engine(),
            template_registry=template_registry(),
        ),
    )

    # Query loader for tree-sitter queries
    query_loader: "providers.Singleton[QueryLoaderProtocol]" = cast(
        "providers.Singleton[QueryLoaderProtocol]",
        providers.Singleton(
            "repomap_tool.code_analysis.query_loader.FileQueryLoader"
        ),  # Corrected from FileTemplateLoader
    )

    # Tag Cache
    tag_cache: "providers.Singleton[TreeSitterTagCache]" = cast(
        "providers.Singleton[TreeSitterTagCache]",
        providers.Singleton(
            "repomap_tool.core.tag_cache.TreeSitterTagCache",
            cache_dir=config.cache_dir,
        ),
    )

    # File discovery service provider
    file_discovery_service: "providers.Singleton[FileDiscoveryService]" = cast(
        "providers.Singleton[FileDiscoveryService]",
        providers.Singleton(
            "repomap_tool.code_analysis.file_discovery_service.FileDiscoveryService",
            project_root=config.project_root,
        ),
    )

    # Tree-sitter Parser (centralized for all dependent services)
    tree_sitter_parser: "providers.Singleton[TreeSitterParser]" = cast(
        "providers.Singleton[TreeSitterParser]",
        providers.Singleton(
            "repomap_tool.code_analysis.tree_sitter_parser.TreeSitterParser",
            project_root=config.project_root,
            cache=tag_cache(),  # Ensure cache is passed correctly as a resolved instance
            query_loader=query_loader(),  # Ensure query_loader is passed correctly as a resolved instance
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

    # Python Call Analyzer
    python_call_analyzer: "providers.Singleton[PythonCallAnalyzer]" = cast(
        "providers.Singleton[PythonCallAnalyzer]",
        providers.Singleton(
            "repomap_tool.code_analysis.call_graph_builder.PythonCallAnalyzer",
            tree_sitter_parser=tree_sitter_parser,
        ),
    )

    # JavaScript Call Analyzer
    javascript_call_analyzer: "providers.Singleton[JavaScriptCallAnalyzer]" = cast(
        "providers.Singleton[JavaScriptCallAnalyzer]",
        providers.Singleton(
            "repomap_tool.code_analysis.call_graph_builder.JavaScriptCallAnalyzer",
            project_root=config.project_root,
            tree_sitter_parser=tree_sitter_parser,
        ),
    )

    # Call Graph Builder (uses the injected analyzers)
    call_graph_builder: "providers.Singleton[CallGraphBuilder]" = cast(
        "providers.Singleton[CallGraphBuilder]",
        providers.Singleton(
            "repomap_tool.code_analysis.call_graph_builder.CallGraphBuilder",
            project_root=config.project_root,
            python_call_analyzer=python_call_analyzer,
            javascript_call_analyzer=javascript_call_analyzer,
        ),
    )

    # Import Analyzer
    import_analyzer: "providers.Singleton[ImportAnalyzer]" = cast(
        "providers.Singleton[ImportAnalyzer]",
        providers.Singleton(
            "repomap_tool.code_analysis.import_analyzer.ImportAnalyzer",
            project_root=config.project_root,
            tree_sitter_parser=tree_sitter_parser,
        ),
    )

    # AST File Analyzer
    ast_file_analyzer: "providers.Singleton[ASTFileAnalyzer]" = cast(
        "providers.Singleton[ASTFileAnalyzer]",
        providers.Singleton(
            "repomap_tool.code_analysis.ast_file_analyzer.ASTFileAnalyzer",
            project_root=config.project_root,
            tree_sitter_parser=tree_sitter_parser,
        ),
    )

    # Core dependency graph
    dependency_graph: "providers.Singleton[AdvancedDependencyGraph]" = cast(
        "providers.Singleton[AdvancedDependencyGraph]",
        providers.Singleton(
            "repomap_tool.code_analysis.advanced_dependency_graph.AdvancedDependencyGraph",
            import_analyzer=import_analyzer,
            call_graph_builder=call_graph_builder,
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
            ast_analyzer=ast_file_analyzer,  # Corrected: ast_analyzer to ast_file_analyzer
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
            ast_analyzer=ast_file_analyzer,  # Corrected: ast_analyzer to ast_file_analyzer
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

    # Density analysis services (Added)
    density_analyzer: "providers.Factory[DensityAnalyzer]" = cast(
        "providers.Factory[DensityAnalyzer]",
        providers.Factory(
            "repomap_tool.code_analysis.density_analyzer.DensityAnalyzer",
            tree_sitter_parser=tree_sitter_parser,  # Use the registered tree_sitter_parser provider
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
        model_name="nomic-ai/CodeRankEmbed",
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

    # Controllers
    centrality_controller: "providers.Factory[CentralityController]" = cast(
        "providers.Factory[CentralityController]",
        providers.Factory(
            "repomap_tool.cli.controllers.centrality_controller.CentralityController",
            dependency_graph=dependency_graph,
            centrality_calculator=centrality_calculator,
            centrality_engine=centrality_analysis_engine,
            ast_analyzer=ast_file_analyzer,  # Corrected: ast_analyzer to ast_file_analyzer
            path_resolver=path_resolver,
            import_analyzer=import_analyzer,
        ),
    )

    impact_controller: "providers.Factory[ImpactController]" = cast(
        "providers.Factory[ImpactController]",
        providers.Factory(
            "repomap_tool.cli.controllers.impact_controller.ImpactController",
            dependency_graph=dependency_graph,
            impact_analyzer=impact_analyzer,
            impact_engine=impact_analysis_engine,
            ast_analyzer=ast_file_analyzer,  # Corrected: ast_analyzer to ast_file_analyzer
            path_resolver=path_resolver,
        ),
    )

    # Density controller (Added)
    density_controller: "providers.Factory[DensityController]" = cast(
        "providers.Factory[DensityController]",
        providers.Factory(
            "repomap_tool.cli.controllers.density_controller.DensityController",
            density_analyzer=density_analyzer,
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

    # RepoMapConfig provider that converts dictionary to RepoMapConfig object
    repo_map_config: "providers.Singleton[RepoMapConfig]" = cast(
        "providers.Singleton[RepoMapConfig]",
        providers.Singleton(
            "repomap_tool.models.RepoMapConfig",
            project_root=config.project_root,
            cache_dir=config.cache_dir,
            dependencies=config.dependencies,
            fuzzy_match=config.fuzzy_match,
            embedding=config.embedding,
            semantic_match=config.semantic_match,
            performance=config.performance,
            trees=config.trees,
            output=config.output,
            log_level=config.log_level,
            verbose=config.verbose,
        ),
    )

    # Search Engine
    search_engine: "providers.Singleton[SearchEngine]" = cast(
        "providers.Singleton[SearchEngine]",
        providers.Singleton(
            "repomap_tool.core.search_engine.SearchEngine",
            fuzzy_matcher=fuzzy_matcher,
            semantic_matcher=adaptive_semantic_matcher,
            hybrid_matcher=hybrid_matcher,
        ),
    )

    # RepoMap Service
    repo_map_service: "providers.Singleton[RepoMapService]" = cast(
        "providers.Singleton[RepoMapService]",
        providers.Singleton(
            "repomap_tool.core.repo_map.RepoMapService",
            config=repo_map_config,
            console=console_manager(),  # Pass the resolved console_manager instance
            fuzzy_matcher=fuzzy_matcher,
            semantic_matcher=adaptive_semantic_matcher,
            embedding_matcher=embedding_matcher,
            hybrid_matcher=hybrid_matcher,
            dependency_graph=dependency_graph,
            impact_analyzer=impact_analyzer,
            centrality_calculator=centrality_calculator,
            spellchecker_service=spellchecker_service,
            tree_sitter_parser=tree_sitter_parser,
            tag_cache=tag_cache,
            file_discovery_service=file_discovery_service,
        ),
    )

    # Search controller for exploration
    search_controller: "providers.Factory[SearchController]" = cast(
        "providers.Factory[SearchController]",
        providers.Factory(
            "repomap_tool.cli.controllers.search_controller.SearchController",
            repomap_service=repo_map_service,
            search_engine=search_engine,
            fuzzy_matcher=fuzzy_matcher,
            # Use adaptive semantic matcher by default
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
        config: The initial RepoMapConfig (can be minimal for CLI startup).

    Returns:
        An unconfigured Container instance.
    """
    container = Container()

    # The container's config will be fully loaded by configure_container in each CLI command.
    # For initial setup, we still need to provide a minimal config so providers can be resolved.
    # The actual configuration will be applied later using container.config.from_dict.
    container.config.from_dict(
        {
            "project_root": config.project_root,
            "cache_dir": config.cache_dir,
            "dependencies": {"enable_impact_analysis": False},
            "fuzzy_match": {"threshold": 0.7, "strategies": [], "cache_results": False},
            "embedding": {"cache_dir": None},
            "semantic_match": {"threshold": 0.2},
            "performance": {"max_workers": 1, "enable_progress": False},
            "verbose": False,
        }
    )

    logger.debug(
        f"Dependency injection container created but not fully configured (id={id(container)})"
    )
    return container


def get_container() -> Optional[Container]:
    """Get the current container instance."""
    return Container.instance if hasattr(Container, "instance") else None
