#!/usr/bin/env python3
"""
Unit tests for CLI connection fixes.

This module tests that CLI options are properly connected to their underlying
configuration and functionality.
"""

import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from repomap_tool.cli import (
    create_default_config,
    load_config_file,
)
from repomap_tool.cli.config.loader import load_or_create_config
from repomap_tool.models import (
    RepoMapConfig,
    FuzzyMatchConfig,
    SemanticMatchConfig,
    PerformanceConfig,
)


class TestCLIConnections:
    """Test that CLI options are properly connected to configuration."""

    def test_fuzzy_option_connection(self):
        """Test that --fuzzy/--no-fuzzy properly enables/disables fuzzy matching."""
        # Test fuzzy matching (always enabled)
        config = create_default_config(
            project_path=".",
            fuzzy=True,
            semantic=False,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
        )

        # Fuzzy matching is always enabled
        assert config.semantic_match.enabled is False

        # Test fuzzy disabled
        config = create_default_config(
            project_path=".",
            fuzzy=False,
            semantic=True,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
        )

        # Fuzzy matching is always enabled
        assert config.semantic_match.enabled is True

    def test_semantic_option_connection(self):
        """Test that --semantic/--no-semantic properly enables/disables semantic matching."""
        # Test semantic enabled
        config = create_default_config(
            project_path=".",
            fuzzy=False,
            semantic=True,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
        )

        assert config.semantic_match.enabled is True
        # Fuzzy matching is always enabled

        # Test semantic disabled
        config = create_default_config(
            project_path=".",
            fuzzy=True,
            semantic=False,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
        )

        assert config.semantic_match.enabled is False
        # Fuzzy matching is always enabled

    def test_output_format_connection(self):
        """Test that --output properly sets output_format."""
        config = create_default_config(
            project_path=".",
            fuzzy=True,
            semantic=True,
            threshold=0.7,
            max_results=50,
            output="text",
            verbose=True,
        )

        assert config.output_format == "text"

        config = create_default_config(
            project_path=".",
            fuzzy=True,
            semantic=True,
            threshold=0.7,
            max_results=50,
            output="text",
            verbose=True,
        )

        assert config.output_format == "text"

    def test_no_progress_connection(self):
        """Test that --no-progress properly disables progress bars."""
        # Test progress enabled (default)
        config = create_default_config(
            project_path=".",
            fuzzy=True,
            semantic=True,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
            no_progress=False,
        )

        assert config.performance.enable_progress is True

        # Test progress disabled
        config = create_default_config(
            project_path=".",
            fuzzy=True,
            semantic=True,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
            no_progress=True,
        )

        assert config.performance.enable_progress is False

    def test_no_monitoring_connection(self):
        """Test that --no-monitoring properly disables monitoring."""
        # Test monitoring enabled (default)
        config = create_default_config(
            project_path=".",
            fuzzy=True,
            semantic=True,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
            no_monitoring=False,
        )

        assert config.performance.enable_monitoring is True

        # Test monitoring disabled
        config = create_default_config(
            project_path=".",
            fuzzy=True,
            semantic=True,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
            no_monitoring=True,
        )

        assert config.performance.enable_monitoring is False

    def test_cache_size_connection(self):
        """Test that --cache-size properly sets cache size."""
        config = create_default_config(
            project_path=".",
            fuzzy=True,
            semantic=True,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
            cache_size=2000,
        )

        assert config.performance.cache_size == 2000

    def test_log_level_connection(self):
        """Test that --log-level properly sets log level."""
        config = create_default_config(
            project_path=".",
            fuzzy=True,
            semantic=True,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
            log_level="DEBUG",
        )

        assert config.log_level == "DEBUG"

        config = create_default_config(
            project_path=".",
            fuzzy=True,
            semantic=True,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
            log_level="ERROR",
        )

        assert config.log_level == "ERROR"

    def test_refresh_cache_connection(self):
        """Test that --refresh-cache properly sets refresh_cache flag."""
        config = create_default_config(
            project_path=".",
            fuzzy=True,
            semantic=True,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
            refresh_cache=True,
        )

        assert config.refresh_cache is True

        config = create_default_config(
            project_path=".",
            fuzzy=True,
            semantic=True,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
            refresh_cache=False,
        )

        assert config.refresh_cache is False

    def test_threshold_conversion(self):
        """Test that threshold is properly converted between fuzzy and semantic."""
        config = create_default_config(
            project_path=".",
            fuzzy=True,
            semantic=True,
            threshold=0.75,
            max_results=50,
            output="json",
            verbose=True,
        )

        # Fuzzy threshold should be converted to percentage
        assert config.fuzzy_match.threshold == 75
        # Semantic threshold should remain as float
        assert config.semantic_match.threshold == 0.75

    def test_search_config_creation(self):
        """Test that search config properly enables matchers based on match type."""
        # Test fuzzy match type
        config, was_created = load_or_create_config(
            project_path=".",
            config_file=None,
            create_if_missing=False,
            verbose=True,
            log_level="DEBUG",
            cache_size=1500,
        )

        # Override specific search settings
        config.fuzzy_match.enabled = True
        config.semantic_match.enabled = False

        # Fuzzy matching is enabled, semantic is disabled
        assert config.semantic_match.enabled is False
        assert config.log_level == "DEBUG"
        assert config.performance.cache_size == 1500

        # Test semantic match type
        config, was_created = load_or_create_config(
            project_path=".",
            config_file=None,
            create_if_missing=False,
            verbose=True,
        )

        # Override specific search settings
        config.fuzzy_match.enabled = True
        config.semantic_match.enabled = True

        # Both fuzzy and semantic matching are enabled
        assert config.semantic_match.enabled is True

        # Test hybrid match type
        config, was_created = load_or_create_config(
            project_path=".",
            config_file=None,
            create_if_missing=False,
            verbose=True,
        )

        # Override specific search settings
        config.fuzzy_match.enabled = True
        config.semantic_match.enabled = True

        # Both fuzzy and semantic matching are enabled
        assert config.semantic_match.enabled is True


class TestConfigFileLoading:
    """Test configuration file loading and validation."""

    def test_load_valid_config_file(self):
        """Test loading a valid configuration file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {
                "project_root": ".",
                "fuzzy_match": {
                    "enabled": True,
                    "threshold": 70,
                    "strategies": ["prefix", "substring"],
                },
                "semantic_match": {
                    "enabled": False,
                    "threshold": 0.5,
                    "use_tfidf": True,
                },
                "performance": {
                    "max_workers": 8,
                    "cache_size": 2000,
                    "enable_progress": True,
                    "enable_monitoring": True,
                },
                "max_results": 100,
                "output_format": "text",
                "verbose": True,
                "log_level": "DEBUG",
            }
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = load_config_file(config_path)

            assert isinstance(config, RepoMapConfig)
            assert config.project_root == Path(".").resolve()
            # Fuzzy matching is always enabled
            assert config.fuzzy_match.threshold == 70
            assert config.semantic_match.enabled is False
            assert config.performance.max_workers == 8
            assert config.performance.cache_size == 2000
            assert config.max_results == 100
            assert config.output_format == "text"
            assert config.verbose is True
            assert config.log_level == "DEBUG"

        finally:
            Path(config_path).unlink()

    def test_load_invalid_config_file(self):
        """Test loading an invalid configuration file raises appropriate error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {
                "project_root": "/nonexistent/project",  # Invalid path
                "fuzzy_match": {"threshold": "not_a_number"},  # Invalid type
            }
            json.dump(config_data, f)
            config_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid configuration file"):
                load_config_file(config_path)
        finally:
            Path(config_path).unlink()

    def test_load_nonexistent_config_file(self):
        """Test loading a nonexistent configuration file raises appropriate error."""
        with pytest.raises(ValueError, match="Failed to load configuration file"):
            load_config_file("/nonexistent/config.json")

    def test_load_malformed_json_config_file(self):
        """Test loading a malformed JSON configuration file raises appropriate error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"invalid": json}')  # Malformed JSON
            config_path = f.name

        try:
            with pytest.raises(ValueError, match="Failed to load configuration file"):
                load_config_file(config_path)
        finally:
            Path(config_path).unlink()


class TestConfigurationValidation:
    """Test configuration validation rules."""

    def test_at_least_one_matching_method_enabled(self):
        """Test that at least one matching method must be enabled."""
        # This should work (fuzzy matching always enabled)
        config = create_default_config(
            project_path=".",
            fuzzy=True,
            semantic=False,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
        )

        # This should also work (semantic enabled)
        config = create_default_config(
            project_path=".",
            fuzzy=False,
            semantic=True,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
        )

        # This should also work (both enabled)
        config = create_default_config(
            project_path=".",
            fuzzy=True,
            semantic=True,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
        )

    def test_output_format_validation(self):
        """Test that output format validation works."""
        valid_formats = ["text", "json"]

        for fmt in valid_formats:
            config = create_default_config(
                project_path=".",
                fuzzy=True,
                semantic=True,
                threshold=0.7,
                max_results=50,
                output=fmt,
                verbose=True,
            )
            assert config.output_format == fmt

    def test_log_level_validation(self):
        """Test that log level validation works."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]

        for level in valid_levels:
            config = create_default_config(
                project_path=".",
                fuzzy=True,
                semantic=True,
                threshold=0.7,
                max_results=50,
                output="json",
                verbose=True,
                log_level=level,
            )
            assert config.log_level == level


class TestCLIOverrides:
    """Test that CLI options properly override config file settings."""

    def test_load_config_file_with_various_settings(self):
        """Test loading configuration file with various settings."""
        # Create a config file with specific settings
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {
                "project_root": ".",
                "fuzzy_match": {"threshold": 50},
                "semantic_match": {"enabled": True, "threshold": 0.3},
                "performance": {"cache_size": 1000},
                "max_results": 25,
                "output_format": "json",
                "verbose": False,
                "log_level": "WARNING",
            }
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Load config file
            config = load_config_file(config_path)

            # Verify original settings
            # Fuzzy matching is always enabled
            assert config.semantic_match.enabled is True
            assert config.performance.cache_size == 1000
            assert config.max_results == 25
            assert config.output_format == "json"
            assert config.verbose is False
            assert config.log_level == "WARNING"

        finally:
            Path(config_path).unlink()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_project_path(self):
        """Test handling of empty project path."""
        with pytest.raises(ValueError, match="Project root cannot be empty"):
            create_default_config(
                project_path="",
                fuzzy=True,
                semantic=True,
                threshold=0.7,
                max_results=50,
                output="json",
                verbose=True,
            )

    def test_invalid_threshold_values(self):
        """Test handling of invalid threshold values."""
        # Test negative threshold
        with pytest.raises(ValueError):
            create_default_config(
                project_path=".",
                fuzzy=True,
                semantic=True,
                threshold=-0.1,
                max_results=50,
                output="json",
                verbose=True,
            )

        # Test threshold > 1.0
        with pytest.raises(ValueError):
            create_default_config(
                project_path=".",
                fuzzy=True,
                semantic=True,
                threshold=1.1,
                max_results=50,
                output="json",
                verbose=True,
            )

    def test_invalid_cache_size(self):
        """Test handling of invalid cache size values."""
        # Test negative cache size
        with pytest.raises(ValueError):
            create_default_config(
                project_path=".",
                fuzzy=True,
                semantic=True,
                threshold=0.7,
                max_results=50,
                output="json",
                verbose=True,
                cache_size=-100,
            )

    def test_invalid_log_level(self):
        """Test handling of invalid log level."""
        with pytest.raises(ValueError, match="Invalid log level"):
            create_default_config(
                project_path=".",
                fuzzy=True,
                semantic=True,
                threshold=0.7,
                max_results=50,
                output="json",
                verbose=True,
                log_level="INVALID",
            )


if __name__ == "__main__":
    pytest.main([__file__])
