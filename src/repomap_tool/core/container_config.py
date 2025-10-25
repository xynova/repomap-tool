"""
Container configuration utilities.

This module provides functions for configuring the dependency injection container
without creating circular imports.
"""

from typing import Any
from repomap_tool.core.logging_service import get_logger
from repomap_tool.models import RepoMapConfig
from repomap_tool.cli.output.standard_formatters import FormatterRegistry
from repomap_tool.cli.output.templates.engine import TemplateEngine
from repomap_tool.cli.output.templates.registry import TemplateRegistry
from repomap_tool.cli.output.console_manager import ConsoleManager

logger = get_logger(__name__)


def configure_container(container: Any, config_obj: RepoMapConfig) -> None:
    """Configures the container with the given config object and registers default formatters."""
    logger.debug(
        f"Configuring container (id={id(container)}) with RepoMapConfig: {config_obj.project_root}"
    )
    # Update configuration providers - use from_dict since RepoMapConfig is BaseModel, not BaseSettings
    container.config.from_dict(config_obj.model_dump())

    # Resolve necessary services to pass to the registration function
    template_engine_instance = container.template_engine()
    template_registry_instance = container.template_registry()
    console_manager_instance = container.console_manager()
    formatter_registry_instance = container.formatter_registry()

    logger.debug(
        f"FormatterRegistry instance ID before registration: {id(formatter_registry_instance)}"
    )
    _register_default_formatters(
        formatter_registry=formatter_registry_instance,
        template_engine=template_engine_instance,
        template_registry=template_registry_instance,
        console_manager=console_manager_instance,
        config=config_obj,
    )
    logger.debug(
        f"FormatterRegistry instance ID after registration: {id(formatter_registry_instance)}, Total registered: {len(formatter_registry_instance.get_all_formatters())}"
    )


def _register_default_formatters(
    formatter_registry: FormatterRegistry,
    template_engine: TemplateEngine,
    template_registry: TemplateRegistry,
    console_manager: ConsoleManager,
    config: RepoMapConfig,
) -> None:
    """Registers the default formatters with the FormatterRegistry."""
    logger.debug(
        f"Registering default formatters for FormatterRegistry (id={id(formatter_registry)})"
    )

    # Import formatters here to avoid circular imports
    from repomap_tool.cli.output.standard_formatters import (
        ProjectInfoFormatter,
        DictFormatter,
        ListFormatter,
        StringFormatter,
        ErrorResponseFormatter,
        SuccessResponseFormatter,
        SearchResponseFormatter,
    )
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
    from repomap_tool.models import (
        ProjectInfo,
        ErrorResponse,
        SuccessResponse,
        SearchResponse,
    )

    # Register core formatters
    # Register ProjectInfoFormatter
    project_info_formatter = ProjectInfoFormatter(
        template_engine=template_engine,
        template_registry=template_registry,
        console_manager=console_manager,
    )
    formatter_registry.register_formatter(project_info_formatter, ProjectInfo)

    # Register DictFormatter for generic dictionary output
    dict_formatter = DictFormatter(
        template_engine=template_engine,
        template_registry=template_registry,
        console_manager=console_manager,
    )
    formatter_registry.register_formatter(dict_formatter, dict)

    # Register ListFormatter for generic list output
    list_formatter = ListFormatter(
        template_engine=template_engine,
        template_registry=template_registry,
        console_manager=console_manager,
    )
    formatter_registry.register_formatter(list_formatter, list)

    # Register Error and Success Response Formatters
    error_response_formatter = ErrorResponseFormatter(
        template_engine=template_engine,
        template_registry=template_registry,
        console_manager=console_manager,
    )
    formatter_registry.register_formatter(error_response_formatter, ErrorResponse)

    success_response_formatter = SuccessResponseFormatter(
        template_engine=template_engine,
        template_registry=template_registry,
        console_manager=console_manager,
    )
    formatter_registry.register_formatter(success_response_formatter, SuccessResponse)

    # Register Search Response Formatter
    search_response_formatter = SearchResponseFormatter(
        template_engine=template_engine,
        template_registry=template_registry,
        console_manager=console_manager,
    )
    formatter_registry.register_formatter(search_response_formatter, SearchResponse)

    # Register ViewModels specific formatters
    # Centrality ViewModels
    centrality_view_model_formatter = CentralityViewModelFormatter(
        template_engine=template_engine,
        template_registry=template_registry,
        console_manager=console_manager,
    )
    formatter_registry.register_formatter(
        centrality_view_model_formatter, CentralityViewModel
    )

    # Density ViewModels
    density_analysis_formatter = DensityAnalysisFormatter(
        template_engine=template_engine,
        template_registry=template_registry,
        console_manager=console_manager,
    )
    formatter_registry.register_formatter(
        density_analysis_formatter, DensityAnalysisViewModel
    )

    # Impact ViewModels
    impact_view_model_formatter = ImpactViewModelFormatter(
        template_engine=template_engine,
        template_registry=template_registry,
        console_manager=console_manager,
    )
    formatter_registry.register_formatter(impact_view_model_formatter, ImpactViewModel)

    # Exploration ViewModels
    exploration_view_model_formatter = ExplorationViewModelFormatter(
        template_engine=template_engine,
        template_registry=template_registry,
        console_manager=console_manager,
    )
    formatter_registry.register_formatter(
        exploration_view_model_formatter, ExplorationViewModel
    )

    logger.debug(
        f"Finished registering default formatters for FormatterRegistry (id={id(formatter_registry)}). Total registered: {len(formatter_registry.get_all_formatters())}"
    )
