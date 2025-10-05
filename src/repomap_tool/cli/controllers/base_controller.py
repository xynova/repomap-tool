"""
Base Controller class for CLI Controllers.

This module provides the base Controller class that all CLI Controllers
should inherit from, following proper MVC architecture patterns.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .view_models import ControllerConfig


logger = logging.getLogger(__name__)


class BaseController(ABC):
    """Base class for all CLI Controllers.

    Controllers orchestrate business logic and return ViewModels
    for the view layer to format and display.
    """

    def __init__(self, config: Optional[ControllerConfig] = None):
        """Initialize the Controller.

        Args:
            config: Controller configuration
        """
        self.config = config
        self.logger = logger

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the controller's main operation.

        This method should be implemented by subclasses to perform
        their specific business logic orchestration.

        Returns:
            ViewModel instance
        """
        pass

    def _validate_config(self, config: ControllerConfig) -> None:
        """Validate controller configuration.

        Args:
            config: Configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
        if config.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")

        if config.compression_level not in ["low", "medium", "high"]:
            raise ValueError("compression_level must be one of: low, medium, high")

    def _log_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """Log controller operation details.

        Args:
            operation: Name of the operation
            details: Operation details
        """
        if self.config and self.config.verbose:
            self.logger.info(f"Controller operation: {operation}")
            self.logger.debug(f"Operation details: {details}")

    def _estimate_tokens(self, data: Any) -> int:
        """Estimate token count for data.

        Args:
            data: Data to estimate tokens for

        Returns:
            Estimated token count
        """
        # Simple token estimation (in production, would use tiktoken)
        if isinstance(data, str):
            return int(len(data.split()) * 1.3)  # Rough estimate
        elif isinstance(data, (list, dict)):
            return int(len(str(data).split()) * 1.3)
        else:
            return int(len(str(data).split()) * 1.3)
