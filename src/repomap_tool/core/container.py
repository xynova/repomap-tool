"""
Dependency injection container for RepoMap services.

This module provides a centralized container for managing dependencies
and ensuring proper lifecycle management of services.
"""

import logging
from typing import Optional

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

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
    dependency_graph = providers.Singleton(
        "repomap_tool.dependencies.advanced_dependency_graph.AdvancedDependencyGraph",
    )
    
    # AST analyzer (needed by centrality engine)
    ast_analyzer = providers.Singleton(
        "repomap_tool.dependencies.ast_file_analyzer.ASTFileAnalyzer",
    )
    
    # Centrality analysis services
    centrality_calculator = providers.Singleton(
        "repomap_tool.dependencies.centrality_calculator.CentralityCalculator",
        dependency_graph=dependency_graph,
    )
    
    centrality_analysis_engine = providers.Factory(
        "repomap_tool.dependencies.centrality_analysis_engine.CentralityAnalysisEngine",
        ast_analyzer=ast_analyzer,
        centrality_calculator=centrality_calculator,
        dependency_graph=dependency_graph,
    )
    
    # Impact analysis services
    impact_analyzer = providers.Singleton(
        "repomap_tool.dependencies.impact_analyzer.ImpactAnalyzer",
        dependency_graph=dependency_graph,
    )
    
    impact_analysis_engine = providers.Factory(
        "repomap_tool.dependencies.impact_analysis_engine.ImpactAnalysisEngine",
        ast_analyzer=ast_analyzer,
    )
    
    # LLM file analyzer with proper dependency injection
    llm_file_analyzer = providers.Factory(
        "repomap_tool.dependencies.llm_file_analyzer.LLMFileAnalyzer",
        dependency_graph=dependency_graph,
        centrality_engine=centrality_analysis_engine,
        impact_engine=impact_analysis_engine,
        centrality_calculator=centrality_calculator,
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
    container.config.from_dict({
        "project_root": config.project_root,
        "dependencies": {
            "enable_impact_analysis": config.dependencies.enable_impact_analysis,
        },
        "verbose": config.verbose,
    })
    
    logger.info("Dependency injection container created and configured")
    return container


def get_container() -> Optional[Container]:
    """Get the current container instance.
    
    Returns:
        Container instance if available, None otherwise
    """
    return Container.instance if hasattr(Container, 'instance') else None
