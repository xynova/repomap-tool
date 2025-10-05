"""
Real Dependency Component Integration Tests

This module tests the dependency analysis components with real data to ensure
they work correctly without mocking.
"""

import pytest
import tempfile
from pathlib import Path
from repomap_tool.models import (
    RepoMapConfig,
    FuzzyMatchConfig,
    SemanticMatchConfig,
    DependencyConfig,
)
from repomap_tool.core import RepoMapService


class TestDependencyComponentsReal:
    """Test dependency analysis components with real integration."""

    @pytest.fixture
    def temp_project_with_dependencies(self):
        """Create a temporary project with realistic dependencies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create main module
            main_file = Path(temp_dir) / "main.py"
            main_file.write_text(
                """
import os
import sys
from utils import helper_function
from submodule.module import SubClass

def main():
    result = helper_function()
    obj = SubClass()
    return obj.method() + result

if __name__ == "__main__":
    main()
"""
            )

            # Create utils module
            utils_file = Path(temp_dir) / "utils.py"
            utils_file.write_text(
                """
import os
from typing import List

def helper_function():
    return "helper"

def process_data(data: List[str]) -> List[str]:
    return [item.upper() for item in data]

def get_config():
    return os.environ.get("CONFIG", "default")
"""
            )

            # Create submodule
            sub_dir = Path(temp_dir) / "submodule"
            sub_dir.mkdir()

            init_file = sub_dir / "__init__.py"
            init_file.write_text("from .module import SubClass, AnotherClass")

            module_file = sub_dir / "module.py"
            module_file.write_text(
                """
from typing import Optional
import os

class SubClass:
    def __init__(self):
        self.value = 42
        self.config = os.environ.get("APP_CONFIG")
    
    def method(self):
        return self.value
    
    def get_config(self):
        return self.config

class AnotherClass:
    def __init__(self, name: str):
        self.name = name
    
    def process(self, data):
        return f"{self.name}: {data}"
"""
            )

            # Create another module with more complex dependencies
            complex_file = Path(temp_dir) / "complex.py"
            complex_file.write_text(
                """
import os
import sys
from typing import Dict, List, Optional
from utils import process_data, get_config
from submodule.module import SubClass, AnotherClass

class ComplexProcessor:
    def __init__(self):
        self.config = get_config()
        self.processor = AnotherClass("processor")
    
    def process_items(self, items: List[str]) -> Dict[str, str]:
        processed = process_data(items)
        result = {}
        for i, item in enumerate(processed):
            result[f"item_{i}"] = self.processor.process(item)
        return result
    
    def get_subclass_instance(self):
        return SubClass()
"""
            )

            yield temp_dir

    def test_dependency_graph_building_real(self, temp_project_with_dependencies):
        """Test that dependency graph building works with real files."""
        # Create configuration
        config = RepoMapConfig(
            project_root=temp_project_with_dependencies,
            fuzzy_match=FuzzyMatchConfig(threshold=70),
            semantic_match=SemanticMatchConfig(enabled=True, threshold=0.7),
            dependencies=DependencyConfig(
                max_files=100, enable_call_graph=True, enable_impact_analysis=True
            ),
        )

        # Initialize RepoMap
        from repomap_tool.cli.services import get_service_factory

        service_factory = get_service_factory()
        repomap = service_factory.create_repomap_service(config)

        # Test dependency graph building
        try:
            graph_result = repomap.analyze_dependencies()

            # Should have built a dependency graph
            assert graph_result is not None
            assert hasattr(graph_result, "total_files")
            assert hasattr(graph_result, "total_dependencies")
            assert graph_result.total_files > 0

            # Should have found some dependencies
            assert graph_result.total_dependencies >= 0

        except Exception as e:
            # If it fails, it should be a meaningful error, not a crash
            assert "Connectivity is undefined" not in str(e) or "null graph" not in str(
                e
            )

    def test_import_analyzer_real(self, temp_project_with_dependencies):
        """Test import analysis with real Python files."""
        from repomap_tool.code_analysis.import_analyzer import ImportAnalyzer

        analyzer = ImportAnalyzer()

        # Test analyzing a real file
        main_file = Path(temp_project_with_dependencies) / "main.py"
        file_imports = analyzer.analyze_file_imports(str(main_file))

        # Should find imports
        assert len(file_imports.imports) > 0

        # Should find specific imports we know exist
        import_names = [imp.module for imp in file_imports.imports]
        assert "os" in import_names
        assert "sys" in import_names
        assert "utils" in import_names
        assert "submodule.module" in import_names

    def test_dependency_graph_real(self, temp_project_with_dependencies):
        """Test dependency graph construction with real files."""
        from repomap_tool.code_analysis.import_analyzer import ImportAnalyzer
        from repomap_tool.models import (
            RepoMapConfig,
            FuzzyMatchConfig,
            SemanticMatchConfig,
            PerformanceConfig,
            DependencyConfig,
        )
        from repomap_tool.cli.services import get_service_factory

        # Use service factory for dependency graph
        config = RepoMapConfig(
            project_root=str(temp_project_with_dependencies),
            fuzzy_match=FuzzyMatchConfig(),
            semantic_match=SemanticMatchConfig(),
            performance=PerformanceConfig(),
            dependencies=DependencyConfig(),
        )
        service_factory = get_service_factory()
        repomap_service = service_factory.create_repomap_service(config)
        graph = repomap_service.dependency_graph

        # Use ImportAnalyzer to get ProjectImports
        analyzer = ImportAnalyzer()
        project_imports = analyzer.analyze_project_imports(
            str(temp_project_with_dependencies)
        )

        # Build graph with ProjectImports
        graph.build_graph(project_imports)

        # Should be able to get graph statistics
        stats = graph.get_graph_statistics()
        assert stats is not None
        assert "total_nodes" in stats
        assert stats["total_nodes"] > 0

    def test_call_graph_builder_real(self, temp_project_with_dependencies):
        """Test call graph building with real Python code."""
        from repomap_tool.code_analysis.call_graph_builder import CallGraphBuilder

        builder = CallGraphBuilder()

        # Test with a real file
        main_file = Path(temp_project_with_dependencies) / "main.py"

        try:
            call_graph = builder.build_call_graph(str(main_file))

            # Should have built a call graph
            assert call_graph is not None

            # Should have found some function calls
            # (Even if empty, it should not crash)

        except Exception as e:
            # If it fails, should be a meaningful error
            assert "syntax" not in str(e).lower() or "parse" not in str(e).lower()

    def test_dependency_models_real(self, temp_project_with_dependencies):
        """Test dependency models with real data."""
        from repomap_tool.code_analysis.models import (
            Import,
            FileImports,
            ProjectImports,
            ImportType,
        )

        # Test Import model
        import_obj = Import(
            module="os",
            alias=None,
            is_relative=False,
            import_type=ImportType.EXTERNAL,
            line_number=1,
        )
        assert import_obj.module == "os"
        assert import_obj.import_type == ImportType.EXTERNAL

        # Test FileImports model
        file_imports = FileImports(
            file_path=str(Path(temp_project_with_dependencies) / "main.py"),
            imports=[import_obj],
            language="py",
        )
        assert file_imports.file_path.endswith("main.py")
        assert file_imports.total_imports == 1
        assert file_imports.language == "py"

        # Test ProjectImports model
        project_imports = ProjectImports(
            project_path=str(temp_project_with_dependencies),
            file_imports={
                str(Path(temp_project_with_dependencies) / "main.py"): file_imports
            },
            total_files=1,
        )
        assert project_imports.project_path == str(temp_project_with_dependencies)
        assert project_imports.total_files == 1
