#!/usr/bin/env python3
"""
Edge Case and "Easy to Break" Tests

This module tests boundary conditions, error scenarios, and ways to break the system.
These tests focus on robustness and error handling rather than happy path scenarios.
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock

from repomap_tool.core.search_engine import (
    fuzzy_search,
    semantic_search,
    hybrid_search,
    basic_search,
)
from repomap_tool.core.analyzer import (
    analyze_file_types,
    analyze_identifier_types,
)
from repomap_tool.models import (
    RepoMapConfig,
    SearchRequest,
    FuzzyMatchConfig,
)
from repomap_tool.core.repo_map import DockerRepoMap


class TestSearchEngineEdgeCases:
    """Test edge cases that can break search engine functions."""

    def test_fuzzy_search_with_malicious_input(self):
        """Test fuzzy search with potentially malicious input."""
        # Arrange - Various malicious inputs
        malicious_inputs = [
            "",  # Empty string
            "a" * 10000,  # Very long string
            "\x00\x01\x02",  # Binary data
            "test\x00injection",  # Null byte injection
            "test\n\r\t",  # Control characters
            "test<script>alert('xss')</script>",  # XSS attempt
            "test'; DROP TABLE users; --",  # SQL injection attempt
            "test" + "\\" * 1000,  # Many backslashes
            "test" + "\\x00" * 100,  # Many null bytes
        ]

        mock_matcher = Mock()
        mock_matcher.match_identifiers.return_value = []

        for malicious_input in malicious_inputs:
            # Act
            results = fuzzy_search(malicious_input, ["test"], mock_matcher, 10)

            # Assert - Should not crash or behave unexpectedly
            assert isinstance(results, list)
            assert all(isinstance(r.identifier, str) for r in results)

    def test_semantic_search_with_unicode_edge_cases(self):
        """Test semantic search with Unicode edge cases."""
        # Arrange - Unicode edge cases
        unicode_inputs = [
            "café",  # Accented characters
            "测试",  # Chinese characters
            "🎉🎊🎈",  # Emojis
            "test\u0000test",  # Null character
            "test\u200b",  # Zero-width space
            "test\u2028",  # Line separator
            "test\u2029",  # Paragraph separator
            "test\ufeff",  # Byte order mark
            "test" + "\u0300" * 100,  # Many combining characters
        ]

        mock_matcher = Mock()
        mock_matcher.find_semantic_matches.return_value = []

        for unicode_input in unicode_inputs:
            # Act
            results = semantic_search(unicode_input, ["test"], mock_matcher, 10)

            # Assert - Should handle Unicode gracefully
            assert isinstance(results, list)

    def test_hybrid_search_with_corrupted_matcher(self):
        """Test hybrid search with corrupted or broken matcher."""
        # Arrange - Various broken matcher scenarios
        broken_matchers = [
            Mock(build_tfidf_model=Mock(side_effect=Exception("Corrupted model"))),
            Mock(match_identifiers=Mock(side_effect=MemoryError("Out of memory"))),
            Mock(build_tfidf_model=Mock(side_effect=RecursionError("Stack overflow"))),
        ]

        for broken_matcher in broken_matchers:
            # Act
            results = hybrid_search("test", ["test"], broken_matcher, 10)

            # Assert - Should handle broken matcher gracefully
            assert isinstance(results, list)
            assert len(results) == 0

    def test_basic_search_with_extreme_inputs(self):
        """Test basic search with extreme input conditions."""
        # Arrange - Extreme inputs
        extreme_cases = [
            ("", []),  # Empty query, empty identifiers
            ("", ["test"]),  # Empty query, non-empty identifiers
            ("test", []),  # Non-empty query, empty identifiers
            ("a" * 10000, ["test"]),  # Very long query
            ("test", ["a" * 10000]),  # Very long identifier
            ("test", ["test"] * 10000),  # Many identifiers
            ("\x00", ["test"]),  # Query with null byte
            ("test", ["\x00"]),  # Identifier with null byte
        ]

        for query, identifiers in extreme_cases:
            # Act
            results = basic_search(query, identifiers, 10)

            # Assert - Should not crash
            assert isinstance(results, list)
            assert all(isinstance(r.identifier, str) for r in results)

    def test_search_functions_with_none_inputs(self):
        """Test search functions with None inputs."""
        # Arrange
        search_functions = [
            (fuzzy_search, Mock()),
        ]

        for search_func, mock_matcher in search_functions:
            # Act & Assert - Should handle None gracefully (defensive programming)
            # The functions catch exceptions and return empty lists
            try:
                results = search_func(None, ["test"], mock_matcher, 10)
                assert isinstance(results, list)
            except Exception as e:
                pytest.fail(f"None query input broke the system: {e}")

            try:
                results = search_func("test", None, mock_matcher, 10)
                assert isinstance(results, list)
            except Exception as e:
                pytest.fail(f"None identifiers input broke the system: {e}")

    def test_search_functions_that_need_improvement(self):
        """Test search functions that need improvement for None input handling."""
        # Arrange - Functions that currently don't handle None inputs properly
        # Test semantic_search with proper mock configuration
        semantic_mock = Mock()
        semantic_mock.find_semantic_matches.return_value = []

        # Test hybrid_search with proper mock configuration
        hybrid_mock = Mock()
        hybrid_mock.build_tfidf_model.return_value = None
        hybrid_mock.match_identifiers.return_value = []

        search_functions = [
            (semantic_search, semantic_mock),
            (hybrid_search, hybrid_mock),
        ]

        for search_func, mock_matcher in search_functions:
            # Act & Assert - Should handle None gracefully (defensive programming)
            # The functions catch exceptions and return empty lists
            try:
                results = search_func(None, ["test"], mock_matcher, 10)
                assert isinstance(results, list)
            except Exception as e:
                pytest.fail(f"None query input broke the system: {e}")

            try:
                results = search_func("test", None, mock_matcher, 10)
                assert isinstance(results, list)
            except Exception as e:
                pytest.fail(f"None identifiers input broke the system: {e}")

    def test_search_functions_with_invalid_types(self):
        """Test search functions with invalid type inputs."""
        # Arrange
        invalid_inputs = [
            123,  # Integer instead of string
            3.14,  # Float instead of string
            True,  # Boolean instead of string
            [],  # List instead of string
            {},  # Dict instead of string
            set(),  # Set instead of string
        ]

        mock_matcher = Mock()
        mock_matcher.match_identifiers.return_value = []

        for invalid_input in invalid_inputs:
            # Act & Assert - Should handle invalid types gracefully (defensive programming)
            try:
                results = fuzzy_search(invalid_input, ["test"], mock_matcher, 10)
                assert isinstance(results, list)
            except Exception as e:
                pytest.fail(f"Invalid type input broke the system: {e}")

    def test_search_functions_with_negative_limits(self):
        """Test search functions with negative limits."""
        # Arrange
        mock_matcher = Mock()
        mock_matcher.match_identifiers.return_value = [("test", 100)]

        # Act
        results = fuzzy_search("test", ["test"], mock_matcher, -1)

        # Assert - Should handle negative limits gracefully
        assert isinstance(results, list)

    def test_search_functions_with_zero_limits(self):
        """Test search functions with zero limits."""
        # Arrange
        mock_matcher = Mock()
        mock_matcher.match_identifiers.return_value = [("test", 100)]

        # Act
        results = fuzzy_search("test", ["test"], mock_matcher, 0)

        # Assert - Should return empty list
        assert len(results) == 0


class TestAnalyzerEdgeCases:
    """Test edge cases that can break analyzer functions."""

    def test_analyze_file_types_with_malicious_paths(self):
        """Test file type analysis with malicious file paths."""
        # Arrange - Malicious file paths
        malicious_paths = [
            "",  # Empty path
            "a" * 10000,  # Very long path
            "../../../etc/passwd",  # Path traversal attempt
            "test\x00.py",  # Path with null byte
            "test\n.py",  # Path with newline
            "test\r.py",  # Path with carriage return
            "test\t.py",  # Path with tab
            "test<script>.py",  # Path with script tags
            "test'; DROP TABLE files; --.py",  # SQL injection in path
            "test" + "\\" * 1000 + ".py",  # Many backslashes
        ]

        for malicious_path in malicious_paths:
            # Act
            result = analyze_file_types([malicious_path])

            # Assert - Should not crash
            assert isinstance(result, dict)

    def test_analyze_identifier_types_with_malicious_identifiers(self):
        """Test identifier analysis with malicious identifiers."""
        # Arrange - Malicious identifiers
        malicious_identifiers = {
            "",  # Empty identifier
            "a" * 10000,  # Very long identifier
            "\x00\x01\x02",  # Binary data
            "test\x00injection",  # Null byte injection
            "test\n\r\t",  # Control characters
            "test<script>alert('xss')</script>",  # XSS attempt
            "test'; DROP TABLE identifiers; --",  # SQL injection
            "test" + "\\" * 1000,  # Many backslashes
            "test" + "\\x00" * 100,  # Many null bytes
            "🎉🎊🎈",  # Emojis
            "测试",  # Chinese characters
            "café",  # Accented characters
        }

        # Act
        result = analyze_identifier_types(malicious_identifiers)

        # Assert - Should not crash
        assert isinstance(result, dict)
        assert "functions" in result
        assert "classes" in result
        assert "variables" in result
        assert "constants" in result
        assert "other" in result

    def test_analyze_identifier_types_with_extreme_cases(self):
        """Test identifier analysis with extreme cases."""
        # Arrange - Extreme cases
        extreme_cases = [
            set(),  # Empty set
            {"a" * 10000},  # Very long identifier
            {"a", "b", "c"} | {"d", "e", "f"} | {"g", "h", "i"},  # Multiple identifiers
            {
                "a" + str(i) for i in range(100)
            },  # Many unique identifiers (reduced for performance)
            {
                "a" * i for i in range(100)
            },  # Many different lengths (reduced for performance)
        ]

        for extreme_case in extreme_cases:
            # Act
            result = analyze_identifier_types(extreme_case)

            # Assert - Should not crash
            assert isinstance(result, dict)
            assert all(isinstance(v, int) for v in result.values())

    def test_analyze_identifier_types_with_invalid_types(self):
        """Test identifier analysis with invalid types."""
        # Arrange - Invalid types that should raise exceptions
        invalid_inputs = [
            None,
            123,
            3.14,
            True,
        ]

        for invalid_input in invalid_inputs:
            # Act & Assert - Should handle invalid types gracefully
            # Note: The function currently doesn't validate input types
            # This test documents the expected behavior for future improvements
            with pytest.raises((TypeError, AttributeError)):
                analyze_identifier_types(invalid_input)

    def test_analyze_identifier_types_with_coercible_types(self):
        """Test identifier analysis with types that can be coerced."""
        # Arrange - Types that can be converted to sets
        coercible_inputs = [
            [],  # Empty list (can be converted to set)
            {},  # Empty dict (can be converted to set)
        ]

        for input_data in coercible_inputs:
            # Act & Assert - Should handle coercible types gracefully
            try:
                result = analyze_identifier_types(set(input_data))
                assert isinstance(result, dict)
            except Exception as e:
                pytest.fail(f"Coercible type failed: {e}")


class TestRepoMapEdgeCases:
    """Test edge cases that can break the main RepoMap functionality."""

    def test_repo_map_with_nonexistent_project(self):
        """Test RepoMap with nonexistent project path."""
        # Arrange
        nonexistent_paths = [
            "/nonexistent/path",
            "/tmp/nonexistent_" + str(os.getpid()),
            "relative/nonexistent/path",
            "",  # Empty path
        ]

        for path in nonexistent_paths:
            # Act & Assert - Should handle nonexistent paths gracefully
            with pytest.raises((ValueError, FileNotFoundError)):
                config = RepoMapConfig(project_root=path)
                DockerRepoMap(config)

    def test_repo_map_with_file_as_project_root(self):
        """Test RepoMap with a file as project root (should be directory)."""
        # Arrange
        with tempfile.NamedTemporaryFile() as temp_file:
            # Act & Assert - Should handle file as project root gracefully
            with pytest.raises((ValueError, IsADirectoryError)):
                config = RepoMapConfig(project_root=temp_file.name)
                DockerRepoMap(config)

    def test_repo_map_with_empty_directory(self):
        """Test RepoMap with empty directory."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            config = RepoMapConfig(project_root=temp_dir)
            repomap = DockerRepoMap(config)

            # Act
            project_info = repomap.analyze_project()

            # Assert - Should handle empty directory gracefully
            assert project_info.total_files == 0
            assert project_info.total_identifiers == 0

    def test_repo_map_with_large_directory(self):
        """Test RepoMap with very large directory structure."""
        # Arrange - Create large directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create many nested directories and files
            for i in range(100):
                subdir = Path(temp_dir) / f"dir_{i}"
                subdir.mkdir()
                for j in range(10):
                    file_path = subdir / f"file_{j}.py"
                    file_path.write_text(f"def function_{i}_{j}(): pass")

            config = RepoMapConfig(project_root=temp_dir)
            repomap = DockerRepoMap(config)

            # Act
            project_info = repomap.analyze_project()

            # Assert - Should handle large directory gracefully
            assert project_info.total_files > 0
            assert project_info.total_identifiers > 0

    def test_repo_map_with_corrupted_files(self):
        """Test RepoMap with corrupted or unreadable files."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create corrupted files
            corrupted_files = [
                ("binary.bin", b"\x00\x01\x02\x03"),
                ("unicode_error.py", "def test(): \x00 pass".encode("utf-8")),
                ("permission_denied.py", "def test(): pass"),
            ]

            for filename, content in corrupted_files:
                file_path = Path(temp_dir) / filename
                if filename == "permission_denied.py":
                    file_path.write_text("def test(): pass")
                    # Make file unreadable (Unix only)
                    if os.name != "nt":
                        os.chmod(file_path, 0o000)
                else:
                    file_path.write_bytes(content)

            config = RepoMapConfig(project_root=temp_dir)
            repomap = DockerRepoMap(config)

            # Act
            project_info = repomap.analyze_project()

            # Assert - Should handle corrupted files gracefully
            assert isinstance(project_info.total_files, int)
            assert isinstance(project_info.total_identifiers, int)

    def test_repo_map_with_symlinks(self):
        """Test RepoMap with symbolic links."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file and a symlink to it
            original_file = Path(temp_dir) / "original.py"
            original_file.write_text("def original(): pass")

            symlink_file = Path(temp_dir) / "symlink.py"
            if os.name != "nt":  # Unix-like systems
                symlink_file.symlink_to(original_file)
            else:
                # On Windows, create a copy instead
                shutil.copy2(original_file, symlink_file)

            config = RepoMapConfig(project_root=temp_dir)
            repomap = DockerRepoMap(config)

            # Act
            project_info = repomap.analyze_project()

            # Assert - Should handle symlinks gracefully
            assert isinstance(project_info.total_files, int)

    def test_repo_map_with_circular_symlinks(self):
        """Test RepoMap with circular symbolic links."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            if os.name != "nt":  # Unix-like systems only
                # Create circular symlinks
                link1 = Path(temp_dir) / "link1"
                link2 = Path(temp_dir) / "link2"
                link1.symlink_to(link2)
                link2.symlink_to(link1)

                config = RepoMapConfig(project_root=temp_dir)
                repomap = DockerRepoMap(config)

                # Act
                project_info = repomap.analyze_project()

                # Assert - Should handle circular symlinks gracefully
                assert isinstance(project_info.total_files, int)

    def test_repo_map_with_special_files(self):
        """Test RepoMap with special files (devices, sockets, etc.)."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create various special files
            special_files = [
                ("fifo", "mkfifo"),  # Named pipe
                ("socket", "socket"),  # Socket
            ]

            for filename, file_type in special_files:
                file_path = Path(temp_dir) / filename
                if file_type == "mkfifo" and os.name != "nt":
                    os.mkfifo(file_path)
                elif file_type == "socket" and os.name != "nt":
                    import socket

                    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    sock.bind(str(file_path))
                    sock.close()

            config = RepoMapConfig(project_root=temp_dir)
            repomap = DockerRepoMap(config)

            # Act
            project_info = repomap.analyze_project()

            # Assert - Should handle special files gracefully
            assert isinstance(project_info.total_files, int)


class TestConfigurationEdgeCases:
    """Test edge cases with configuration."""

    def test_config_with_invalid_thresholds(self):
        """Test configuration with invalid threshold values."""
        # Arrange - Invalid threshold values
        invalid_thresholds = [
            -1,  # Negative threshold
            101,  # Above 100
            1000,  # Way above 100
            -1000,  # Way below 0
        ]

        for threshold in invalid_thresholds:
            # Act & Assert - Should handle invalid thresholds gracefully
            with pytest.raises(ValueError):
                FuzzyMatchConfig(threshold=threshold)

    def test_config_with_invalid_paths(self):
        """Test configuration with invalid paths."""
        # Arrange - Invalid paths
        invalid_paths = [
            "",  # Empty path
            "a" * 10000,  # Very long path
            "\x00",  # Path with null byte
            "test\n",  # Path with newline
            "test\r",  # Path with carriage return
            "test\t",  # Path with tab
        ]

        for path in invalid_paths:
            # Act & Assert - Should handle invalid paths gracefully
            with pytest.raises(ValueError):
                RepoMapConfig(project_root=path)

    def test_config_with_extreme_values(self):
        """Test configuration with extreme values."""
        # Arrange - Extreme values
        extreme_values = [
            {"map_tokens": 0},  # Zero tokens
            {"map_tokens": 1000000},  # Very many tokens
            {"max_results": 0},  # Zero max results
            {"max_results": 1000000},  # Very many max results
        ]

        for extreme_value in extreme_values:
            # Act & Assert - Should handle extreme values gracefully
            with pytest.raises(ValueError):
                RepoMapConfig(project_root=".", **extreme_value)


class TestMemoryAndPerformanceEdgeCases:
    """Test edge cases related to memory and performance."""

    def test_search_with_many_identifiers(self):
        """Test search with very many identifiers."""
        # Arrange - Many identifiers
        many_identifiers = [f"identifier_{i}" for i in range(10000)]
        mock_matcher = Mock()
        mock_matcher.match_identifiers.return_value = []

        # Act
        results = fuzzy_search("test", many_identifiers, mock_matcher, 10)

        # Assert - Should handle many identifiers gracefully
        assert isinstance(results, list)

    def test_analyzer_with_many_files(self):
        """Test analyzer with very many files."""
        # Arrange - Many files
        many_files = [f"file_{i}.py" for i in range(10000)]

        # Act
        result = analyze_file_types(many_files)

        # Assert - Should handle many files gracefully
        assert isinstance(result, dict)
        assert result["py"] == 10000

    def test_identifier_analysis_with_many_identifiers(self):
        """Test identifier analysis with very many identifiers."""
        # Arrange - Many identifiers
        many_identifiers = {f"identifier_{i}" for i in range(10000)}

        # Act
        result = analyze_identifier_types(many_identifiers)

        # Assert - Should handle many identifiers gracefully
        assert isinstance(result, dict)
        assert sum(result.values()) == 10000


class TestConcurrencyEdgeCases:
    """Test edge cases related to concurrency."""

    def test_concurrent_access_to_shared_resources(self):
        """Test concurrent access to shared resources."""
        # Arrange
        import threading

        results = []
        errors = []

        def search_worker():
            try:
                mock_matcher = Mock()
                mock_matcher.match_identifiers.return_value = [("test", 100)]
                result = fuzzy_search("test", ["test"], mock_matcher, 10)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Act - Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=search_worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Assert - Should handle concurrent access gracefully
        assert len(results) == 10
        assert len(errors) == 0


class TestIntegrationEdgeCases:
    """Test edge cases in integration scenarios."""

    def test_full_workflow_with_edge_cases(self):
        """Test full workflow with various edge cases."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with edge cases
            edge_case_files = [
                ("empty.py", ""),
                ("unicode.py", "def café(): pass"),
                ("emoji.py", "def 🎉(): pass"),
                ("chinese.py", "def 测试(): pass"),
                ("control_chars.py", "def test\x00(): pass"),
                ("very_long.py", "def " + "a" * 1000 + "(): pass"),
            ]

            for filename, content in edge_case_files:
                file_path = Path(temp_dir) / filename
                file_path.write_text(content)

            config = RepoMapConfig(project_root=temp_dir)
            repomap = DockerRepoMap(config)

            # Act
            project_info = repomap.analyze_project()

            # Assert - Should handle edge cases gracefully
            assert isinstance(project_info.total_files, int)
            assert isinstance(project_info.total_identifiers, int)

            # Test search with edge cases
            search_request = SearchRequest(
                query="test", match_type="fuzzy", max_results=5
            )
            search_response = repomap.search_identifiers(search_request)

            # Assert - Should handle search with edge cases gracefully
            assert isinstance(search_response.total_results, int)
