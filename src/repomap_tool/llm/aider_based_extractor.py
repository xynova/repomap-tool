"""
Aider-based critical line extractor using tree-sitter.

This module replaces the regex-based language analyzers with aider's
tree-sitter functionality that we already have available.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .critical_line_extractor import CriticalLine

logger = logging.getLogger(__name__)


class AiderBasedExtractor:
    """Critical line extractor using aider's tree-sitter functionality."""

    def __init__(self, repo_map: Any) -> None:
        """Initialize with aider RepoMap instance.

        Args:
            repo_map: Aider RepoMap instance with tree-sitter support
        """
        self.repo_map = repo_map

    def extract_critical_lines(
        self, file_path: str, symbol_content: str = ""
    ) -> List[Dict[str, Any]]:
        """Extract critical lines using aider's tree-sitter parsing.

        Args:
            file_path: Path to the file to analyze
            symbol_content: Optional symbol content (not used with tree-sitter)

        Returns:
            List of critical line dictionaries with tree-sitter data
        """
        try:
            # Use aider's get_tags to get proper AST-based analysis
            tags = self.repo_map.get_tags(file_path, file_path)

            critical_lines = []
            for tag in tags:
                # Convert aider tag to our format
                critical_line = {
                    "line_number": tag.line,
                    "content": tag.name,
                    "confidence": self._calculate_confidence(tag),
                    "reason": self._get_reason_from_kind(tag.kind),
                    "tag_kind": tag.kind,
                    "tag_name": tag.name,
                    # Add more tag attributes if available
                }

                # Add column info if available
                if hasattr(tag, "col"):
                    critical_line["column"] = tag.col

                critical_lines.append(critical_line)

            logger.debug(
                f"Extracted {len(critical_lines)} critical lines from {file_path}"
            )
            return critical_lines

        except Exception as e:
            logger.warning(f"Failed to extract critical lines from {file_path}: {e}")
            return []

    def _calculate_confidence(self, tag: Any) -> float:
        """Calculate confidence score based on tag kind.

        Args:
            tag: Aider tag object

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Higher confidence for definitions, lower for references
        if tag.kind == "def":
            return 0.9
        elif tag.kind == "ref":
            return 0.7
        else:
            return 0.5

    def _get_reason_from_kind(self, kind: str) -> str:
        """Get human-readable reason from tag kind.

        Args:
            kind: Tag kind from aider

        Returns:
            Human-readable reason string
        """
        kind_mapping = {
            "def": "function_or_class_definition",
            "ref": "reference_or_call",
            "import": "import_statement",
            "class": "class_definition",
            "function": "function_definition",
        }
        return kind_mapping.get(kind, f"unknown_kind_{kind}")


class CriticalLineExtractor:
    """Updated critical line extractor using aider's tree-sitter functionality."""

    def __init__(self, repo_map: Any = None) -> None:
        """Initialize with optional repo_map.

        Args:
            repo_map: Optional aider RepoMap instance
        """
        self.repo_map = repo_map
        self.aider_extractor = None

        if repo_map:
            self.aider_extractor = AiderBasedExtractor(repo_map)

    def extract_critical_lines(
        self, path_or_content: str, language: str = "python"
    ) -> List[CriticalLine]:
        """Extract critical lines from a file path or raw content.

        Args:
            path_or_content: File path or raw code content to analyze
            language: Programming language (used for fallback)

        Returns:
            List of CriticalLine objects sorted by importance
        """
        # If we have aider extractor and the input is a valid file path, use it
        if self.aider_extractor and isinstance(path_or_content, str):
            try:
                p = Path(path_or_content)
                if p.is_file():
                    # Convert aider results to CriticalLine objects
                    aider_results = self.aider_extractor.extract_critical_lines(
                        path_or_content
                    )
                    return self._convert_to_critical_lines(aider_results)
            except (OSError, ValueError):
                # Not a valid path, treat as content
                pass

        # Fallback to simple pattern matching for raw content or if Aider extractor is unavailable
        return self._fallback_extraction(path_or_content)

    def _convert_to_critical_lines(
        self, aider_results: List[Dict[str, Any]]
    ) -> List[CriticalLine]:
        """Convert aider results to CriticalLine objects."""
        critical_lines = []
        for result in aider_results:
            critical_line = CriticalLine(
                line_number=result.get("line_number", 1),
                content=result.get("content", ""),
                importance=result.get("confidence", 0.5),
                pattern_type=result.get("reason", "tree_sitter_analysis"),
                context=result.get("tag_kind", ""),
            )
            critical_lines.append(critical_line)
        return critical_lines

    def _fallback_extraction(self, content: str) -> List[CriticalLine]:
        """Simple fallback extraction for non-file content."""
        critical_lines = []
        lines = content.split("\n")

        for i, line in enumerate(lines):
            # Simple patterns for common constructs
            if any(
                pattern in line
                for pattern in ["def ", "class ", "return ", "if ", "import "]
            ):
                critical_line = CriticalLine(
                    line_number=i + 1,
                    content=line.strip(),
                    importance=0.6,
                    pattern_type="simple_pattern_match",
                )
                critical_lines.append(critical_line)

        return critical_lines

    def get_implementation_essence(
        self, symbol_content: str, language: str = "python"
    ) -> str:
        """Get a concise summary of what the symbol does.

        Args:
            symbol_content: Raw code content
            language: Programming language

        Returns:
            Concise description of the symbol's purpose
        """
        critical_lines = self.extract_critical_lines(symbol_content, language)

        if not critical_lines:
            return "Implementation details not available"

        # Create essence from critical lines
        essence_parts = []
        for line in critical_lines[:2]:  # Use top 2 lines
            essence_parts.append(line.content.strip())

        return " | ".join(essence_parts)
