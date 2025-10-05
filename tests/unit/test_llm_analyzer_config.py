"""
Tests for LLM analyzer configuration and dependencies.

This module tests the LLM analyzer configuration objects and
dependency injection patterns.
"""

import pytest
from unittest.mock import Mock
from pydantic import ValidationError

from repomap_tool.code_analysis.llm_analyzer_config import (
    LLMAnalyzerConfig,
    LLMAnalyzerDependencies,
)


class TestLLMAnalyzerConfig:
    """Test LLM analyzer configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = LLMAnalyzerConfig()

        assert config.max_tokens == 4000
        assert config.enable_impact_analysis is True
        assert config.enable_centrality_analysis is True
        assert config.enable_code_snippets is True
        assert config.max_snippets_per_file == 3
        assert config.snippet_max_lines == 10
        assert config.analysis_timeout == 30
        assert config.cache_results is True
        assert config.verbose is False

    def test_custom_config(self):
        """Test custom configuration values."""
        config = LLMAnalyzerConfig(
            max_tokens=6000,
            enable_impact_analysis=False,
            enable_centrality_analysis=False,
            enable_code_snippets=False,
            max_snippets_per_file=5,
            snippet_max_lines=15,
            analysis_timeout=60,
            cache_results=False,
            verbose=True,
        )

        assert config.max_tokens == 6000
        assert config.enable_impact_analysis is False
        assert config.enable_centrality_analysis is False
        assert config.enable_code_snippets is False
        assert config.max_snippets_per_file == 5
        assert config.snippet_max_lines == 15
        assert config.analysis_timeout == 60
        assert config.cache_results is False
        assert config.verbose is True

    def test_config_validation_max_tokens(self):
        """Test max_tokens validation."""
        # Valid values
        config = LLMAnalyzerConfig(max_tokens=1000)
        assert config.max_tokens == 1000

        config = LLMAnalyzerConfig(max_tokens=8000)
        assert config.max_tokens == 8000

        # Invalid values
        with pytest.raises(ValidationError):
            LLMAnalyzerConfig(max_tokens=500)  # Too low

        with pytest.raises(ValidationError):
            LLMAnalyzerConfig(max_tokens=10000)  # Too high

    def test_config_validation_max_snippets(self):
        """Test max_snippets_per_file validation."""
        # Valid values
        config = LLMAnalyzerConfig(max_snippets_per_file=1)
        assert config.max_snippets_per_file == 1

        config = LLMAnalyzerConfig(max_snippets_per_file=10)
        assert config.max_snippets_per_file == 10

        # Invalid values
        with pytest.raises(ValidationError):
            LLMAnalyzerConfig(max_snippets_per_file=0)  # Too low

        with pytest.raises(ValidationError):
            LLMAnalyzerConfig(max_snippets_per_file=15)  # Too high

    def test_config_validation_snippet_lines(self):
        """Test snippet_max_lines validation."""
        # Valid values
        config = LLMAnalyzerConfig(snippet_max_lines=5)
        assert config.snippet_max_lines == 5

        config = LLMAnalyzerConfig(snippet_max_lines=20)
        assert config.snippet_max_lines == 20

        # Invalid values
        with pytest.raises(ValidationError):
            LLMAnalyzerConfig(snippet_max_lines=3)  # Too low

        with pytest.raises(ValidationError):
            LLMAnalyzerConfig(snippet_max_lines=25)  # Too high

    def test_config_validation_timeout(self):
        """Test analysis_timeout validation."""
        # Valid values
        config = LLMAnalyzerConfig(analysis_timeout=5)
        assert config.analysis_timeout == 5

        config = LLMAnalyzerConfig(analysis_timeout=120)
        assert config.analysis_timeout == 120

        # Invalid values
        with pytest.raises(ValidationError):
            LLMAnalyzerConfig(analysis_timeout=3)  # Too low

        with pytest.raises(ValidationError):
            LLMAnalyzerConfig(analysis_timeout=150)  # Too high

    def test_config_immutability(self):
        """Test that config is immutable after creation."""
        config = LLMAnalyzerConfig(max_tokens=5000)

        # Should not be able to modify after creation
        with pytest.raises(ValidationError):
            config.max_tokens = 6000

    def test_config_extra_fields(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError):
            LLMAnalyzerConfig(extra_field="not_allowed")


class TestLLMAnalyzerDependencies:
    """Test LLM analyzer dependencies."""

    def test_dependencies_creation(self):
        """Test dependencies creation with all required fields."""
        mock_dependency_graph = Mock()
        mock_ast_analyzer = Mock()
        mock_token_optimizer = Mock()
        mock_context_selector = Mock()
        mock_hierarchical_formatter = Mock()
        mock_path_resolver = Mock()
        mock_impact_engine = Mock()
        mock_centrality_engine = Mock()
        mock_centrality_calculator = Mock()

        dependencies = LLMAnalyzerDependencies(
            dependency_graph=mock_dependency_graph,
            project_root="/test/project",
            ast_analyzer=mock_ast_analyzer,
            token_optimizer=mock_token_optimizer,
            context_selector=mock_context_selector,
            hierarchical_formatter=mock_hierarchical_formatter,
            path_resolver=mock_path_resolver,
            impact_engine=mock_impact_engine,
            centrality_engine=mock_centrality_engine,
            centrality_calculator=mock_centrality_calculator,
        )

        assert dependencies.dependency_graph is mock_dependency_graph
        assert dependencies.project_root == "/test/project"
        assert dependencies.ast_analyzer is mock_ast_analyzer
        assert dependencies.token_optimizer is mock_token_optimizer
        assert dependencies.context_selector is mock_context_selector
        assert dependencies.hierarchical_formatter is mock_hierarchical_formatter
        assert dependencies.path_resolver is mock_path_resolver
        assert dependencies.impact_engine is mock_impact_engine
        assert dependencies.centrality_engine is mock_centrality_engine
        assert dependencies.centrality_calculator is mock_centrality_calculator

    def test_dependencies_missing_required_fields(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(ValidationError):
            LLMAnalyzerDependencies(
                dependency_graph=Mock(),
                project_root="/test/project",
                # Missing other required fields
            )

    def test_dependencies_project_root_validation(self):
        """Test project_root validation."""
        mock_deps = {
            "dependency_graph": Mock(),
            "ast_analyzer": Mock(),
            "token_optimizer": Mock(),
            "context_selector": Mock(),
            "hierarchical_formatter": Mock(),
            "path_resolver": Mock(),
            "impact_engine": Mock(),
            "centrality_engine": Mock(),
            "centrality_calculator": Mock(),
        }

        # Valid project root
        dependencies = LLMAnalyzerDependencies(project_root="/valid/path", **mock_deps)
        assert dependencies.project_root == "/valid/path"

        # Empty project root should be stripped
        dependencies = LLMAnalyzerDependencies(
            project_root="  /valid/path  ", **mock_deps
        )
        assert dependencies.project_root == "/valid/path"

    def test_dependencies_immutability(self):
        """Test that dependencies are immutable after creation."""
        dependencies = LLMAnalyzerDependencies(
            dependency_graph=Mock(),
            project_root="/test/project",
            ast_analyzer=Mock(),
            token_optimizer=Mock(),
            context_selector=Mock(),
            hierarchical_formatter=Mock(),
            path_resolver=Mock(),
            impact_engine=Mock(),
            centrality_engine=Mock(),
            centrality_calculator=Mock(),
        )

        # Should not be able to modify after creation
        with pytest.raises(ValidationError):
            dependencies.project_root = "/new/path"

    def test_dependencies_extra_fields(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError):
            LLMAnalyzerDependencies(
                dependency_graph=Mock(),
                project_root="/test/project",
                ast_analyzer=Mock(),
                token_optimizer=Mock(),
                context_selector=Mock(),
                hierarchical_formatter=Mock(),
                path_resolver=Mock(),
                impact_engine=Mock(),
                centrality_engine=Mock(),
                centrality_calculator=Mock(),
                extra_field="not_allowed",
            )

    def test_dependencies_with_none_values(self):
        """Test dependencies with None values (should fail validation)."""
        with pytest.raises(ValidationError):
            LLMAnalyzerDependencies(
                dependency_graph=None,  # Should not be None
                project_root="/test/project",
                ast_analyzer=Mock(),
                token_optimizer=Mock(),
                context_selector=Mock(),
                hierarchical_formatter=Mock(),
                path_resolver=Mock(),
                impact_engine=Mock(),
                centrality_engine=Mock(),
                centrality_calculator=Mock(),
            )


class TestLLMAnalyzerConfigIntegration:
    """Test LLM analyzer configuration integration."""

    def test_config_and_dependencies_together(self):
        """Test that config and dependencies work together."""
        config = LLMAnalyzerConfig(
            max_tokens=5000,
            enable_impact_analysis=True,
            verbose=True,
        )

        dependencies = LLMAnalyzerDependencies(
            dependency_graph=Mock(),
            project_root="/test/project",
            ast_analyzer=Mock(),
            token_optimizer=Mock(),
            context_selector=Mock(),
            hierarchical_formatter=Mock(),
            path_resolver=Mock(),
            impact_engine=Mock(),
            centrality_engine=Mock(),
            centrality_calculator=Mock(),
        )

        # Both should be valid
        assert config.max_tokens == 5000
        assert dependencies.project_root == "/test/project"

    def test_config_serialization(self):
        """Test that config can be serialized."""
        config = LLMAnalyzerConfig(
            max_tokens=5000,
            enable_impact_analysis=False,
            verbose=True,
        )

        # Should be able to convert to dict
        config_dict = config.model_dump()
        assert isinstance(config_dict, dict)
        assert config_dict["max_tokens"] == 5000
        assert config_dict["enable_impact_analysis"] is False
        assert config_dict["verbose"] is True

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "max_tokens": 6000,
            "enable_impact_analysis": True,
            "enable_centrality_analysis": False,
            "verbose": True,
        }

        config = LLMAnalyzerConfig(**config_dict)

        assert config.max_tokens == 6000
        assert config.enable_impact_analysis is True
        assert config.enable_centrality_analysis is False
        assert config.verbose is True
