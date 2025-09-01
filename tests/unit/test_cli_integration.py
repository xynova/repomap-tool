#!/usr/bin/env python3
"""
Integration tests for CLI commands using click.testing.CliRunner.

This module tests actual CLI command execution and exception handling
to achieve higher test coverage above 70%.
"""

import pytest
import tempfile
import json
from unittest.mock import patch, Mock
from pathlib import Path
from click.testing import CliRunner

from src.repomap_tool.cli import cli


class TestCLIIntegration:
    """Test actual CLI command execution and exception handling."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        self.test_project = Path(".")

    @patch('src.repomap_tool.cli.DockerRepoMap')
    def test_analyze_command_exception_handling(self, mock_repo_map):
        """Test analyze command with real exception handling."""
        # Mock DockerRepoMap to raise an exception
        mock_repo_map.side_effect = Exception("Test analysis error")
        
        # Test the actual CLI command
        result = self.runner.invoke(cli, ['analyze', str(self.test_project)])
        
        # Verify error handling
        assert result.exit_code == 1
        assert "Error: Test analysis error" in result.output

    @patch('src.repomap_tool.cli.DockerRepoMap')
    def test_search_command_exception_handling(self, mock_repo_map):
        """Test search command with real exception handling."""
        # Mock DockerRepoMap to raise an exception
        mock_repo_map.side_effect = Exception("Test search error")
        
        # Test the actual CLI command
        result = self.runner.invoke(cli, ['search', str(self.test_project), 'test_query'])
        
        # Verify error handling
        assert result.exit_code == 1
        assert "Error: Test search error" in result.output

    @patch('src.repomap_tool.cli.create_default_config')
    def test_config_command_exception_handling(self, mock_create_config):
        """Test config command with real exception handling."""
        # Mock create_default_config to raise an exception
        mock_create_config.side_effect = Exception("Test config error")
        
        # Test the actual CLI command
        result = self.runner.invoke(cli, ['config', str(self.test_project)])
        
        # Verify error handling
        assert result.exit_code == 1
        assert "Error: Test config error" in result.output

    @patch('src.repomap_tool.cli.DockerRepoMap')
    def test_performance_command_exception_handling(self, mock_repo_map):
        """Test performance command with real exception handling."""
        # Mock DockerRepoMap to raise an exception
        mock_repo_map.side_effect = Exception("Test performance error")
        
        # Test the actual CLI command
        result = self.runner.invoke(cli, ['performance', str(self.test_project)])
        
        # Verify error handling
        assert result.exit_code == 1
        assert "Error: Test performance error" in result.output

    @patch('src.repomap_tool.cli.DockerRepoMap')
    def test_performance_command_monitoring_disabled(self, mock_repo_map):
        """Test performance command when monitoring is disabled."""
        # Mock the RepoMap instance
        mock_instance = Mock()
        mock_instance.get_performance_metrics.return_value = {"monitoring_disabled": True}
        mock_repo_map.return_value = mock_instance
        
        # Test the actual CLI command
        result = self.runner.invoke(cli, ['performance', str(self.test_project)])
        
        # Verify output
        assert result.exit_code == 0
        assert "Performance monitoring is disabled" in result.output

    @patch('src.repomap_tool.cli.DockerRepoMap')
    def test_performance_command_with_error_metrics(self, mock_repo_map):
        """Test performance command when metrics contain an error."""
        # Mock the RepoMap instance
        mock_instance = Mock()
        mock_instance.get_performance_metrics.return_value = {"error": "Test metrics error"}
        mock_repo_map.return_value = mock_instance
        
        # Test the actual CLI command
        result = self.runner.invoke(cli, ['performance', str(self.test_project)])
        
        # Verify output
        assert result.exit_code == 0
        assert "Error getting metrics: Test metrics error" in result.output

    @patch('src.repomap_tool.cli.DockerRepoMap')
    def test_performance_command_with_full_metrics(self, mock_repo_map):
        """Test performance command with complete metrics data."""
        # Mock realistic performance metrics
        mock_metrics = {
            "configuration": {
                "max_workers": 4,
                "parallel_threshold": 10,
                "enable_progress": True,
                "enable_monitoring": True
            },
            "processing_stats": {
                "total_files": 100,
                "successful_files": 95,
                "failed_files": 5,
                "success_rate": 95.0,
                "total_identifiers": 1000,
                "processing_time": 2.5,
                "files_per_second": 40.0
            },
            "file_size_stats": {
                "total_size_mb": 10.5,
                "avg_size_kb": 105.0,
                "largest_file_kb": 500.0
            }
        }
        
        # Mock the RepoMap instance
        mock_instance = Mock()
        mock_instance.get_performance_metrics.return_value = mock_metrics
        mock_repo_map.return_value = mock_instance
        
        # Test the actual CLI command
        result = self.runner.invoke(cli, ['performance', str(self.test_project)])
        
        # Verify output contains table data
        assert result.exit_code == 0
        assert "Performance Metrics" in result.output
        assert "Max Workers" in result.output
        assert "Total Files" in result.output
        assert "Total Size (MB)" in result.output

    def test_config_command_with_output_file(self):
        """Test config command with output file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            # Test the actual CLI command with output file
            result = self.runner.invoke(cli, ['config', str(self.test_project), '--output', temp_file_path])
            
            # Verify success
            assert result.exit_code == 0
            assert "Configuration saved to:" in result.output
            assert temp_file_path in result.output
            
            # Verify file was created and contains valid JSON
            with open(temp_file_path, 'r') as f:
                config_data = json.load(f)
            
            # Verify config structure
            assert "project_root" in config_data
            assert "fuzzy_match" in config_data
            assert "semantic_match" in config_data
            assert "performance" in config_data
            
        finally:
            # Clean up
            Path(temp_file_path).unlink(missing_ok=True)

    def test_config_command_without_output_file(self):
        """Test config command without output file (display to console)."""
        # Test the actual CLI command without output file
        result = self.runner.invoke(cli, ['config', str(self.test_project)])
        
        # Verify success
        assert result.exit_code == 0
        assert "Generated Configuration" in result.output
        assert "project_root" in result.output
        assert "fuzzy_match" in result.output

    def test_version_command(self):
        """Test version command."""
        # Test the actual CLI command
        result = self.runner.invoke(cli, ['version'])
        
        # Verify output
        assert result.exit_code == 0
        assert "Docker RepoMap" in result.output
        assert "Version: 0.1.0" in result.output

    def test_analyze_command_with_invalid_project_path(self):
        """Test analyze command with invalid project path."""
        # Test with non-existent path
        result = self.runner.invoke(cli, ['analyze', '/non/existent/path'])
        
        # Should fail due to path validation
        assert result.exit_code != 0

    def test_search_command_with_invalid_project_path(self):
        """Test search command with invalid project path."""
        # Test with non-existent path
        result = self.runner.invoke(cli, ['search', '/non/existent/path', 'test'])
        
        # Should fail due to path validation
        assert result.exit_code != 0

    def test_performance_command_with_invalid_project_path(self):
        """Test performance command with invalid project path."""
        # Test with non-existent path
        result = self.runner.invoke(cli, ['performance', '/non/existent/path'])
        
        # Should fail due to path validation
        assert result.exit_code != 0

    def test_config_command_with_invalid_project_path(self):
        """Test config command with invalid project path."""
        # Test with non-existent path
        result = self.runner.invoke(cli, ['config', '/non/existent/path'])
        
        # Should fail due to path validation
        assert result.exit_code != 0

    def test_analyze_command_help(self):
        """Test analyze command help."""
        # Test help output
        result = self.runner.invoke(cli, ['analyze', '--help'])
        
        # Verify help text
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "PROJECT_PATH" in result.output
        assert "Options:" in result.output

    def test_search_command_help(self):
        """Test search command help."""
        # Test help output
        result = self.runner.invoke(cli, ['search', '--help'])
        
        # Verify help text
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "PROJECT_PATH" in result.output
        assert "QUERY" in result.output

    def test_config_command_help(self):
        """Test config command help."""
        # Test help output
        result = self.runner.invoke(cli, ['config', '--help'])
        
        # Verify help text
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "PROJECT_PATH" in result.output
        assert "Options:" in result.output

    def test_performance_command_help(self):
        """Test performance command help."""
        # Test help output
        result = self.runner.invoke(cli, ['performance', '--help'])
        
        # Verify help text
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "PROJECT_PATH" in result.output
        assert "Options:" in result.output

    def test_version_command_help(self):
        """Test version command help."""
        # Test help output
        result = self.runner.invoke(cli, ['version', '--help'])
        
        # Verify help text
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "Show version information" in result.output


if __name__ == "__main__":
    pytest.main([__file__])
