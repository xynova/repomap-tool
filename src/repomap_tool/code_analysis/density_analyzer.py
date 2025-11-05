"""Density analysis service for code identifier counting and categorization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import os

from repomap_tool.core.logging_service import get_logger
from repomap_tool.code_analysis.models import CodeTag
from repomap_tool.code_analysis.tree_sitter_parser import TreeSitterParser

logger = get_logger(__name__)


class IdentifierCategory(str, Enum):
    """Categories for identifier classification"""

    CLASSES = "classes"
    FUNCTIONS = "functions"
    METHODS = "methods"
    VARIABLES = "variables"
    IMPORTS = "imports"


@dataclass
class FileDensity:
    """Density metrics for a single file"""

    file_path: str  # Absolute path
    relative_path: str  # Relative to project root
    total_identifiers: int
    categories: Dict[str, int]  # category -> count
    primary_identifiers: int  # classes + functions + methods


@dataclass
class PackageDensity:  # Changed from ModuleDensity to avoid confusion
    """Density metrics for a package/directory"""

    package_path: str  # Relative directory path
    total_identifiers: int
    file_count: int
    files: List[FileDensity]  # Sorted by density descending
    categories: Dict[str, int]  # Aggregated counts
    avg_identifiers_per_file: float


class DensityAnalyzer:
    """Analyzes code density using tree-sitter parsing."""

    def __init__(self, tree_sitter_parser: TreeSitterParser):
        """Initialize with injected TreeSitterParser."""
        # All dependencies are required and injected via DI container
        self.parser = tree_sitter_parser

    def analyze_file(self, file_path: str, project_root: str) -> FileDensity:
        """Analyze identifier density for a single file."""
        # Use get_tags() now that interface is fixed
        tags = self.parser.get_tags(file_path)
        return self._categorize_tags(tags, file_path, project_root)

    def analyze_files(
        self, file_paths: List[str], project_root: str
    ) -> List[FileDensity]:
        """Analyze multiple files, return sorted by density."""
        densities = []
        for fp in file_paths:
            file_density = self.analyze_file(fp, project_root)
            if (
                file_density.total_identifiers > 0
            ):  # Only include files with identifiers
                densities.append(file_density)
        return sorted(densities, key=lambda x: x.total_identifiers, reverse=True)

    def analyze_package(
        self, package_path: str, file_paths: List[str], project_root: str
    ) -> PackageDensity:
        """Analyze package density with files sorted by density."""
        file_densities = self.analyze_files(file_paths, project_root)

        total = sum(f.total_identifiers for f in file_densities)
        categories = self._aggregate_categories(file_densities)
        avg = total / len(file_densities) if file_densities else 0

        return PackageDensity(
            package_path=package_path,
            total_identifiers=total,
            file_count=len(file_densities),
            files=file_densities,
            categories=categories,
            avg_identifiers_per_file=avg,
        )

    def _categorize_tags(
        self, tags: List[CodeTag], file_path: str, project_root: str
    ) -> FileDensity:
        """Categorize tags into identifier types."""
        categories = {cat.value: 0 for cat in IdentifierCategory}

        for tag in tags:
            category = self._map_tag_to_category(tag.kind)
            if category:
                categories[category] += 1

        primary = (
            categories[IdentifierCategory.CLASSES]
            + categories[IdentifierCategory.FUNCTIONS]
            + categories[IdentifierCategory.METHODS]
        )

        return FileDensity(
            file_path=file_path,
            relative_path=os.path.relpath(file_path, project_root),
            total_identifiers=sum(categories.values()),
            categories=categories,
            primary_identifiers=primary,
        )

    def _aggregate_categories(
        self, file_densities: List[FileDensity]
    ) -> Dict[str, int]:
        """Aggregate category counts across multiple files."""
        aggregated = {cat.value: 0 for cat in IdentifierCategory}
        for file_density in file_densities:
            for category, count in file_density.categories.items():
                aggregated[category] += count
        return aggregated

    def _map_tag_to_category(self, tag_kind: str) -> Optional[str]:
        """Map tree-sitter tag kind to identifier category."""
        kind_lower = tag_kind.lower()

        # Classes, interfaces, enums, types
        if any(
            x in kind_lower for x in ["class", "interface", "enum", "type", "record"]
        ):
            return IdentifierCategory.CLASSES

        # Functions (top-level)
        if "function" in kind_lower and "call" not in kind_lower:
            if "method" not in kind_lower:
                return IdentifierCategory.FUNCTIONS

        # Methods (class members)
        if "method" in kind_lower or "constructor" in kind_lower:
            return IdentifierCategory.METHODS

        if any(x in kind_lower for x in ["variable", "field", "property", "parameter"]):
            if "call" not in kind_lower:  # Ensure 'call' is not categorized as variable
                return IdentifierCategory.VARIABLES

        if "import" in kind_lower or "require" in kind_lower or "export" in kind_lower:
            return IdentifierCategory.IMPORTS

        return None
