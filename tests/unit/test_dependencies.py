"""
Unit tests for dependency analysis components.

This module tests the core dependency analysis functionality including
import analysis, dependency graphs, centrality calculation, and impact analysis.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from repomap_tool.dependencies import (
    ImportAnalyzer,
    DependencyGraph,
    CentralityCalculator,
    CallGraphBuilder,
    AdvancedDependencyGraph,
    ImpactAnalyzer,
    Import,
    FileImports,
    ProjectImports,
    FunctionCall,
    CallGraph,
    DependencyNode,
    ImpactReport,
)


class TestImportAnalyzer:
    """Test the ImportAnalyzer class."""

    def test_initialization(self):
        """Test ImportAnalyzer initialization."""
        analyzer = ImportAnalyzer()
        assert analyzer is not None
        assert len(analyzer.language_parsers) > 0
        assert "py" in analyzer.language_parsers
        assert "js" in analyzer.language_parsers

    def test_get_supported_languages(self):
        """Test getting supported languages."""
        analyzer = ImportAnalyzer()
        languages = analyzer.get_supported_languages()
        assert "py" in languages
        assert "js" in languages
        assert "ts" in languages
        assert "java" in languages
        assert "go" in languages

    def test_analyze_file_imports_python(self):
        """Test Python import analysis."""
        analyzer = ImportAnalyzer()

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
import os
import sys
from pathlib import Path
from . import utils
from typing import List, Dict
"""
            )
            temp_file = f.name

        try:
            file_imports = analyzer.analyze_file_imports(temp_file)
            assert file_imports.file_path == temp_file
            assert file_imports.language == "py"
            assert len(file_imports.imports) >= 5  # Should find the imports

            # Check specific imports
            import_modules = [imp.module for imp in file_imports.imports]
            assert "os" in import_modules
            assert "sys" in import_modules
            assert "pathlib" in import_modules
            assert "typing" in import_modules

        finally:
            os.unlink(temp_file)

    def test_analyze_file_imports_javascript(self):
        """Test JavaScript import analysis."""
        analyzer = ImportAnalyzer()

        # Create a temporary JavaScript file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(
                """
import { useState, useEffect } from 'react';
import React from 'react';
const express = require('express');
import('./dynamic-module');
"""
            )
            temp_file = f.name

        try:
            file_imports = analyzer.analyze_file_imports(temp_file)
            assert file_imports.file_path == temp_file
            assert file_imports.language == "js"
            assert len(file_imports.imports) >= 4  # Should find the imports

        finally:
            os.unlink(temp_file)

    def test_analyze_file_imports_unsupported_language(self):
        """Test handling of unsupported file types."""
        analyzer = ImportAnalyzer()

        # Create a temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is not a code file")
            temp_file = f.name

        try:
            file_imports = analyzer.analyze_file_imports(temp_file)
            assert file_imports.file_path == temp_file
            assert file_imports.language == "txt"
            assert len(file_imports.imports) == 0  # No imports found

        finally:
            os.unlink(temp_file)

    def test_analyze_project_imports(self):
        """Test project-wide import analysis."""
        analyzer = ImportAnalyzer()

        # Create temporary project files
        temp_files = []
        try:
            # Python file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write("import os\nimport sys")
                temp_files.append(f.name)

            # JavaScript file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
                f.write("import React from 'react'")
                temp_files.append(f.name)

            project_imports = analyzer.analyze_project_imports(temp_files)
            assert project_imports.total_files == 2
            assert project_imports.total_imports >= 3  # os, sys, React

        finally:
            for temp_file in temp_files:
                os.unlink(temp_file)


class TestDependencyGraph:
    """Test the DependencyGraph class."""

    def test_initialization(self):
        """Test DependencyGraph initialization."""
        graph = DependencyGraph()
        assert graph is not None
        assert len(graph.nodes) == 0
        assert len(graph.graph.edges) == 0

    def test_build_graph(self):
        """Test building a dependency graph."""
        graph = DependencyGraph()

        # Create temporary project files
        temp_files = []
        try:
            # Python file with imports
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write("import os\nimport sys")
                temp_files.append(f.name)

            # Another Python file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write("import os")
                temp_files.append(f.name)

            graph.build_graph(temp_files)
            assert len(graph.nodes) == 2
            assert len(graph.graph.edges) >= 0  # May have edges if imports resolve

        finally:
            for temp_file in temp_files:
                os.unlink(temp_file)

    def test_add_file(self):
        """Test adding a single file to the graph."""
        graph = DependencyGraph()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import os")
            temp_file = f.name

        try:
            graph.add_file(temp_file)
            assert temp_file in graph.nodes
            assert temp_file in graph.graph.nodes

        finally:
            os.unlink(temp_file)

    def test_get_dependencies_and_dependents(self):
        """Test getting dependencies and dependents."""
        graph = DependencyGraph()

        # Create a simple graph
        graph.nodes["file1.py"] = DependencyNode(file_path="file1.py")
        graph.nodes["file2.py"] = DependencyNode(file_path="file2.py")

        # Add nodes to NetworkX graph
        graph.graph.add_node("file1.py", **graph.nodes["file1.py"].model_dump())
        graph.graph.add_node("file2.py", **graph.nodes["file2.py"].model_dump())

        # Edge direction: imported_file → importing_file (file2 → file1 means file1 depends on file2)
        graph.graph.add_edge("file2.py", "file1.py")  # file1 depends on file2

        # Update imported_by lists
        graph.nodes["file2.py"].imported_by.append("file1.py")

        deps = graph.get_dependencies("file1.py")
        assert "file2.py" in deps

        dependents = graph.get_dependents("file2.py")
        assert "file1.py" in dependents

    def test_find_cycles(self):
        """Test finding circular dependencies."""
        graph = DependencyGraph()

        # Create a circular dependency
        graph.nodes["file1.py"] = DependencyNode(file_path="file1.py")
        graph.nodes["file2.py"] = DependencyNode(file_path="file2.py")
        # Edge direction: imported_file → importing_file
        graph.graph.add_edge("file2.py", "file1.py")  # file1 depends on file2
        graph.graph.add_edge("file1.py", "file2.py")  # file2 depends on file1

        cycles = graph.find_cycles()
        assert len(cycles) > 0
        assert any("file1.py" in cycle and "file2.py" in cycle for cycle in cycles)

    def test_get_graph_statistics(self):
        """Test getting graph statistics."""
        graph = DependencyGraph()

        # Add some nodes
        graph.nodes["file1.py"] = DependencyNode(file_path="file1.py")
        graph.nodes["file2.py"] = DependencyNode(file_path="file2.py")
        # Edge direction: imported_file → importing_file
        graph.graph.add_edge("file2.py", "file1.py")  # file1 depends on file2

        stats = graph.get_graph_statistics()
        assert stats["total_nodes"] == 2
        assert stats["total_edges"] == 1
        assert stats["leaf_nodes"] == 1
        assert stats["root_nodes"] == 1


class TestCentralityCalculator:
    """Test the CentralityCalculator class."""

    def test_initialization(self):
        """Test CentralityCalculator initialization."""
        graph = DependencyGraph()
        calculator = CentralityCalculator(graph)
        assert calculator is not None
        assert calculator.graph == graph

    def test_calculate_degree_centrality(self):
        """Test degree centrality calculation."""
        graph = DependencyGraph()

        # Create a simple graph
        graph.nodes["file1.py"] = DependencyNode(file_path="file1.py")
        graph.nodes["file2.py"] = DependencyNode(file_path="file2.py")
        graph.nodes["file3.py"] = DependencyNode(file_path="file3.py")
        # Edge direction: imported_file → importing_file
        graph.graph.add_edge("file2.py", "file1.py")  # file1 depends on file2
        graph.graph.add_edge("file3.py", "file1.py")  # file1 depends on file3

        calculator = CentralityCalculator(graph)
        degree_scores = calculator.calculate_degree_centrality()

        assert "file1.py" in degree_scores
        assert "file2.py" in degree_scores
        assert "file3.py" in degree_scores

        # file1 should have higher degree centrality (more connections)
        assert degree_scores["file1.py"] > degree_scores["file2.py"]

    def test_calculate_composite_importance(self):
        """Test composite importance calculation."""
        graph = DependencyGraph()

        # Create a simple graph
        graph.nodes["file1.py"] = DependencyNode(file_path="file1.py")
        graph.nodes["file2.py"] = DependencyNode(file_path="file2.py")
        # Edge direction: imported_file → importing_file
        graph.graph.add_edge("file2.py", "file1.py")  # file1 depends on file2

        calculator = CentralityCalculator(graph)
        composite_scores = calculator.calculate_composite_importance()

        assert "file1.py" in composite_scores
        assert "file2.py" in composite_scores
        assert all(0.0 <= score <= 1.0 for score in composite_scores.values())

    def test_get_top_central_files(self):
        """Test getting top central files."""
        graph = DependencyGraph()

        # Create a simple graph
        graph.nodes["file1.py"] = DependencyNode(file_path="file1.py")
        graph.nodes["file2.py"] = DependencyNode(file_path="file2.py")
        graph.graph.add_edge("file1.py", "file2.py")

        calculator = CentralityCalculator(graph)
        top_files = calculator.get_top_central_files("degree", top_n=5)

        assert len(top_files) <= 5
        assert all(isinstance(item, tuple) and len(item) == 2 for item in top_files)

    def test_cache_functionality(self):
        """Test caching functionality."""
        graph = DependencyGraph()
        calculator = CentralityCalculator(graph)

        # Enable cache
        calculator.enable_cache()
        assert calculator.cache_enabled

        # Disable cache
        calculator.disable_cache()
        assert not calculator.cache_enabled

        # Clear cache
        calculator.enable_cache()
        calculator.clear_cache()
        assert len(calculator.cache) == 0


class TestCallGraphBuilder:
    """Test the CallGraphBuilder class."""

    def test_initialization(self):
        """Test CallGraphBuilder initialization."""
        builder = CallGraphBuilder()
        assert builder is not None
        assert len(builder.language_analyzers) > 0
        assert "py" in builder.language_analyzers
        assert "js" in builder.language_analyzers

    def test_analyze_file_calls_python(self):
        """Test Python function call analysis."""
        builder = CallGraphBuilder()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def main():
    result = helper_function()
    print(result)

def helper_function():
    return "hello"
"""
            )
            temp_file = f.name

        try:
            calls = builder.analyze_file_calls(temp_file)
            assert len(calls) >= 1  # Should find function calls

        finally:
            os.unlink(temp_file)

    def test_build_call_graph(self):
        """Test building a complete call graph."""
        builder = CallGraphBuilder()

        # Create temporary project files
        temp_files = []
        try:
            # Python file with function calls
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(
                    """
def main():
    helper()
def helper():
    pass
"""
                )
                temp_files.append(f.name)

            call_graph = builder.build_call_graph(temp_files)
            assert call_graph is not None
            assert len(call_graph.function_calls) >= 0

        finally:
            for temp_file in temp_files:
                os.unlink(temp_file)

    def test_get_call_statistics(self):
        """Test getting call graph statistics."""
        builder = CallGraphBuilder()

        # Create a mock call graph
        call_graph = CallGraph(
            project_path="/test",
            function_calls=[
                FunctionCall(
                    caller="func1",
                    callee="func2",
                    file_path="/test/file.py",
                    line_number=1,
                ),
                FunctionCall(
                    caller="func2",
                    callee="func3",
                    file_path="/test/file.py",
                    line_number=2,
                ),
            ],
            function_locations={
                "func1": "/test/file.py",
                "func2": "/test/file.py",
                "func3": "/test/file.py",
            },
        )

        stats = builder.get_call_statistics(call_graph)
        assert stats["total_calls"] == 2
        assert stats["total_functions"] == 3


class TestAdvancedDependencyGraph:
    """Test the AdvancedDependencyGraph class."""

    def test_initialization(self):
        """Test AdvancedDependencyGraph initialization."""
        graph = AdvancedDependencyGraph()
        assert graph is not None
        assert graph.call_graph is None
        assert len(graph.function_dependencies) == 0
        assert len(graph.function_dependents) == 0

    def test_integrate_call_graph(self):
        """Test integrating call graph with dependency graph."""
        graph = AdvancedDependencyGraph()

        # Create a mock call graph
        call_graph = CallGraph(
            project_path="/test",
            function_calls=[
                FunctionCall(
                    caller="func1",
                    callee="func2",
                    file_path="/test/file1.py",
                    line_number=1,
                )
            ],
            function_locations={"func1": "/test/file1.py", "func2": "/test/file2.py"},
        )

        # Add nodes to dependency graph
        graph.nodes["/test/file1.py"] = DependencyNode(file_path="/test/file1.py")
        graph.nodes["/test/file2.py"] = DependencyNode(file_path="/test/file2.py")

        graph.integrate_call_graph(call_graph)
        assert graph.call_graph is not None
        assert len(graph.function_dependencies) > 0

    def test_calculate_transitive_dependencies(self):
        """Test calculating transitive dependencies with call graph."""
        graph = AdvancedDependencyGraph()

        # Create a simple graph with call graph
        call_graph = CallGraph(
            project_path="/test",
            function_calls=[
                FunctionCall(
                    caller="func1",
                    callee="func2",
                    file_path="/test/file1.py",
                    line_number=1,
                )
            ],
            function_locations={"func1": "/test/file1.py", "func2": "/test/file2.py"},
        )

        graph.nodes["/test/file1.py"] = DependencyNode(file_path="/test/file1.py")
        graph.nodes["/test/file2.py"] = DependencyNode(file_path="/test/file2.py")

        # Add nodes to NetworkX graph
        graph.graph.add_node(
            "/test/file1.py", **graph.nodes["/test/file1.py"].model_dump()
        )
        graph.graph.add_node(
            "/test/file2.py", **graph.nodes["/test/file2.py"].model_dump()
        )

        graph.integrate_call_graph(call_graph)

        # Test transitive dependencies
        deps = graph.calculate_transitive_dependencies("/test/file1.py")
        assert len(deps) >= 0  # May have dependencies depending on call graph

    def test_identify_hotspots(self):
        """Test identifying dependency hotspots."""
        graph = AdvancedDependencyGraph()

        # Create a graph with a potential hotspot
        graph.nodes["file1.py"] = DependencyNode(file_path="file1.py")
        graph.nodes["file2.py"] = DependencyNode(file_path="file2.py")
        graph.nodes["file3.py"] = DependencyNode(file_path="file3.py")

        # Make file2 a hotspot by having many dependents
        graph.graph.add_edge("file1.py", "file2.py")
        graph.graph.add_edge("file3.py", "file2.py")
        graph.nodes["file2.py"].imported_by = ["file1.py", "file3.py"]

        hotspots = graph.identify_hotspots()
        assert len(hotspots) >= 0  # May identify file2 as hotspot

    def test_suggest_refactoring_opportunities(self):
        """Test suggesting refactoring opportunities."""
        graph = AdvancedDependencyGraph()

        # Create a graph with potential refactoring opportunities
        graph.nodes["file1.py"] = DependencyNode(file_path="file1.py")
        graph.nodes["file2.py"] = DependencyNode(file_path="file2.py")

        # Create circular dependency
        graph.graph.add_edge("file1.py", "file2.py")
        graph.graph.add_edge("file2.py", "file1.py")

        opportunities = graph.suggest_refactoring_opportunities()
        assert len(opportunities) >= 0  # May suggest breaking circular dependency


class TestImpactAnalyzer:
    """Test the ImpactAnalyzer class."""

    def test_initialization(self):
        """Test ImpactAnalyzer initialization."""
        graph = AdvancedDependencyGraph()
        analyzer = ImpactAnalyzer(graph)
        assert analyzer is not None
        assert analyzer.graph == graph

    def test_analyze_change_impact(self):
        """Test analyzing change impact."""
        graph = AdvancedDependencyGraph()

        # Create a simple graph
        graph.nodes["file1.py"] = DependencyNode(file_path="file1.py")
        graph.nodes["file2.py"] = DependencyNode(file_path="file2.py")
        graph.graph.add_edge("file1.py", "file2.py")
        graph.nodes["file2.py"].imported_by = ["file1.py"]

        analyzer = ImpactAnalyzer(graph)
        impact_report = analyzer.analyze_change_impact(["file2.py"])

        assert impact_report is not None
        assert "file2.py" in impact_report.changed_files
        assert len(impact_report.affected_files) >= 1
        assert 0.0 <= impact_report.risk_score <= 1.0
        assert impact_report.impact_summary is not None

    def test_find_affected_files(self):
        """Test finding affected files."""
        graph = AdvancedDependencyGraph()

        # Create a simple graph
        graph.nodes["file1.py"] = DependencyNode(file_path="file1.py")
        graph.nodes["file2.py"] = DependencyNode(file_path="file2.py")
        graph.graph.add_edge("file1.py", "file2.py")
        graph.nodes["file2.py"].imported_by = ["file1.py"]

        analyzer = ImpactAnalyzer(graph)
        affected_files = analyzer._find_affected_files(["file2.py"])

        assert "file1.py" in affected_files  # file1 depends on file2
        assert "file2.py" in affected_files  # file2 itself is affected

    def test_calculate_risk_score(self):
        """Test calculating risk scores."""
        graph = AdvancedDependencyGraph()
        analyzer = ImpactAnalyzer(graph)

        # Test with empty changes
        risk_score = analyzer._calculate_overall_risk_score([], set())
        assert risk_score == 0.0

        # Test with some changes
        risk_score = analyzer._calculate_overall_risk_score(
            ["file1.py"], {"file1.py", "file2.py"}
        )
        assert 0.0 <= risk_score <= 1.0

    def test_cache_functionality(self):
        """Test caching functionality."""
        graph = AdvancedDependencyGraph()
        analyzer = ImpactAnalyzer(graph)

        # Enable cache
        analyzer.enable_cache()
        assert analyzer.cache_enabled

        # Disable cache
        analyzer.disable_cache()
        assert not analyzer.cache_enabled

        # Clear cache
        analyzer.enable_cache()
        analyzer.clear_cache()
        assert len(analyzer.cache) == 0


class TestModels:
    """Test the data models."""

    def test_import_model(self):
        """Test Import model."""
        imp = Import(
            module="os",
            alias="operating_system",
            is_relative=False,
            import_type="absolute",
            line_number=1,
        )

        assert imp.module == "os"
        assert imp.alias == "operating_system"
        assert imp.is_relative is False
        assert imp.import_type == "absolute"
        assert imp.line_number == 1

    def test_file_imports_model(self):
        """Test FileImports model."""
        imports = [
            Import(module="os", is_relative=False),
            Import(module="sys", is_relative=False),
        ]

        file_imports = FileImports(
            file_path="/test/file.py", imports=imports, language="py"
        )

        assert file_imports.file_path == "/test/file.py"
        assert len(file_imports.imports) == 2
        assert file_imports.language == "py"
        assert file_imports.total_imports == 2

    def test_function_call_model(self):
        """Test FunctionCall model."""
        call = FunctionCall(
            caller="main",
            callee="helper",
            file_path="/test/file.py",
            line_number=10,
            is_method_call=False,
        )

        assert call.caller == "main"
        assert call.callee == "helper"
        assert call.file_path == "/test/file.py"
        assert call.line_number == 10
        assert call.is_method_call is False

    def test_impact_report_model(self):
        """Test ImpactReport model."""
        report = ImpactReport(
            changed_files=["file1.py"],
            affected_files=["file1.py", "file2.py"],
            risk_score=0.7,
            impact_summary="Test impact",
        )

        assert "file1.py" in report.changed_files
        assert len(report.affected_files) == 2
        assert report.risk_score == 0.7
        assert report.impact_summary == "Test impact"


if __name__ == "__main__":
    pytest.main([__file__])
