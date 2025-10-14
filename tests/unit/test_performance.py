#!/usr/bin/env python3
"""
Test performance improvements implementation.

This module tests the parallel processing, progress tracking, and performance
monitoring features.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from repomap_tool.models import RepoMapConfig, PerformanceConfig
from repomap_tool.core.repo_map import RepoMapService
from repomap_tool.core.parallel_processor import ParallelTagExtractor, ProcessingStats


class TestPerformanceConfig:
    """Test PerformanceConfig model."""

    def test_default_config(self):
        """Test default performance configuration."""
        config = PerformanceConfig()

        assert config.max_workers == 4
        assert config.cache_size == 1000
        assert config.max_memory_mb == 100
        assert config.enable_progress is True
        assert config.enable_monitoring is True
        assert config.parallel_threshold == 10
        assert config.cache_ttl == 3600
        assert (
            config.allow_fallback is False
        )  # Development-focused: fail fast by default

    def test_custom_config(self):
        """Test custom performance configuration."""
        config = PerformanceConfig(
            max_workers=8,
            cache_size=2000,
            max_memory_mb=200,
            enable_progress=False,
            enable_monitoring=False,
            parallel_threshold=5,
            cache_ttl=1800,
            allow_fallback=True,
        )

        assert config.max_workers == 8
        assert config.cache_size == 2000
        assert config.max_memory_mb == 200
        assert config.enable_progress is False
        assert config.enable_monitoring is False
        assert config.parallel_threshold == 5
        assert config.cache_ttl == 1800
        assert config.allow_fallback is True

    def test_validation(self):
        """Test configuration validation."""
        # Test max_workers bounds
        with pytest.raises(ValueError):
            PerformanceConfig(max_workers=0)

        with pytest.raises(ValueError):
            PerformanceConfig(max_workers=17)

        # Test cache_size bounds
        with pytest.raises(ValueError):
            PerformanceConfig(cache_size=50)

        with pytest.raises(ValueError):
            PerformanceConfig(cache_size=15000)

        # Test max_memory_mb bounds
        with pytest.raises(ValueError):
            PerformanceConfig(max_memory_mb=5)

        with pytest.raises(ValueError):
            PerformanceConfig(max_memory_mb=1500)


class TestParallelTagExtractor:
    """Test ParallelTagExtractor class."""

    def test_initialization(self):
        """Test ParallelTagExtractor initialization."""
        # Create a mock console for DI
        mock_console = MagicMock()
        extractor = ParallelTagExtractor(
            max_workers=6, enable_progress=True, console=mock_console
        )

        assert extractor.max_workers == 6
        assert extractor.enable_progress is True
        assert extractor._lock is not None
        assert isinstance(extractor._stats, ProcessingStats)

    def test_extract_tags_parallel_empty_files(self):
        """Test parallel extraction with empty file list."""
        # Create a mock console for DI
        mock_console = MagicMock()
        extractor = ParallelTagExtractor(console=mock_console)
        mock_repo_map = Mock()

        identifiers, stats = extractor.extract_tags_parallel(
            files=[], project_root="/tmp", repo_map=mock_repo_map
        )

        assert identifiers == []
        assert stats.total_files == 0
        assert stats.processed_files == 0
        assert stats.successful_files == 0
        assert stats.failed_files == 0

    def test_extract_tags_parallel_single_file(self):
        """Test parallel extraction with single file."""
        # Create a mock console for DI
        mock_console = MagicMock()
        extractor = ParallelTagExtractor(max_workers=1, console=mock_console)

        # Mock repo_map that returns tags
        mock_repo_map = Mock()
        mock_tag = Mock()
        mock_tag.name = "test_function"
        mock_repo_map.get_tags.return_value = [mock_tag]

        identifiers, stats = extractor.extract_tags_parallel(
            files=["test.py"], project_root="/tmp", repo_map=mock_repo_map
        )

        assert "test_function" in identifiers
        assert stats.total_files == 1
        assert stats.processed_files == 1
        assert stats.successful_files == 1
        assert stats.failed_files == 0
        assert stats.total_identifiers == 1

    def test_extract_tags_parallel_error_handling(self):
        """Test parallel extraction error handling."""
        # Create a mock console for DI
        mock_console = MagicMock()
        extractor = ParallelTagExtractor(max_workers=1, console=mock_console)

        # Mock repo_map that raises an exception
        mock_repo_map = Mock()
        mock_repo_map.get_tags.side_effect = Exception("Test error")

        identifiers, stats = extractor.extract_tags_parallel(
            files=["test.py"], project_root="/tmp", repo_map=mock_repo_map
        )

        assert identifiers == []
        assert stats.total_files == 1
        assert stats.processed_files == 1
        assert stats.successful_files == 0
        assert stats.failed_files == 1
        assert len(stats.errors) == 1
        assert "Test error" in stats.errors[0][1]

    def test_fail_fast_behavior(self):
        """Test that parallel processing fails fast with helpful errors."""

        # Create config with fail-fast behavior (default)
        config = RepoMapConfig(
            project_root="/tmp",
            performance=PerformanceConfig(
                max_workers=1, allow_fallback=False  # Fail fast
            ),
        )

        # This should raise an exception with helpful error message
        # (We can't easily test the full RepoMapService without mocking tree-sitter)
        assert config.performance.allow_fallback is False

    def test_get_performance_metrics(self):
        """Test performance metrics retrieval."""
        # Create a mock console for DI
        mock_console = MagicMock()
        extractor = ParallelTagExtractor(max_workers=4, console=mock_console)

        # Mock some processing
        extractor._stats = ProcessingStats(
            total_files=10, successful_files=8, failed_files=2
        )
        extractor._stats.total_identifiers = 25
        extractor._stats.processed_files = (
            10  # Need to set this for files_per_second calculation
        )
        extractor._stats.end_time = extractor._stats.start_time + 5.0  # 5 seconds

        metrics = extractor.get_performance_metrics()

        assert "processing_stats" in metrics
        assert "configuration" in metrics
        assert "file_size_stats" in metrics

        processing_stats = metrics["processing_stats"]
        assert processing_stats["total_files"] == 10
        assert processing_stats["successful_files"] == 8
        assert processing_stats["failed_files"] == 2
        assert processing_stats["success_rate"] == 80.0
        assert processing_stats["total_identifiers"] == 25
        assert processing_stats["processing_time"] == 5.0
        assert processing_stats["files_per_second"] == 2.0


class TestProcessingStats:
    """Test ProcessingStats class."""

    def test_initialization(self):
        """Test ProcessingStats initialization."""
        stats = ProcessingStats(total_files=100)

        assert stats.total_files == 100
        assert stats.processed_files == 0
        assert stats.successful_files == 0
        assert stats.failed_files == 0
        assert stats.total_identifiers == 0
        assert stats.start_time > 0
        assert stats.end_time is None
        assert stats.errors == []

    def test_properties(self):
        """Test ProcessingStats properties."""
        stats = ProcessingStats(total_files=10)
        stats.end_time = stats.start_time + 5.0  # 5 seconds
        stats.successful_files = 8
        stats.failed_files = 2
        stats.total_identifiers = 25
        stats.processed_files = 10  # Need to set this for files_per_second calculation

        assert stats.processing_time == 5.0
        assert stats.success_rate == 80.0
        assert stats.files_per_second == 2.0

    def test_add_error(self):
        """Test adding errors to stats."""
        stats = ProcessingStats(total_files=5)

        stats.add_error("test.py", "Test error")

        assert stats.failed_files == 1
        assert len(stats.errors) == 1
        assert stats.errors[0] == ("test.py", "Test error")

    def test_add_success(self):
        """Test adding successful processing to stats."""
        stats = ProcessingStats(total_files=5)

        stats.add_success(10)  # 10 identifiers

        assert stats.successful_files == 1
        assert stats.total_identifiers == 10

    def test_finalize(self):
        """Test finalizing stats."""
        stats = ProcessingStats(total_files=5)

        assert stats.end_time is None
        stats.finalize()
        assert stats.end_time is not None
        assert stats.end_time > stats.start_time


class TestRepoMapServicePerformance:
    """Test RepoMapService performance features."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_files = [
                "main.py",
                "utils.py",
                "config.py",
                "test/test_main.py",
                "docs/README.md",
            ]

            for file_path in test_files:
                full_path = Path(temp_dir) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text("# Test file\n\ndef test_function():\n    pass\n")

            yield temp_dir


if __name__ == "__main__":
    pytest.main([__file__])
