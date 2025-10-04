"""
Tests for the centralized console management system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Optional, Dict, Any

import click
from rich.console import Console

from repomap_tool.cli.output.console_manager import (
    ConsoleManager,
    DefaultConsoleManager,
    ConsoleManagerFactory,
    get_console_manager,
    set_console_manager,
    get_managed_console,
    configure_managed_console,
    get_console_from_context,
    log_console_operation,
)
from repomap_tool.cli.utils.console import ConsoleProvider


class TestDefaultConsoleManager:
    """Test the DefaultConsoleManager implementation."""

    def test_init_with_default_provider(self):
        """Test initialization with default provider."""
        manager = ConsoleManagerFactory.create_default_manager()
        assert manager._provider is not None
        assert manager._enable_logging is True
        assert manager._logger is not None

    def test_init_with_custom_provider(self):
        """Test initialization with custom provider."""
        mock_provider = Mock(spec=ConsoleProvider)
        manager = DefaultConsoleManager(provider=mock_provider)
        assert manager._provider == mock_provider

    def test_init_with_logging_disabled(self):
        """Test initialization with logging disabled."""
        manager = ConsoleManagerFactory.create_default_manager(enable_logging=False)
        assert manager._enable_logging is False
        assert manager._logger is None

    def test_get_console_with_context(self):
        """Test getting console with Click context."""
        mock_provider = Mock(spec=ConsoleProvider)
        mock_console = Mock(spec=Console)
        mock_provider.get_console.return_value = mock_console

        manager = DefaultConsoleManager(provider=mock_provider)
        mock_ctx = Mock(spec=click.Context)

        result = manager.get_console(mock_ctx)

        assert result == mock_console
        mock_provider.get_console.assert_called_once_with(mock_ctx)

    def test_get_console_without_context(self):
        """Test getting console without context."""
        mock_provider = Mock(spec=ConsoleProvider)
        mock_console = Mock(spec=Console)
        mock_provider.get_console.return_value = mock_console

        manager = DefaultConsoleManager(provider=mock_provider)

        result = manager.get_console()

        assert result == mock_console
        mock_provider.get_console.assert_called_once_with(None)

    def test_get_console_provider_error(self):
        """Test console retrieval when provider raises error."""
        mock_provider = Mock(spec=ConsoleProvider)
        mock_provider.get_console.side_effect = Exception("Provider error")

        manager = DefaultConsoleManager(provider=mock_provider)

        # Should raise the exception
        with pytest.raises(Exception, match="Provider error"):
            manager.get_console()

    def test_configure_console_with_theme(self):
        """Test console configuration with theme."""
        mock_provider = Mock(spec=ConsoleProvider)
        mock_console = Mock(spec=Console)
        mock_provider.get_console.return_value = mock_console

        manager = DefaultConsoleManager(provider=mock_provider)
        mock_theme = Mock()

        result = manager.configure_console(theme=mock_theme)

        # Should create new console with theme
        assert isinstance(result, Console)

    def test_configure_console_with_no_color(self):
        """Test console configuration with no_color option."""
        mock_provider = Mock(spec=ConsoleProvider)
        mock_console = Mock(spec=Console)
        mock_provider.get_console.return_value = mock_console

        manager = DefaultConsoleManager(provider=mock_provider)

        result = manager.configure_console(no_color=True)

        # Should create new console with no_color
        assert isinstance(result, Console)

    def test_configure_console_provider_error(self):
        """Test console configuration when provider raises error."""
        mock_provider = Mock(spec=ConsoleProvider)
        mock_provider.get_console.side_effect = Exception("Provider error")

        manager = DefaultConsoleManager(provider=mock_provider)

        # Should raise the exception
        with pytest.raises(Exception, match="Provider error"):
            manager.configure_console(no_color=True)

    def test_log_console_usage_with_logging_enabled(self):
        """Test logging console usage when logging is enabled."""
        manager = ConsoleManagerFactory.create_default_manager(enable_logging=True)

        with patch.object(manager._logger, "debug") as mock_debug:
            manager.log_console_usage("test_operation", key="value")

            mock_debug.assert_called_once()
            call_args = mock_debug.call_args
            assert "test_operation" in call_args[0][0]
            assert call_args[1]["extra"]["operation"] == "test_operation"
            assert call_args[1]["extra"]["context"]["key"] == "value"

    def test_log_console_usage_with_logging_disabled(self):
        """Test logging console usage when logging is disabled."""
        manager = ConsoleManagerFactory.create_default_manager(enable_logging=False)

        # Should not raise any errors
        manager.log_console_usage("test_operation", key="value")

    def test_get_usage_stats(self):
        """Test getting usage statistics."""
        manager = ConsoleManagerFactory.create_default_manager(enable_logging=True)

        # Log some operations
        manager.log_console_usage("operation1")
        manager.log_console_usage("operation2")
        manager.log_console_usage("operation1")

        stats = manager.get_usage_stats()

        assert stats["operation1"] == 2
        assert stats["operation2"] == 1

    def test_reset_usage_stats(self):
        """Test resetting usage statistics."""
        manager = ConsoleManagerFactory.create_default_manager(enable_logging=True)

        # Log some operations
        manager.log_console_usage("operation1")
        manager.log_console_usage("operation2")

        # Reset stats
        manager.reset_usage_stats()

        stats = manager.get_usage_stats()
        assert len(stats) == 0


class TestConsoleManagerFactory:
    """Test the ConsoleManagerFactory."""

    def test_create_default_manager(self):
        """Test creating default manager."""
        manager = ConsoleManagerFactory.create_default_manager()

        assert isinstance(manager, DefaultConsoleManager)
        assert manager._enable_logging is True

    def test_create_default_manager_with_custom_provider(self):
        """Test creating default manager with custom provider."""
        mock_provider = Mock(spec=ConsoleProvider)
        manager = ConsoleManagerFactory.create_default_manager(provider=mock_provider)

        assert isinstance(manager, DefaultConsoleManager)
        assert manager._provider == mock_provider

    def test_create_default_manager_with_logging_disabled(self):
        """Test creating default manager with logging disabled."""
        manager = ConsoleManagerFactory.create_default_manager(enable_logging=False)

        assert isinstance(manager, DefaultConsoleManager)
        assert manager._enable_logging is False

    def test_create_console_manager_default_type(self):
        """Test creating console manager with default type."""
        manager = ConsoleManagerFactory.create_console_manager()

        assert isinstance(manager, DefaultConsoleManager)

    def test_create_console_manager_unknown_type(self):
        """Test creating console manager with unknown type."""
        with pytest.raises(ValueError, match="Unknown console manager type"):
            ConsoleManagerFactory.create_console_manager("unknown_type")


class TestGlobalConsoleManager:
    """Test global console manager functionality."""

    def test_get_console_manager_default(self):
        """Test getting default global console manager."""
        # Reset global state
        set_console_manager(None)

        manager = get_console_manager()

        assert isinstance(manager, DefaultConsoleManager)

    def test_set_and_get_console_manager(self):
        """Test setting and getting custom console manager."""
        mock_manager = Mock(spec=ConsoleManager)

        set_console_manager(mock_manager)
        result = get_console_manager()

        assert result == mock_manager

    def test_get_managed_console(self):
        """Test getting managed console."""
        mock_manager = Mock(spec=ConsoleManager)
        mock_console = Mock(spec=Console)
        mock_manager.get_console.return_value = mock_console

        set_console_manager(mock_manager)

        result = get_managed_console()

        assert result == mock_console
        mock_manager.get_console.assert_called_once_with(None)

    def test_get_managed_console_with_context(self):
        """Test getting managed console with context."""
        mock_manager = Mock(spec=ConsoleManager)
        mock_console = Mock(spec=Console)
        mock_manager.get_console.return_value = mock_console
        mock_ctx = Mock(spec=click.Context)

        set_console_manager(mock_manager)

        result = get_managed_console(mock_ctx)

        assert result == mock_console
        mock_manager.get_console.assert_called_once_with(mock_ctx)

    def test_configure_managed_console(self):
        """Test configuring managed console."""
        mock_manager = Mock(spec=ConsoleManager)
        mock_console = Mock(spec=Console)
        mock_manager.configure_console.return_value = mock_console

        set_console_manager(mock_manager)

        result = configure_managed_console(no_color=True)

        assert result == mock_console
        mock_manager.configure_console.assert_called_once_with(None, no_color=True)

    def test_get_console_from_context(self):
        """Test getting console from context."""
        mock_manager = Mock(spec=ConsoleManager)
        mock_console = Mock(spec=Console)
        mock_manager.get_console.return_value = mock_console
        mock_ctx = Mock(spec=click.Context)

        set_console_manager(mock_manager)

        result = get_console_from_context(mock_ctx)

        assert result == mock_console
        mock_manager.get_console.assert_called_once_with(mock_ctx)

    def test_log_console_operation(self):
        """Test logging console operation."""
        mock_manager = Mock(spec=ConsoleManager)

        set_console_manager(mock_manager)

        log_console_operation("test_op", key="value")

        mock_manager.log_console_usage.assert_called_once_with("test_op", key="value")


class TestConsoleManagerIntegration:
    """Integration tests for console manager."""

    def test_console_manager_protocol_compliance(self):
        """Test that DefaultConsoleManager implements ConsoleManager protocol."""
        manager = ConsoleManagerFactory.create_default_manager()

        # Should have all required methods
        assert hasattr(manager, "get_console")
        assert hasattr(manager, "configure_console")
        assert hasattr(manager, "log_console_usage")

        # Should be callable
        assert callable(manager.get_console)
        assert callable(manager.configure_console)
        assert callable(manager.log_console_usage)

    def test_console_manager_with_real_console(self):
        """Test console manager with real console instances."""
        manager = ConsoleManagerFactory.create_default_manager(enable_logging=False)

        # Test getting console
        console1 = manager.get_console()
        assert isinstance(console1, Console)

        # Test configuring console (currently returns same console)
        console2 = manager.configure_console(no_color=True)
        assert isinstance(console2, Console)
        # Note: configure_console currently doesn't change console settings
        # due to DI constraints - it returns the same console instance

    def test_usage_statistics_tracking(self):
        """Test that usage statistics are properly tracked."""
        manager = ConsoleManagerFactory.create_default_manager(enable_logging=True)

        # Perform various operations
        manager.get_console()
        manager.configure_console(no_color=True)
        manager.log_console_usage("custom_operation")

        stats = manager.get_usage_stats()

        assert "get_console" in stats
        assert "configure_console" in stats
        assert "custom_operation" in stats
        assert stats["get_console"] >= 1
        assert stats["configure_console"] >= 1
        assert stats["custom_operation"] >= 1

    def test_error_handling_robustness(self):
        """Test that console manager handles errors gracefully."""
        # Create manager with failing provider
        mock_provider = Mock(spec=ConsoleProvider)
        mock_provider.get_console.side_effect = Exception("Provider failure")

        manager = DefaultConsoleManager(provider=mock_provider, enable_logging=False)

        # Should raise exceptions when provider fails
        with pytest.raises(Exception, match="Provider failure"):
            manager.get_console()

        with pytest.raises(Exception, match="Provider failure"):
            manager.configure_console(no_color=True)

        # Should not raise exceptions for logging
        manager.log_console_usage("test_operation")
