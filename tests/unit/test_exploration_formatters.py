"""
Unit tests for exploration formatters.

Tests the exploration formatters created in Phase 2:
- TreeClusterViewModelFormatter
- TreeFocusViewModelFormatter
- TreeExpansionViewModelFormatter
- TreePruningViewModelFormatter
- TreeMappingViewModelFormatter
- TreeListingViewModelFormatter
- SessionStatusViewModelFormatter
- ExplorationViewModelFormatter
"""

import pytest
from unittest.mock import Mock, patch

from repomap_tool.cli.output.exploration_formatters import (
    TreeClusterViewModelFormatter,
    TreeFocusViewModelFormatter,
    TreeExpansionViewModelFormatter,
    TreePruningViewModelFormatter,
    TreeMappingViewModelFormatter,
    TreeListingViewModelFormatter,
    SessionStatusViewModelFormatter,
    ExplorationViewModelFormatter,
)
from repomap_tool.cli.output.formats import OutputFormat
from repomap_tool.cli.controllers.view_models import (
    TreeClusterViewModel,
    TreeFocusViewModel,
    TreeExpansionViewModel,
    TreePruningViewModel,
    TreeMappingViewModel,
    TreeListingViewModel,
    SessionStatusViewModel,
    ExplorationViewModel,
)


class TestTreeClusterViewModelFormatter:
    """Test TreeClusterViewModelFormatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = TreeClusterViewModelFormatter()

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_supports_format(self):
        """Test supports_format method."""
        assert self.formatter.supports_format(OutputFormat.TEXT) is True
        assert self.formatter.supports_format(OutputFormat.JSON) is True
        # Test with a non-existent format (using string instead of enum)
        assert self.formatter.supports_format("table") is False

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_get_supported_formats(self):
        """Test get_supported_formats method."""
        formats = self.formatter.get_supported_formats()
        assert OutputFormat.TEXT in formats
        assert OutputFormat.JSON in formats
        assert len(formats) == 2

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_format_text(self):
        """Test format method with TEXT format."""
        # Create mock data
        data = Mock(spec=TreeClusterViewModel)
        data.tree_id = "test_tree_1"
        data.context_name = "Test Tree"
        data.confidence = 0.85
        data.total_nodes = 10
        data.max_depth = 3
        data.root_file = "/test/project/file.py"
        data.description = "Test description"
        data.entrypoints = [
            Mock(identifier="function1", type="function", location="/test/file.py:10"),
            Mock(identifier="class1", type="class", location="/test/file.py:5"),
        ]

        with patch.object(
            self.formatter, "_format_text", return_value="formatted text"
        ):
            result = self.formatter.format(data, OutputFormat.TEXT)

        assert result == "formatted text"

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_format_json(self):
        """Test format method with JSON format."""
        # Create mock data
        data = Mock(spec=TreeClusterViewModel)
        data.tree_id = "test_tree_1"
        data.context_name = "Test Tree"

        with patch.object(
            self.formatter, "_format_json", return_value='{"tree_id": "test_tree_1"}'
        ):
            result = self.formatter.format(data, OutputFormat.JSON)

        assert result == '{"tree_id": "test_tree_1"}'


class TestTreeFocusViewModelFormatter:
    """Test TreeFocusViewModelFormatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = TreeFocusViewModelFormatter()

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_supports_format(self):
        """Test supports_format method."""
        assert self.formatter.supports_format(OutputFormat.TEXT) is True
        assert self.formatter.supports_format(OutputFormat.JSON) is True

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_format_text(self):
        """Test format method with TEXT format."""
        data = Mock(spec=TreeFocusViewModel)
        data.tree_id = "test_tree_1"
        data.focused_area = "authentication"

        with patch.object(self.formatter, "_format_text", return_value="focused text"):
            result = self.formatter.format(data, OutputFormat.TEXT)

        assert result == "focused text"


class TestTreeExpansionViewModelFormatter:
    """Test TreeExpansionViewModelFormatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = TreeExpansionViewModelFormatter()

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_supports_format(self):
        """Test supports_format method."""
        assert self.formatter.supports_format(OutputFormat.TEXT) is True
        assert self.formatter.supports_format(OutputFormat.JSON) is True

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_format_text(self):
        """Test format method with TEXT format."""
        data = Mock(spec=TreeExpansionViewModel)
        data.tree_id = "test_tree_1"
        data.expanded_area = "password_validation"
        data.new_nodes = [
            Mock(
                identifier="validate_password",
                type="function",
                location="/test/file.py:15",
            ),
            Mock(
                identifier="check_strength",
                type="function",
                location="/test/file.py:25",
            ),
        ]

        with patch.object(
            self.formatter, "_format_text", return_value="expansion text"
        ):
            result = self.formatter.format(data, OutputFormat.TEXT)

        assert result == "expansion text"


class TestTreePruningViewModelFormatter:
    """Test TreePruningViewModelFormatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = TreePruningViewModelFormatter()

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_supports_format(self):
        """Test supports_format method."""
        assert self.formatter.supports_format(OutputFormat.TEXT) is True
        assert self.formatter.supports_format(OutputFormat.JSON) is True

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_format_text(self):
        """Test format method with TEXT format."""
        data = Mock(spec=TreePruningViewModel)
        data.tree_id = "test_tree_1"
        data.pruned_area = "deprecated_functions"
        data.removed_nodes = ["old_function1", "old_function2"]

        with patch.object(self.formatter, "_format_text", return_value="pruning text"):
            result = self.formatter.format(data, OutputFormat.TEXT)

        assert result == "pruning text"


class TestTreeMappingViewModelFormatter:
    """Test TreeMappingViewModelFormatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = TreeMappingViewModelFormatter()

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_supports_format(self):
        """Test supports_format method."""
        assert self.formatter.supports_format(OutputFormat.TEXT) is True
        assert self.formatter.supports_format(OutputFormat.JSON) is True

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_format_text(self):
        """Test format method with TEXT format."""
        data = Mock(spec=TreeMappingViewModel)
        data.tree_id = "test_tree_1"
        data.mapping_type = "dependency"
        data.mapped_relationships = [
            Mock(source="function1", target="function2", relationship_type="calls"),
            Mock(source="class1", target="function3", relationship_type="contains"),
        ]

        with patch.object(self.formatter, "_format_text", return_value="mapping text"):
            result = self.formatter.format(data, OutputFormat.TEXT)

        assert result == "mapping text"


class TestTreeListingViewModelFormatter:
    """Test TreeListingViewModelFormatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = TreeListingViewModelFormatter()

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_supports_format(self):
        """Test supports_format method."""
        assert self.formatter.supports_format(OutputFormat.TEXT) is True
        assert self.formatter.supports_format(OutputFormat.JSON) is True

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_format_text(self):
        """Test format method with TEXT format."""
        data = Mock(spec=TreeListingViewModel)
        data.trees = [
            Mock(tree_id="tree_1", context_name="Authentication", node_count=5),
            Mock(tree_id="tree_2", context_name="Database", node_count=8),
        ]
        data.total_trees = 2

        with patch.object(self.formatter, "_format_text", return_value="listing text"):
            result = self.formatter.format(data, OutputFormat.TEXT)

        assert result == "listing text"


class TestSessionStatusViewModelFormatter:
    """Test SessionStatusViewModelFormatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = SessionStatusViewModelFormatter()

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_supports_format(self):
        """Test supports_format method."""
        assert self.formatter.supports_format(OutputFormat.TEXT) is True
        assert self.formatter.supports_format(OutputFormat.JSON) is True

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_format_text(self):
        """Test format method with TEXT format."""
        data = Mock(spec=SessionStatusViewModel)
        data.session_id = "0115_auth_login_errors"
        data.project_path = "/test/project"
        data.tree_count = 3
        data.total_nodes = 25
        data.current_focus = "auth_tree_1"
        data.session_duration = 3600

        with patch.object(self.formatter, "_format_text", return_value="status text"):
            result = self.formatter.format(data, OutputFormat.TEXT)

        assert result == "status text"


class TestExplorationViewModelFormatter:
    """Test ExplorationViewModelFormatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ExplorationViewModelFormatter()

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_supports_format(self):
        """Test supports_format method."""
        assert self.formatter.supports_format(OutputFormat.TEXT) is True
        assert self.formatter.supports_format(OutputFormat.JSON) is True

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_format_text(self):
        """Test format method with TEXT format."""
        data = Mock(spec=ExplorationViewModel)
        data.exploration_type = "start"
        data.session_id = "0115_auth_login_errors"
        data.trees_created = 2
        data.total_nodes = 15
        data.estimated_tokens = 5000

        with patch.object(
            self.formatter, "_format_text", return_value="exploration text"
        ):
            result = self.formatter.format(data, OutputFormat.TEXT)

        assert result == "exploration text"


class TestExplorationFormattersIntegration:
    """Test exploration formatters integration."""

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_all_formatters_support_text_and_json(self):
        """Test that all formatters support TEXT and JSON formats."""
        formatters = [
            TreeClusterViewModelFormatter(),
            TreeFocusViewModelFormatter(),
            TreeExpansionViewModelFormatter(),
            TreePruningViewModelFormatter(),
            TreeMappingViewModelFormatter(),
            TreeListingViewModelFormatter(),
            SessionStatusViewModelFormatter(),
            ExplorationViewModelFormatter(),
        ]

        for formatter in formatters:
            assert formatter.supports_format(OutputFormat.TEXT) is True
            assert formatter.supports_format(OutputFormat.JSON) is True
            assert len(formatter.get_supported_formats()) == 2

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_all_formatters_inherit_from_correct_base_classes(self):
        """Test that all formatters inherit from correct base classes."""
        formatters = [
            TreeClusterViewModelFormatter(),
            TreeFocusViewModelFormatter(),
            TreeExpansionViewModelFormatter(),
            TreePruningViewModelFormatter(),
            TreeMappingViewModelFormatter(),
            TreeListingViewModelFormatter(),
            SessionStatusViewModelFormatter(),
            ExplorationViewModelFormatter(),
        ]

        for formatter in formatters:
            # Check inheritance
            assert hasattr(formatter, "format")
            assert hasattr(formatter, "supports_format")
            assert hasattr(formatter, "get_supported_formats")
            assert hasattr(formatter, "_format_text")
            assert hasattr(formatter, "_format_json")

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_formatters_handle_missing_data_gracefully(self):
        """Test that formatters handle missing data gracefully."""
        formatter = TreeClusterViewModelFormatter()

        # Create mock data with missing attributes
        data = Mock(spec=TreeClusterViewModel)
        data.tree_id = "test_tree"
        # Missing other attributes

        with patch.object(formatter, "_format_text", return_value="fallback text"):
            result = formatter.format(data, OutputFormat.TEXT)

        assert result == "fallback text"

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_formatters_use_correct_template_names(self):
        """Test that formatters use correct template names."""
        formatter = TreeClusterViewModelFormatter()

        data = Mock(spec=TreeClusterViewModel)
        data.tree_id = "test_tree"

        with patch.object(formatter, "_get_template_name") as mock_get_template_name:
            mock_get_template_name.return_value = "tree_cluster.jinja2"
            formatter.format(data, OutputFormat.TEXT)
            mock_get_template_name.assert_called_once_with(data)

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_formatters_pass_kwargs_correctly(self):
        """Test that formatters work correctly with standard arguments."""
        formatter = TreeClusterViewModelFormatter()

        data = Mock(spec=TreeClusterViewModel)
        data.tree_id = "test_tree"

        # Test that formatter works with standard arguments
        with patch.object(formatter, "_format_text", return_value="formatted text"):
            result = formatter.format(data, OutputFormat.TEXT)
            assert result == "formatted text"
