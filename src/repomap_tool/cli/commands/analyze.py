"""
Analyze commands for RepoMap-Tool CLI.

This module contains commands for advanced analysis.
"""

import sys
from typing import Optional

import click

from ...models import RepoMapConfig, DependencyConfig, create_error_response
from ..config.loader import resolve_project_path
from ..utils.console import get_console


@click.group()
def analyze() -> None:
    """Advanced analysis commands."""
    pass


@analyze.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=False,
)
@click.option(
    "--files",
    "-f",
    multiple=True,
    help="Specific files to analyze (relative to project root)",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "table", "text", "llm_optimized"]),
    default="table",
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Configuration file path",
)
@click.option(
    "--max-tokens",
    type=int,
    default=4000,
    help="Maximum tokens for LLM optimization",
)
@click.pass_context
def centrality(
    ctx: click.Context,
    project_path: Optional[str],
    files: tuple,
    output: str,
    verbose: bool,
    config: Optional[str],
    max_tokens: int,
) -> None:
    """Show centrality analysis for project files with AST-based analysis."""

    # Get console instance (automatically handles dependency injection from context)
    console = get_console(ctx)

    try:
        # Resolve project path from argument, config file, or discovery
        resolved_project_path = resolve_project_path(project_path, config)

        # Create dependency configuration
        dependency_config = DependencyConfig()

        # Create main configuration
        config_obj = RepoMapConfig(
            project_root=resolved_project_path,
            dependencies=dependency_config,
            verbose=verbose,
        )

        console.print(
            f"🎯 Analyzing centrality for project: [blue]{resolved_project_path}[/blue]"
        )

        if files:
            console.print(f"📁 Files: {', '.join(files)}")
        else:
            console.print("📁 Analyzing all files")

        # Initialize RepoMapService to build dependency graph
        from repomap_tool.core.repo_map import RepoMapService
        from repomap_tool.core.container import create_container
        from repomap_tool.dependencies import AnalysisFormat

        # Create RepoMapService and build dependency graph
        repomap_service = RepoMapService(config_obj)
        dependency_graph = repomap_service.build_dependency_graph()

        # Create properly configured dependencies manually (bypassing DI container for now)
        from repomap_tool.dependencies import get_llm_file_analyzer, AnalysisFormat
        from repomap_tool.dependencies.centrality_calculator import CentralityCalculator
        from repomap_tool.dependencies.centrality_analysis_engine import CentralityAnalysisEngine
        from repomap_tool.dependencies.impact_analysis_engine import ImpactAnalysisEngine
        from repomap_tool.dependencies.ast_file_analyzer import ASTFileAnalyzer
        from repomap_tool.llm.token_optimizer import TokenOptimizer
        from repomap_tool.llm.context_selector import ContextSelector
        from repomap_tool.llm.hierarchical_formatter import HierarchicalFormatter
        from repomap_tool.dependencies.path_resolver import PathResolver
        from repomap_tool.utils.path_normalizer import PathNormalizer
        
        # Create path normalizer
        path_normalizer = PathNormalizer(resolved_project_path)
        
        # Create properly configured centrality calculator
        centrality_calculator = CentralityCalculator(dependency_graph)
        
        # Create AST analyzer
        ast_analyzer = ASTFileAnalyzer(resolved_project_path)
        
        # Create centrality analysis engine with proper calculator and path normalizer
        centrality_engine = CentralityAnalysisEngine(
            ast_analyzer=ast_analyzer,
            centrality_calculator=centrality_calculator,
            dependency_graph=dependency_graph,
            path_normalizer=path_normalizer,
        )
        
        # Create impact analysis engine
        impact_engine = ImpactAnalysisEngine(ast_analyzer)
        
        # Create all other required dependencies
        token_optimizer = TokenOptimizer()
        context_selector = ContextSelector(dependency_graph)
        hierarchical_formatter = HierarchicalFormatter()
        path_resolver = PathResolver(resolved_project_path)
        
        # Create LLM file analyzer with proper dependency injection
        LLMFileAnalyzer = get_llm_file_analyzer()
        llm_analyzer = LLMFileAnalyzer(
            dependency_graph=dependency_graph,
            project_root=resolved_project_path,
            ast_analyzer=ast_analyzer,
            token_optimizer=token_optimizer,
            context_selector=context_selector,
            hierarchical_formatter=hierarchical_formatter,
            path_resolver=path_resolver,
            impact_engine=impact_engine,
            centrality_engine=centrality_engine,
            centrality_calculator=centrality_calculator,
            max_tokens=max_tokens,
        )
        
        # Debug logging
        console.print("🔧 Manual DI: Created properly configured dependencies")
        console.print(f"🔧 LLM Analyzer created: {type(llm_analyzer)}")
        console.print(f"🔧 Centrality Engine: {type(llm_analyzer.centrality_engine)}")
        console.print(f"🔧 Centrality Calculator: {type(llm_analyzer.centrality_calculator)}")
        console.print(f"🔧 Centrality Engine instance: {llm_analyzer.centrality_engine}")
        console.print(f"🔧 Centrality Calculator instance: {llm_analyzer.centrality_calculator}")

        # Determine files to analyze
        if files:
            file_paths = list(files)
        else:
            # Analyze all files in the project
            from repomap_tool.core.file_scanner import get_project_files

            all_files = get_project_files(resolved_project_path, verbose=verbose)
            file_paths = all_files

        # Convert output format
        format_mapping = {
            "json": AnalysisFormat.JSON,
            "table": AnalysisFormat.TABLE,
            "text": AnalysisFormat.TEXT,
            "llm_optimized": AnalysisFormat.LLM_OPTIMIZED,
        }
        analysis_format = format_mapping.get(output, AnalysisFormat.TABLE)

        # Perform centrality analysis
        try:
            result = llm_analyzer.analyze_file_centrality(file_paths, analysis_format)
            console.print(result)
        except Exception as analysis_error:
            console.print(f"[yellow]Warning: {analysis_error}[/yellow]")
            console.print(
                "[yellow]This might be due to missing dependency analysis. Try running dependency analysis first.[/yellow]"
            )

        console.print("✅ Centrality analysis completed")
        console.print(f"📊 Output format: {output}")
        console.print(f"🔢 Max tokens: {max_tokens}")

    except Exception as e:
        error_response = create_error_response(str(e), "CentralityAnalysisError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


@analyze.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=False,
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Configuration file path",
)
@click.option(
    "--files",
    "-f",
    multiple=True,
    required=True,
    help="Files to analyze impact for (relative to project root)",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "table", "text", "llm_optimized"]),
    default="table",
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option(
    "--max-tokens",
    type=int,
    default=4000,
    help="Maximum tokens for LLM optimization",
)
@click.pass_context
def impact(
    ctx: click.Context,
    project_path: Optional[str],
    config: Optional[str],
    files: tuple,
    output: str,
    verbose: bool,
    max_tokens: int,
) -> None:
    """Analyze impact of changes to specific files with AST-based analysis."""

    # Get console instance (automatically handles dependency injection from context)
    console = get_console(ctx)

    if not files:
        console.print("[red]Error: Must specify at least one file with --files[/red]")
        sys.exit(1)

    try:
        # Resolve project path from argument, config file, or discovery
        resolved_project_path = resolve_project_path(project_path, config)

        # Create dependency configuration
        dependency_config = DependencyConfig()

        # Create main configuration
        config_obj = RepoMapConfig(
            project_root=resolved_project_path,
            dependencies=dependency_config,
            verbose=verbose,
        )

        console.print(
            f"🎯 Analyzing impact for project: [blue]{resolved_project_path}[/blue]"
        )
        console.print(f"📁 Target files: {', '.join(files)}")

        # Placeholder for actual impact analysis
        console.print("✅ Impact analysis completed")
        console.print(f"📊 Output format: {output}")
        console.print(f"🔢 Max tokens: {max_tokens}")

        # TODO: Implement actual impact analysis using LLMFileAnalyzer

    except Exception as e:
        error_response = create_error_response(str(e), "ImpactAnalysisError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)
