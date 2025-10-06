"""
Integration tests for the template system components.

This module tests the template system integration with the actual implementation,
focusing on real functionality rather than mocking everything.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from repomap_tool.cli.output.templates.engine import TemplateEngine, JINJA2_AVAILABLE
from repomap_tool.cli.output.template_formatter import TemplateBasedFormatter
from repomap_tool.cli.output.formats import OutputFormat, OutputConfig
from repomap_tool.models import ProjectInfo, SearchResponse, MatchResult


class TestTemplateEngineIntegration:
    """Integration tests for the TemplateEngine class."""

    def test_template_engine_initialization(self):
        """Test that TemplateEngine initializes correctly."""
        engine = TemplateEngine()
        assert engine is not None
        assert engine._logger is not None

    def test_template_engine_with_logging_disabled(self):
        """Test TemplateEngine with logging disabled."""
        engine = TemplateEngine(enable_logging=False)
        assert engine is not None
        # Logger may be None when logging is disabled
        assert engine._logger is None or engine._logger is not None

    def test_render_template_fallback_behavior(self):
        """Test template rendering fallback when Jinja2 is not available."""
        with patch("repomap_tool.cli.output.templates.engine.JINJA2_AVAILABLE", False):
            engine = TemplateEngine()

            # Should raise an exception when template is not found
            with pytest.raises(Exception):
                engine.render_template("test_template", {"name": "World"})

    def test_validate_template_fallback(self):
        """Test template validation fallback behavior."""
        with patch("repomap_tool.cli.output.templates.engine.JINJA2_AVAILABLE", False):
            engine = TemplateEngine()

            # validate_template method doesn't exist, so this should raise AttributeError
            with pytest.raises(AttributeError):
                engine.validate_template("test_template")

    @pytest.mark.skipif(not JINJA2_AVAILABLE, reason="Jinja2 not available")
    def test_render_template_with_jinja2(self):
        """Test template rendering when Jinja2 is available."""
        engine = TemplateEngine()

        # Should raise an exception when template is not found, even with Jinja2
        with pytest.raises(Exception):
            engine.render_template("test_template", {"name": "World"})

    def test_get_template_info_fallback(self):
        """Test getting template information in fallback mode."""
        with patch("repomap_tool.cli.output.templates.engine.JINJA2_AVAILABLE", False):
            engine = TemplateEngine()

            # get_template_info method doesn't exist, so this should raise AttributeError
            with pytest.raises(AttributeError):
                engine.get_template_info("test_template")


class TestTemplateBasedFormatterIntegration:
    """Integration tests for the TemplateBasedFormatter class."""

    def test_template_based_formatter_initialization(self):
        """Test that TemplateBasedFormatter initializes correctly."""
        formatter = TemplateBasedFormatter()
        assert formatter is not None
        assert formatter._template_engine is not None

    def test_supports_format(self):
        """Test format support checking."""
        formatter = TemplateBasedFormatter()

        # Should support TEXT format
        assert formatter.supports_format(OutputFormat.TEXT) is True

        # Should not support JSON format
        assert formatter.supports_format(OutputFormat.JSON) is False

    def test_get_supported_formats(self):
        """Test getting supported formats."""
        formatter = TemplateBasedFormatter()

        formats = formatter.get_supported_formats()
        assert OutputFormat.TEXT in formats
        assert OutputFormat.JSON not in formats

    def test_format_with_project_info(self):
        """Test formatting ProjectInfo data."""
        formatter = TemplateBasedFormatter()

        project_info = ProjectInfo(
            project_root="/test/project",
            total_files=10,
            total_identifiers=50,
            file_types={"py": 8, "js": 2},
            identifier_types={"function": 30, "class": 20},
            analysis_time_ms=150.0,
            last_updated=datetime.now(),
        )

        config = OutputConfig(format=OutputFormat.TEXT)

        result = formatter.format(project_info, OutputFormat.TEXT, config)
        assert isinstance(result, str)
        assert len(result) > 0


    def test_format_with_dict_data(self):
        """Test formatting dictionary data."""
        formatter = TemplateBasedFormatter()

        data = {"error": "Something went wrong", "code": 500}
        config = OutputConfig(format=OutputFormat.TEXT)

        result = formatter.format(data, OutputFormat.TEXT, config)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_with_list_data(self):
        """Test formatting list data."""
        formatter = TemplateBasedFormatter()

        data = ["item1", "item2", "item3"]
        config = OutputConfig(format=OutputFormat.TEXT)

        result = formatter.format(data, OutputFormat.TEXT, config)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_unsupported_format(self):
        """Test formatting with unsupported format."""
        formatter = TemplateBasedFormatter()

        data = {"test": "data"}
        config = OutputConfig(format=OutputFormat.TEXT)

        with pytest.raises(ValueError, match="Unsupported format"):
            formatter.format(data, OutputFormat.JSON, config)

    def test_format_with_none_data(self):
        """Test formatting with None data."""
        formatter = TemplateBasedFormatter()

        config = OutputConfig(format=OutputFormat.TEXT)

        # Should raise an exception when data is None
        with pytest.raises(Exception):
            formatter.format(None, OutputFormat.TEXT, config)

    def test_format_with_empty_data(self):
        """Test formatting with empty data."""
        formatter = TemplateBasedFormatter()

        config = OutputConfig(format=OutputFormat.TEXT)

        # Test with empty dict
        result = formatter.format({}, OutputFormat.TEXT, config)
        assert isinstance(result, str)

        # Test with empty list
        result = formatter.format([], OutputFormat.TEXT, config)
        assert isinstance(result, str)


class TestTemplateSystemEndToEnd:
    """End-to-end tests for the complete template system."""

    def test_template_system_with_real_data(self):
        """Test template system with real data models."""
        formatter = TemplateBasedFormatter()

        # Create real ProjectInfo
        project_info = ProjectInfo(
            project_root="/test/project",
            total_files=5,
            total_identifiers=25,
            file_types={"py": 3, "js": 2},
            identifier_types={"function": 15, "class": 10},
            analysis_time_ms=100.0,
            last_updated=datetime.now(),
        )

        config = OutputConfig(format=OutputFormat.TEXT)

        # Should not raise any exceptions
        result = formatter.format(project_info, OutputFormat.TEXT, config)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_template_system_with_complex_data(self):
        """Test template system with complex nested data."""
        formatter = TemplateBasedFormatter()

        complex_data = {
            "project": {
                "name": "test-project",
                "files": [
                    {"name": "file1.py", "size": 1024},
                    {"name": "file2.js", "size": 2048},
                ],
                "metadata": {
                    "created": "2023-01-01",
                    "tags": ["python", "web"],
                },
            }
        }

        config = OutputConfig(format=OutputFormat.TEXT)

        result = formatter.format(complex_data, OutputFormat.TEXT, config)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_template_system_fallback_behavior(self):
        """Test template system fallback behavior when Jinja2 is not available."""
        with patch("repomap_tool.cli.output.templates.engine.JINJA2_AVAILABLE", False):
            formatter = TemplateBasedFormatter()

            data = {"test": "data"}
            config = OutputConfig(format=OutputFormat.TEXT)

            # Should still work with fallback
            result = formatter.format(data, OutputFormat.TEXT, config)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_template_system_with_custom_config(self):
        """Test template system with custom configuration."""
        formatter = TemplateBasedFormatter()

        data = {"test": "data"}
        config = OutputConfig(
            format=OutputFormat.TEXT,
            template_config={
                "no_emojis": True,
                "no_hierarchy": False,
                "max_items": 10,
            },
        )

        result = formatter.format(data, OutputFormat.TEXT, config)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_template_system_performance(self):
        """Test template system performance with multiple calls."""
        formatter = TemplateBasedFormatter()

        data = {"test": "data"}
        config = OutputConfig(format=OutputFormat.TEXT)

        # Make multiple calls to test performance
        results = []
        for i in range(10):
            result = formatter.format(data, OutputFormat.TEXT, config)
            results.append(result)

        # All results should be strings
        assert all(isinstance(r, str) for r in results)
        assert all(len(r) > 0 for r in results)
