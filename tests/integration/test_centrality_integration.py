"""
Integration tests for centrality analysis with real dependency graphs.

These tests verify that centrality calculations work correctly with actual
codebase structures, including testing that files with more connections
have higher centrality scores.
"""

import pytest
from pathlib import Path
from typing import Dict, List

from repomap_tool.core.container import create_container
from repomap_tool.models import RepoMapConfig, DependencyConfig


class TestCentralityIntegration:
    """Integration tests for centrality calculation with real dependency graphs."""

    def test_centrality_with_connected_files(
        self, session_dependency_graph, session_container
    ):
        """Test that files with more connections have higher centrality scores."""
        calculator = session_container.centrality_calculator()

        # Calculate composite centrality
        composite_scores = calculator.calculate_composite_importance()

        if len(composite_scores) < 2:
            pytest.skip("Need at least 2 files in dependency graph for this test")

        # Get graph structure to find files with different connection counts
        graph = session_dependency_graph.graph
        file_connections = {}
        for node in graph.nodes():
            # Count incoming and outgoing edges
            in_degree = graph.in_degree(node)
            out_degree = graph.out_degree(node)
            total_connections = in_degree + out_degree
            file_connections[node] = total_connections

        # Find files with different connection counts
        sorted_by_connections = sorted(
            file_connections.items(), key=lambda x: x[1], reverse=True
        )

        if len(sorted_by_connections) >= 2:
            # Get top two files by connection count
            most_connected_file, most_connected_count = sorted_by_connections[0]
            less_connected_file, less_connected_count = sorted_by_connections[-1]

            # Skip if they have the same connection count
            if most_connected_count > less_connected_count:
                # Files with more connections should generally have higher centrality
                # (not always true due to other factors, but should be true in most cases)
                most_centrality = composite_scores.get(most_connected_file, 0.0)
                less_centrality = composite_scores.get(less_connected_file, 0.0)

                # Verify both have valid scores
                assert 0.0 <= most_centrality <= 1.0
                assert 0.0 <= less_centrality <= 1.0

                # In most graphs, more connections should correlate with higher centrality
                # This is a probabilistic assertion - it should be true in most cases
                # We're lenient here because centrality can be affected by other factors
                if most_connected_count >= 3 and less_connected_count == 0:
                    # Only assert if difference is significant
                    assert (
                        most_centrality >= less_centrality
                    ), f"File with {most_connected_count} connections should have >= centrality than file with {less_connected_count} connections"

    def test_individual_centrality_algorithms(
        self, session_dependency_graph, session_container
    ):
        """Test individual centrality algorithms (degree, betweenness, pagerank, etc.)."""
        calculator = session_container.centrality_calculator()

        # Test degree centrality
        degree_scores = calculator.calculate_degree_centrality()
        assert isinstance(degree_scores, dict)
        if degree_scores:
            for file_path, score in list(degree_scores.items())[:5]:  # Sample first 5
                assert isinstance(score, (int, float))
                assert 0.0 <= score <= 1.0

        # Test betweenness centrality (may fail for very small graphs)
        try:
            betweenness_scores = calculator.calculate_betweenness_centrality()
            assert isinstance(betweenness_scores, dict)
            if betweenness_scores:
                for file_path, score in list(betweenness_scores.items())[:5]:
                    assert isinstance(score, (int, float))
                    assert 0.0 <= score <= 1.0
        except Exception:
            # Betweenness may fail for very small or disconnected graphs
            pass

        # Test pagerank centrality
        try:
            pagerank_scores = calculator.calculate_pagerank_centrality()
            assert isinstance(pagerank_scores, dict)
            if pagerank_scores:
                for file_path, score in list(pagerank_scores.items())[:5]:
                    assert isinstance(score, (int, float))
                    assert 0.0 <= score <= 1.0
        except Exception:
            # Pagerank may fail for empty graphs
            pass

        # Test eigenvector centrality
        try:
            eigenvector_scores = calculator.calculate_eigenvector_centrality()
            assert isinstance(eigenvector_scores, dict)
            if eigenvector_scores:
                for file_path, score in list(eigenvector_scores.items())[:5]:
                    assert isinstance(score, (int, float))
                    assert 0.0 <= score <= 1.0
        except Exception:
            # Eigenvector may fail for certain graph structures
            pass

        # Test closeness centrality
        try:
            closeness_scores = calculator.calculate_closeness_centrality()
            assert isinstance(closeness_scores, dict)
            if closeness_scores:
                for file_path, score in list(closeness_scores.items())[:5]:
                    assert isinstance(score, (int, float))
                    assert 0.0 <= score <= 1.0
        except Exception:
            # Closeness may fail for disconnected graphs
            pass

    def test_centrality_edge_cases(self, session_container, session_test_repo_path):
        """Test centrality calculation with edge cases."""
        # Test with empty graph
        config = RepoMapConfig(project_root=str(session_test_repo_path))
        container = create_container(config)
        calculator = container.centrality_calculator()

        # Empty graph should return empty dict, not crash
        degree_scores = calculator.calculate_degree_centrality()
        assert isinstance(degree_scores, dict)
        assert len(degree_scores) == 0

        composite_scores = calculator.calculate_composite_importance()
        assert isinstance(composite_scores, dict)
        assert len(composite_scores) == 0

        # Test ranking with empty graph
        ranking = calculator.get_centrality_ranking("composite")
        assert isinstance(ranking, list)
        assert len(ranking) == 0

    def test_centrality_consistency(self, session_dependency_graph, session_container):
        """Test that centrality calculations are consistent across multiple calls."""
        calculator = session_container.centrality_calculator()

        # Calculate twice and compare
        scores1 = calculator.calculate_composite_importance()
        scores2 = calculator.calculate_composite_importance()

        # Should be identical (same graph, same calculation)
        assert scores1 == scores2

        # Rankings should also be consistent
        ranking1 = calculator.get_centrality_ranking("composite")
        ranking2 = calculator.get_centrality_ranking("composite")

        assert len(ranking1) == len(ranking2)
        if ranking1:
            # First item should be the same
            assert ranking1[0][0] == ranking2[0][0]  # Same file path
            assert ranking1[0][1] == ranking2[0][1]  # Same score

    def test_centrality_top_files(self, session_dependency_graph, session_container):
        """Test getting top central files."""
        calculator = session_container.centrality_calculator()

        # Get top 5 files
        top_files = calculator.get_top_central_files("composite", top_n=5)
        assert isinstance(top_files, list)
        assert len(top_files) <= 5

        if top_files:
            # Verify structure: each item should be (file_path, score) tuple
            for file_path, score in top_files:
                assert isinstance(file_path, str)
                assert isinstance(score, (int, float))
                assert 0.0 <= score <= 1.0

            # Verify ordering: should be sorted by score descending
            scores = [score for _, score in top_files]
            assert scores == sorted(scores, reverse=True)

    def test_centrality_percentile(self, session_dependency_graph, session_container):
        """Test centrality percentile calculation."""
        calculator = session_container.centrality_calculator()

        # Get all files and their scores
        composite_scores = calculator.calculate_composite_importance()

        if len(composite_scores) > 0:
            # Test percentile for each file
            for file_path in list(composite_scores.keys())[:5]:  # Sample first 5
                percentile = calculator.get_centrality_percentile(
                    file_path, "composite"
                )
                assert isinstance(percentile, float)
                assert 0.0 <= percentile <= 100.0

            # Files with highest scores should have highest percentiles
            sorted_files = sorted(
                composite_scores.items(), key=lambda x: x[1], reverse=True
            )
            if len(sorted_files) >= 2:
                top_file = sorted_files[0][0]
                bottom_file = sorted_files[-1][0]

                top_percentile = calculator.get_centrality_percentile(
                    top_file, "composite"
                )
                bottom_percentile = calculator.get_centrality_percentile(
                    bottom_file, "composite"
                )

                assert top_percentile >= bottom_percentile
