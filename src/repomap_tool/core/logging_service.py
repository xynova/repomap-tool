"""
Centralized logging service for RepoMap-Tool.

This service provides a single source of truth for logging configuration,
eliminating duplicate logger setup across the codebase.
"""

import logging
import sys
from typing import Optional, Dict, Any
from pathlib import Path

# Global logging configuration
_logging_configured = False
_logger_cache: Dict[str, logging.Logger] = {}


class LoggingService:
    """Centralized logging service for RepoMap-Tool."""

    def __init__(self) -> None:
        """Initialize the logging service."""
        self._configured = False
        self._log_level = logging.INFO
        self._log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self._log_file: Optional[str] = None
        self._enable_console = True
        self._enable_file = False

    def configure(
        self,
        level: str = "INFO",
        format_string: Optional[str] = None,
        log_file: Optional[str] = None,
        enable_console: bool = True,
        enable_file: bool = False,
    ) -> None:
        """Configure the logging service.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            format_string: Custom log format string
            log_file: Path to log file (if file logging enabled)
            enable_console: Whether to enable console logging
            enable_file: Whether to enable file logging
        """
        # Convert string level to logging constant
        numeric_level = getattr(logging, level.upper(), logging.INFO)

        self._log_level = numeric_level
        self._log_format = format_string or self._log_format
        self._log_file = log_file
        self._enable_console = enable_console
        self._enable_file = enable_file

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Add console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(numeric_level)
            console_formatter = logging.Formatter(self._log_format)
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)

        # Add file handler
        if enable_file and log_file:
            try:
                # Ensure log directory exists
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)

                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(numeric_level)
                file_formatter = logging.Formatter(self._log_format)
                file_handler.setFormatter(file_formatter)
                root_logger.addHandler(file_handler)
            except Exception as e:
                # Fallback to console if file logging fails
                print(f"Warning: Failed to configure file logging: {e}")

        self._configured = True

        # Configure external library loggers to be less verbose
        self._configure_external_library_loggers()

        # Log configuration success
        logger = self.get_logger(__name__)
        logger.debug(
            f"Logging service configured: level={level}, console={enable_console}, file={enable_file}"
        )

    def _configure_external_library_loggers(self) -> None:
        """Configure external library loggers to be less verbose."""
        # Configure external libraries directly
        import logging

        # Configure transformers library
        try:
            import transformers

            transformers.logging.set_verbosity_error()

            # Set specific transformers loggers
            transformers_logger = logging.getLogger("transformers_modules")
            transformers_logger.setLevel(logging.ERROR)

        except ImportError:
            pass

        # Configure sentence_transformers library
        try:
            import sentence_transformers

            # Set sentence_transformers logger to ERROR level
            st_logger = logging.getLogger("sentence_transformers")
            st_logger.setLevel(logging.ERROR)

            # Also suppress the specific SentenceTransformer logger
            st_model_logger = logging.getLogger(
                "sentence_transformers.SentenceTransformer"
            )
            st_model_logger.setLevel(logging.ERROR)

            # Suppress any other sentence_transformers related loggers
            st_util_logger = logging.getLogger("sentence_transformers.util")
            st_util_logger.setLevel(logging.ERROR)

        except ImportError:
            pass

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for the specified name.

        Args:
            name: Logger name (typically __name__)

        Returns:
            Logger instance
        """
        # Use cached logger if available
        if name in _logger_cache:
            return _logger_cache[name]

        # Create new logger
        logger = logging.getLogger(name)

        # Cache the logger
        _logger_cache[name] = logger

        return logger

    def set_level(self, level: str) -> None:
        """Set the logging level.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        self._log_level = numeric_level

        # Update root logger level
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        # Update all cached loggers
        for logger in _logger_cache.values():
            logger.setLevel(numeric_level)

    def get_level(self) -> int:
        """Get the current logging level.

        Returns:
            Current logging level
        """
        return self._log_level

    def is_configured(self) -> bool:
        """Check if logging is configured.

        Returns:
            True if logging is configured, False otherwise
        """
        return self._configured

    def get_config(self) -> Dict[str, Any]:
        """Get current logging configuration.

        Returns:
            Dictionary with current logging configuration
        """
        return {
            "level": logging.getLevelName(self._log_level),
            "format": self._log_format,
            "log_file": self._log_file,
            "enable_console": self._enable_console,
            "enable_file": self._enable_file,
            "configured": self._configured,
        }

    def clear_cache(self) -> None:
        """Clear the logger cache."""
        _logger_cache.clear()


# Global logging service instance
_logging_service: Optional[LoggingService] = None


def get_logging_service() -> LoggingService:
    """Get the global logging service instance.

    Returns:
        LoggingService instance
    """
    global _logging_service
    if _logging_service is None:
        _logging_service = LoggingService()
    return _logging_service


def set_logging_service(service: LoggingService) -> None:
    """Set the global logging service instance.

    Args:
        service: LoggingService instance
    """
    global _logging_service
    _logging_service = service


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the specified name.

    This is the main function that should be used throughout the codebase
    instead of logging.getLogger(__name__).

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return get_logging_service().get_logger(name)


def configure_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = False,
) -> None:
    """Configure the global logging service.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom log format string
        log_file: Path to log file (if file logging enabled)
        enable_console: Whether to enable console logging
        enable_file: Whether to enable file logging
    """
    get_logging_service().configure(
        level=level,
        format_string=format_string,
        log_file=log_file,
        enable_console=enable_console,
        enable_file=enable_file,
    )


def set_log_level(level: str) -> None:
    """Set the global logging level.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    get_logging_service().set_level(level)


def get_log_level() -> int:
    """Get the current global logging level.

    Returns:
        Current logging level
    """
    return get_logging_service().get_level()


def is_logging_configured() -> bool:
    """Check if logging is configured.

    Returns:
        True if logging is configured, False otherwise
    """
    return get_logging_service().is_configured()


def get_logging_config() -> Dict[str, Any]:
    """Get current logging configuration.

    Returns:
        Dictionary with current logging configuration
    """
    return get_logging_service().get_config()


# Initialize default logging configuration
def _initialize_default_logging() -> None:
    """Initialize default logging configuration."""
    global _logging_configured
    if not _logging_configured:
        configure_logging(level="INFO")
        _logging_configured = True


# Auto-initialize on import
_initialize_default_logging()


# Configure external libraries immediately on import
def _configure_external_libraries_early() -> None:
    """Configure external library logging as early as possible."""
    _suppress_external_library_logs()


def _suppress_external_library_logs() -> None:
    """Centralized function to suppress external library logs."""
    import logging

    # Configure transformers library
    try:
        import transformers

        transformers.logging.set_verbosity_error()

        # Set specific transformers loggers
        transformers_logger = logging.getLogger("transformers_modules")
        transformers_logger.setLevel(logging.ERROR)

    except ImportError:
        pass

    # Configure sentence-transformers library
    try:
        import sentence_transformers

        sentence_transformers_logger = logging.getLogger("sentence_transformers")
        sentence_transformers_logger.setLevel(logging.WARNING)

        # Also configure the specific SentenceTransformer logger
        st_logger = logging.getLogger("sentence_transformers.SentenceTransformer")
        st_logger.setLevel(logging.WARNING)

    except ImportError:
        pass

    # Configure other external libraries
    external_loggers = ["torch", "numpy", "scipy", "sklearn", "networkx"]

    for logger_name in external_loggers:
        try:
            external_logger = logging.getLogger(logger_name)
            external_logger.setLevel(logging.WARNING)
        except Exception:
            pass


# Configure external libraries immediately
_configure_external_libraries_early()
