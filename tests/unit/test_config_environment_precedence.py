#!/usr/bin/env python3
"""
Test environment variable precedence in configuration system.

This module tests that environment variables properly override file-based
configuration but are overridden by CLI arguments.
"""

import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from repomap_tool.cli import (
    load_or_create_config,
    apply_environment_overrides,
    apply_cli_overrides,
    load_config_file,
)
from repomap_tool.models import RepoMapConfig


class TestEnvironmentVariablePrecedence:
    """Test environment variable precedence over file-based configuration."""

    def test_environment_overrides_file_config(self):
        """Test that environment variables override file-based configuration."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {
                "project_root": ".",
                "verbose": False,
                "log_level": "WARNING",
                "output_format": "text",
                "max_results": 25,
                "fuzzy_match": {
                    "threshold": 60,
                    "strategies": ["prefix", "substring"],
                },
                "semantic_match": {
                    "enabled": False,
                    "threshold": 0.5,
                },
                "performance": {
                    "max_workers": 2,
                    "cache_size": 500,
                    "enable_progress": False,
                },
            }
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Set environment variables that should override file config
            env_vars = {
                "REPOMAP_VERBOSE": "true",
                "REPOMAP_LOG_LEVEL": "DEBUG",
                "REPOMAP_OUTPUT_FORMAT": "json",
                "REPOMAP_MAX_RESULTS": "100",
                "REPOMAP_FUZZY_THRESHOLD": "85",
                "REPOMAP_FUZZY_STRATEGIES": "levenshtein,jaro_winkler",
                "REPOMAP_SEMANTIC_ENABLED": "true",
                "REPOMAP_SEMANTIC_THRESHOLD": "0.8",
                "REPOMAP_MAX_WORKERS": "8",
                "REPOMAP_CACHE_SIZE": "2000",
                "REPOMAP_ENABLE_PROGRESS": "true",
            }

            with patch.dict(os.environ, env_vars):
                config, was_created = load_or_create_config(
                    ".", config_file=config_path
                )

                # Environment variables should override file config
                assert config.verbose is True  # Overridden by REPOMAP_VERBOSE
                assert config.log_level == "DEBUG"  # Overridden by REPOMAP_LOG_LEVEL
                assert (
                    config.output_format == "json"
                )  # Overridden by REPOMAP_OUTPUT_FORMAT
                assert config.max_results == 100  # Overridden by REPOMAP_MAX_RESULTS
                assert (
                    config.fuzzy_match.threshold == 85
                )  # Overridden by REPOMAP_FUZZY_THRESHOLD
                assert config.fuzzy_match.strategies == [
                    "levenshtein",
                    "jaro_winkler",
                ]  # Overridden
                assert (
                    config.semantic_match.enabled is True
                )  # Overridden by REPOMAP_SEMANTIC_ENABLED
                assert (
                    config.semantic_match.threshold == 0.8
                )  # Overridden by REPOMAP_SEMANTIC_THRESHOLD
                assert (
                    config.performance.max_workers == 8
                )  # Overridden by REPOMAP_MAX_WORKERS
                assert (
                    config.performance.cache_size == 2000
                )  # Overridden by REPOMAP_CACHE_SIZE
                assert (
                    config.performance.enable_progress is True
                )  # Overridden by REPOMAP_ENABLE_PROGRESS

        finally:
            Path(config_path).unlink()

    def test_cli_overrides_environment_variables(self):
        """Test that CLI arguments override environment variables."""
        # Set environment variables
        env_vars = {
            "REPOMAP_VERBOSE": "false",
            "REPOMAP_LOG_LEVEL": "WARNING",
            "REPOMAP_FUZZY_THRESHOLD": "70",
            "REPOMAP_MAX_WORKERS": "4",
        }

        with patch.dict(os.environ, env_vars):
            # CLI overrides should take precedence over environment variables
            config, was_created = load_or_create_config(
                ".",
                verbose=True,  # CLI override
                log_level="DEBUG",  # CLI override
                fuzzy_threshold=90,  # CLI override
                max_workers=16,  # CLI override
            )

            # CLI arguments should override environment variables
            assert config.verbose is True  # CLI override wins
            assert config.log_level == "DEBUG"  # CLI override wins
            assert config.fuzzy_match.threshold == 90  # CLI override wins
            assert config.performance.max_workers == 16  # CLI override wins

    def test_environment_variable_validation(self):
        """Test that invalid environment variables are handled gracefully."""
        # Create a temporary config file to avoid loading existing config
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {
                "project_root": ".",
                "max_results": 25,
                "fuzzy_match": {"threshold": 60},
                "semantic_match": {"threshold": 0.5},
                "performance": {"max_workers": 2},
            }
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Set invalid environment variables
            env_vars = {
                "REPOMAP_MAX_RESULTS": "invalid_number",
                "REPOMAP_FUZZY_THRESHOLD": "not_a_number",
                "REPOMAP_MAX_WORKERS": "also_invalid",
                "REPOMAP_SEMANTIC_THRESHOLD": "not_float",
            }

            with patch.dict(os.environ, env_vars):
                config, was_created = load_or_create_config(
                    ".", config_file=config_path
                )

                # Invalid values should be ignored, file values should remain
                assert config.max_results == 25  # File value (invalid env ignored)
                assert (
                    config.fuzzy_match.threshold == 60
                )  # File value (invalid env ignored)
                assert (
                    config.performance.max_workers == 2
                )  # File value (invalid env ignored)
                assert (
                    config.semantic_match.threshold == 0.5
                )  # File value (invalid env ignored)

        finally:
            Path(config_path).unlink()

    def test_boolean_environment_variables(self):
        """Test boolean environment variable parsing."""
        # Test various boolean representations
        env_vars = {
            "REPOMAP_VERBOSE": "true",
            "REPOMAP_SEMANTIC_ENABLED": "1",
            "REPOMAP_ENABLE_PROGRESS": "yes",
            "REPOMAP_ENABLE_MONITORING": "false",
            "REPOMAP_ALLOW_FALLBACK": "0",
            "REPOMAP_FUZZY_CACHE_RESULTS": "no",
        }

        with patch.dict(os.environ, env_vars):
            config, was_created = load_or_create_config(".")

            # Test positive boolean values
            assert config.verbose is True
            assert config.semantic_match.enabled is True
            assert config.performance.enable_progress is True

            # Test negative boolean values
            assert config.performance.enable_monitoring is False
            assert config.performance.allow_fallback is False
            assert config.fuzzy_match.cache_results is False

    def test_cache_directory_environment_variables(self):
        """Test cache directory environment variable handling."""
        # Create a temporary config file to avoid loading existing config
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {"project_root": "."}
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Test new REPOMAP_CACHE_DIR variable
            env_vars = {
                "REPOMAP_CACHE_DIR": "/custom/repomap/cache",
            }

            with patch.dict(os.environ, env_vars):
                config, was_created = load_or_create_config(
                    ".", config_file=config_path
                )
                assert config.cache_dir == Path("/custom/repomap/cache")

            # Test legacy CACHE_DIR variable (should still work)
            env_vars = {
                "CACHE_DIR": "/legacy/cache/dir",
            }

            with patch.dict(os.environ, env_vars):
                config, was_created = load_or_create_config(
                    ".", config_file=config_path
                )
                assert config.cache_dir == Path("/legacy/cache/dir")

            # Test precedence: REPOMAP_CACHE_DIR should override CACHE_DIR
            env_vars = {
                "CACHE_DIR": "/legacy/cache/dir",
                "REPOMAP_CACHE_DIR": "/new/repomap/cache",
            }

            with patch.dict(os.environ, env_vars):
                config, was_created = load_or_create_config(
                    ".", config_file=config_path
                )
                assert config.cache_dir == Path("/new/repomap/cache")

        finally:
            Path(config_path).unlink()

    def test_tree_configuration_environment_variables(self):
        """Test tree configuration environment variables."""
        env_vars = {
            "REPOMAP_TREE_MAX_DEPTH": "5",
            "REPOMAP_TREE_MAX_TREES_PER_SESSION": "20",
            "REPOMAP_TREE_ENTRYPOINT_THRESHOLD": "0.8",
            "REPOMAP_TREE_ENABLE_CODE_SNIPPETS": "false",
            "REPOMAP_TREE_CACHE_STRUCTURES": "true",
        }

        with patch.dict(os.environ, env_vars):
            config, was_created = load_or_create_config(".")

            assert config.trees.max_depth == 5
            assert config.trees.max_trees_per_session == 20
            assert config.trees.entrypoint_threshold == 0.8
            assert config.trees.enable_code_snippets is False
            assert config.trees.cache_tree_structures is True

    def test_dependency_configuration_environment_variables(self):
        """Test dependency configuration environment variables."""
        env_vars = {
            "REPOMAP_DEP_CACHE_GRAPHS": "false",
            "REPOMAP_DEP_MAX_GRAPH_SIZE": "5000",
            "REPOMAP_DEP_ENABLE_CALL_GRAPH": "true",
            "REPOMAP_DEP_ENABLE_IMPACT_ANALYSIS": "false",
            "REPOMAP_DEP_CENTRALITY_ALGORITHMS": "degree,betweenness",
            "REPOMAP_DEP_MAX_CENTRALITY_CACHE_SIZE": "500",
            "REPOMAP_DEP_PERFORMANCE_THRESHOLD_SECONDS": "15.0",
        }

        with patch.dict(os.environ, env_vars):
            config, was_created = load_or_create_config(".")

            assert config.dependencies.cache_graphs is False
            assert config.dependencies.max_graph_size == 5000
            assert config.dependencies.enable_call_graph is True
            assert config.dependencies.enable_impact_analysis is False
            assert config.dependencies.centrality_algorithms == [
                "degree",
                "betweenness",
            ]
            assert config.dependencies.max_centrality_cache_size == 500
            assert config.dependencies.performance_threshold_seconds == 15.0

    def test_apply_environment_overrides_function(self):
        """Test the apply_environment_overrides function directly."""
        # Create a base config
        config = RepoMapConfig(project_root=".")

        # Set environment variables
        env_vars = {
            "REPOMAP_VERBOSE": "true",
            "REPOMAP_LOG_LEVEL": "DEBUG",
            "REPOMAP_FUZZY_THRESHOLD": "85",
            "REPOMAP_SEMANTIC_ENABLED": "true",
        }

        with patch.dict(os.environ, env_vars):
            updated_config = apply_environment_overrides(config)

            assert updated_config.verbose is True
            assert updated_config.log_level == "DEBUG"
            assert updated_config.fuzzy_match.threshold == 85
            assert updated_config.semantic_match.enabled is True

    def test_apply_cli_overrides_function(self):
        """Test the apply_cli_overrides function directly."""
        # Create a base config
        config = RepoMapConfig(project_root=".")

        # Test CLI overrides
        overrides = {
            "verbose": True,
            "log_level": "DEBUG",
            "fuzzy_threshold": 90,
            "semantic_enabled": True,
            "max_workers": 8,
        }

        updated_config = apply_cli_overrides(config, overrides)

        assert updated_config.verbose is True
        assert updated_config.log_level == "DEBUG"
        assert updated_config.fuzzy_match.threshold == 90
        assert updated_config.semantic_match.enabled is True
        assert updated_config.performance.max_workers == 8

    def test_complete_precedence_chain(self):
        """Test the complete precedence chain: CLI > ENV > FILE > DEFAULTS."""
        # Create a config file with specific values
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {
                "project_root": ".",
                "verbose": False,  # File says False
                "log_level": "WARNING",  # File says WARNING
                "fuzzy_match": {"threshold": 60},  # File says 60
                "performance": {"max_workers": 2},  # File says 2
            }
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Set environment variables (should override file)
            env_vars = {
                "REPOMAP_VERBOSE": "true",  # ENV says True
                "REPOMAP_LOG_LEVEL": "INFO",  # ENV says INFO
                "REPOMAP_FUZZY_THRESHOLD": "70",  # ENV says 70
                "REPOMAP_MAX_WORKERS": "4",  # ENV says 4
            }

            with patch.dict(os.environ, env_vars):
                # CLI arguments (should override everything)
                config, was_created = load_or_create_config(
                    ".",
                    config_file=config_path,
                    verbose=False,  # CLI says False (overrides ENV True)
                    log_level="DEBUG",  # CLI says DEBUG (overrides ENV INFO)
                    fuzzy_threshold=80,  # CLI says 80 (overrides ENV 70)
                    max_workers=8,  # CLI says 8 (overrides ENV 4)
                )

                # CLI should win over everything
                assert config.verbose is False  # CLI override
                assert config.log_level == "DEBUG"  # CLI override
                assert config.fuzzy_match.threshold == 80  # CLI override
                assert config.performance.max_workers == 8  # CLI override

        finally:
            Path(config_path).unlink()

    def test_environment_variables_with_no_config_file(self):
        """Test environment variables work when no config file exists."""
        # Use a temporary directory to avoid existing config files
        with tempfile.TemporaryDirectory() as temp_dir:
            env_vars = {
                "REPOMAP_VERBOSE": "true",
                "REPOMAP_LOG_LEVEL": "DEBUG",
                "REPOMAP_FUZZY_THRESHOLD": "85",
                "REPOMAP_SEMANTIC_ENABLED": "true",
            }

            with patch.dict(os.environ, env_vars):
                config, was_created = load_or_create_config(temp_dir)

                # Environment variables should be applied to default config
                assert config.verbose is True
                assert config.log_level == "DEBUG"
                assert config.fuzzy_match.threshold == 85
                assert config.semantic_match.enabled is True
                assert was_created is True  # Should create new config file
