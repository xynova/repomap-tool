"""
Protocols for type safety in repomap-tool.

This module defines protocols and type-safe interfaces for the core components.
"""

from typing import (
    Protocol,
    List,
    Set,
    Optional,
    Dict,
    Any,
    TypedDict,
    Union,
    Type,
    TypeVar,
)
from abc import ABC, abstractmethod  # Import ABC and abstractmethod from abc module
from pathlib import Path

from repomap_tool.code_analysis.models import CodeTag
from repomap_tool.models import OutputConfig, OutputFormat, AnalysisFormat
import click
from rich.console import Console
from repomap_tool.core.logging_service import (
    get_logger,
)  # Correct import for get_logger

# Removed ConsoleManagerProtocol and TemplateLoader imports to avoid circular dependencies

# Type variables for generic formatters
T = TypeVar("T")


class RepoMapProtocol(Protocol):
    """Protocol for RepoMap-like objects."""

    def get_tags(self, file_path: str, rel_fname: str) -> List[CodeTag]: ...

    def get_ranked_tags_map(
        self, files: List[str], max_tokens: int
    ) -> Optional[str]: ...


class MatcherProtocol(Protocol):
    """Protocol for matcher objects."""

    def match_identifiers(
        self, query: str, all_identifiers: Set[str], threshold: Optional[float] = None
    ) -> List[tuple[str, int]]: ...

    def clear_cache(self) -> None: ...

    def get_cache_stats(self) -> Dict[str, Any]: ...


class FuzzyMatcherProtocol(MatcherProtocol):
    """Protocol for fuzzy matcher objects."""

    threshold: int
    strategies: List[str]
    cache_results: bool
    verbose: bool
    enabled: bool


class SemanticMatcherProtocol(MatcherProtocol):
    """Protocol for semantic matcher objects."""

    threshold: float
    use_tfidf: bool
    min_word_length: int
    cache_results: bool
    enabled: bool


class HybridMatcherProtocol(MatcherProtocol):
    """Protocol for hybrid matcher objects."""

    fuzzy_threshold: int
    semantic_threshold: float
    verbose: bool
    enabled: bool


class CacheManagerProtocol(Protocol):
    """Protocol for cache manager objects."""

    def get(self, key: str) -> Optional[Any]: ...

    def set(self, key: str, value: Any) -> None: ...

    def clear(self) -> None: ...

    def get_stats(self) -> Dict[str, Any]: ...

    def cleanup_expired(self) -> int: ...

    def resize(self, new_max_size: int) -> None: ...


class FileScannerProtocol(Protocol):
    """Protocol for file scanner objects."""

    def scan_files(self, project_root: Path) -> List[str]: ...

    def should_ignore_file(self, file_path: str) -> bool: ...


class ProjectAnalyzerProtocol(Protocol):
    """Protocol for project analyzer objects."""

    def analyze_project(self) -> Dict[str, Any]: ...

    def get_project_info(self) -> Dict[str, Any]: ...


# TypedDict definitions for structured data
# These are moved to models.py

# Type aliases for better readability
IdentifierSet = Set[str]
MatchResult = tuple[str, int]
CacheStats = Dict[str, Any]
ProjectInfo = Dict[str, Any]


class QueryLoaderProtocol(Protocol):
    """Protocol for loading tree-sitter query strings."""

    custom_queries_dir: Path

    def load_query(self, language: str) -> Optional[str]:
        """Loads the query string for a given language."""
        ...


class FormatterProtocol(Protocol):
    """Protocol for all formatter implementations."""

    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> Union[str, None]:
        """Format data to the specified output format."""
        ...

    def supports_format(self, output_format: OutputFormat) -> bool:
        """Check if this formatter supports the specified format."""
        ...

    def get_supported_formats(self) -> List[OutputFormat]:
        """Get list of supported output formats."""
        ...


class BaseFormatter(ABC):
    """Abstract base class for all formatters."""

    def __init__(
        self,
        *,  # Make subsequent arguments keyword-only
        console_manager: Any,  # Use Any to avoid circular import issues
        template_engine: Any,  # Use Any to avoid circular import issues
        template_registry: Optional["TemplateRegistryProtocol"],
        enable_logging: bool = True,
    ) -> None:
        """Initialize the base formatter."""
        if console_manager is None:
            raise ValueError(
                "ConsoleManagerProtocol must be injected - no fallback allowed"
            )
        if template_engine is None:
            raise ValueError("TemplateEngine must be injected - no fallback allowed")
        if template_registry is None:
            raise ValueError(
                "TemplateRegistryProtocol must be injected - no fallback allowed"
            )

        self._console_manager = console_manager
        self._template_engine = template_engine
        self._template_registry = template_registry
        self._enable_logging = enable_logging  # Store enable_logging
        self._logger = get_logger(self.__class__.__name__) if enable_logging else None
        self._supported_formats: List[OutputFormat] = []

    @abstractmethod
    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> Union[str, None]:
        """Format data to the specified output format."""
        pass

    @abstractmethod
    def supports_format(self, output_format: OutputFormat) -> bool:
        """Check if this formatter supports the specified format."""
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[OutputFormat]:
        """Get list of supported output formats."""
        pass

    def get_console(self, ctx: Optional[click.Context] = None) -> Console:
        """Get console instance for output."""
        if self._console_manager:
            return self._console_manager.get_console(ctx)  # type: ignore[no-any-return]
        else:
            from repomap_tool.cli.utils.console import get_console

            return get_console(ctx)

    def log_formatting(self, operation: str, **context: Any) -> None:
        """Log formatting operation."""
        if self._enable_logging and self._logger:
            self._logger.debug(
                f"Formatter operation: {operation}",
                extra={
                    "operation": operation,
                    "formatter": self.__class__.__name__,
                    "context": context,
                },
            )


class DataFormatter(FormatterProtocol):
    """Protocol for data-specific formatters."""

    def format_data(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> Union[str, None]:
        """Format specific data type."""
        ...

    def validate_data(self, data: Any) -> bool:
        """Validate that data is compatible with this formatter."""
        return True

    def get_data_type(self) -> Type[Any]:
        """Get the data type this formatter handles."""
        return Any


class TemplateFormatter(FormatterProtocol):
    """Protocol for template-based formatters."""

    def load_template(
        self,
        template_name: str,
        config: Optional[OutputConfig] = None,
    ) -> str:
        """Load a template for formatting."""
        return ""

    def render_template(
        self,
        template: str,
        data: Any,
        config: Optional[OutputConfig] = None,
    ) -> str:
        """Render template with data."""
        return ""

    def get_available_templates(self) -> List[str]:
        """Get list of available templates."""
        return []


class FormatterRegistryProtocol(Protocol):
    """Protocol for formatter registry."""

    def register_formatter(
        self,
        formatter: FormatterProtocol,
        data_type: Optional[Type[Any]] = None,
    ) -> None:
        """Register a formatter."""
        ...

    def get_formatter(
        self,
        data_type: Type[Any],
        output_format: OutputFormat,
    ) -> Optional[FormatterProtocol]:
        """Get formatter for data type and format."""
        ...

    def get_all_formatters(self) -> List[FormatterProtocol]:
        """Get all registered formatters."""
        ...

    def unregister_formatter(
        self,
        formatter: FormatterProtocol,
    ) -> None:
        """Unregister a formatter."""
        ...


class TagCacheProtocol(Protocol):
    """Protocol for caching tree-sitter tags (CodeTag objects)."""

    def get_tags(self, file_path: str) -> Optional[List[CodeTag]]:
        """Retrieve cached tags for a file.
        Args:
            file_path: The absolute path to the file.
        Returns:
            A list of CodeTag objects if found and valid, otherwise None.
        """
        ...

    def set_tags(self, file_path: str, tags: List[CodeTag]) -> None:
        """Cache tags for a file.
        Args:
            file_path: The absolute path to the file.
            tags: The list of CodeTag objects to cache.
        """
        ...

    def invalidate_file(self, file_path: str) -> None:
        """Invalidate the cache for a specific file.
        Args:
            file_path: The absolute path to the file to invalidate.
        """
        ...

    def clear(self) -> None:
        """Clear the entire cache."""
        ...

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache usage.
        Returns:
            A dictionary containing cache statistics.
        """
        ...


class TemplateRegistryProtocol(Protocol):
    """Protocol for template registry implementations."""

    def register_template(
        self, template_name: str, template_content: str, overwrite: bool = False
    ) -> None:
        """Register a template."""
        ...

    def unregister_template(self, template_name: str) -> None:
        """Unregister a template."""
        ...

    def get_template(self, template_name: str) -> Optional[str]:
        """Get template content."""
        ...

    def list_templates(self) -> List[str]:
        """List all registered templates."""
        ...

    def template_exists(self, template_name: str) -> bool:
        """Check if template exists."""
        ...


class OutputManagerProtocol(Protocol):
    """Protocol for output manager implementations."""

    def display(
        self, data: Any, config: OutputConfig, ctx: Optional[click.Context] = None
    ) -> None:
        """Display data to the console with proper formatting."""
        ...

    def display_error(
        self,
        error: Union[Exception, Any],
        config: OutputConfig,
        ctx: Optional[click.Context] = None,
    ) -> None:
        """Display an error message with consistent formatting."""
        ...

    def display_success(
        self, message: str, config: OutputConfig, ctx: Optional[click.Context] = None
    ) -> None:
        """Display a success message with consistent formatting."""
        ...

    def display_progress(
        self, message: str, progress: Optional[float] = None, ctx: Optional[Any] = None
    ) -> None:
        """Display progress of a long-running operation."""
        ...

    def get_formatter(self, data: Any, output_format: Any) -> Optional[Any]:
        """Get an appropriate formatter for the given data and format."""
        ...

    def set_config(self, config: Any) -> None:
        """Set the output manager's configuration."""
        ...


class FormatterFactoryProtocol(Protocol):
    """Protocol for formatter factory."""

    def create_formatter(
        self,
        formatter_type: str,
        **kwargs: Any,
    ) -> FormatterProtocol:
        """Create a formatter of the specified type."""
        ...

    def get_available_types(self) -> List[str]:
        """Get list of available formatter types."""
        ...


class ConsoleManagerProtocol(Protocol):
    """Protocol for console manager implementations."""

    def get_console(self, ctx: Optional[click.Context] = None) -> Console:
        """Get a console instance."""

    @abstractmethod
    def configure(self, no_color: bool = False) -> None:
        """Configure the console settings, e.g., enable/disable color."""

    @abstractmethod
    def log_operation(self, operation: str, context: Dict[str, Any]) -> None:
        """Log a console operation."""

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get console usage statistics."""
        ...

    def reset_usage_stats(self) -> None:
        """Reset console usage statistics."""
        ...


# Forward reference for TemplateEngine to prevent circular imports
# TemplateEngine = TypeVar("TemplateEngine")
