"""
Custom exception hierarchy for repomap-tool.

This module defines specific exception types for different error scenarios,
enabling better error handling, recovery, and debugging.
"""

from typing import Optional, Any, Dict, Callable, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])


class RepoMapError(Exception):
    """Base exception for all repomap-tool errors."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} (Context: {context_str})"
        return self.message


class ConfigurationError(RepoMapError):
    """Raised when configuration is invalid or missing."""

    pass


class FileAccessError(RepoMapError):
    """Raised when there are issues accessing files or directories."""

    pass


class TagExtractionError(RepoMapError):
    """Raised when there are issues extracting tags from files."""

    pass


class MatcherError(RepoMapError):
    """Raised when matchers encounter errors during operation."""

    pass


class CacheError(RepoMapError):
    """Raised when cache operations fail."""

    pass


class ValidationError(RepoMapError):
    """Raised when data validation fails."""

    pass


class SearchError(RepoMapError):
    """Raised when search operations fail."""

    pass


class ProjectAnalysisError(RepoMapError):
    """Raised when project analysis fails."""

    pass


class RepoMapMemoryError(RepoMapError):
    """Raised when memory limits are exceeded."""

    pass


class NetworkError(RepoMapError):
    """Raised when network operations fail."""

    pass


class RepoMapTimeoutError(RepoMapError):
    """Raised when operations timeout."""

    pass


class ParallelProcessingError(RepoMapError):
    """Raised when parallel processing encounters an error."""

    pass


# Utility functions for error handling
def safe_operation(
    operation_name: str, context: Optional[Dict[str, Any]] = None
) -> Callable[[F], F]:
    """Decorator for wrapping operations with safe error handling."""

    def decorator(func: F) -> F:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except RepoMapError:
                # Re-raise our custom exceptions as-is
                raise
            except FileNotFoundError as e:
                raise FileAccessError(
                    f"File not found during {operation_name}",
                    context=context or {"file_path": str(e)},
                )
            except PermissionError as e:
                raise FileAccessError(
                    f"Permission denied during {operation_name}",
                    context=context or {"file_path": str(e)},
                )
            except MemoryError:
                raise RepoMapMemoryError(
                    f"Memory limit exceeded during {operation_name}",
                    context=context or {"operation": operation_name},
                )
            except TimeoutError:
                raise RepoMapTimeoutError(
                    f"Operation timed out during {operation_name}",
                    context=context or {"operation": operation_name},
                )
            except Exception as e:
                # Log unexpected errors and wrap them
                import logging

                logger = logging.getLogger(__name__)
                logger.error(
                    f"Unexpected error during {operation_name}: {e}",
                    extra={"context": context, "exception_type": type(e).__name__},
                )
                raise RepoMapError(
                    f"Unexpected error during {operation_name}: {e}",
                    context=context
                    or {"operation": operation_name, "original_error": str(e)},
                )

        return cast(F, wrapper)

    return decorator


def handle_errors(func: F) -> F:
    """Simpler decorator for basic error handling."""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except RepoMapError:
            raise
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error in {func.__name__}: {e}")
            raise RepoMapError(f"Error in {func.__name__}: {e}")

    return cast(F, wrapper)
