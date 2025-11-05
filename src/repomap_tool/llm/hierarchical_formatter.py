from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from repomap_tool.core.logging_service import get_logger

logger = get_logger(__name__)


class HierarchicalFormatter:
    """Formats data into a hierarchical, LLM-friendly structure."""

    def __init__(self) -> None:
        logger.info("HierarchicalFormatter initialized")

    def format(self, data: Any, indent_level: int = 0) -> str:
        """Formats the given data into a hierarchical string representation."""
        if data is None:
            return ""

        indent = "  " * indent_level
        formatted_lines: List[str] = []  # Explicitly define type of formatted_lines

        if isinstance(data, dict):
            for key, value in data.items():
                formatted_lines.append(f"{indent}{key}: ")
                if isinstance(value, (dict, list)) and value:
                    formatted_lines.append(self.format(value, indent_level + 1))
                else:
                    formatted_lines[-1] += str(value)
        elif isinstance(data, list):
            for item in data:
                formatted_lines.append(f"{indent}- ")
                if isinstance(item, (dict, list)) and item:
                    formatted_lines.append(self.format(item, indent_level + 1))
                else:
                    formatted_lines[-1] += str(item)
        else:
            formatted_lines.append(f"{indent}{data}")

        return "\n".join(formatted_lines)
