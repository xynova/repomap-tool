"""
Unit tests for dependency analysis components using DI container.

This module tests the core dependency analysis functionality including
import analysis, dependency graphs, centrality calculation, and impact analysis.
All tests use the dependency injection container for proper service creation.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from repomap_tool.dependencies import (
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
from repomap_tool.cli.services import get_service_factory


class TestImportAnalyzer:
    """Test the ImportAnalyzer class."""

    def test_initialization(self):
        """Test ImportAnalyzer initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = RepoMapConfig(project_root=temp_dir)
            container = create_container(config)
            analyzer = container.import_analyzer()
            assert analyzer is not None
            assert len(analyzer.language_parsers) > 0
            assert "py" in analyzer.language_parsers
            assert "js" in analyzer.language_parsers

    def test_get_supported_languages(self):
        """Test getting supported languages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = RepoMapConfig(project_root=temp_dir)
            container = create_container(config)
            analyzer = container.import_analyzer()
            languages = analyzer.get_supported_languages()
            assert "py" in languages
            assert "js" in languages
            assert "ts" in languages
            assert "java" in languages
            assert "go" in languages

    def test_analyze_python_file(self):
        """Test analyzing a Python file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test Python file
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, "w") as f:
                f.write(
                    """
import os
from pathlib import Path
import numpy as np
from .local_module import LocalClass
"""
                )

            config = RepoMapConfig(project_root=temp_dir)
            container = create_container(config)
            analyzer = container.import_analyzer()

            imports = analyzer.analyze_file_imports(test_file)
            assert imports is not None
            assert len(imports.imports) >= 4  # os, pathlib, numpy, local_module


class TestDependencyGraph:
    """Test the DependencyGraph class."""

    def test_initialization(self):
        """Test DependencyGraph initialization."""
        # Create config and use service factory
        config = RepoMapConfig(
            project_root=".",
            fuzzy_match=FuzzyMatchConfig(),
            semantic_match=SemanticMatchConfig(),
            performance=PerformanceConfig(),
            dependencies=DependencyConfig(),
        )
        service_factory = get_service_factory()
        repomap_service = service_factory.create_repomap_service(config)
        graph = repomap_service.dependency_graph
        assert graph is not None
        assert len(graph.nodes) == 0
        assert len(graph.graph.edges) == 0

    def test_add_file(self):
        """Test adding files to the graph."""
        # Create config and use service factory
        config = RepoMapConfig(
            project_root=".",
            fuzzy_match=FuzzyMatchConfig(),
            semantic_match=SemanticMatchConfig(),
            performance=PerformanceConfig(),
            dependencies=DependencyConfig(),
        )
        service_factory = get_service_factory()
        repomap_service = service_factory.create_repomap_service(config)
        graph = repomap_service.dependency_graph
        graph.add_file("test.py")
        assert "test.py" in graph.nodes
        assert graph.nodes["test.py"].file_path == "test.py"

    def test_build_graph_with_imports(self):
        """Test building graph with import data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            file1 = os.path.join(temp_dir, "file1.py")
            file2 = os.path.join(temp_dir, "file2.py")

            with open(file1, "w") as f:
                f.write("import file2")
            with open(file2, "w") as f:
                f.write("# file2 content")

            # Create import analyzer and analyze files
            config = RepoMapConfig(project_root=temp_dir)
            container = create_container(config)
            analyzer = container.import_analyzer()

            # Analyze project imports (pass project path, not file list)
            project_imports = analyzer.analyze_project_imports(temp_dir)

            # Build dependency graph
            config = RepoMapConfig(
                project_root=temp_dir,
                fuzzy_match=FuzzyMatchConfig(),
                semantic_match=SemanticMatchConfig(),
                performance=PerformanceConfig(),
                dependencies=DependencyConfig(),
            )
            service_factory = get_service_factory()
            repomap_service = service_factory.create_repomap_service(config)
            graph = repomap_service.dependency_graph
            graph.build_graph(project_imports)

            # Check that dependencies were added
            assert "file1.py" in graph.nodes
            assert "file2.py" in graph.nodes

    def test_get_dependencies(self):
        """Test getting file dependencies."""
        # Create config and use service factory
        config = RepoMapConfig(
            project_root=".",
            fuzzy_match=FuzzyMatchConfig(),
            semantic_match=SemanticMatchConfig(),
            performance=PerformanceConfig(),
            dependencies=DependencyConfig(),
        )
        service_factory = get_service_factory()
        repomap_service = service_factory.create_repomap_service(config)
        graph = repomap_service.dependency_graph
        graph.add_file("file1.py")
        graph.add_file("file2.py")
        graph.add_file("file3.py")

        # Test getting dependencies (should return empty list for files with no dependencies)
        deps = graph.get_dependencies("file1.py")
        assert isinstance(deps, list)

    def test_get_dependents(self):
        """Test getting files that depend on a given file."""
        # Create config and use service factory
        config = RepoMapConfig(
            project_root=".",
            fuzzy_match=FuzzyMatchConfig(),
            semantic_match=SemanticMatchConfig(),
            performance=PerformanceConfig(),
            dependencies=DependencyConfig(),
        )
        service_factory = get_service_factory()
        repomap_service = service_factory.create_repomap_service(config)
        graph = repomap_service.dependency_graph
        graph.add_file("file1.py")
        graph.add_file("file2.py")
        graph.add_file("file3.py")

        # Test getting dependents (should return empty list for files with no dependents)
        dependents = graph.get_dependents("file2.py")
        assert isinstance(dependents, list)


class TestCentralityCalculator:
    """Test the CentralityCalculator class using DI container."""

    def test_initialization(self):
        """Test CentralityCalculator initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = RepoMapConfig(project_root=temp_dir)
            container = create_container(config)
            calculator = container.centrality_calculator()
            assert calculator is not None

    def test_calculate_degree_centrality(self):
        """Test degree centrality calculation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = RepoMapConfig(project_root=temp_dir)
            container = create_container(config)
            calculator = container.centrality_calculator()

            # Test that calculator can be called (it will handle empty graph gracefully)
            degree_scores = calculator.calculate_degree_centrality()
            assert isinstance(degree_scores, dict)


class TestCallGraphBuilder:
    """Test the CallGraphBuilder class using DI container."""

    def test_initialization(self):
        """Test CallGraphBuilder initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = RepoMapConfig(project_root=temp_dir)
            container = create_container(config)
            builder = container.call_analyzer()
            assert builder is not None

    def test_analyze_file_calls_python(self):
        """Test Python function call analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test Python file with function calls
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, "w") as f:
                f.write(
                    """
def function_a():
    return function_b()

def function_b():
    return function_c()

def function_c():
    return "hello"
"""
                )

            config = RepoMapConfig(project_root=temp_dir)
            container = create_container(config)
            builder = container.call_analyzer()

            calls = builder.analyze_file_calls(test_file)
            assert (
                len(calls) >= 2
            )  # function_a calls function_b, function_b calls function_c


class TestAdvancedDependencyGraph:
    """Test the AdvancedDependencyGraph class using DI container."""

    def test_initialization(self):
        """Test AdvancedDependencyGraph initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = RepoMapConfig(project_root=temp_dir)
            container = create_container(config)
            graph = container.dependency_graph()
            assert graph is not None

    def test_integrate_call_graph(self):
        """Test integrating call graph with dependency graph."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = RepoMapConfig(project_root=temp_dir)
            container = create_container(config)
            graph = container.dependency_graph()

            # Create a simple call graph with required project_path
            call_graph = CallGraph(project_path=temp_dir)

            # Integrate call graph
            graph.integrate_call_graph(call_graph)

            # Verify integration
            assert graph.call_graph is not None


class TestImpactAnalyzer:
    """Test the ImpactAnalyzer class using DI container."""

    def test_initialization(self):
        """Test ImpactAnalyzer initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = RepoMapConfig(project_root=temp_dir)
            container = create_container(config)
            analyzer = container.impact_analyzer()
            assert analyzer is not None

    def test_analyze_change_impact(self):
        """Test analyzing change impact."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = RepoMapConfig(project_root=temp_dir)
            container = create_container(config)
            analyzer = container.impact_analyzer()

            # Test that analyzer can be called (it will handle empty graph gracefully)
            impact_report = analyzer.analyze_change_impact(["file2.py"])
            assert impact_report is not None
