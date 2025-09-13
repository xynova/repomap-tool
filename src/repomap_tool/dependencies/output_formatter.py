"""
Output formatting module for LLM-optimized file analysis.

This module handles output formatting, token optimization, and format selection
for analysis results.
"""

import logging
from typing import List, Any

from .models import AnalysisFormat, FileImpactAnalysis, FileCentralityAnalysis
from ..llm.token_optimizer import TokenOptimizer

logger = logging.getLogger(__name__)


class OutputFormatter:
    """Handles output formatting for analysis results."""

    def __init__(self, max_tokens: int = 4000):
        """Initialize the output formatter.

        Args:
            max_tokens: Maximum tokens for LLM-optimized output
        """
        self.max_tokens = max_tokens
        self.token_optimizer = TokenOptimizer()
        logger.info(f"OutputFormatter initialized with max_tokens: {max_tokens}")

    def format_analysis(
        self, analyses: List[Any], format_type: AnalysisFormat, analysis_type: str
    ) -> str:
        """Format analysis results based on type and format.

        Args:
            analyses: List of analysis objects
            format_type: Output format type
            analysis_type: Type of analysis ("impact" or "centrality")

        Returns:
            Formatted analysis string
        """
        if analysis_type == "impact":
            return self._format_impact_analysis(analyses, format_type)
        elif analysis_type == "centrality":
            return self._format_centrality_analysis(analyses, format_type)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")

    def _format_impact_analysis(
        self, analyses: List[FileImpactAnalysis], format_type: AnalysisFormat
    ) -> str:
        """Format impact analysis results."""
        if format_type == AnalysisFormat.LLM_OPTIMIZED:
            return self._format_llm_optimized_impact(analyses)
        elif format_type == AnalysisFormat.JSON:
            return self._format_json_impact(analyses)
        elif format_type == AnalysisFormat.TABLE:
            return self._format_table_impact(analyses)
        else:
            return self._format_text_impact(analyses)

    def _format_centrality_analysis(
        self, analyses: List[FileCentralityAnalysis], format_type: AnalysisFormat
    ) -> str:
        """Format centrality analysis results."""
        if format_type == AnalysisFormat.LLM_OPTIMIZED:
            return self._format_llm_optimized_centrality(analyses)
        elif format_type == AnalysisFormat.JSON:
            return self._format_json_centrality(analyses)
        elif format_type == AnalysisFormat.TABLE:
            return self._format_table_centrality(analyses)
        else:
            return self._format_text_centrality(analyses)

    def _format_llm_optimized_impact(self, analyses: List[FileImpactAnalysis]) -> str:
        """Format impact analysis for LLM consumption."""
        if len(analyses) == 1:
            return self._format_single_file_impact_llm(analyses[0])
        else:
            return self._format_multiple_files_impact_llm(analyses)

    def _format_single_file_impact_llm(self, analysis: FileImpactAnalysis) -> str:
        """Format single file impact analysis for LLM."""
        from pathlib import Path

        output = []
        file_name = Path(analysis.file_path).name

        output.append(f"=== Impact Analysis: {file_name} ===")
        output.append("")

        # Direct dependencies
        output.append("DIRECT DEPENDENCIES (what this file imports/calls):")
        for dep in analysis.direct_dependencies[:10]:  # Limit for token budget
            output.append(f"├── {dep['file']}:{dep['line']} (import {dep['imported']})")
        if len(analysis.direct_dependencies) > 10:
            output.append(f"└── ... and {len(analysis.direct_dependencies) - 10} more")
        output.append("")

        # Reverse dependencies
        output.append("REVERSE DEPENDENCIES (what imports/calls this file):")
        for dep in analysis.reverse_dependencies[:10]:  # Limit for token budget
            output.append(
                f"├── {Path(dep['file']).name}:{dep['line']} ({dep['relationship']})"
            )
        if len(analysis.reverse_dependencies) > 10:
            output.append(f"└── ... and {len(analysis.reverse_dependencies) - 10} more")
        output.append("")

        # Function call analysis
        if analysis.function_call_analysis:
            output.append("FUNCTION CALL ANALYSIS:")
            for call in analysis.function_call_analysis[:5]:  # Limit for token budget
                output.append(f"├── {call['function']}() called at line {call['line']}")
            if len(analysis.function_call_analysis) > 5:
                output.append(
                    f"└── ... and {len(analysis.function_call_analysis) - 5} more calls"
                )
            output.append("")

        # Structural impact
        output.append("STRUCTURAL IMPACT (if function signatures change):")
        output.append(
            f"├── If functions change → {analysis.structural_impact['defined_functions']} functions affected"
        )
        output.append(
            f"├── If classes change → {analysis.structural_impact['defined_classes']} classes affected"
        )
        output.append(
            f"└── Total dependents → {len(analysis.reverse_dependencies)} files potentially affected"
        )

        # Optimize for token budget
        result = "\n".join(output)
        return self.token_optimizer.optimize_for_token_budget(result, self.max_tokens)

    def _format_multiple_files_impact_llm(
        self, analyses: List[FileImpactAnalysis]
    ) -> str:
        """Format multiple files impact analysis for LLM."""
        from pathlib import Path
        from typing import Set

        output = []

        output.append(
            f"=== Impact Analysis: {', '.join(Path(a.file_path).name for a in analyses)} ==="
        )
        output.append("")

        output.append("FILES ANALYZED:")
        for analysis in analyses:
            output.append(f"├── {Path(analysis.file_path).name}")
        output.append("")

        # Combined dependencies
        all_direct_deps: Set[str] = set()
        all_reverse_deps: Set[str] = set()

        for analysis in analyses:
            for dep in analysis.direct_dependencies:
                all_direct_deps.add(dep["file"])
            for dep in analysis.reverse_dependencies:
                all_reverse_deps.add(Path(dep["file"]).name)

        output.append("COMBINED DEPENDENCIES:")
        for dep_name in list(all_direct_deps)[:10]:
            output.append(f"├── {dep_name}")
        if len(all_direct_deps) > 10:
            output.append(f"└── ... and {len(all_direct_deps) - 10} more")
        output.append("")

        output.append("COMBINED REVERSE DEPENDENCIES:")
        for dep_name in list(all_reverse_deps)[:10]:
            output.append(f"├── {dep_name}")
        if len(all_reverse_deps) > 10:
            output.append(f"└── ... and {len(all_reverse_deps) - 10} more")

        # Optimize for token budget
        result = "\n".join(output)
        return self.token_optimizer.optimize_for_token_budget(result, self.max_tokens)

    def _format_llm_optimized_centrality(
        self, analyses: List[FileCentralityAnalysis]
    ) -> str:
        """Format centrality analysis for LLM consumption."""
        if len(analyses) == 1:
            return self._format_single_file_centrality_llm(analyses[0])
        else:
            return self._format_multiple_files_centrality_llm(analyses)

    def _format_single_file_centrality_llm(
        self, analysis: FileCentralityAnalysis
    ) -> str:
        """Format single file centrality analysis for LLM."""
        from pathlib import Path

        output = []
        file_name = Path(analysis.file_path).name

        output.append(f"=== Centrality Analysis: {file_name} ===")
        output.append("")

        output.append(
            f"📊 IMPORTANCE SCORE: {analysis.centrality_score:.3f}/1.0 (Rank: {analysis.rank}/{analysis.total_files})"
        )
        output.append("")

        # Dependency analysis
        output.append("🔗 FILE CONNECTIONS:")
        output.append(
            f"├── Files this imports from: {analysis.dependency_analysis['direct_imports']} files"
        )
        output.append(
            f"├── Files that import this: {analysis.dependency_analysis['reverse_dependencies']} files"
        )
        output.append(
            f"└── Total connections: {analysis.dependency_analysis['total_connections']}"
        )
        output.append("")

        # Centrality breakdown
        output.append("📈 IMPORTANCE METRICS (0.0 = low, 1.0 = high):")

        if analysis.centrality_breakdown is None:
            output.append(
                "├── ❌ Centrality Analysis Error: No centrality data available"
            )
            output.append(
                "└── 💡 Note: Run dependency analysis first to enable centrality calculations"
            )
        else:
            # Map technical terms to user-friendly ones
            metric_info = {
                "degree": ("Connection Count", "how many files this connects to"),
                "betweenness": (
                    "Bridge Factor",
                    "how often this file sits between others",
                ),
                "pagerank": ("Influence Score", "overall influence in the codebase"),
                "eigenvector": (
                    "Network Authority",
                    "connections to other important files",
                ),
                "closeness": ("Accessibility", "how easily reachable from other files"),
            }

            metric_count = 0
            total_metrics = len(analysis.centrality_breakdown)

            for metric, score in analysis.centrality_breakdown.items():
                metric_count += 1
                if metric in metric_info:
                    name, explanation = metric_info[metric]
                    prefix = "├──" if metric_count < total_metrics else "├──"
                    output.append(f"{prefix} {name}: {score:.3f} ({explanation})")
                else:
                    fallback_name = metric.replace("_", " ").title()
                    prefix = "├──" if metric_count < total_metrics else "├──"
                    output.append(f"{prefix} {fallback_name}: {score:.3f}")

            output.append(f"└── Overall Importance: {analysis.centrality_score:.3f}")

        output.append("")

        # Structural impact
        output.append("💥 CHANGE IMPACT:")
        output.append(
            f"├── If this file changes → {analysis.structural_impact['if_file_changes']} files potentially affected"
        )
        output.append(
            f"├── If functions change → {analysis.structural_impact['if_functions_change']} functions affected"
        )
        output.append(
            f"└── If classes change → {analysis.structural_impact['if_classes_change']} classes affected"
        )

        # Optimize for token budget
        result = "\n".join(output)
        return self.token_optimizer.optimize_for_token_budget(result, self.max_tokens)

    def _format_multiple_files_centrality_llm(
        self, analyses: List[FileCentralityAnalysis]
    ) -> str:
        """Format multiple files centrality analysis for LLM."""
        from pathlib import Path

        output = []

        output.append(
            f"=== Centrality Analysis: {', '.join(Path(a.file_path).name for a in analyses)} ==="
        )
        output.append("")

        # Sort by centrality score
        sorted_analyses = sorted(
            analyses, key=lambda x: x.centrality_score, reverse=True
        )

        output.append("CENTRALITY RANKINGS:")
        for i, analysis in enumerate(sorted_analyses, 1):
            file_name = Path(analysis.file_path).name
            output.append(
                f"{i}. {file_name}: {analysis.centrality_score:.3f} (rank {analysis.rank})"
            )
        output.append("")

        # Combined analysis
        total_connections = sum(
            a.dependency_analysis["total_connections"] for a in analyses
        )
        total_functions = sum(
            a.function_call_analysis["defined_functions"] for a in analyses
        )

        output.append("COMBINED ANALYSIS:")
        output.append(f"├── Total connections: {total_connections}")
        output.append(f"├── Total defined functions: {total_functions}")
        output.append(
            f"└── Average centrality: {sum(a.centrality_score for a in analyses) / len(analyses):.3f}"
        )

        # Optimize for token budget
        result = "\n".join(output)
        return self.token_optimizer.optimize_for_token_budget(result, self.max_tokens)

    def _format_json_impact(self, analyses: List[FileImpactAnalysis]) -> str:
        """Format impact analysis as JSON."""
        import json

        data = []
        for analysis in analyses:
            data.append(
                {
                    "file_path": analysis.file_path,
                    "direct_dependencies": analysis.direct_dependencies,
                    "reverse_dependencies": analysis.reverse_dependencies,
                    "function_call_analysis": analysis.function_call_analysis,
                    "structural_impact": analysis.structural_impact,
                    "risk_assessment": analysis.risk_assessment,
                    "suggested_tests": analysis.suggested_tests,
                }
            )
        return json.dumps(data, indent=2)

    def _format_json_centrality(self, analyses: List[FileCentralityAnalysis]) -> str:
        """Format centrality analysis as JSON."""
        import json

        data = []
        for analysis in analyses:
            data.append(
                {
                    "file_path": analysis.file_path,
                    "centrality_score": analysis.centrality_score,
                    "rank": analysis.rank,
                    "total_files": analysis.total_files,
                    "dependency_analysis": analysis.dependency_analysis,
                    "function_call_analysis": analysis.function_call_analysis,
                    "centrality_breakdown": analysis.centrality_breakdown,
                    "structural_impact": analysis.structural_impact,
                }
            )
        return json.dumps(data, indent=2)

    def _format_table_impact(self, analyses: List[FileImpactAnalysis]) -> str:
        """Format impact analysis as table."""
        from pathlib import Path

        output = []
        for analysis in analyses:
            file_name = Path(analysis.file_path).name
            output.append(f"File: {file_name}")
            output.append(f"  Direct Dependencies: {len(analysis.direct_dependencies)}")
            output.append(
                f"  Reverse Dependencies: {len(analysis.reverse_dependencies)}"
            )
            output.append(f"  Function Calls: {len(analysis.function_call_analysis)}")
            output.append("")
        return "\n".join(output)

    def _format_table_centrality(self, analyses: List[FileCentralityAnalysis]) -> str:
        """Format centrality analysis as table."""
        from pathlib import Path

        output = []
        for analysis in analyses:
            file_name = Path(analysis.file_path).name
            output.append(f"File: {file_name}")
            output.append(f"  Centrality Score: {analysis.centrality_score:.3f}")
            output.append(f"  Rank: {analysis.rank}/{analysis.total_files}")
            output.append(
                f"  Total Connections: {analysis.dependency_analysis['total_connections']}"
            )
            output.append("")
        return "\n".join(output)

    def _format_text_impact(self, analyses: List[FileImpactAnalysis]) -> str:
        """Format impact analysis as plain text."""
        return self._format_llm_optimized_impact(analyses)

    def _format_text_centrality(self, analyses: List[FileCentralityAnalysis]) -> str:
        """Format centrality analysis as plain text."""
        return self._format_llm_optimized_centrality(analyses)

    def optimize_for_tokens(self, content: str, max_tokens: int) -> str:
        """Optimize content for token budget.

        Args:
            content: Content to optimize
            max_tokens: Maximum token limit

        Returns:
            Optimized content
        """
        return self.token_optimizer.optimize_for_token_budget(content, max_tokens)
