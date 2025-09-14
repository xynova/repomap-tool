"""
Dependency injection container for RepoMap services.

This module provides a centralized container for managing dependencies
and ensuring proper lifecycle management of services.
"""

import logging
from typing import TYPE_CHECKING, Optional, cast

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

if TYPE_CHECKING:
    from repomap_tool.dependencies.advanced_dependency_graph import (
        AdvancedDependencyGraph,
    )
    from repomap_tool.dependencies.ast_file_analyzer import ASTFileAnalyzer
    from repomap_tool.dependencies.centrality_analysis_engine import (
        CentralityAnalysisEngine,
    )
    from repomap_tool.dependencies.centrality_calculator import CentralityCalculator
    from repomap_tool.dependencies.impact_analysis_engine import ImpactAnalysisEngine
    from repomap_tool.dependencies.impact_analyzer import ImpactAnalyzer
    from repomap_tool.dependencies.llm_file_analyzer import LLMFileAnalyzer
    from repomap_tool.dependencies.path_resolver import PathResolver
    from repomap_tool.llm.context_selector import ContextSelector
    from repomap_tool.llm.hierarchical_formatter import HierarchicalFormatter
    from repomap_tool.llm.token_optimizer import TokenOptimizer
    from repomap_tool.utils.path_normalizer import PathNormalizer

from ..dependencies import (
    get_advanced_dependency_graph,
    get_centrality_calculator,
    get_centrality_analysis_engine,
    get_impact_analyzer,
    get_impact_analysis_engine,
    get_llm_file_analyzer,
)
from ..models import RepoMapConfig

logger = logging.getLogger(__name__)


class Container(containers.DeclarativeContainer):
    """Dependency injection container for RepoMap services."""

    # Configuration
    config = providers.Configuration()

    # Core dependency graph
    dependency_graph: "providers.Singleton[AdvancedDependencyGraph]" = cast(
        "providers.Singleton[AdvancedDependencyGraph]",
        providers.Singleton(
            "repomap_tool.dependencies.advanced_dependency_graph.AdvancedDependencyGraph",
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
            "repomap_tool.dependencies.ast_file_analyzer.ASTFileAnalyzer",
            project_root=config.project_root,
        ),
    )

    # Centrality analysis services
    centrality_calculator: "providers.Singleton[CentralityCalculator]" = cast(
        "providers.Singleton[CentralityCalculator]",
        providers.Singleton(
            "repomap_tool.dependencies.centrality_calculator.CentralityCalculator",
            dependency_graph=dependency_graph,
        ),
    )

    centrality_analysis_engine: "providers.Factory[CentralityAnalysisEngine]" = cast(
        "providers.Factory[CentralityAnalysisEngine]",
        providers.Factory(
            "repomap_tool.dependencies.centrality_analysis_engine.CentralityAnalysisEngine",
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
            "repomap_tool.dependencies.impact_analyzer.ImpactAnalyzer",
            dependency_graph=dependency_graph,
        ),
    )

    impact_analysis_engine: "providers.Factory[ImpactAnalysisEngine]" = cast(
        "providers.Factory[ImpactAnalysisEngine]",
        providers.Factory(
            "repomap_tool.dependencies.impact_analysis_engine.ImpactAnalysisEngine",
            ast_analyzer=ast_analyzer,
        ),
    )

    # LLM services
    token_optimizer: "providers.Singleton[TokenOptimizer]" = cast(
        "providers.Singleton[TokenOptimizer]",
        providers.Singleton(
            "repomap_tool.llm.token_optimizer.TokenOptimizer",
        ),
    )

    context_selector: "providers.Singleton[ContextSelector]" = cast(
        "providers.Singleton[ContextSelector]",
        providers.Singleton(
            "repomap_tool.llm.context_selector.ContextSelector",
            dependency_graph=dependency_graph,
        ),
    )

    hierarchical_formatter: "providers.Singleton[HierarchicalFormatter]" = cast(
        "providers.Singleton[HierarchicalFormatter]",
        providers.Singleton(
            "repomap_tool.llm.hierarchical_formatter.HierarchicalFormatter",
        ),
    )

    path_resolver: "providers.Singleton[PathResolver]" = cast(
        "providers.Singleton[PathResolver]",
        providers.Singleton(
            "repomap_tool.dependencies.path_resolver.PathResolver",
            project_root=config.project_root,
        ),
    )

    # LLM file analyzer with proper dependency injection
    llm_file_analyzer: "providers.Factory[LLMFileAnalyzer]" = cast(
        "providers.Factory[LLMFileAnalyzer]",
        providers.Factory(
            "repomap_tool.dependencies.llm_file_analyzer.LLMFileAnalyzer",
            dependency_graph=dependency_graph,
            project_root=config.project_root,
            ast_analyzer=ast_analyzer,
            token_optimizer=token_optimizer,
            context_selector=context_selector,
            hierarchical_formatter=hierarchical_formatter,
            path_resolver=path_resolver,
            impact_engine=impact_analysis_engine,
            centrality_engine=centrality_analysis_engine,
            centrality_calculator=centrality_calculator,
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
                "project_root": config.project_root,
                "dependencies": {
                    "enable_impact_analysis": (
                        config.dependencies.enable_impact_analysis
                        if config.dependencies
                        else False
                    ),
                },
                "verbose": config.verbose,
            }
        )
        logger.info("Dependency injection container created and configured")
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
