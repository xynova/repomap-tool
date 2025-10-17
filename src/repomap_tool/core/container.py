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
from repomap_tool.code_analysis.centrality_analysis_engine import CentralityAnalysisEngine
from repomap_tool.code_analysis.centrality_calculator import CentralityCalculator
from repomap_tool.code_analysis.impact_analysis_engine import ImpactAnalysisEngine
from repomap_tool.code_analysis.impact_analyzer import ImpactAnalyzer
from repomap_tool.code_analysis.path_resolver import PathResolver
from repomap_tool.code_analysis.import_analyzer import ImportAnalyzer
from repomap_tool.code_analysis.call_graph_builder import CallGraphBuilder
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
from repomap_tool.protocols import QueryLoaderProtocol
from repomap_tool.code_analysis.query_loader import FileQueryLoader
from repomap_tool.code_analysis.tree_sitter_parser import TreeSitterParser
from repomap_tool.core.repo_map import RepoMapService
from repomap_tool.code_analysis.call_graph_builder import PythonCallAnalyzer, JavaScriptCallAnalyzer
from repomap_tool.cli.output.manager import OutputManager
from repomap_tool.cli.output.console_manager import ConsoleManagerProtocol, DefaultConsoleManager, ConsoleProvider # Import ConsoleProvider
from repomap_tool.cli.utils.console import RichConsoleFactory # Import RichConsoleFactory
from repomap_tool.cli.output.templates.engine import TemplateEngine # Import TemplateEngine
from repomap_tool.cli.output.templates.registry import (
    DefaultTemplateRegistry,
    TemplateRegistryProtocol,
)
from repomap_tool.cli.output.templates.config import TemplateConfig # Import TemplateConfig
from repomap_tool.cli.output.standard_formatters import FormatterRegistry, get_formatter_registry, ProjectInfoFormatter, DictFormatter, ListFormatter, StringFormatter # Import FormatterRegistry and get_formatter_registry

# Legacy factory functions removed - using DI container instead
from ..models import RepoMapConfig
from ..code_analysis.density_analyzer import DensityAnalyzer
from repomap_tool.models import ProjectInfo

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
            "repomap_tool.cli.output.console_manager.DefaultConsoleManager", # Use concrete class
            provider=console_provider(), # Pass the resolved ConsoleProvider instance
        ),
    )

    # Console (callable to get console instance)
    console: "providers.Callable[Console]" = cast(
        "providers.Callable[Console]",
        providers.Callable(console_manager().get_console),
    )

    # Template Engine and Registry
    template_config: "providers.Singleton[TemplateConfig]" = providers.Singleton(
        TemplateConfig, # Default template config
    )

    template_registry: "providers.Singleton[TemplateRegistryProtocol]" = providers.Singleton(
        DefaultTemplateRegistry,  # Use the concrete implementation
    )

    template_engine: "providers.Singleton[TemplateEngine]" = providers.Singleton(
        TemplateEngine,
        template_registry=template_registry, # Reference the provider directly
        template_loader=providers.Singleton("repomap_tool.cli.output.templates.loader.FileTemplateLoader"), # Add template_loader
    )

    # Formatter Registry
    formatter_registry: "providers.Singleton[FormatterRegistry]" = providers.Singleton(
        FormatterRegistry,
    )
    # Output Manager (uses the injected console manager, template engine, and formatter registry)
    output_manager: "providers.Singleton[OutputManager]" = cast(
        "providers.Singleton[OutputManager]",
        providers.Singleton(
            "repomap_tool.cli.output.manager.OutputManager",
            console_manager=console_manager(), # Call the provider to get the instance
            formatter_registry=formatter_registry(), # Call the provider to get the instance
            template_engine=template_engine(), # Call the provider to get the instance
            template_registry=template_registry(), # Call the provider to get the instance
        ),
    )

    # Query loader for tree-sitter queries
    query_loader: "providers.Singleton[QueryLoaderProtocol]" = cast(
        "providers.Singleton[QueryLoaderProtocol]",
        providers.Singleton("repomap_tool.code_analysis.query_loader.FileQueryLoader"), # Corrected from FileTemplateLoader
    )

    # Tag Cache
    tag_cache: "providers.Singleton[TreeSitterTagCache]" = cast(
        "providers.Singleton[TreeSitterTagCache]",
        providers.Singleton(
            "repomap_tool.core.tag_cache.TreeSitterTagCache",
            cache_dir=config.cache_dir,
        ),
    )

    # Tree-sitter Parser (centralized for all dependent services)
    tree_sitter_parser: "providers.Singleton[TreeSitterParser]" = cast(
        "providers.Singleton[TreeSitterParser]",
        providers.Singleton(
            "repomap_tool.code_analysis.tree_sitter_parser.TreeSitterParser",
            project_root=config.project_root,
            cache=tag_cache(), # Ensure cache is passed correctly as a resolved instance
            query_loader=query_loader(), # Ensure query_loader is passed correctly as a resolved instance
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
            ast_analyzer=ast_file_analyzer, # Corrected: ast_analyzer to ast_file_analyzer
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
            ast_analyzer=ast_file_analyzer, # Corrected: ast_analyzer to ast_file_analyzer
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
            tree_sitter_parser=tree_sitter_parser, # Use the registered tree_sitter_parser provider
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
            ast_analyzer=ast_file_analyzer, # Corrected: ast_analyzer to ast_file_analyzer
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
            ast_analyzer=ast_file_analyzer, # Corrected: ast_analyzer to ast_file_analyzer
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

    # Search controller for exploration
    search_controller: "providers.Factory[SearchController]" = cast(
        "providers.Factory[SearchController]",
        providers.Factory(
            "repomap_tool.cli.controllers.search_controller.SearchController",
            repomap_service=None,  # Will be injected from context
            search_engine=None,  # Optional
            fuzzy_matcher=fuzzy_matcher,
            # Dynamically select semantic_matcher based on config
            semantic_matcher=providers.Selector(
                config.semantic_match.enabled,
                true=adaptive_semantic_matcher, # Use adaptive if enabled
                false=domain_semantic_matcher, # Fallback to domain if disabled
            ),
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

    # RepoMap Service
    repo_map_service: "providers.Singleton[RepoMapService]" = cast(
        "providers.Singleton[RepoMapService]",
        providers.Singleton(
            "repomap_tool.core.repo_map.RepoMapService",
            config=config,
            console=console_manager(), # Pass the resolved console_manager instance
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
        ),
    )


def create_container(config: RepoMapConfig) -> Container:
    """Create and configure the dependency injection container."""
    container = Container()

    # Configure the container with the provided config
    try:
        container.config.from_dict(
            {
                "project_root": config.project_root,
                "cache_dir": config.cache_dir,
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
                "embedding": {
                    "cache_dir": config.embedding.cache_dir,
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

    # Register default formatters after the container is configured
    _register_default_formatters(container.formatter_registry,
                                 container.console_manager,
                                 container.template_engine,
                                 container.template_registry)

    return container


def _register_default_formatters(registry: FormatterRegistry,
                                 console_manager: ConsoleManagerProtocol,
                                 template_engine: TemplateEngine,
                                 template_registry: TemplateRegistryProtocol) -> None:
    """Register default formatters."""
    # Register standard formatters
    registry().register_formatter(ProjectInfoFormatter(template_engine=template_engine,
                                                    template_registry=template_registry,
                                                    console_manager=console_manager),
                                ProjectInfo)
    registry().register_formatter(DictFormatter(template_engine=template_engine,
                                             template_registry=template_registry,
                                             console_manager=console_manager),
                                dict)
    registry().register_formatter(ListFormatter(template_engine=template_engine,
                                            template_registry=template_registry,
                                            console_manager=console_manager),
                                list)
    registry().register_formatter(StringFormatter(template_engine=template_engine,
                                                template_registry=template_registry,
                                                console_manager=console_manager),
                                str)

    # Register controller ViewModel formatters
    from repomap_tool.cli.controllers.view_models import CentralityViewModel, ImpactViewModel, SearchViewModel, DensityAnalysisViewModel, TreeClusterViewModel, TreeFocusViewModel, TreeExpansionViewModel, TreePruningViewModel, TreeMappingViewModel, TreeListingViewModel, SessionStatusViewModel, ExplorationViewModel
    from repomap_tool.cli.output.controller_formatters import CentralityViewModelFormatter, ImpactViewModelFormatter, SearchViewModelFormatter, DensityAnalysisFormatter
    from repomap_tool.cli.output.exploration_formatters import TreeClusterViewModelFormatter, TreeFocusViewModelFormatter, TreeExpansionViewModelFormatter, TreePruningViewModelFormatter, TreeMappingViewModelFormatter, TreeListingViewModelFormatter, SessionStatusViewModelFormatter, ExplorationViewModelFormatter


    registry().register_formatter(CentralityViewModelFormatter(template_engine=template_engine,
                                                            template_registry=template_registry,
                                                            console_manager=console_manager),
                                CentralityViewModel)
    registry().register_formatter(ImpactViewModelFormatter(template_engine=template_engine,
                                                        template_registry=template_registry,
                                                        console_manager=console_manager),
                                ImpactViewModel)

    # Register SearchViewModel formatter
    registry().register_formatter(SearchViewModelFormatter(template_engine=template_engine,
                                                        template_registry=template_registry,
                                                        console_manager=console_manager),
                                SearchViewModel)

    # Register DensityAnalysisViewModel formatter
    registry().register_formatter(DensityAnalysisFormatter(template_engine=template_engine,
                                                       template_registry=template_registry,
                                                       console_manager=console_manager),
                                DensityAnalysisViewModel)

    # Register exploration ViewModel formatters
    registry().register_formatter(TreeClusterViewModelFormatter(template_engine=template_engine,
                                                            template_registry=template_registry,
                                                            console_manager=console_manager),
                                TreeClusterViewModel)
    registry().register_formatter(TreeFocusViewModelFormatter(template_engine=template_engine,
                                                          template_registry=template_registry,
                                                          console_manager=console_manager),
                                TreeFocusViewModel)
    registry().register_formatter(TreeExpansionViewModelFormatter(template_engine=template_engine,
                                                              template_registry=template_registry,
                                                              console_manager=console_manager),
                                TreeExpansionViewModel)
    registry().register_formatter(TreePruningViewModelFormatter(template_engine=template_engine,
                                                            template_registry=template_registry,
                                                            console_manager=console_manager),
                                TreePruningViewModel)
    registry().register_formatter(TreeMappingViewModelFormatter(template_engine=template_engine,
                                                            template_registry=template_registry,
                                                            console_manager=console_manager),
                                TreeMappingViewModel)
    registry().register_formatter(TreeListingViewModelFormatter(template_engine=template_engine,
                                                            template_registry=template_registry,
                                                            console_manager=console_manager),
                                TreeListingViewModel)
    registry().register_formatter(SessionStatusViewModelFormatter(template_engine=template_engine,
                                                              template_registry=template_registry,
                                                              console_manager=console_manager),
                                SessionStatusViewModel)
    registry().register_formatter(ExplorationViewModelFormatter(template_engine=template_engine,
                                                            template_registry=template_registry,
                                                            console_manager=console_manager),
                                ExplorationViewModel)

def get_container() -> Optional[Container]:
    """Get the current container instance."""
    return Container.instance if hasattr(Container, "instance") else None
