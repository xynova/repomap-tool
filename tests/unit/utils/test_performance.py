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
import time
import shutil
from repomap_tool.core.file_scanner import get_project_files

from repomap_tool.models import RepoMapConfig, PerformanceConfig
from repomap_tool.core.repo_map import RepoMapService


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


class TestGeneralPerformance:
    """Test general performance of core RepoMap functionalities."""

    def test_file_scanning_performance(self, session_test_repo_path):
        """Test performance of file scanning with various files."""
        # Arrange
        num_files = 100  # Reduced from 1000 to 100
        file_size_kb = 1  # Reduced from 10MB to 1KB per file
        test_files_dir = session_test_repo_path.parent / "temp_large_repo"
        test_files_dir.mkdir(exist_ok=True)

        # Create dummy files with reasonable size
        for i in range(num_files):
            (test_files_dir / f"file_{i}.py").write_text(
                "#" * (file_size_kb * 1024)  # 1KB per file
            )

        start_time = time.time()
        _ = get_project_files(str(test_files_dir))
        end_time = time.time()
        duration = end_time - start_time

        # Assert that scanning is reasonably fast (e.g., less than 2 seconds for 100 files)
        assert duration < 2

        # Cleanup
        shutil.rmtree(test_files_dir)


if __name__ == "__main__":
    pytest.main([__file__])
