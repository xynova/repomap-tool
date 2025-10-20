import pytest
from click.testing import CliRunner
import click
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
from repomap_tool.models import SuccessResponse, OutputConfig, ErrorResponse # Import ErrorResponse
from repomap_tool.cli.output.manager import OutputManager # Import OutputManager to mock it correctly

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


# Fixture for CliRunner - use the one that injects the container
@pytest.fixture
def runner(cli_runner_with_container: CliRunner):
    return cli_runner_with_container


def test_density_command_file_scope_text_output(
    runner,
    mock_density_controller,
    mock_file_density_view_model,
):
    with patch("repomap_tool.core.container.create_container") as mock_create_container:
        # Mock the entire container and its density_controller provider
        mock_container_instance = MagicMock()
        mock_create_container.return_value = mock_container_instance
        mock_container_instance.density_controller.return_value = mock_density_controller
        
        # Also mock the container in the Click context
        def mock_cli_call(*args, **kwargs):
            ctx = click.Context(cli, obj={})
            ctx.obj["container"] = mock_container_instance
            ctx.obj["no_color"] = True
            return cli.invoke(ctx, args, **kwargs)
        
        with patch("repomap_tool.cli.main.cli.__call__", new=mock_cli_call):
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
        # Mock the entire container and its density_controller provider
        mock_container_instance = MagicMock()
        mock_create_container.return_value = mock_container_instance
        mock_container_instance.density_controller.return_value = mock_density_controller

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
    session_container,
):
    # Mock the entire container and its density_controller provider
    mock_container_instance = MagicMock()
    mock_container_instance.density_controller.return_value = mock_density_controller

    mock_density_controller.execute.return_value = DensityAnalysisViewModel(
        scope="file",
        results=[mock_file_density_view_model],
        total_files_analyzed=1,
        limit=10,
        min_identifiers=1,
        analysis_summary={},
    )

    # Mock the OutputManager directly via the container's provider
    mock_output_manager = MagicMock(spec=OutputManager)

    with (
        session_container.density_controller.override(mock_density_controller),
        session_container.output_manager.override(mock_output_manager),
    ):
        result = runner.invoke(
            cli, ["inspect", "density", ".", "--scope", "file", "-o", "json"]
        )

        assert result.exit_code == 0, f"CLI command failed with output: {result.output}"

        # Assert that display was called once (for the ViewModel)
        mock_output_manager.display.assert_called_once()
        called_args, called_kwargs = mock_output_manager.display.call_args
        response = called_args[0]
        output_config = called_args[1]

        assert isinstance(response, DensityAnalysisViewModel)
        assert isinstance(output_config, OutputConfig)
        assert output_config.format.value == "json"

        # Assert that display_success was also called
        mock_output_manager.display_success.assert_called_once()
        success_args, success_kwargs = mock_output_manager.display_success.call_args
        assert "density analysis completed" in success_args[0].lower()
        assert success_args[1].format.value == "json"


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
