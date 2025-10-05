"""
Integration tests for centrality ranking consistency.

This module tests that centrality analysis returns consistent rankings
between table format and individual file analysis.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

from repomap_tool.core.config_factory import get_config_factory
from repomap_tool.cli.services import get_service_factory
from repomap_tool.code_analysis import AnalysisFormat
from repomap_tool.code_analysis.format_utils import format_table_centrality
from repomap_tool.code_analysis.llm_file_analyzer import LLMFileAnalyzer


class TestCentralityRankingConsistency:
    """Test that centrality rankings are consistent between different output formats."""

    @pytest.fixture
    def test_project(self):
        """Create a temporary test project with multiple files."""
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)

        # Create a simple project structure with dependencies
        (project_path / "src").mkdir()
        (project_path / "src" / "core").mkdir()
        (project_path / "src" / "utils").mkdir()
        (project_path / "tests").mkdir()

        # Create main.py (most central file - imports everything)
        main_py = project_path / "src" / "main.py"
        main_py.write_text(
            """
import sys
from src.core.task import Task
from src.core.config import Config
from src.utils.helpers import Helper

def main():
    task = Task()
    config = Config()
    helper = Helper()
    return task.run(config, helper)

if __name__ == "__main__":
    main()
"""
        )

        # Create core/task.py (imported by main)
        task_py = project_path / "src" / "core" / "task.py"
        task_py.write_text(
            """
from src.core.config import Config
from src.utils.helpers import Helper

class Task:
    def __init__(self):
        self.config = Config()
        self.helper = Helper()

    def run(self, config, helper):
        return helper.process(config)
"""
        )

        # Create core/config.py (imported by main and task)
        config_py = project_path / "src" / "core" / "config.py"
        config_py.write_text(
            """
class Config:
    def __init__(self):
        self.settings = {"debug": True}

    def get_setting(self, key):
        return self.settings.get(key)
"""
        )

        # Create utils/helpers.py (imported by main and task)
        helpers_py = project_path / "src" / "utils" / "helpers.py"
        helpers_py.write_text(
            """
def process(config):
    return f"Processing with config: {config.get_setting('debug')}"

def utility_function():
    return "utility"
"""
        )

        # Create test file (least central - only imports main)
        test_py = project_path / "tests" / "test_main.py"
        test_py.write_text(
            """
import sys
sys.path.append('src')
from src.main import main

def test_main():
    result = main()
    assert result is not None
"""
        )

        # Create __init__.py files to make them proper Python packages
        (project_path / "src" / "__init__.py").write_text("")
        (project_path / "src" / "core" / "__init__.py").write_text("")
        (project_path / "src" / "utils" / "__init__.py").write_text("")

        yield str(project_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def config(self, test_project):
        """Create configuration for the test project."""
        config_factory = get_config_factory()
        return config_factory.create_analysis_config(
            project_root=test_project,
            verbose=False,
        )

    @pytest.fixture
    def service_factory(self, config):
        """Create service factory with test configuration."""
        return get_service_factory()

    @pytest.fixture
    def repomap_service(self, service_factory, config):
        """Create RepoMap service for testing."""
        service = service_factory.create_repomap_service(config)
        # Build dependency graph
        service.build_dependency_graph()
        return service

    @pytest.fixture
    def llm_analyzer(self, service_factory, config):
        """Create LLM analyzer for testing."""
        return service_factory.get_llm_analyzer(config)

    def test_centrality_table_vs_individual_consistency(
        self, test_project, llm_analyzer
    ):
        """Test that table format and individual file analysis return consistent rankings."""
        # Get all Python files in the project
        project_files = [
            "src/main.py",
            "src/core/task.py",
            "src/core/config.py",
            "src/utils/helpers.py",
            "tests/test_main.py",
        ]

        # Get centrality analysis in table format
        table_result = llm_analyzer.analyze_file_centrality(
            project_files, AnalysisFormat.TEXT
        )

        # Parse table result to extract rankings
        table_rankings = self._parse_table_rankings(table_result)

        # Get individual file analyses
        individual_rankings = {}
        for file_path in project_files:
            individual_result = llm_analyzer.analyze_file_centrality(
                [file_path], AnalysisFormat.TEXT
            )
            individual_rankings[file_path] = self._parse_table_rankings(
                individual_result
            )

        # Verify consistency
        self._verify_ranking_consistency(table_rankings, individual_rankings)

    def test_centrality_scores_consistency(self, test_project, llm_analyzer):
        """Test that centrality scores are consistent between table and individual analysis."""
        project_files = [
            "src/main.py",
            "src/core/task.py",
            "src/core/config.py",
            "src/utils/helpers.py",
            "tests/test_main.py",
        ]

        # Get table analysis
        table_result = llm_analyzer.analyze_file_centrality(
            project_files, AnalysisFormat.TEXT
        )
        table_scores = self._parse_table_scores(table_result)

        # Get individual analyses
        individual_scores = {}
        for file_path in project_files:
            individual_result = llm_analyzer.analyze_file_centrality(
                [file_path], AnalysisFormat.TEXT
            )
            individual_scores[file_path] = self._parse_table_scores(individual_result)

        # Verify scores are consistent
        for file_path in project_files:
            table_score = table_scores.get(file_path, 0.0)
            individual_score = individual_scores.get(file_path, {}).get(file_path, 0.0)

            assert abs(table_score - individual_score) < 0.001, (
                f"Score mismatch for {file_path}: "
                f"table={table_score}, individual={individual_score}"
            )

    def test_most_important_files_first(self, test_project, llm_analyzer):
        """Test that the most important files appear first in the table."""
        project_files = [
            "src/main.py",
            "src/core/task.py",
            "src/core/config.py",
            "src/utils/helpers.py",
            "tests/test_main.py",
        ]

        # Get table analysis
        table_result = llm_analyzer.analyze_file_centrality(
            project_files, AnalysisFormat.TEXT
        )

        # Parse the table to get files in order
        files_in_order = self._parse_table_file_order(table_result)
        scores_in_order = self._parse_table_scores(table_result)

        # Verify that files are ordered by centrality score (descending)
        for i in range(len(files_in_order) - 1):
            current_file = files_in_order[i]
            next_file = files_in_order[i + 1]

            current_score = scores_in_order.get(current_file, 0.0)
            next_score = scores_in_order.get(next_file, 0.0)

            assert current_score >= next_score, (
                f"Files not ordered by centrality: "
                f"{current_file} (score={current_score}) should come before "
                f"{next_file} (score={next_score})"
            )

    def _parse_table_rankings(self, table_result: str) -> Dict[str, int]:
        """Parse rankings from table format output."""
        rankings = {}
        lines = table_result.split("\n")

        for line in lines:
            if "│" in line or "─" in line or "Score" in line:
                continue
            if not line.strip():
                continue

            # Parse table row: Score Rank Conn Imports Rev Deps Functions File
            parts = line.split()
            if len(parts) >= 7:
                try:
                    score = float(parts[0])
                    rank = int(parts[1])
                    # File path is the last part (may contain spaces)
                    file_path = " ".join(parts[6:])
                    rankings[file_path] = rank
                except (ValueError, IndexError):
                    continue

        return rankings

    def _parse_table_scores(self, table_result: str) -> Dict[str, float]:
        """Parse centrality scores from table format output."""
        scores = {}
        lines = table_result.split("\n")

        for line in lines:
            if "│" in line or "─" in line or "Score" in line:
                continue
            if not line.strip():
                continue

            # Parse table row: Score Rank Conn Imports Rev Deps Functions File
            parts = line.split()
            if len(parts) >= 7:
                try:
                    score = float(parts[0])
                    # File path is the last part (may contain spaces)
                    file_path = " ".join(parts[6:])
                    scores[file_path] = score
                except (ValueError, IndexError):
                    continue

        return scores

    def _parse_table_file_order(self, table_result: str) -> List[str]:
        """Parse file order from table format output."""
        files = []
        lines = table_result.split("\n")

        for line in lines:
            if "│" in line or "─" in line or "Score" in line:
                continue
            if not line.strip():
                continue

            # Parse table row: Score Rank Conn Imports Rev Deps Functions File
            parts = line.split()
            if len(parts) >= 7:
                try:
                    # File path is the last part (may contain spaces)
                    file_path = " ".join(parts[6:])
                    files.append(file_path)
                except (ValueError, IndexError):
                    continue

        return files

    def _verify_ranking_consistency(
        self,
        table_rankings: Dict[str, int],
        individual_rankings: Dict[str, Dict[str, int]],
    ):
        """Verify that rankings are consistent between table and individual analysis."""
        for file_path, table_rank in table_rankings.items():
            individual_rank = individual_rankings.get(file_path, {}).get(file_path, 0)

            assert table_rank == individual_rank, (
                f"Ranking inconsistency for {file_path}: "
                f"table rank={table_rank}, individual rank={individual_rank}"
            )

    def test_ranking_consistency_with_specific_files(self, test_project, llm_analyzer):
        """Test ranking consistency when analyzing specific files only."""
        # Test with just the most important files
        important_files = ["src/main.py", "src/core/task.py"]

        # Get table analysis for these files
        table_result = llm_analyzer.analyze_file_centrality(
            important_files, AnalysisFormat.TEXT
        )
        table_rankings = self._parse_table_rankings(table_result)

        # Get individual analyses
        individual_rankings = {}
        for file_path in important_files:
            individual_result = llm_analyzer.analyze_file_centrality(
                [file_path], AnalysisFormat.TEXT
            )
            individual_rankings[file_path] = self._parse_table_rankings(
                individual_result
            )

        # Verify consistency
        self._verify_ranking_consistency(table_rankings, individual_rankings)

        # Verify that the most important file (main.py) has the highest score
        table_scores = self._parse_table_scores(table_result)
        main_score = table_scores.get("src/main.py", 0.0)
        task_score = table_scores.get("src/core/task.py", 0.0)

        assert main_score >= task_score, (
            f"main.py should have higher or equal centrality score: "
            f"main.py={main_score}, task.py={task_score}"
        )
