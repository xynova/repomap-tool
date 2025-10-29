from __future__ import annotations

import os
from typing import Dict, List, Optional

from repomap_tool.core.logging_service import get_logger
from repomap_tool.code_analysis.file_discovery_service import (
    create_file_discovery_service,
)
from repomap_tool.code_analysis.path_resolver import PathResolver
from repomap_tool.code_analysis.density_analyzer import (
    DensityAnalyzer,
    FileDensity,
    PackageDensity,
)

from .base_controller import BaseController
from .view_models import (
    ControllerConfig,
    DensityAnalysisViewModel,
    FileDensityViewModel,
    PackageDensityViewModel,
)

logger = get_logger(__name__)


class DensityController(BaseController):
    """Controller for density analysis operations."""

    def __init__(
        self,
        density_analyzer: DensityAnalyzer,
        path_resolver: PathResolver,
        config: Optional[ControllerConfig] = None,
    ):
        """Initialize with injected dependencies."""
        super().__init__(config)

        # All dependencies are required and injected via DI container

        self.density_analyzer = density_analyzer
        self.path_resolver = path_resolver

    def execute(
        self,
        file_paths: Optional[List[str]] = None,
        scope: str = "file",
        limit: int = 10,
        min_identifiers: int = 1,
    ) -> DensityAnalysisViewModel:
        """Execute density analysis."""
        if self.config is None:
            raise ValueError("ControllerConfig must be set before executing")

        project_root = self.config.project_root  # Get project_root from config

        # Use centralized file discovery if no files provided
        if file_paths is None:
            file_discovery = create_file_discovery_service(project_root)
            file_paths = file_discovery.get_code_files(exclude_tests=True)

        if scope == "file":
            return self._analyze_files(file_paths, project_root, limit, min_identifiers)
        else:
            return self._analyze_packages(
                file_paths, project_root, limit, min_identifiers
            )

    def _analyze_files(
        self, file_paths: List[str], project_root: str, limit: int, min_identifiers: int
    ) -> DensityAnalysisViewModel:
        """Analyze files and return top results."""
        file_densities = self.density_analyzer.analyze_files(file_paths, project_root)

        # Filter by minimum identifiers and apply limit
        filtered = [
            fd for fd in file_densities if fd.total_identifiers >= min_identifiers
        ]
        top_results = filtered[:limit]

        # Convert to ViewModels
        view_models = [
            FileDensityViewModel(
                file_path=fd.file_path,
                relative_path=fd.relative_path,
                total_identifiers=fd.total_identifiers,
                primary_identifiers=fd.primary_identifiers,
                categories=fd.categories,
            )
            for fd in top_results
        ]

        return DensityAnalysisViewModel(
            scope="file",
            results=view_models,
            total_files_analyzed=len(file_paths),
            limit=limit,
            min_identifiers=min_identifiers,
            analysis_summary={
                "total_files": len(file_paths),
                "files_with_identifiers": len(filtered),
                "avg_identifiers_per_file": (
                    sum(fd.total_identifiers for fd in file_densities)
                    / len(file_densities)
                    if file_densities
                    else 0
                ),
            },
        )

    def _analyze_packages(
        self, file_paths: List[str], project_root: str, limit: int, min_identifiers: int
    ) -> DensityAnalysisViewModel:
        """Group files by package and analyze each package."""
        # Group files by package (directory)
        packages: Dict[str, List[str]] = {}
        for file_path in file_paths:
            package_dir = os.path.dirname(os.path.relpath(file_path, project_root))
            if package_dir not in packages:
                packages[package_dir] = []
            packages[package_dir].append(file_path)

        # Analyze each package
        package_densities = []
        for package_path, package_files in packages.items():
            package_density = self.density_analyzer.analyze_package(
                package_path, package_files, project_root
            )
            if package_density.total_identifiers >= min_identifiers:
                package_densities.append(package_density)

        # Sort by total identifiers and apply limit
        package_densities.sort(key=lambda x: x.total_identifiers, reverse=True)
        top_packages = package_densities[:limit]

        # Convert to ViewModels
        view_models = []
        for package in top_packages:
            file_view_models = [
                FileDensityViewModel(
                    file_path=fd.file_path,
                    relative_path=fd.relative_path,
                    total_identifiers=fd.total_identifiers,
                    primary_identifiers=fd.primary_identifiers,
                    categories=fd.categories,
                )
                for fd in package.files
            ]

            view_models.append(
                PackageDensityViewModel(
                    package_path=package.package_path,
                    total_identifiers=package.total_identifiers,
                    file_count=package.file_count,
                    avg_identifiers_per_file=package.avg_identifiers_per_file,
                    files=file_view_models,
                    categories=package.categories,
                )
            )

        return DensityAnalysisViewModel(
            scope="package",
            results=view_models,
            total_files_analyzed=len(file_paths),
            limit=limit,
            min_identifiers=min_identifiers,
            analysis_summary={
                "total_packages": len(packages),
                "packages_with_identifiers": len(package_densities),
                "total_files": len(file_paths),
            },
        )
