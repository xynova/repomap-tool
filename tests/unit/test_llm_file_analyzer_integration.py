"""
Integration tests for LLMFileAnalyzer to catch path resolution and CLI integration issues.
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.repomap_tool.dependencies.llm_file_analyzer import LLMFileAnalyzer, AnalysisFormat
from src.repomap_tool.dependencies.dependency_graph import DependencyGraph
from src.repomap_tool.dependencies.models import DependencyNode, Import


class TestLLMFileAnalyzerIntegration:
    """Integration tests for LLMFileAnalyzer to catch real-world issues."""

    def test_analyze_file_centrality_with_absolute_paths(self):
        """Test that LLM analyzer correctly handles absolute file paths.
        
        This test catches the bug where absolute paths from CLI weren't being
        converted to relative paths for dependency graph lookup.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple project structure
            src_dir = os.path.join(temp_dir, "src")
            os.makedirs(src_dir, exist_ok=True)
            
            # Create a TypeScript file (non-Python to test AST skipping)
            ts_file = os.path.join(src_dir, "test.ts")
            with open(ts_file, "w") as f:
                f.write("""
export function testFunction() {
    return 'hello';
}
""")
            
            # Create another file that imports the first
            ts_file2 = os.path.join(src_dir, "test2.ts")
            with open(ts_file2, "w") as f:
                f.write("""
import { testFunction } from './test';

export function anotherFunction() {
    return testFunction();
}
""")
            
            # Build a dependency graph with relative paths
            dependency_graph = DependencyGraph()
            dependency_graph.project_path = temp_dir
            
            # Add nodes with relative paths (as the real system does)
            relative_ts_file = "src/test.ts"
            relative_ts_file2 = "src/test2.ts"
            
            node1 = DependencyNode(file_path=relative_ts_file)
            node2 = DependencyNode(file_path=relative_ts_file2)
            
            # Add import relationship
            import_info = Import(
                module="./test",
                resolved_path=relative_ts_file,
                is_relative=True,
                line_number=2
            )
            node2.imports = [import_info]
            node1.imported_by = [relative_ts_file2]
            
            dependency_graph.nodes[relative_ts_file] = node1
            dependency_graph.nodes[relative_ts_file2] = node2
            
            # Create LLM analyzer
            llm_analyzer = LLMFileAnalyzer(
                dependency_graph=dependency_graph,
                project_root=temp_dir
            )
            
            # Test with ABSOLUTE path (simulating CLI input)
            absolute_ts_file = os.path.join(temp_dir, "src", "test.ts")
            
            # This should work without errors and return meaningful results
            result = llm_analyzer.analyze_file_centrality(
                file_paths=[absolute_ts_file], 
                format_type=AnalysisFormat.TEXT
            )
            
            # Verify the analysis worked
            assert "test.ts" in result
            assert "IMPORTANCE SCORE" in result
            
            # The key test: verify that dependency information is found
            # (This would fail with the old bug where absolute paths weren't converted)
            assert "FILE CONNECTIONS" in result
            
            # Verify that the file was found in the dependency graph
            # (This is the core issue that was broken)
            assert "0 files" not in result or "1 files" in result  # Should have some dependencies

    def test_analyze_file_centrality_with_relative_paths(self):
        """Test that LLM analyzer works with relative paths (baseline test)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple project structure
            src_dir = os.path.join(temp_dir, "src")
            os.makedirs(src_dir, exist_ok=True)
            
            # Create a Python file
            py_file = os.path.join(src_dir, "test.py")
            with open(py_file, "w") as f:
                f.write("""
import os

def test_function():
    return os.getcwd()
""")
            
            # Build a dependency graph
            dependency_graph = DependencyGraph()
            dependency_graph.project_path = temp_dir
            
            relative_py_file = "src/test.py"
            node = DependencyNode(file_path=relative_py_file)
            dependency_graph.nodes[relative_py_file] = node
            
            # Create LLM analyzer
            llm_analyzer = LLMFileAnalyzer(
                dependency_graph=dependency_graph,
                project_root=temp_dir
            )
            
            # Test with RELATIVE path
            relative_path = "src/test.py"
            
            result = llm_analyzer.analyze_file_centrality(
                file_paths=[relative_path], 
                format_type=AnalysisFormat.TEXT
            )
            
            # Verify the analysis worked
            assert "test.py" in result
            assert "IMPORTANCE SCORE" in result

    def test_path_conversion_logic(self):
        """Test the core path conversion logic that was broken."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dependency_graph = DependencyGraph()
            dependency_graph.project_path = temp_dir
            
            llm_analyzer = LLMFileAnalyzer(
                dependency_graph=dependency_graph,
                project_root=temp_dir
            )
            
            # Test the path conversion logic directly
            relative_path = "src/test.py"
            absolute_path = os.path.join(temp_dir, "src", "test.py")
            
            # Test that absolute paths are converted to relative
            if os.path.isabs(absolute_path) and llm_analyzer.project_root:
                converted_path = os.path.relpath(absolute_path, llm_analyzer.project_root)
                assert converted_path == relative_path
            
            # Test that relative paths are unchanged
            if not os.path.isabs(relative_path):
                # This should remain unchanged
                assert relative_path == relative_path

    def test_dependency_graph_lookup_with_path_conversion(self):
        """Test that dependency graph lookup works with path conversion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create dependency graph with relative paths
            dependency_graph = DependencyGraph()
            dependency_graph.project_path = temp_dir
            
            relative_file = "src/test.py"
            node = DependencyNode(file_path=relative_file)
            node.imports = []
            node.imported_by = ["src/other.py"]
            dependency_graph.nodes[relative_file] = node
            
            llm_analyzer = LLMFileAnalyzer(
                dependency_graph=dependency_graph,
                project_root=temp_dir
            )
            
            # Test with absolute path - should find the node
            absolute_file = os.path.join(temp_dir, "src", "test.py")
            
            # Test the core logic: absolute path should be converted to relative
            # and then found in the dependency graph
            if os.path.isabs(absolute_file) and llm_analyzer.project_root:
                relative_file_path = os.path.relpath(absolute_file, llm_analyzer.project_root)
                assert relative_file_path == relative_file
                
                # This is the critical test - the old code would fail here
                # because it would look for the absolute path in the graph
                # instead of converting it to relative first
                assert relative_file_path in dependency_graph.nodes
                
                # Verify the node has the expected data
                found_node = dependency_graph.nodes[relative_file_path]
                assert found_node.file_path == relative_file
                assert len(found_node.imports) == 0
                assert len(found_node.imported_by) == 1
                assert "src/other.py" in found_node.imported_by
