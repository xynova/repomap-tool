"""
Centrality analysis module for LLM-optimized file analysis.

This module handles centrality calculations, rankings, and importance metrics
for files within a project dependency graph.
"""

import logging
import os
from typing import List, Dict, Optional, Any
from pathlib import Path

from .ast_file_analyzer import FileAnalysisResult
from .centrality_calculator import CentralityCalculator
from .advanced_dependency_graph import AdvancedDependencyGraph
from .analysis_models import FileCentralityAnalysis, AnalysisFormat
from ..llm.token_optimizer import TokenOptimizer

logger = logging.getLogger(__name__)


class CentralityAnalyzer:
    """Handles centrality analysis for files in a project."""

    def __init__(
        self,
        dependency_graph: Optional[AdvancedDependencyGraph] = None,
        project_root: Optional[str] = None,
        max_tokens: int = 4000,
    ):
        """Initialize the centrality analyzer.

        Args:
            dependency_graph: Advanced dependency graph for analysis
            project_root: Root path of the project
            max_tokens: Maximum tokens for LLM-optimized output
        """
        self.dependency_graph = dependency_graph
        self.project_root = project_root
        self.max_tokens = max_tokens
        self.token_optimizer = TokenOptimizer()
        self.centrality_calculator: Optional[CentralityCalculator]

        # Initialize centrality calculator if dependency graph is available
        if dependency_graph:
            self.centrality_calculator = CentralityCalculator(dependency_graph)
        else:
            self.centrality_calculator = None

        logger.info(f"CentralityAnalyzer initialized for project: {project_root}")

    def analyze_file_centrality(
        self, file_path: str, ast_result: FileAnalysisResult, all_files: List[str]
    ) -> FileCentralityAnalysis:
        """Analyze centrality for a single file.

        Args:
            file_path: Path to the file to analyze
            ast_result: AST analysis result for the file
            all_files: List of all files in the project

        Returns:
            FileCentralityAnalysis object
        """
        # Convert absolute path to relative path for dependency graph lookup
        if os.path.isabs(file_path) and self.project_root:
            try:
                relative_file_path = os.path.relpath(file_path, self.project_root)
            except ValueError:
                # If paths are on different drives (Windows), use the original path
                relative_file_path = file_path
        else:
            relative_file_path = file_path

        # Calculate centrality score
        centrality_score = 0.0
        rank = 1
        total_files = 0
        all_scores = {}
        if self.centrality_calculator:
            all_scores = self.centrality_calculator.calculate_composite_importance()
            centrality_score = all_scores.get(relative_file_path, 0.0)
            total_files = len(all_scores) if all_scores else 0

            # Calculate rank
            if all_scores:
                sorted_scores = sorted(
                    all_scores.items(), key=lambda x: x[1], reverse=True
                )
                for i, (fpath, score) in enumerate(sorted_scores, 1):
                    if fpath == relative_file_path:
                        rank = i
                        break

        # If centrality calculator failed or returned empty results, use fallback
        if total_files == 0:
            if self.dependency_graph and len(self.dependency_graph.nodes) > 0:
                total_files = len(self.dependency_graph.nodes)
            else:
                total_files = len(all_files) if all_files else 1

        # Dependency analysis - use dependency graph data when available
        if self.dependency_graph and relative_file_path in self.dependency_graph.nodes:
            node = self.dependency_graph.nodes[relative_file_path]
            direct_imports = len(node.imports) if node.imports else 0
            reverse_dependencies = len(node.imported_by) if node.imported_by else 0
            # Get actual lists for detailed analysis
            import_list = list(node.imports) if node.imports else []
            reverse_dep_list = list(node.imported_by) if node.imported_by else []
        else:
            # Fallback to AST results for Python files
            direct_imports = len(ast_result.imports)
            # Note: This would need access to ast_analyzer for reverse dependencies
            # For now, we'll use a simplified approach
            reverse_dependencies = 0
            import_list = (
                [imp.module for imp in ast_result.imports] if ast_result.imports else []
            )
            reverse_dep_list = []

        dependency_analysis = {
            "direct_imports": direct_imports,
            "reverse_dependencies": reverse_dependencies,
            "total_connections": direct_imports + reverse_dependencies,
            "import_list": import_list[:15],  # Show more for LLM analysis
            "reverse_dep_list": reverse_dep_list,  # Show ALL inbound deps for LLM
            "import_list_truncated": len(import_list) > 15,
            "reverse_dep_list_truncated": False,  # Don't truncate inbound deps
        }

        # Function call analysis - simplified for now
        function_call_analysis: Dict[str, Any] = {
            "total_calls": len(ast_result.function_calls),
            "internal_calls": 0,  # Would need function call analyzer
            "external_calls": 0,  # Would need function call analyzer
            "defined_functions": len(ast_result.defined_functions),
            "most_called_function": None,  # Would need function call analyzer
            "top_called_functions": [],  # Would need function call analyzer
            "internal_functions": [],  # Would need function call analyzer
            "external_functions": [],  # Would need function call analyzer
            "external_with_sources": [],  # Would need function call analyzer
            "most_used_class": None,  # Would need function call analyzer
        }

        # Get actual centrality breakdown from calculator
        centrality_breakdown: Optional[Dict[str, float]] = None
        if self.centrality_calculator:
            try:
                # Initialize the breakdown dictionary
                centrality_breakdown = {}

                # Get individual centrality measures for this file
                degree_scores = self.centrality_calculator.calculate_degree_centrality()
                betweenness_scores = (
                    self.centrality_calculator.calculate_betweenness_centrality()
                )
                pagerank_scores = (
                    self.centrality_calculator.calculate_pagerank_centrality()
                )

                # Only include metrics that were successfully calculated
                if degree_scores and relative_file_path in degree_scores:
                    centrality_breakdown["degree"] = degree_scores[relative_file_path]
                if betweenness_scores and relative_file_path in betweenness_scores:
                    centrality_breakdown["betweenness"] = betweenness_scores[
                        relative_file_path
                    ]
                if pagerank_scores and relative_file_path in pagerank_scores:
                    centrality_breakdown["pagerank"] = pagerank_scores[
                        relative_file_path
                    ]

                # Try to get additional metrics if they work
                try:
                    eigenvector_scores = (
                        self.centrality_calculator.calculate_eigenvector_centrality()
                    )
                    if eigenvector_scores and relative_file_path in eigenvector_scores:
                        centrality_breakdown["eigenvector"] = eigenvector_scores[
                            relative_file_path
                        ]
                except Exception as e:
                    logger.debug(f"Eigenvector centrality calculation failed: {e}")

                try:
                    closeness_scores = (
                        self.centrality_calculator.calculate_closeness_centrality()
                    )
                    if closeness_scores and relative_file_path in closeness_scores:
                        centrality_breakdown["closeness"] = closeness_scores[
                            relative_file_path
                        ]
                except Exception as e:
                    logger.debug(f"Closeness centrality calculation failed: {e}")

            except Exception as e:
                logger.error(f"Error calculating detailed centrality breakdown: {e}")
                # No fake calculations - report the error to user
                centrality_breakdown = None
        else:
            # No centrality calculator available - inform user
            logger.warning(
                "No centrality calculator available - run dependency analysis first"
            )
            centrality_breakdown = None

        # Structural impact - use dependency graph data when available
        if self.dependency_graph and relative_file_path in self.dependency_graph.nodes:
            node = self.dependency_graph.nodes[relative_file_path]
            files_affected = len(node.imported_by) if node.imported_by else 0
        else:
            # Fallback to AST results for Python files
            files_affected = 0  # Would need ast_analyzer for reverse dependencies

        structural_impact = {
            "if_file_changes": files_affected,
            "if_functions_change": len(ast_result.defined_functions),
            "if_classes_change": len(ast_result.defined_classes),
        }

        return FileCentralityAnalysis(
            file_path=file_path,
            centrality_score=centrality_score,
            rank=rank,
            total_files=total_files,
            dependency_analysis=dependency_analysis,
            function_call_analysis=function_call_analysis,
            centrality_breakdown=centrality_breakdown,
            structural_impact=structural_impact,
        )

    def format_centrality_analysis(
        self, analyses: List[FileCentralityAnalysis], format_type: AnalysisFormat
    ) -> str:
        """Format centrality analysis results.

        Args:
            analyses: List of FileCentralityAnalysis objects
            format_type: Output format type

        Returns:
            Formatted centrality analysis string
        """
        if format_type == AnalysisFormat.LLM_OPTIMIZED:
            return self._format_llm_optimized_centrality(analyses)
        elif format_type == AnalysisFormat.JSON:
            return self._format_json_centrality(analyses)
        elif format_type == AnalysisFormat.TABLE:
            return self._format_table_centrality(analyses)
        else:
            return self._format_text_centrality(analyses)

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

        # Show actual dependency lists if available
        import_list = analysis.dependency_analysis.get("import_list", [])
        reverse_dep_list = analysis.dependency_analysis.get("reverse_dep_list", [])

        if import_list:
            output.append("📤 OUTBOUND DEPENDENCIES (imports):")
            for i, dep in enumerate(import_list):
                # Convert to relative path for cleaner display
                dep_display = Path(dep).name if dep else dep
                prefix = "├──" if i < len(import_list) - 1 else "└──"
                output.append(f"│   {prefix} {dep_display}")
            if analysis.dependency_analysis.get("import_list_truncated"):
                output.append(
                    f"│   └── ... and {analysis.dependency_analysis['direct_imports'] - len(import_list)} more"
                )
            output.append("")

        if reverse_dep_list:
            output.append("📥 INBOUND DEPENDENCIES (files that import this):")

            # Group dependencies by directory for better organization
            deps_by_dir: dict[str, list[tuple[str, str]]] = {}
            for dep in reverse_dep_list:
                # Show relative path with context
                if dep.startswith(self.project_root):
                    dep_relative = os.path.relpath(dep, self.project_root)
                else:
                    dep_relative = dep

                # Extract meaningful directory context
                parts = Path(dep_relative).parts
                if len(parts) > 1:
                    dir_path = str(Path(*parts[:-1]))  # Directory path
                    filename = parts[-1]  # Just filename
                else:
                    dir_path = "."
                    filename = dep_relative

                if dir_path not in deps_by_dir:
                    deps_by_dir[dir_path] = []
                deps_by_dir[dir_path].append((dep, filename))

            # Display grouped dependencies
            dir_count = 0
            total_dirs = len(deps_by_dir)

            for dir_path, files in deps_by_dir.items():
                dir_count += 1
                dir_prefix = "├──" if dir_count < total_dirs else "└──"

                if len(files) == 1:
                    # Single file in directory - show inline
                    dep, filename = files[0]
                    if dir_path == ".":
                        output.append(f"│   {dir_prefix} {filename}")
                    else:
                        output.append(f"│   {dir_prefix} {dir_path}/{filename}")
                else:
                    # Multiple files in directory - group them
                    output.append(f"│   {dir_prefix} {dir_path}/ ({len(files)} files)")
                    for j, (dep, filename) in enumerate(files):
                        file_prefix = "├──" if j < len(files) - 1 else "└──"
                        output.append(f"│   │   {file_prefix} {filename}")

            output.append("")

        # Function call analysis
        output.append("⚙️ FUNCTION USAGE:")

        total_calls = analysis.function_call_analysis["total_calls"]
        internal_calls = analysis.function_call_analysis.get("internal_calls", 0)
        external_calls = analysis.function_call_analysis.get("external_calls", 0)

        output.append(f"├── Total function calls: {total_calls}")
        output.append(
            f"├── Internal calls: {internal_calls} ({internal_calls/total_calls*100:.1f}%)"
            if total_calls > 0
            else "├── Internal calls: 0"
        )
        output.append(
            f"├── External calls: {external_calls} ({external_calls/total_calls*100:.1f}%)"
            if total_calls > 0
            else "├── External calls: 0"
        )
        output.append(
            f"├── Functions defined: {analysis.function_call_analysis['defined_functions']}"
        )

        output.append("")

        # Centrality breakdown with user-friendly terms
        output.append("📈 IMPORTANCE METRICS (0.0 = low, 1.0 = high):")

        # Map technical terms to user-friendly ones with explanations
        metric_info = {
            "degree": ("Connection Count", "how many files this connects to"),
            "betweenness": ("Bridge Factor", "how often this file sits between others"),
            "pagerank": ("Influence Score", "overall influence in the codebase"),
            "eigenvector": (
                "Network Authority",
                "connections to other important files",
            ),
            "closeness": ("Accessibility", "how easily reachable from other files"),
        }

        # Check if we have centrality breakdown data
        if analysis.centrality_breakdown is None:
            output.append(
                "├── ❌ Centrality Analysis Error: No centrality data available"
            )
            output.append(
                "└── 💡 Note: Run dependency analysis first to enable centrality calculations"
            )
            output.append("")
            return "\n".join(output)

        # Check if we have error information instead of metrics
        if "error" in analysis.centrality_breakdown:
            output.append(
                f"├── ❌ Centrality Analysis Error: {analysis.centrality_breakdown['error']}"
            )
            if "note" in analysis.centrality_breakdown:
                output.append(f"└── 💡 Note: {analysis.centrality_breakdown['note']}")
            output.append("")
            return "\n".join(output)

        # Display actual centrality metrics
        metric_count = 0
        total_metrics = len(analysis.centrality_breakdown)

        for metric, score in analysis.centrality_breakdown.items():
            metric_count += 1
            if metric in metric_info:
                name, explanation = metric_info[metric]
                prefix = "├──" if metric_count < total_metrics else "├──"
                output.append(f"{prefix} {name}: {score:.3f} ({explanation})")
            else:
                # Fallback for any new metrics
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

    def _format_table_centrality(self, analyses: List[FileCentralityAnalysis]) -> str:
        """Format centrality analysis as table."""
        # This would use Rich tables - simplified for now
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

    def _format_text_centrality(self, analyses: List[FileCentralityAnalysis]) -> str:
        """Format centrality analysis as plain text."""
        return self._format_llm_optimized_centrality(analyses)
