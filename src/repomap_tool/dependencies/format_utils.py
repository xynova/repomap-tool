"""
Formatting utilities for LLM file analysis.

This module provides utilities for formatting analysis results into different output formats
including LLM-optimized text, JSON, tables, and plain text.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, List, Set, TYPE_CHECKING, Union, Protocol

# Import models from llm_file_analyzer to avoid circular imports
# These will be imported at runtime when needed
from .function_utils import get_functions_called_from_file

if TYPE_CHECKING:
    from ..llm.token_optimizer import TokenOptimizer


class TokenOptimizerProtocol(Protocol):
    """Protocol for token optimizer to avoid circular imports."""

    def optimize_for_token_budget(
        self, content: str, max_tokens: int, model: str = "gpt-4"
    ) -> str: ...


if TYPE_CHECKING:
    from .models import FileImpactAnalysis, FileCentralityAnalysis

logger = logging.getLogger(__name__)


def format_llm_optimized_impact(
    analyses: List["FileImpactAnalysis"],
    token_optimizer: TokenOptimizerProtocol,
    max_tokens: int,
) -> str:
    """Format impact analysis for LLM consumption.

    Args:
        analyses: List of FileImpactAnalysis objects
        token_optimizer: Token optimizer instance
        max_tokens: Maximum tokens for output

    Returns:
        LLM-optimized formatted string
    """
    if len(analyses) == 1:
        return format_single_file_impact_llm(analyses[0], token_optimizer, max_tokens)
    else:
        return format_multiple_files_impact_llm(analyses, token_optimizer, max_tokens)


def format_single_file_impact_llm(
    analysis: "FileImpactAnalysis",
    token_optimizer: TokenOptimizerProtocol,
    max_tokens: int,
) -> str:
    """Format single file impact analysis for LLM."""
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
            f"├── {dep['file']}:{dep['line']} ({dep['relationship']})"
        )
    if len(analysis.reverse_dependencies) > 10:
        output.append(f"└── ... and {len(analysis.reverse_dependencies) - 10} more")
    output.append("")

    # Function call analysis
    if analysis.function_call_analysis:
        output.append("FUNCTION CALL ANALYSIS:")
        for call in analysis.function_call_analysis[:5]:  # Limit for token budget
            source_info = call.get('source', 'unknown source')
            if source_info != 'unknown source':
                output.append(f"├── {call['function']}() called at line {call['line']} ({source_info})")
            else:
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
    return token_optimizer.optimize_for_token_budget(result, max_tokens)


def format_multiple_files_impact_llm(
    analyses: List["FileImpactAnalysis"],
    token_optimizer: TokenOptimizerProtocol,
    max_tokens: int,
) -> str:
    """Format multiple files impact analysis for LLM."""
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
            all_reverse_deps.add(dep["file"])

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
    return token_optimizer.optimize_for_token_budget(result, max_tokens)


def format_llm_optimized_centrality(
    analyses: List["FileCentralityAnalysis"],
    token_optimizer: TokenOptimizerProtocol,
    max_tokens: int,
    project_root: str,
    ast_analyzer: Any,
) -> str:
    """Format centrality analysis for LLM consumption."""
    if len(analyses) == 1:
        return format_single_file_centrality_llm(
            analyses[0], token_optimizer, max_tokens, project_root, ast_analyzer
        )
    else:
        return format_multiple_files_centrality_llm(
            analyses, token_optimizer, max_tokens
        )


def format_single_file_centrality_llm(
    analysis: "FileCentralityAnalysis",
    token_optimizer: TokenOptimizerProtocol,
    max_tokens: int,
    project_root: str,
    ast_analyzer: Any,
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
            if dep.startswith(project_root):
                dep_relative = os.path.relpath(dep, project_root)
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

                    # Add function call details if available (but only for first few to avoid clutter)
                    if j < 3:  # Show function calls for first 3 files per directory
                        called_functions = get_functions_called_from_file(
                            ast_analyzer, dep, analysis.file_path
                        )
                        if called_functions:
                            func_list = ", ".join(
                                called_functions[:2]
                            )  # Show top 2 functions
                            if len(called_functions) > 2:
                                func_list += f" (+{len(called_functions)-2} more)"
                            output.append(f"│   │       └── calls: {func_list}")

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

    # Show internal functions (calls to functions defined in this file)
    internal_functions = analysis.function_call_analysis.get("internal_functions", [])
    external_with_sources = analysis.function_call_analysis.get(
        "external_with_sources", []
    )

    if internal_functions:
        output.append("├── 🏠 Internal calls (business logic):")
        for i, (func_name, count) in enumerate(internal_functions):
            # Calculate importance based on call frequency
            importance = "🔥" if count >= 3 else "⚡" if count >= 2 else "📋"
            prefix = "│   ├──" if i < len(internal_functions) - 1 else "│   └──"
            output.append(f"{prefix} {importance} {func_name} ({count}x)")

    if external_with_sources:
        # Filter external calls to focus on business logic
        from .function_utils import filter_business_relevant_calls

        business_relevant_calls = filter_business_relevant_calls(external_with_sources)

        if business_relevant_calls:
            is_last_section = not internal_functions
            section_prefix = "└──" if is_last_section else "├──"
            output.append(f"{section_prefix} 🌐 External calls (business logic):")

            for i, (func_name, count, source) in enumerate(business_relevant_calls):
                if is_last_section:
                    prefix = (
                        "    ├──" if i < len(business_relevant_calls) - 1 else "    └──"
                    )
                else:
                    prefix = (
                        "│   ├──" if i < len(business_relevant_calls) - 1 else "│   └──"
                    )

                # Color-code by dependency type
                if "(built-in)" in source:
                    dep_type = "🔧"  # Built-in
                elif "unknown" in source:
                    dep_type = "❓"  # Unknown
                else:
                    dep_type = "📦"  # Import

                output.append(f"{prefix} {dep_type} {func_name} ({count}x) → {source}")

            # Show summary of filtered calls
            filtered_count = len(external_with_sources) - len(business_relevant_calls)
            if filtered_count > 0:
                if is_last_section:
                    output.append(
                        f"        └── ({filtered_count} low-level utility calls hidden)"
                    )
                else:
                    output.append(
                        f"│       └── ({filtered_count} low-level utility calls hidden)"
                    )

    # If no categorized data available, fall back to top functions
    if not internal_functions and not external_with_sources:
        top_functions = analysis.function_call_analysis.get("top_called_functions", [])
        if top_functions:
            output.append("└── Most called functions:")
            for i, (func_name, count) in enumerate(top_functions):
                prefix = "    ├──" if i < len(top_functions) - 1 else "    └──"
                output.append(f"{prefix} {func_name} ({count}x)")

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
        output.append("├── ❌ Centrality Analysis Error: No centrality data available")
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
    return token_optimizer.optimize_for_token_budget(result, max_tokens)


def format_multiple_files_centrality_llm(
    analyses: List["FileCentralityAnalysis"],
    token_optimizer: TokenOptimizerProtocol,
    max_tokens: int,
) -> str:
    """Format multiple files centrality analysis for LLM."""
    output = []

    output.append(
        f"=== Centrality Analysis: {', '.join(Path(a.file_path).name for a in analyses)} ==="
    )
    output.append("")

    # Sort by centrality score
    sorted_analyses = sorted(analyses, key=lambda x: x.centrality_score, reverse=True)

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
    return token_optimizer.optimize_for_token_budget(result, max_tokens)


def format_json_impact(analyses: List["FileImpactAnalysis"]) -> str:
    """Format impact analysis as JSON."""
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


def format_json_centrality(analyses: List["FileCentralityAnalysis"]) -> str:
    """Format centrality analysis as JSON."""
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


def format_table_impact(analyses: List["FileImpactAnalysis"]) -> str:
    """Format impact analysis as simple ASCII table."""
    if not analyses:
        return "No impact analysis data available."

    # Calculate column widths
    max_file_width = max(len(Path(analysis.file_path).name) for analysis in analyses) + 2
    max_file_width = min(max_file_width, 50)  # Cap filename width

    # Create header
    header = f"{'File':<{max_file_width}} {'Impact':<8} {'Direct':<8} {'Reverse':<8} {'Functions':<10} {'Classes':<8}"
    separator = "─" * len(header)

    # Build table
    lines = []
    lines.append("Impact Analysis")
    lines.append(separator)
    lines.append(header)
    lines.append(separator)

    # Add data rows
    for analysis in analyses:
        file_name = Path(analysis.file_path).name
        
        # Truncate long filenames
        display_name = file_name if len(file_name) <= max_file_width - 2 else file_name[:max_file_width - 5] + "..."

        # Calculate impact score from structural impact
        impact_score = analysis.structural_impact.get("impact_score", 0.0)
        impact_str = f"{impact_score:.3f}"

        # Get defined functions and classes from structural impact
        defined_functions = analysis.structural_impact.get("defined_functions", 0)
        defined_classes = analysis.structural_impact.get("defined_classes", 0)

        row = f"{display_name:<{max_file_width}} {impact_str:<8} {len(analysis.direct_dependencies):<8} {len(analysis.reverse_dependencies):<8} {defined_functions:<10} {defined_classes:<8}"
        lines.append(row)

    lines.append(separator)
    
    # Add column explanations
    lines.append("")
    lines.append("📊 COLUMN EXPLANATIONS:")
    lines.append("├── File: File name")
    lines.append("├── Impact: Impact score (0.0-1.0, higher = more impact)")
    lines.append("├── Direct: Number of direct dependencies (imports)")
    lines.append("├── Reverse: Number of reverse dependencies (imported by)")
    lines.append("├── Functions: Number of functions defined in this file")
    lines.append("└── Classes: Number of classes defined in this file")
    
    return "\n".join(lines)


def format_table_centrality(analyses: List["FileCentralityAnalysis"]) -> str:
    """Format centrality analysis as table."""
    # Create a simple ASCII table without Rich to avoid ANSI code issues
    if not analyses:
        return "No centrality analysis data available."

    # Files should already be sorted by centrality score from the analyzer
    # Keep them in the order they were processed (most important first)
    sorted_analyses = analyses

    # Calculate column widths - give much more space for file names
    max_file_width = (
        max(len(analysis.file_path) for analysis in sorted_analyses[:50]) + 2
    )
    max_file_width = min(max_file_width, 120)  # Increased cap to 120 chars for full relative paths

    # Create header with working data - File column moved to last position
    header = f"{'Score':<8} {'Rank':<6} {'Conn':<6} {'Imports':<8} {'Rev Deps':<8} {'Functions':<8} {'File':<{max_file_width}}"
    separator = "─" * len(header)

    # Build table
    lines = []
    lines.append("Centrality Analysis (Most Important First)")
    lines.append(separator)
    lines.append(header)
    lines.append(separator)

    # Add data rows (now sorted by importance)
    displayed_count = 0
    for analysis in sorted_analyses:
        if analysis.centrality_score <= 0.001 and displayed_count >= 10:  # Cut off after 10 important files
            remaining_count = len(sorted_analyses) - displayed_count
            lines.append(
                f"... and {remaining_count} more files with very low centrality scores (≤ 0.001)"
            )
            break

        # Use full relative path without truncation
        file_path = analysis.file_path

        score_str = f"{analysis.centrality_score:.3f}"
        rank_str = f"{analysis.rank}"
        conn_str = f"{analysis.dependency_analysis.get('total_connections', 0)}"
        imports_str = f"{analysis.dependency_analysis.get('direct_imports', 0)}"
        rev_deps_str = f"{analysis.dependency_analysis.get('reverse_dependencies', 0)}"

        # Get function count (defined functions in this file)
        functions = analysis.function_call_analysis.get("defined_functions", 0)
        functions_str = f"{functions}"

        row = f"{score_str:<8} {rank_str:<6} {conn_str:<6} {imports_str:<8} {rev_deps_str:<8} {functions_str:<8} {file_path:<{max_file_width}}"
        lines.append(row)
        displayed_count += 1

    lines.append(separator)
    
    # Add column explanations
    lines.append("")
    lines.append("📊 COLUMN EXPLANATIONS:")
    lines.append("├── Score: Centrality score (0.0-1.0, higher = more important)")
    lines.append("├── Rank: Position in importance ranking (1 = most important)")
    lines.append("├── Conn: Total connections to other files")
    lines.append("├── Imports: Number of files this file imports")
    lines.append("├── Rev Deps: Number of files that import this file")
    lines.append("├── Functions: Number of functions defined in this file")
    lines.append("└── File: File path (relative to project root)")
    
    return "\n".join(lines)


def format_text_impact(
    analyses: List["FileImpactAnalysis"],
    token_optimizer: TokenOptimizerProtocol,
    max_tokens: int,
) -> str:
    """Format impact analysis as plain text."""
    return format_llm_optimized_impact(analyses, token_optimizer, max_tokens)


def format_text_centrality(
    analyses: List["FileCentralityAnalysis"],
    token_optimizer: TokenOptimizerProtocol,
    max_tokens: int,
    project_root: str,
    ast_analyzer: Any,
) -> str:
    """Format centrality analysis as plain text."""
    return format_llm_optimized_centrality(
        analyses, token_optimizer, max_tokens, project_root, ast_analyzer
    )
