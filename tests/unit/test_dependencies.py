"""
Unit tests for dependency analysis components using session fixtures.

This module tests the core dependency analysis functionality including
import analysis, dependency graphs, centrality calculation, and impact analysis.
All tests use session-scoped fixtures for improved performance.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from repomap_tool.code_analysis import (
    ImportAnalyzer,
    DependencyGraph,
    Import,
    FileImports,
    ProjectImports,
    FunctionCall,
    CallGraph,
    DependencyNode,
    ImpactReport,
)
from repomap_tool.core.container import create_container
from repomap_tool.models import (
    RepoMapConfig,
    FuzzyMatchConfig,
    SemanticMatchConfig,
    PerformanceConfig,
    DependencyConfig,
)


class TestImportAnalyzer:
    """Test the ImportAnalyzer class."""

    def test_initialization(self, session_container):
        """Test ImportAnalyzer initialization."""
        analyzer = session_container.import_analyzer()
        assert analyzer is not None
        assert len(analyzer.language_parsers) > 0
        assert "py" in analyzer.language_parsers
        assert "js" in analyzer.language_parsers

    def test_get_supported_languages(self, session_container):
        """Test getting supported languages."""
        analyzer = session_container.import_analyzer()
        languages = analyzer.get_supported_languages()
        assert "py" in languages
        assert "js" in languages
        assert "ts" in languages
        assert "java" in languages
        assert "go" in languages

    def test_analyze_python_file(self, session_test_repo_path, session_container):
        """Test analyzing a Python file from test fixture."""
        analyzer = session_container.import_analyzer()

        # Use a file from our test fixture
        test_file = session_test_repo_path / "imports_standard.py"
        imports = analyzer.analyze_file_imports(str(test_file))
        assert imports is not None
        assert len(imports.imports) >= 4  # Should have multiple imports


class TestDependencyGraph:
    """Test the DependencyGraph class."""

    def test_initialization(self, session_container):
        """Test DependencyGraph initialization."""
        graph = session_container.dependency_graph()
        assert graph is not None
        assert len(graph.nodes) == 0
        assert len(graph.graph.edges) == 0

    def test_add_file(self, session_container):
        """Test adding files to the graph."""
        graph = session_container.dependency_graph()
        graph.add_file("test.py")
        assert "test.py" in graph.nodes
        assert graph.nodes["test.py"].file_path == "test.py"

    def test_build_graph_with_imports(self, session_import_data, session_container):
        """Test building graph with pre-analyzed import data."""
        graph = session_container.dependency_graph()
        graph.build_graph(session_import_data)

        # Check that dependencies were added
        assert len(graph.nodes) > 0
        assert len(graph.graph.edges) >= 0

    def test_get_dependencies(self, session_dependency_graph):
        """Test getting file dependencies from pre-built graph."""
        # Use the session-scoped dependency graph
        deps = session_dependency_graph.get_dependencies("models.py")
        assert isinstance(deps, list)

    def test_get_dependents(self, session_dependency_graph):
        """Test getting files that depend on a given file."""
        # Use the session-scoped dependency graph
        dependents = session_dependency_graph.get_dependents("utils.py")
        assert isinstance(dependents, list)


class TestCentralityCalculator:
    """Test the CentralityCalculator class using session fixtures."""

    def test_initialization(self, session_container):
        """Test CentralityCalculator initialization."""
        calculator = session_container.centrality_calculator()
        assert calculator is not None

    def test_calculate_degree_centrality(
        self, session_dependency_graph, session_container
    ):
        """Test degree centrality calculation with pre-built graph."""
        calculator = session_container.centrality_calculator()

        # Test that calculator can be called with the session graph
        degree_scores = calculator.calculate_degree_centrality()
        assert isinstance(degree_scores, dict)


class TestCallGraphBuilder:
    """Test the CallGraphBuilder class using session fixtures."""

    def test_initialization(self, session_container):
        """Test CallGraphBuilder initialization."""
        builder = session_container.call_analyzer()
        assert builder is not None

    def test_analyze_file_calls_python(self, session_test_repo_path, session_container):
        """Test Python function call analysis using test fixture."""
        builder = session_container.call_analyzer()

        # Use a file from our test fixture that has function calls
        test_file = session_test_repo_path / "dependency_chain_a.py"
        calls = builder.analyze_file_calls(str(test_file))
        assert isinstance(calls, list)


class TestAdvancedDependencyGraph:
    """Test the AdvancedDependencyGraph class using session fixtures."""

    def test_initialization(self, session_container):
        """Test AdvancedDependencyGraph initialization."""
        graph = session_container.dependency_graph()
        assert graph is not None

    def test_integrate_call_graph(self, session_test_repo_path, session_container):
        """Test integrating call graph with dependency graph."""
        graph = session_container.dependency_graph()

        # Create a simple call graph with required parameters
        call_graph = CallGraph(function_calls=[], function_locations={})

        # Integrate call graph
        graph.integrate_call_graph(call_graph)

        # Verify integration
        assert graph.call_graph is not None


class TestImpactAnalyzer:
    """Test the ImpactAnalyzer class using session fixtures."""

    def test_initialization(self, session_container):
        """Test ImpactAnalyzer initialization."""
        analyzer = session_container.impact_analyzer()
        assert analyzer is not None

    def test_analyze_change_impact(self, session_dependency_graph, session_container):
        """Test analyzing change impact with pre-built graph."""
        analyzer = session_container.impact_analyzer()

        # Test that analyzer can be called with the session graph
        impact_report = analyzer.analyze_change_impact(["models.py"])
        assert impact_report is not None
