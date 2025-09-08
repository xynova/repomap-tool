#!/usr/bin/env python3
"""
Test CLI project path fix - ensure commands use correct project path from session data.
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from repomap_tool.cli import cli, get_project_path_from_session
from repomap_tool.models import ExplorationSession
from repomap_tool.trees import SessionManager


class TestCLIProjectPathFix:
    """Test that CLI commands use correct project path from session data."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.test_project_dir = Path(self.temp_dir) / "test_project"
        self.test_project_dir.mkdir()

        # Create a simple test file
        (self.test_project_dir / "test.py").write_text("print('hello world')")

        # Create another directory to test from
        self.other_dir = Path(self.temp_dir) / "other_dir"
        self.other_dir.mkdir()

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_get_project_path_from_session_success(self):
        """Test successful retrieval of project path from session."""
        # Create a mock session
        session_id = "test_session_123"
        project_path = str(self.test_project_dir)

        session = ExplorationSession(session_id=session_id, project_path=project_path)

        # Mock SessionManager
        with patch("repomap_tool.trees.SessionManager") as mock_session_manager_class:
            mock_session_manager = MagicMock()
            mock_session_manager_class.return_value = mock_session_manager
            mock_session_manager.get_session.return_value = session

            # Test the function
            result = get_project_path_from_session(session_id)

            assert result == project_path
            mock_session_manager.get_session.assert_called_once_with(session_id)

    def test_get_project_path_from_session_not_found(self):
        """Test handling when session is not found."""
        session_id = "nonexistent_session"

        # Mock SessionManager
        with patch("repomap_tool.trees.SessionManager") as mock_session_manager_class:
            mock_session_manager = MagicMock()
            mock_session_manager_class.return_value = mock_session_manager
            mock_session_manager.get_session.return_value = None

            # Test the function
            result = get_project_path_from_session(session_id)

            assert result is None

    def test_get_project_path_from_session_error(self):
        """Test handling when session retrieval raises an exception."""
        session_id = "error_session"

        # Mock SessionManager to raise an exception
        with patch("repomap_tool.trees.SessionManager") as mock_session_manager_class:
            mock_session_manager = MagicMock()
            mock_session_manager_class.return_value = mock_session_manager
            mock_session_manager.get_session.side_effect = Exception("Session error")

            # Test the function
            result = get_project_path_from_session(session_id)

            assert result is None

    def test_focus_command_uses_session_project_path(self):
        """Test that focus command uses project path from session data."""
        session_id = "test_session_456"
        project_path = str(self.test_project_dir)

        # Create a mock session
        session = ExplorationSession(session_id=session_id, project_path=project_path)

        # Mock the session manager and tree manager
        with (
            patch("repomap_tool.trees.SessionManager") as mock_session_manager_class,
            patch("repomap_tool.trees.TreeManager") as mock_tree_manager_class,
            patch("repomap_tool.cli.RepoMapService") as mock_repomap_class,
        ):

            mock_session_manager = MagicMock()
            mock_session_manager_class.return_value = mock_session_manager
            mock_session_manager.get_session.return_value = session

            mock_tree_manager = MagicMock()
            mock_tree_manager_class.return_value = mock_tree_manager
            mock_tree_manager.focus_tree.return_value = True

            mock_repomap = MagicMock()
            mock_repomap_class.return_value = mock_repomap

            # Set environment variable
            with patch.dict(os.environ, {"REPOMAP_SESSION": session_id}):
                # Change to different directory
                with self.runner.isolated_filesystem():
                    os.chdir(self.other_dir)

                    # Run focus command
                    result = self.runner.invoke(
                        cli, ["explore", "focus", "test_tree_id"]
                    )

                    # Verify the command succeeded
                    assert result.exit_code == 0
                    assert "✅ Focused on tree: test_tree_id" in result.output

                    # Verify RepoMapService was initialized with correct project path
                    mock_repomap_class.assert_called_once()
                    call_args = mock_repomap_class.call_args
                    config = call_args[0][0]  # First positional argument
                    assert os.path.realpath(
                        str(config.project_root)
                    ) == os.path.realpath(project_path)

    def test_expand_command_uses_session_project_path(self):
        """Test that expand command uses project path from session data."""
        session_id = "test_session_789"
        project_path = str(self.test_project_dir)

        # Create a mock session
        session = ExplorationSession(session_id=session_id, project_path=project_path)

        # Mock the session manager and tree manager
        with (
            patch("repomap_tool.trees.SessionManager") as mock_session_manager_class,
            patch("repomap_tool.trees.TreeManager") as mock_tree_manager_class,
            patch("repomap_tool.cli.RepoMapService") as mock_repomap_class,
        ):

            mock_session_manager = MagicMock()
            mock_session_manager_class.return_value = mock_session_manager
            mock_session_manager.get_session.return_value = session

            mock_tree_manager = MagicMock()
            mock_tree_manager_class.return_value = mock_tree_manager
            mock_tree_manager.expand_tree.return_value = True

            mock_repomap = MagicMock()
            mock_repomap_class.return_value = mock_repomap

            # Set environment variable
            with patch.dict(os.environ, {"REPOMAP_SESSION": session_id}):
                # Change to different directory
                with self.runner.isolated_filesystem():
                    os.chdir(self.other_dir)

                    # Run expand command
                    result = self.runner.invoke(cli, ["explore", "expand", "test_area"])

                    # Verify the command succeeded
                    assert result.exit_code == 0
                    assert "✅ Expanded tree in area: test_area" in result.output

                    # Verify RepoMapService was initialized with correct project path
                    mock_repomap_class.assert_called_once()
                    call_args = mock_repomap_class.call_args
                    config = call_args[0][0]  # First positional argument
                    assert os.path.realpath(
                        str(config.project_root)
                    ) == os.path.realpath(project_path)

    def test_prune_command_uses_session_project_path(self):
        """Test that prune command uses project path from session data."""
        session_id = "test_session_101"
        project_path = str(self.test_project_dir)

        # Create a mock session
        session = ExplorationSession(session_id=session_id, project_path=project_path)

        # Mock the session manager and tree manager
        with (
            patch("repomap_tool.trees.SessionManager") as mock_session_manager_class,
            patch("repomap_tool.trees.TreeManager") as mock_tree_manager_class,
            patch("repomap_tool.cli.RepoMapService") as mock_repomap_class,
        ):

            mock_session_manager = MagicMock()
            mock_session_manager_class.return_value = mock_session_manager
            mock_session_manager.get_session.return_value = session

            mock_tree_manager = MagicMock()
            mock_tree_manager_class.return_value = mock_tree_manager
            mock_tree_manager.prune_tree.return_value = True

            mock_repomap = MagicMock()
            mock_repomap_class.return_value = mock_repomap

            # Set environment variable
            with patch.dict(os.environ, {"REPOMAP_SESSION": session_id}):
                # Change to different directory
                with self.runner.isolated_filesystem():
                    os.chdir(self.other_dir)

                    # Run prune command
                    result = self.runner.invoke(cli, ["explore", "prune", "test_area"])

                    # Verify the command succeeded
                    assert result.exit_code == 0
                    assert "✅ Pruned tree in area: test_area" in result.output

                    # Verify RepoMapService was initialized with correct project path
                    mock_repomap_class.assert_called_once()
                    call_args = mock_repomap_class.call_args
                    config = call_args[0][0]  # First positional argument
                    assert os.path.realpath(
                        str(config.project_root)
                    ) == os.path.realpath(project_path)

    def test_map_command_uses_session_project_path(self):
        """Test that map command uses project path from session data."""
        session_id = "test_session_202"
        project_path = str(self.test_project_dir)

        # Create a mock session
        session = ExplorationSession(session_id=session_id, project_path=project_path)

        # Mock the session manager and tree manager
        with (
            patch("repomap_tool.trees.SessionManager") as mock_session_manager_class,
            patch("repomap_tool.trees.TreeManager") as mock_tree_manager_class,
            patch("repomap_tool.trees.TreeMapper") as mock_tree_mapper_class,
            patch("repomap_tool.cli.RepoMapService") as mock_repomap_class,
        ):

            mock_session_manager = MagicMock()
            mock_session_manager_class.return_value = mock_session_manager
            mock_session_manager.get_session.return_value = session

            mock_tree_manager = MagicMock()
            mock_tree_manager_class.return_value = mock_tree_manager
            mock_tree_manager.get_tree_state.return_value = MagicMock()

            mock_tree_mapper = MagicMock()
            mock_tree_mapper_class.return_value = mock_tree_mapper
            mock_tree_mapper.generate_tree_map.return_value = "Mock tree map"

            mock_repomap = MagicMock()
            mock_repomap_class.return_value = mock_repomap

            # Set environment variable
            with patch.dict(os.environ, {"REPOMAP_SESSION": session_id}):
                # Change to different directory
                with self.runner.isolated_filesystem():
                    os.chdir(self.other_dir)

                    # Run map command
                    result = self.runner.invoke(cli, ["explore", "map"])

                    # Verify the command succeeded
                    assert result.exit_code == 0
                    assert "Mock tree map" in result.output

                    # Verify RepoMapService was initialized with correct project path
                    mock_repomap_class.assert_called_once()
                    call_args = mock_repomap_class.call_args
                    config = call_args[0][0]  # First positional argument
                    assert os.path.realpath(
                        str(config.project_root)
                    ) == os.path.realpath(project_path)

    def test_list_trees_command_uses_session_project_path(self):
        """Test that list-trees command uses project path from session data."""
        session_id = "test_session_303"
        project_path = str(self.test_project_dir)

        # Create a mock session with some trees
        session = ExplorationSession(session_id=session_id, project_path=project_path)
        session.exploration_trees = {"tree1": MagicMock(), "tree2": MagicMock()}

        # Mock the session manager
        with (
            patch("repomap_tool.trees.SessionManager") as mock_session_manager_class,
            patch("repomap_tool.cli.RepoMapService") as mock_repomap_class,
        ):

            mock_session_manager = MagicMock()
            mock_session_manager_class.return_value = mock_session_manager
            mock_session_manager.get_session.return_value = session

            mock_repomap = MagicMock()
            mock_repomap_class.return_value = mock_repomap

            # Set environment variable
            with patch.dict(os.environ, {"REPOMAP_SESSION": session_id}):
                # Change to different directory
                with self.runner.isolated_filesystem():
                    os.chdir(self.other_dir)

                    # Run list-trees command
                    result = self.runner.invoke(cli, ["explore", "trees"])

                    # Verify the command succeeded
                    assert result.exit_code == 0

                    # Verify RepoMapService was initialized with correct project path
                    mock_repomap_class.assert_called_once()
                    call_args = mock_repomap_class.call_args
                    config = call_args[0][0]  # First positional argument
                    assert os.path.realpath(
                        str(config.project_root)
                    ) == os.path.realpath(project_path)

    def test_commands_fail_when_session_not_found(self):
        """Test that commands fail gracefully when session is not found."""
        session_id = "nonexistent_session"

        # Mock SessionManager to return None
        with patch("repomap_tool.trees.SessionManager") as mock_session_manager_class:
            mock_session_manager = MagicMock()
            mock_session_manager_class.return_value = mock_session_manager
            mock_session_manager.get_session.return_value = None

            # Set environment variable
            with patch.dict(os.environ, {"REPOMAP_SESSION": session_id}):
                # Test focus command
                result = self.runner.invoke(cli, ["explore", "focus", "test_tree"])
                assert (
                    result.exit_code == 0
                )  # Command doesn't exit with error, just returns
                assert "💡 Make sure you have an active session" in result.output

                # Test expand command
                result = self.runner.invoke(cli, ["explore", "expand", "test_area"])
                assert result.exit_code == 0
                assert "💡 Make sure you have an active session" in result.output

                # Test prune command
                result = self.runner.invoke(cli, ["explore", "prune", "test_area"])
                assert result.exit_code == 0
                assert "💡 Make sure you have an active session" in result.output

                # Test map command
                result = self.runner.invoke(cli, ["explore", "map"])
                assert result.exit_code == 0
                assert "💡 Make sure you have an active session" in result.output

                # Test list-trees command
                result = self.runner.invoke(cli, ["explore", "trees"])
                assert result.exit_code == 0
                assert "💡 Make sure you have an active session" in result.output

    def test_commands_work_from_different_directories(self):
        """Test that commands work correctly when run from different directories."""
        session_id = "test_session_404"
        project_path = str(self.test_project_dir)

        # Create a mock session
        session = ExplorationSession(session_id=session_id, project_path=project_path)

        # Mock the session manager and tree manager
        with (
            patch("repomap_tool.trees.SessionManager") as mock_session_manager_class,
            patch("repomap_tool.trees.TreeManager") as mock_tree_manager_class,
            patch("repomap_tool.cli.RepoMapService") as mock_repomap_class,
        ):

            mock_session_manager = MagicMock()
            mock_session_manager_class.return_value = mock_session_manager
            mock_session_manager.get_session.return_value = session

            mock_tree_manager = MagicMock()
            mock_tree_manager_class.return_value = mock_tree_manager
            mock_tree_manager.focus_tree.return_value = True

            mock_repomap = MagicMock()
            mock_repomap_class.return_value = mock_repomap

            # Set environment variable
            with patch.dict(os.environ, {"REPOMAP_SESSION": session_id}):
                # Test from multiple different directories
                test_dirs = [
                    self.other_dir,
                    Path(self.temp_dir) / "yet_another_dir",
                    Path.home(),  # User's home directory
                ]

                for test_dir in test_dirs:
                    if not test_dir.exists():
                        test_dir.mkdir(parents=True)

                    with self.runner.isolated_filesystem():
                        os.chdir(test_dir)

                        # Run focus command
                        result = self.runner.invoke(
                            cli, ["explore", "focus", "test_tree"]
                        )

                        # Verify the command succeeded
                        assert result.exit_code == 0
                        assert "✅ Focused on tree: test_tree" in result.output

                        # Verify RepoMapService was initialized with correct project path
                        mock_repomap_class.assert_called_once()
                        call_args = mock_repomap_class.call_args
                        config = call_args[0][0]  # First positional argument
                        assert os.path.realpath(
                            str(config.project_root)
                        ) == os.path.realpath(project_path)

                        # Reset mock for next iteration
                        mock_repomap_class.reset_mock()
