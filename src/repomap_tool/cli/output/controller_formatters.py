"""
Formatters for Controller ViewModels.

This module provides formatters for the ViewModels returned by Controllers,
following proper MVC architecture patterns.
"""

from __future__ import annotations

import logging
from repomap_tool.core.logging_service import get_logger
from typing import Any, List, Optional

import click

from .protocols import DataFormatter
from .formats import OutputFormat
from .template_formatter import TemplateBasedFormatter
from .templates.engine import get_template_engine
from ..controllers.view_models import (
    SearchViewModel,
    CentralityViewModel,
    ImpactViewModel,
    TreeClusterViewModel,
    TreeFocusViewModel,
    TreeExpansionViewModel,
    TreePruningViewModel,
    TreeMappingViewModel,
    TreeListingViewModel,
    SessionStatusViewModel,
    ExplorationViewModel,
    ProjectAnalysisViewModel,
    FileDensityViewModel,
    PackageDensityViewModel,
    DensityAnalysisViewModel,
)


logger = get_logger(__name__)


class CentralityViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for CentralityViewModel objects."""

    def __init__(self, template_engine: Optional[Any] = None):
        """Initialize the formatter.

        Args:
            template_engine: Template engine for rendering
        """
        super().__init__(template_engine=template_engine)

    def supports_format(self, output_format: OutputFormat) -> bool:
        """Check if this formatter supports the given output format.

        Args:
            output_format: Output format to check

        Returns:
            True if format is supported
        """
        return output_format in [OutputFormat.TEXT, OutputFormat.JSON]

    def get_supported_formats(self) -> List[OutputFormat]:
        """Get list of supported output formats.

        Returns:
            List of supported output formats
        """
        return [OutputFormat.TEXT, OutputFormat.JSON]

    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[Any] = None,
        ctx: Optional[click.Context] = None,
    ) -> str:
        """Format CentralityViewModel data.

        Args:
            data: CentralityViewModel to format
            output_format: Desired output format
            config: Output configuration
            ctx: Click context

        Returns:
            Formatted string
        """
        if output_format == OutputFormat.JSON:
            return self._format_json(data)
        elif output_format == OutputFormat.TEXT:
            return self._format_text(data, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _format_json(self, data: Any) -> str:
        """Format data as JSON.

        Args:
            data: CentralityViewModel to format

        Returns:
            JSON string
        """
        import json

        # Convert ViewModel to dictionary
        json_data = {
            "files": [
                {
                    "file_path": file.file_path,
                    "line_count": file.line_count,
                    "centrality_score": file.centrality_score,
                    "symbols": [
                        {
                            "name": symbol.name,
                            "line_number": symbol.line_number,
                            "symbol_type": symbol.symbol_type,
                            "centrality_score": symbol.centrality_score,
                            "importance_score": symbol.importance_score,
                        }
                        for symbol in file.symbols
                    ],
                }
                for file in data.files
            ],
            "rankings": data.rankings,
            "total_files": data.total_files,
            "analysis_summary": data.analysis_summary,
            "token_count": data.token_count,
            "max_tokens": data.max_tokens,
            "compression_level": data.compression_level,
        }

        return json.dumps(json_data, indent=2)

    def _format_text(self, data: Any, config: Optional[Any] = None) -> str:
        """Format data as text using tabulate for table format.

        Args:
            data: CentralityViewModel to format
            config: Output configuration

        Returns:
            Formatted text string
        """
        try:
            from tabulate import tabulate

            # Build table data from rankings
            if not data.rankings:
                return "No centrality analysis data available."

            # Prepare table headers and data
            headers = [
                "Rank",
                "File",
                "Score",
                "Connections",
                "Imports",
                "Rev Deps",
                "Functions",
            ]
            table_data = []

            for ranking in data.rankings:
                # Get additional data from files if available
                file_info = next(
                    (f for f in data.files if f.file_path == ranking["file_path"]), None
                )

                # Use the file path directly without cleaning to preserve special characters like [id]
                file_path = ranking["file_path"].replace("[", r"\[")

                # Format the data for the table - keep full file paths
                row = [
                    ranking["rank"],
                    file_path,
                    f"{ranking['centrality_score']:.3f}",
                    ranking.get("connections", 0),
                    ranking.get("imports", 0),
                    ranking.get("reverse_dependencies", 0),
                    ranking.get("functions", 0),
                ]
                table_data.append(row)

            # Create the table with tabulate
            table = tabulate(
                table_data,
                headers=headers,
                tablefmt="grid",
                stralign="left",
                numalign="right",
            )

            # Add summary information
            summary = f"""
Centrality Analysis
==================
Total Files: {data.total_files}
Token Count: {data.token_count}/{data.max_tokens}
Compression: {data.compression_level}

{table}

Column Explanations:
- Rank: Position in importance ranking (1 = most important)
- Score: Centrality score (0.0-1.0, higher = more important)
- Connections: Total connections to other files
- Imports: Number of files this file imports
- Rev Deps: Number of files that import this file
- Functions: Number of functions defined in this file
- File: File path (relative to project root)
"""
            return summary

        except Exception as e:
            logger.error(f"Table formatting failed: {e}")
            return self._format_fallback(data)

    def _format_fallback(self, data: Any, template_config: Optional[Any] = None) -> str:
        """Fallback formatting if template fails.

        Args:
            data: CentralityViewModel to format

        Returns:
            Simple formatted string
        """
        output = []
        output.append("Centrality Analysis")
        output.append("=" * 40)
        output.append(f"Total Files: {data.total_files}")
        output.append(f"Token Count: {data.token_count}/{data.max_tokens}")

        if data.rankings:
            output.append("\nRankings:")
            for ranking in data.rankings[:5]:  # Show top 5
                output.append(
                    f"  {ranking['rank']}. {ranking['file_path']} ({ranking['centrality_score']:.2f})"
                )

        return "\n".join(output)


class ImpactViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for ImpactViewModel objects."""

    def __init__(self, template_engine: Optional[Any] = None):
        """Initialize the formatter.

        Args:
            template_engine: Template engine for rendering
        """
        super().__init__(template_engine=template_engine)

    def supports_format(self, output_format: OutputFormat) -> bool:
        """Check if this formatter supports the given output format.

        Args:
            output_format: Output format to check

        Returns:
            True if format is supported
        """
        return output_format in [OutputFormat.TEXT, OutputFormat.JSON]

    def get_supported_formats(self) -> List[OutputFormat]:
        """Get list of supported output formats.

        Returns:
            List of supported output formats
        """
        return [OutputFormat.TEXT, OutputFormat.JSON]

    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[Any] = None,
        ctx: Optional[click.Context] = None,
    ) -> str:
        """Format ImpactViewModel data.

        Args:
            data: ImpactViewModel to format
            output_format: Desired output format
            config: Output configuration
            ctx: Click context

        Returns:
            Formatted string
        """
        if output_format == OutputFormat.JSON:
            return self._format_json(data)
        elif output_format == OutputFormat.TEXT:
            return self._format_text(data, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _format_json(self, data: Any) -> str:
        """Format data as JSON.

        Args:
            data: ImpactViewModel to format

        Returns:
            JSON string
        """
        import json

        # Convert ViewModel to dictionary
        json_data = {
            "changed_files": data.changed_files,
            "affected_files": [
                {
                    "file_path": file.file_path,
                    "line_count": file.line_count,
                    "impact_risk": file.impact_risk,
                    "symbols": [
                        {
                            "name": symbol.name,
                            "line_number": symbol.line_number,
                            "symbol_type": symbol.symbol_type,
                            "impact_risk": symbol.impact_risk,
                            "importance_score": symbol.importance_score,
                        }
                        for symbol in file.symbols
                    ],
                }
                for file in data.affected_files
            ],
            "impact_scope": data.impact_scope,
            "risk_assessment": data.risk_assessment,
            "total_affected": data.total_affected,
            "token_count": data.token_count,
            "max_tokens": data.max_tokens,
            "compression_level": data.compression_level,
        }

        return json.dumps(json_data, indent=2)

    def _format_text(self, data: Any, config: Optional[Any] = None) -> str:
        """Format data as text using template.

        Args:
            data: ImpactViewModel to format
            config: Output configuration

        Returns:
            Formatted text string
        """
        try:
            # Convert OutputConfig to TemplateConfig
            template_config = self._create_template_config(config)
            return self._template_engine.render_template(
                "impact_analysis", data, template_config
            )
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return self._format_fallback(data)

    def _format_fallback(self, data: Any, template_config: Optional[Any] = None) -> str:
        """Fallback formatting if template fails.

        Args:
            data: ImpactViewModel to format

        Returns:
            Simple formatted string
        """
        output = []
        output.append("Impact Analysis")
        output.append("=" * 40)
        output.append(f"Changed Files: {len(data.changed_files)}")
        output.append(f"Affected Files: {data.total_affected}")
        output.append(f"Token Count: {data.token_count}/{data.max_tokens}")

        if data.changed_files:
            output.append("\nChanged Files:")
            for file in data.changed_files:
                output.append(f"  - {file}")

        if data.risk_assessment:
            output.append(
                f"\nRisk Level: {data.risk_assessment.get('overall_risk_level', 'unknown').upper()}"
            )

        return "\n".join(output)


class SearchViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for SearchViewModel objects."""

    def __init__(self, template_engine: Optional[Any] = None):
        """Initialize the formatter.

        Args:
            template_engine: Template engine for rendering
        """
        super().__init__(template_engine=template_engine)

    def supports_format(self, output_format: OutputFormat) -> bool:
        """Check if this formatter supports the given output format.

        Args:
            output_format: Output format to check

        Returns:
            True if format is supported
        """
        return output_format in [OutputFormat.TEXT, OutputFormat.JSON]

    def get_supported_formats(self) -> List[OutputFormat]:
        """Get list of supported output formats.

        Returns:
            List of supported output formats
        """
        return [OutputFormat.TEXT, OutputFormat.JSON]

    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[Any] = None,
        ctx: Optional[click.Context] = None,
    ) -> str:
        """Format SearchViewModel data.

        Args:
            data: SearchViewModel to format
            output_format: Output format (TEXT or JSON)
            config: Output configuration
            ctx: Click context

        Returns:
            Formatted string
        """
        if not isinstance(data, SearchViewModel):
            raise ValueError(f"Expected SearchViewModel, got {type(data)}")

        if output_format == OutputFormat.JSON:
            return self._format_json(data)
        elif output_format == OutputFormat.TEXT:
            return self._format_text(data, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _format_json(self, data: SearchViewModel) -> str:
        """Format data as JSON.

        Args:
            data: SearchViewModel to format

        Returns:
            JSON string
        """
        import json

        # Convert to dictionary for JSON serialization
        result_dict = {
            "query": data.query,
            "total_results": data.total_results,
            "search_strategy": data.search_strategy,
            "execution_time": data.execution_time,
            "threshold": data.threshold,
            "match_type": data.match_type,
            "search_time_ms": data.search_time_ms,
            "cache_hit": data.cache_hit,
            "spellcheck_suggestions": data.spellcheck_suggestions,
            "token_count": data.token_count,
            "max_tokens": data.max_tokens,
            "compression_level": data.compression_level,
            "results": [
                {
                    "name": result.name,
                    "file_path": result.file_path,
                    "line_number": result.line_number,
                    "symbol_type": result.symbol_type,
                    "importance_score": result.importance_score,
                    "is_critical": result.is_critical,
                    "centrality_score": result.centrality_score,
                    "impact_risk": result.impact_risk,
                }
                for result in data.results
            ],
            "metadata": data.metadata,
            "performance_metrics": data.performance_metrics,
        }

        return json.dumps(result_dict, indent=2)

    def _format_text(self, data: SearchViewModel, config: Optional[Any] = None) -> str:
        """Format data as text using template.

        Args:
            data: SearchViewModel to format
            config: Output configuration

        Returns:
            Formatted text string
        """
        try:
            # Convert OutputConfig to TemplateConfig
            template_config = self._create_template_config(config)
            return self._template_engine.render_template(
                "search_results", data, template_config
            )
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return self._format_fallback(data)

    def _format_fallback(
        self, data: SearchViewModel, template_config: Optional[Any] = None
    ) -> str:
        """Fallback formatting if template fails.

        Args:
            data: SearchViewModel to format

        Returns:
            Simple formatted string
        """
        output = []
        output.append("Search Results")
        output.append("=" * 40)
        output.append(f"Query: {data.query}")
        output.append(f"Total Results: {data.total_results}")
        output.append(f"Search Strategy: {data.search_strategy}")
        output.append(f"Execution Time: {data.execution_time:.3f}s")
        output.append(f"Token Count: {data.token_count}/{data.max_tokens}")

        if data.results:
            output.append("\nResults:")
            for i, result in enumerate(data.results, 1):
                output.append(f"  {i}. {result.name}")
                output.append(f"     File: {result.file_path}")
                output.append(f"     Line: {result.line_number}")
                output.append(f"     Score: {result.importance_score:.3f}")
                if result.is_critical:
                    output.append(f"     Critical: Yes")
                output.append("")

        if data.performance_metrics:
            output.append("Performance Metrics:")
            for key, value in data.performance_metrics.items():
                output.append(f"  {key}: {value}")

        return "\n".join(output)


class DensityAnalysisFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for DensityAnalysisViewModel."""

    def __init__(self, template_engine: Optional[Any] = None):
        """Initialize the formatter."""
        super().__init__(template_engine=template_engine)

    def supports_format(self, output_format: OutputFormat) -> bool:
        """Check if this formatter supports the given output format."""
        return output_format in [OutputFormat.TEXT, OutputFormat.JSON]

    def get_supported_formats(self) -> List[OutputFormat]:
        """Get list of supported output formats."""
        return [OutputFormat.TEXT, OutputFormat.JSON]

    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[Any] = None,
        ctx: Optional[click.Context] = None,
    ) -> str:
        """Format DensityAnalysisViewModel data."""
        if not isinstance(data, DensityAnalysisViewModel):
            raise ValueError(f"Expected DensityAnalysisViewModel, got {type(data)}")

        if output_format == OutputFormat.JSON:
            return self._format_json(data)
        elif output_format == OutputFormat.TEXT:
            return self._format_text(data, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _format_json(self, data: DensityAnalysisViewModel) -> str:
        """Format data as JSON."""
        import json
        from dataclasses import asdict

        # Use asdict to convert dataclass to dictionary
        json_data = asdict(data)
        return json.dumps(json_data, indent=2)

    def _format_text(
        self, data: DensityAnalysisViewModel, config: Optional[Any] = None
    ) -> str:
        """Format data as text using template."""
        try:
            template_config = self._create_template_config(config)
            return self._template_engine.render_template(
                "density_analysis", data, template_config
            )
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return self._format_fallback(data)

    def _format_fallback(
        self, data: DensityAnalysisViewModel, template_config: Optional[Any] = None
    ) -> str:
        """Fallback formatting if template fails."""
        output = []
        output.append("Code Density Analysis")
        output.append("=" * 40)
        output.append(f"Scope: {data.scope.upper()}")
        output.append(f"Total Files Analyzed: {data.total_files_analyzed}")
        output.append(f"Showing Top: {data.limit} results")
        output.append(f"Min Identifiers: {data.min_identifiers}")

        if data.results:
            output.append("\nResults:")
            for i, result in enumerate(data.results, 1):
                if isinstance(result, FileDensityViewModel):
                    output.append(f"  {i}. File: {result.relative_path}")
                    output.append(f"     Total Identifiers: {result.total_identifiers}")
                    output.append(
                        f"     Primary Identifiers: {result.primary_identifiers}"
                    )
                    output.append(f"     Categories: {result.categories}")
                elif isinstance(result, PackageDensityViewModel):
                    output.append(f"  {i}. Package: {result.package_path}/")
                    output.append(f"     Total Identifiers: {result.total_identifiers}")
                    output.append(f"     File Count: {result.file_count}")
                    output.append(
                        f"     Avg Identifiers per File: {result.avg_identifiers_per_file:.1f}"
                    )
                    output.append(f"     Categories: {result.categories}")
                    output.append("       Top files:")
                    for j, file_in_package in enumerate(result.files[:5]):
                        output.append(
                            f"         - {file_in_package.relative_path} ({file_in_package.total_identifiers})"
                        )
                output.append("")

        return "\n".join(output)
