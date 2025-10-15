import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
import json
import os

from repomap_tool.cli import cli
from repomap_tool.code_analysis.density_analyzer import (
    FileDensity,
    PackageDensity,
    IdentifierCategory,
)
from repomap_tool.cli.controllers.view_models import (
    DensityAnalysisViewModel,
    FileDensityViewModel,
    PackageDensityViewModel,
)


# Mock data for DensityController
@pytest.fixture
def mock_file_density_view_model():
    return FileDensityViewModel(
        file_path="/test_project/src/main.py",
        relative_path="src/main.py",
        total_identifiers=10,
        primary_identifiers=7,
        categories={
            IdentifierCategory.CLASSES: 1,
            IdentifierCategory.FUNCTIONS: 3,
            IdentifierCategory.METHODS: 3,
            IdentifierCategory.VARIABLES: 2,
            IdentifierCategory.IMPORTS: 1,
        },
    )


@pytest.fixture
def mock_package_density_view_model(mock_file_density_view_model):
    return PackageDensityViewModel(
        package_path="src",
        total_identifiers=15,
        file_count=2,
        avg_identifiers_per_file=7.5,
        files=[mock_file_density_view_model],
        categories={
            IdentifierCategory.CLASSES: 1,
            IdentifierCategory.FUNCTIONS: 4,
            IdentifierCategory.METHODS: 3,
            IdentifierCategory.VARIABLES: 4,
            IdentifierCategory.IMPORTS: 3,
        },
    )


@pytest.fixture
def mock_density_controller():
    controller = MagicMock()
    controller.config = MagicMock()
    controller.config.output_format = "text"
    return controller


# Fixture for CliRunner
@pytest.fixture
def runner():
    return CliRunner()


def test_density_command_file_scope_text_output(
    runner,
    mock_density_controller,
    mock_file_density_view_model,
):
    with patch("repomap_tool.core.container.create_container") as mock_create_container:
        mock_create_container.return_value.density_controller.return_value = (
            mock_density_controller
        )
        mock_density_controller.execute.return_value = DensityAnalysisViewModel(
            scope="file",
            results=[mock_file_density_view_model],
            total_files_analyzed=1,
            limit=10,
            min_identifiers=1,
            analysis_summary={
                "total_files": 1,
                "files_with_identifiers": 1,
                "avg_identifiers_per_file": 10.0,
            },
        )

        result = runner.invoke(
            cli, ["inspect", "density", ".", "--scope", "file", "-o", "text"]
        )

        assert result.exit_code == 0
        assert "CODE DENSITY ANALYSIS" in result.output
        assert "FILE DENSITY (by identifier count)" in result.output
        assert "src/main.py" in result.output
        assert "Total: 10 identifiers" in result.output
        assert "Classes: 1" in result.output
        assert "Functions: 3" in result.output
        assert "Methods: 3" in result.output
        assert "Variables: 2" in result.output
        assert "Imports: 1" in result.output


def test_density_command_package_scope_text_output(
    runner,
    mock_density_controller,
    mock_package_density_view_model,
):
    with patch("repomap_tool.core.container.create_container") as mock_create_container:
        mock_create_container.return_value.density_controller.return_value = (
            mock_density_controller
        )
        mock_density_controller.execute.return_value = DensityAnalysisViewModel(
            scope="package",
            results=[mock_package_density_view_model],
            total_files_analyzed=2,
            limit=10,
            min_identifiers=1,
            analysis_summary={
                "total_packages": 1,
                "packages_with_identifiers": 1,
                "total_files": 2,
            },
        )

        result = runner.invoke(
            cli, ["inspect", "density", ".", "--scope", "package", "-o", "text"]
        )

        assert result.exit_code == 0
        assert "CODE DENSITY ANALYSIS" in result.output
        assert "PACKAGE DENSITY (by total identifiers)" in result.output
        assert "src/" in result.output
        assert "Total: 15 identifiers across 2 files" in result.output
        assert "Avg per file: 7.5" in result.output
        assert (
            "Categories: {'classes': 1, 'functions': 4, 'methods': 3, 'variables': 4, 'imports': 3}"
            in result.output
        )  # Full dictionary output
        assert "Top files in package:" in result.output
        assert "src/main.py (10)" in result.output


def test_density_command_json_output(
    runner,
    mock_density_controller,
    mock_file_density_view_model,
):
    with (
        patch("repomap_tool.core.container.create_container") as mock_create_container,
        patch("repomap_tool.cli.output.get_output_manager") as mock_get_output_manager,
    ):

        mock_create_container.return_value.density_controller.return_value = (
            mock_density_controller
        )
        mock_density_controller.execute.return_value = DensityAnalysisViewModel(
            scope="file",
            results=[mock_file_density_view_model],
            total_files_analyzed=1,
            limit=10,
            min_identifiers=1,
            analysis_summary={},
        )

        # Mock the display method of OutputManager to capture JSON output
        mock_output_manager_instance = MagicMock()
        mock_get_output_manager.return_value = mock_output_manager_instance

        runner.invoke(
            cli, ["inspect", "density", ".", "--scope", "file", "-o", "json"]
        )

        # Assert that display was called with the correct ViewModel and format
        mock_output_manager_instance.display.assert_called_once()
        called_args, called_kwargs = mock_output_manager_instance.display.call_args
        displayed_view_model = called_args[0]
        output_config = called_args[1]

        assert isinstance(displayed_view_model, DensityAnalysisViewModel)
        assert output_config.format.value == "json"


def test_density_command_error_handling(runner):
    with patch("repomap_tool.core.container.create_container") as mock_create_container:
        mock_create_container.side_effect = Exception("DI Container Error")

        result = runner.invoke(cli, ["inspect", "density", ".", "-o", "text"])

        assert result.exit_code == 1
        assert "Error: DI Container Error" in result.output


def test_density_command_missing_project_path(runner):
    result = runner.invoke(cli, ["inspect", "density"])

    assert (
        result.exit_code == 0
    )  # Default project path is ".", so it should not exit with error
    assert "CODE DENSITY ANALYSIS" in result.output
