import pytest
from typing import List, Dict
from unittest.mock import Mock

from repomap_tool.code_analysis.density_analyzer import (
    DensityAnalyzer,
    IdentifierCategory,
    FileDensity,
    PackageDensity,
)
from repomap_tool.code_analysis.models import CodeTag
from repomap_tool.code_analysis.tree_sitter_parser import TreeSitterParser


# Mock TreeSitterParser for controlled tag output
@pytest.fixture
def mock_tree_sitter_parser():
    mock_parser = Mock(spec=TreeSitterParser)
    return mock_parser


# Fixture for DensityAnalyzer with mocked parser
@pytest.fixture
def density_analyzer(mock_tree_sitter_parser):
    return DensityAnalyzer(tree_sitter_parser=mock_tree_sitter_parser)


def create_mock_tags(tag_data: List[Dict]) -> List[CodeTag]:
    tags = []
    for data in tag_data:
        tags.append(
            CodeTag(
                name=data["name"], kind=data["kind"], file="/app/test_file.py", line=1
            )
        )
    return tags


def test_identifier_category_enum():
    assert IdentifierCategory.CLASSES == "classes"
    assert IdentifierCategory.FUNCTIONS == "functions"
    assert IdentifierCategory.METHODS == "methods"
    assert IdentifierCategory.VARIABLES == "variables"
    assert IdentifierCategory.IMPORTS == "imports"


def test_map_tag_to_category_python(density_analyzer):
    assert (
        density_analyzer._map_tag_to_category("name.definition.class")
        == IdentifierCategory.CLASSES
    )
    assert (
        density_analyzer._map_tag_to_category("function.definition")
        == IdentifierCategory.FUNCTIONS
    )
    assert (
        density_analyzer._map_tag_to_category("method.definition")
        == IdentifierCategory.METHODS
    )
    assert (
        density_analyzer._map_tag_to_category("variable.assignment")
        == IdentifierCategory.VARIABLES
    )
    assert (
        density_analyzer._map_tag_to_category("import_statement")
        == IdentifierCategory.IMPORTS
    )
    assert density_analyzer._map_tag_to_category("call") is None


def test_map_tag_to_category_javascript(density_analyzer):
    assert (
        density_analyzer._map_tag_to_category("class_declaration")
        == IdentifierCategory.CLASSES
    )
    assert (
        density_analyzer._map_tag_to_category("function_declaration")
        == IdentifierCategory.FUNCTIONS
    )
    assert (
        density_analyzer._map_tag_to_category("method_definition")
        == IdentifierCategory.METHODS
    )
    assert (
        density_analyzer._map_tag_to_category("variable_declarator")
        == IdentifierCategory.VARIABLES
    )
    assert (
        density_analyzer._map_tag_to_category("import_statement")
        == IdentifierCategory.IMPORTS
    )
    assert density_analyzer._map_tag_to_category("call_expression") is None


def test_categorize_tags(density_analyzer, mock_tree_sitter_parser):
    file_path = "/app/test_file.py"
    project_root = "/app"
    tag_data = [
        {"name": "MyClass", "kind": "name.definition.class"},
        {"name": "my_func", "kind": "function.definition"},
        {"name": "my_method", "kind": "method.definition"},
        {"name": "x", "kind": "variable.assignment"},
        {"name": "np", "kind": "import_statement"},
        {"name": "another_var", "kind": "variable.assignment"},
        {"name": "another_func_call", "kind": "call"},  # Should be ignored
    ]
    mock_tree_sitter_parser.get_tags.return_value = create_mock_tags(tag_data)

    file_density = density_analyzer.analyze_file(file_path, project_root)

    assert file_density.file_path == file_path
    assert file_density.relative_path == "test_file.py"
    assert file_density.total_identifiers == 6
    assert file_density.primary_identifiers == 3
    assert file_density.categories == {
        IdentifierCategory.CLASSES: 1,
        IdentifierCategory.FUNCTIONS: 1,
        IdentifierCategory.METHODS: 1,
        IdentifierCategory.VARIABLES: 2,
        IdentifierCategory.IMPORTS: 1,
    }


def test_analyze_files(density_analyzer, mock_tree_sitter_parser):
    file1_path = "/app/file1.py"
    file2_path = "/app/file2.py"
    project_root = "/app"

    mock_tree_sitter_parser.get_tags.side_effect = [
        create_mock_tags(
            [{"name": "A", "kind": "class"}, {"name": "b", "kind": "variable"}]
        ),  # 2 identifiers
        create_mock_tags([{"name": "C", "kind": "function"}]),  # 1 identifier
    ]

    file_paths = [file1_path, file2_path]
    results = density_analyzer.analyze_files(file_paths, project_root)

    assert len(results) == 2
    assert results[0].file_path == file1_path  # Sorted by density (descending)
    assert results[0].total_identifiers == 2
    assert results[1].file_path == file2_path
    assert results[1].total_identifiers == 1


def test_analyze_package(density_analyzer, mock_tree_sitter_parser):
    file1_path = "/app/package_a/file1.py"
    file2_path = "/app/package_a/file2.py"
    file3_path = "/app/package_a/file3.py"
    project_root = "/app"
    package_path = "package_a"

    mock_tree_sitter_parser.get_tags.side_effect = [
        create_mock_tags(
            [{"name": "A", "kind": "class"}, {"name": "b", "kind": "variable"}]
        ),  # 2 identifiers
        create_mock_tags(
            [
                {"name": "C", "kind": "function"},
                {"name": "d", "kind": "import"},
                {"name": "e", "kind": "method"},
            ]
        ),  # 3 identifiers
        create_mock_tags([{"name": "F", "kind": "variable"}]),  # 1 identifier
    ]

    file_paths = [file1_path, file2_path, file3_path]
    package_density = density_analyzer.analyze_package(
        package_path, file_paths, project_root
    )

    assert package_density.package_path == package_path
    assert package_density.total_identifiers == 6
    assert package_density.file_count == 3
    assert f"{package_density.avg_identifiers_per_file:.1f}" == "2.0"
    assert package_density.categories == {
        IdentifierCategory.CLASSES: 1,
        IdentifierCategory.FUNCTIONS: 1,
        IdentifierCategory.METHODS: 1,
        IdentifierCategory.VARIABLES: 2,
        IdentifierCategory.IMPORTS: 1,
    }
    assert len(package_density.files) == 3
    assert (
        package_density.files[0].relative_path == "package_a/file2.py"
    )  # Sorted by density
    assert package_density.files[1].relative_path == "package_a/file1.py"
    assert package_density.files[2].relative_path == "package_a/file3.py"


def test_analyze_package_empty_files(density_analyzer, mock_tree_sitter_parser):
    file_path = "/app/package_b/empty.py"
    project_root = "/app"
    package_path = "package_b"

    mock_tree_sitter_parser.get_tags.return_value = create_mock_tags([])  # No tags

    file_paths = [file_path]
    package_density = density_analyzer.analyze_package(
        package_path, file_paths, project_root
    )

    assert package_density.total_identifiers == 0
    assert package_density.file_count == 0
    assert package_density.avg_identifiers_per_file == 0.0
    assert not package_density.files
    assert all(count == 0 for count in package_density.categories.values())
