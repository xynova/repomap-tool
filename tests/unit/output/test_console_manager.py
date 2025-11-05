"""
Tests for the centralized console management system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, ANY
from typing import Optional, Dict, Any

import click
from rich.console import Console

from repomap_tool.cli.output.console_manager import (
    ConsoleManagerProtocol,
    DefaultConsoleManager,
    log_console_operation,
)
from repomap_tool.cli.utils.console import ConsoleProvider, RichConsoleFactory


class TestDefaultConsoleManager:
    """Test the DefaultConsoleManager implementation."""

    def test_init_with_default_provider(self) -> None:
        """Test initialization with default provider."""
        manager = DefaultConsoleManager(
            provider=ConsoleProvider(factory=RichConsoleFactory())
        )
        assert manager._provider is not None
        assert isinstance(manager._provider, ConsoleProvider)
        assert isinstance(manager._provider._factory, RichConsoleFactory)
        assert manager.enable_logging is True
        assert manager.logger is not None

    def test_init_with_custom_provider(self) -> None:
        """Test initialization with custom provider."""
        mock_provider = Mock(spec=ConsoleProvider)
        manager = DefaultConsoleManager(provider=mock_provider)
        assert manager._provider == mock_provider

    def test_init_with_logging_disabled(self) -> None:
        """Test initialization with logging disabled."""
        manager = DefaultConsoleManager(
            provider=ConsoleProvider(factory=RichConsoleFactory()), enable_logging=False
        )
        assert manager.enable_logging is False
        assert manager.logger is None

    def test_get_console_with_context(self) -> None:
        """Test getting console with Click context."""
        mock_provider = Mock(spec=ConsoleProvider)
        mock_console = Mock(spec=Console)
        mock_provider.get_console.return_value = mock_console

        manager = DefaultConsoleManager(
            provider=mock_provider, enable_logging=False
        )  # Disable logging for this test
        mock_ctx = Mock(spec=click.Context)
        mock_ctx.obj = {}  # Add mock obj attribute

        result = manager.get_console(mock_ctx)

        assert result == mock_console
        mock_provider.get_console.assert_called_once_with(mock_ctx)

    def test_get_console_without_context(self) -> None:
        """Test getting console without context."""
        mock_provider = Mock(spec=ConsoleProvider)
        mock_console = Mock(spec=Console)
        mock_provider.get_console.return_value = mock_console

        manager = DefaultConsoleManager(provider=mock_provider)

        result = manager.get_console()

        assert result == mock_console
        mock_provider.get_console.assert_called_once_with(None)

    def test_get_console_provider_error(self) -> None:
        """Test console retrieval when provider raises error."""
        mock_provider = Mock(spec=ConsoleProvider)
        mock_provider.get_console.side_effect = Exception("Provider error")

        manager = DefaultConsoleManager(provider=mock_provider)

        with pytest.raises(Exception, match="Provider error"):
            manager.get_console()

    def test_configure_with_no_color(self) -> None:
        """Test console configuration with no_color option."""
        initial_provider = ConsoleProvider(factory=RichConsoleFactory(), no_color=False)
        manager = DefaultConsoleManager(provider=initial_provider, enable_logging=True)

        with patch.object(
            manager, "_log_operation"
        ) as mock_log_operation:  # Patch _log_operation directly
            manager.configure(no_color=True)
            # Assert that the internal provider was re-created with no_color=True
            assert manager._provider._no_color is True
            mock_log_operation.assert_called_once_with(
                "configure_console", context={"no_color": True}
            )

    def test_log_console_operation_with_logging_enabled(self) -> None:
        """Test logging console operation when logging is enabled."""
        manager = DefaultConsoleManager(
            provider=ConsoleProvider(factory=RichConsoleFactory()), enable_logging=True
        )
        with patch.object(manager.logger, "debug") as mock_debug:
            manager.log_operation("test_operation", {"key": "value"})
            mock_debug.assert_called_once()
            call_args = mock_debug.call_args
            assert "test_operation" in call_args[0][0]
            assert call_args[1]["extra"]["operation"] == "test_operation"
            assert (
                call_args[1]["extra"]["context"]["key"] == "value"
            )  # Changed from 'details' to 'context'

    def test_log_console_operation_with_logging_disabled(self) -> None:
        """Test logging console operation when logging is disabled."""
        manager = DefaultConsoleManager(
            provider=ConsoleProvider(factory=RichConsoleFactory()), enable_logging=False
        )
        manager.log_operation("test_operation", {"key": "value"})
        # No assertion needed, just ensure it doesn't crash

    def test_get_usage_stats(self) -> Dict[str, int]:
        """Test getting usage statistics."""
        manager = DefaultConsoleManager(
            provider=ConsoleProvider(factory=RichConsoleFactory()), enable_logging=True
        )
        manager.log_operation("operation1", {})
        manager.log_operation("operation2", {})
        manager.log_operation("operation1", {})
        stats = manager.get_usage_stats()
        assert stats["operation1"] == 2
        assert stats["operation2"] == 1
        return stats

    def test_reset_usage_stats(self) -> None:
        """Test resetting usage statistics."""
        manager = DefaultConsoleManager(
            provider=ConsoleProvider(factory=RichConsoleFactory()), enable_logging=True
        )
        manager.log_operation("operation1", {})
        manager.log_operation("operation2", {})
        manager.reset_usage_stats()
        stats = manager.get_usage_stats()
        assert len(stats) == 0


class TestConsoleManagerIntegration:
    """Integration tests for console manager."""

    def test_console_manager_protocol_compliance(self) -> None:
        """Test that DefaultConsoleManager implements ConsoleManager protocol."""
        manager = DefaultConsoleManager(
            provider=ConsoleProvider(factory=RichConsoleFactory())
        )
        assert hasattr(manager, "get_console")
        assert hasattr(manager, "configure")  # Updated to configure
        assert hasattr(manager, "log_operation")
        assert hasattr(manager, "get_usage_stats")
        assert hasattr(manager, "reset_usage_stats")
        assert callable(manager.get_console)
        assert callable(manager.configure)  # Updated to configure
        assert callable(manager.log_operation)
        assert callable(manager.get_usage_stats)
        assert callable(manager.reset_usage_stats)

    def test_console_manager_with_real_console(self) -> None:
        """Test console manager with real console instances."""
        provider = ConsoleProvider(factory=RichConsoleFactory())
        manager = DefaultConsoleManager(provider=provider, enable_logging=False)
        console1 = manager.get_console()
        assert isinstance(console1, Console)

        # Configure the manager and verify new consoles reflect the setting
        manager.configure(no_color=True)
        console2 = manager.get_console()
        assert console2.no_color is True

        manager.configure(no_color=False)
        console3 = manager.get_console()
        assert console3.no_color is False

    def test_usage_statistics_tracking(self) -> None:
        """Test that usage statistics are properly tracked."""
        manager = DefaultConsoleManager(
            provider=ConsoleProvider(factory=RichConsoleFactory()), enable_logging=True
        )
        manager.get_console()
        manager.configure(no_color=True)  # Updated to configure
        manager.log_operation("custom_operation", {})
        stats = manager.get_usage_stats()
        assert "get_console" in stats
        assert (
            "configure_console" in stats
        )  # Should be configure_console even if the method is just configure
        assert "custom_operation" in stats
        assert stats["get_console"] >= 1
        assert stats["configure_console"] >= 1
        assert stats["custom_operation"] >= 1

    def test_error_handling_robustness(self) -> None:
        """Test that console manager handles errors gracefully."""
        mock_console_returned_by_provider = Mock(spec=Console)

        # Mock the RichConsoleFactory first
        mock_rich_factory = Mock(spec=RichConsoleFactory)
        mock_rich_factory.create_console.return_value = (
            mock_console_returned_by_provider
        )

        # Mock the ConsoleProvider class itself
        mock_provider_instance = Mock(spec=ConsoleProvider)
        mock_provider_instance.get_console.side_effect = Exception(
            "Initial provider failure"
        )
        mock_provider_instance._factory = (
            mock_rich_factory  # Ensure the mock provider uses our mock factory
        )

        # Patch ConsoleProvider constructor directly. This will be used when DefaultConsoleManager.configure calls ConsoleProvider(...)
        with patch(
            "repomap_tool.cli.output.console_manager.ConsoleProvider",
            return_value=mock_provider_instance,
        ):
            # Initial manager uses a provider that fails
            manager = DefaultConsoleManager(
                provider=mock_provider_instance, enable_logging=False
            )

            with pytest.raises(Exception, match="Initial provider failure"):
                manager.get_console()

            # Now, configure the manager. This will call ConsoleProvider internally, which is patched to return mock_provider_instance
            manager.configure(no_color=True)

            # The internal _provider of manager should now be our mock_provider_instance
            assert manager._provider == mock_provider_instance
            assert manager._provider._factory == mock_rich_factory

            # After configure, the get_console should now use the mocked factory which returns mock_console_returned_by_provider
            # Since we set the side_effect for get_console, it will still raise the Initial provider failure
            with pytest.raises(Exception, match="Initial provider failure"):
                manager.get_console()

            manager.log_operation("test_operation", {})
