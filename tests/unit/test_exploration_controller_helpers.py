"""
Unit tests for ExplorationController helper methods.

Tests the helper methods implemented in Phase 1:
- _cluster_search_results()
- _extract_entrypoints()
- _create_exploration_session()
- _estimate_token_count()
- _build_tree_structure()
- _extract_code_snippets()
- _build_session_stats()
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from repomap_tool.cli.controllers.exploration_controller import ExplorationController
from repomap_tool.cli.controllers.view_models import TreeClusterViewModel
from repomap_tool.models import ExplorationSession, ExplorationTree, TreeNode


class TestExplorationControllerHelpers:
    """Test ExplorationController helper methods."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_search_controller = Mock()
        self.mock_session_manager = Mock()
        self.mock_tree_builder = Mock()

        # Create ExplorationController instance
        self.controller = ExplorationController(
            search_controller=self.mock_search_controller,
            session_manager=self.mock_session_manager,
            tree_builder=self.mock_tree_builder,
        )

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_cluster_search_results_empty_results(self):
        """Test _cluster_search_results with empty results."""
        # Call method
        clusters = self.controller._cluster_search_results([], "test intent")

        # Assertions
        assert clusters == []

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_cluster_search_results_with_results(self):
        """Test _cluster_search_results with search results."""
        # Create mock search results
        result1 = Mock()
        result1.file_path = "/test/project/file1.py"
        result1.identifier = "function1"

        result2 = Mock()
        result2.file_path = "/test/project/file1.py"
        result2.identifier = "function2"

        result3 = Mock()
        result3.file_path = "/test/project/file2.py"
        result3.identifier = "function3"

        # Create a SearchViewModel object
        from repomap_tool.cli.controllers.view_models import SearchViewModel

        search_results = SearchViewModel(
            query="test query",
            results=[result1, result2, result3],
            total_results=3,
            search_strategy="fuzzy",
            execution_time=0.1,
            token_count=100,
            max_tokens=1000,
        )

        with patch("repomap_tool.core.config_service.get_config", return_value=5):
            # Call method
            clusters = self.controller._cluster_search_results(
                search_results, "test intent"
            )

        # Assertions
        assert len(clusters) == 2  # Two files
        assert clusters[0]["file_path"] == "/test/project/file1.py"
        assert clusters[1]["file_path"] == "/test/project/file2.py"
        assert clusters[0]["intent"] == "test intent"
        assert clusters[0]["cluster_type"] == "file_based"

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_cluster_search_results_max_clusters_limit(self):
        """Test _cluster_search_results respects max clusters limit."""
        # Create many search results
        results_list = []
        for i in range(10):
            result = Mock()
            result.file_path = f"/test/project/file{i}.py"
            result.identifier = f"function{i}"
            results_list.append(result)

        # Create a SearchViewModel object
        from repomap_tool.cli.controllers.view_models import SearchViewModel

        search_results = SearchViewModel(
            query="test query",
            results=results_list,
            total_results=10,
            search_strategy="fuzzy",
            execution_time=0.1,
            token_count=100,
            max_tokens=1000,
        )

        with patch(
            "repomap_tool.core.config_service.get_config", return_value=3
        ):  # Limit to 3
            # Call method
            clusters = self.controller._cluster_search_results(
                search_results, "test intent"
            )

        # Assertions
        assert len(clusters) == 3  # Should be limited to 3

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_extract_entrypoints_no_tree(self):
        """Test _extract_entrypoints with no tree."""
        # Call method
        entrypoints = self.controller._extract_entrypoints(None)

        # Assertions
        assert entrypoints == []

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_extract_entrypoints_with_tree(self):
        """Test _extract_entrypoints with tree nodes."""
        # Create mock tree with nodes
        tree = Mock()
        tree.nodes = [
            Mock(
                identifier="function1",
                location="/test/file.py:10",
                node_type="function",
                depth=1,
                relevance_score=0.8,
            ),
            Mock(
                identifier="function2",
                location="/test/file.py:20",
                node_type="function",
                depth=1,
                relevance_score=0.9,
            ),
            Mock(
                identifier="class1",
                location="/test/file.py:5",
                node_type="class",
                depth=0,
                relevance_score=0.7,
            ),
        ]

        with patch("repomap_tool.core.config_service.get_config", return_value=10):
            # Call method
            entrypoints = self.controller._extract_entrypoints(tree)

        # Assertions
        assert len(entrypoints) == 3
        assert entrypoints[0]["identifier"] == "function2"  # Sorted by relevance
        assert entrypoints[0]["relevance_score"] == 0.9
        assert entrypoints[1]["identifier"] == "function1"
        assert entrypoints[2]["identifier"] == "class1"

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_extract_entrypoints_max_entrypoints_limit(self):
        """Test _extract_entrypoints respects max entrypoints limit."""
        # Create mock tree with many nodes
        tree = Mock()
        tree.nodes = [
            Mock(
                identifier=f"function{i}",
                location=f"/test/file.py:{i}",
                node_type="function",
                depth=1,
                relevance_score=0.8,
            )
            for i in range(15)
        ]

        with patch(
            "repomap_tool.core.config_service.get_config", return_value=5
        ):  # Limit to 5
            # Call method
            entrypoints = self.controller._extract_entrypoints(tree)

        # Assertions
        assert len(entrypoints) == 5  # Should be limited to 5

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_create_exploration_session(self):
        """Test _create_exploration_session creates session with trees."""
        # Create mock tree clusters
        tree_cluster1 = Mock(spec=TreeClusterViewModel)
        tree_cluster1.context_name = "Tree 1"
        tree_cluster1.max_depth = 3

        tree_cluster2 = Mock(spec=TreeClusterViewModel)
        tree_cluster2.context_name = "Tree 2"
        tree_cluster2.max_depth = 2

        trees = [tree_cluster1, tree_cluster2]

        # Mock session manager
        self.mock_session_manager.persist_session = Mock()

        # Call method
        self.controller._create_exploration_session(
            "test_session", "/test/project", trees
        )

        # Assertions
        self.mock_session_manager.persist_session.assert_called_once()
        saved_session = self.mock_session_manager.persist_session.call_args[0][0]
        assert isinstance(saved_session, ExplorationSession)
        assert saved_session.session_id == "test_session"
        assert saved_session.project_path == "/test/project"
        assert len(saved_session.exploration_trees) == 2
        assert saved_session.current_focus == "tree_1"

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_create_exploration_session_empty_trees(self):
        """Test _create_exploration_session with empty trees."""
        # Mock session manager
        self.mock_session_manager.persist_session = Mock()

        # Call method
        self.controller._create_exploration_session("test_session", "/test/project", [])

        # Assertions
        self.mock_session_manager.persist_session.assert_called_once()
        saved_session = self.mock_session_manager.persist_session.call_args[0][0]
        assert saved_session.current_focus is None

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_estimate_token_count_empty_trees(self):
        """Test _estimate_token_count with empty trees."""
        # Call method
        token_count = self.controller._estimate_token_count([])

        # Assertions
        assert token_count == 0

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_estimate_token_count_with_trees(self):
        """Test _estimate_token_count with trees."""
        # Create mock trees
        tree1 = Mock()
        tree1.nodes = [Mock(), Mock(), Mock()]  # 3 nodes

        tree2 = Mock()
        tree2.nodes = [Mock(), Mock()]  # 2 nodes

        trees = [tree1, tree2]

        with patch("repomap_tool.core.config_service.get_config") as mock_get_config:
            # Configure the mock to return specific values for specific keys
            def config_side_effect(key, default):
                if key == "EXPLORATION_TOKENS_PER_NODE":
                    return 50
                elif key == "EXPLORATION_TREE_OVERHEAD":
                    return 100
                elif key == "EXPLORATION_FALLBACK_TOKENS":
                    return 200
                return default

            mock_get_config.side_effect = config_side_effect

            # Call method
            token_count = self.controller._estimate_token_count(trees)

        # Assertions
        # Tree1: 3 nodes * 50 + 100 overhead = 250
        # Tree2: 2 nodes * 50 + 100 overhead = 200
        # Total: 450
        assert token_count == 450

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_estimate_token_count_fallback(self):
        """Test _estimate_token_count with trees without nodes."""
        # Create mock trees without nodes attribute
        tree1 = Mock()
        del tree1.nodes  # Remove nodes attribute

        tree2 = Mock()
        del tree2.nodes  # Remove nodes attribute

        trees = [tree1, tree2]

        with patch(
            "repomap_tool.core.config_service.get_config", return_value=200
        ):  # fallback_tokens
            # Call method
            token_count = self.controller._estimate_token_count(trees)

        # Assertions
        assert token_count == 400  # 2 trees * 200 fallback

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_build_tree_structure_no_tree(self):
        """Test _build_tree_structure with no tree."""
        # Call method
        structure = self.controller._build_tree_structure(None)

        # Assertions
        assert structure == {}

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_build_tree_structure_with_tree(self):
        """Test _build_tree_structure with tree."""
        # Create mock tree
        tree = Mock()
        tree.tree_id = "test_tree"
        tree.context_name = "Test Tree"
        tree.max_depth = 3
        tree.current_depth = 2
        tree.expanded_areas = {"area1", "area2"}
        tree.pruned_areas = {"area3"}

        # Create mock nodes
        node1 = Mock()
        node1.identifier = "function1"
        node1.location = "/test/file.py:10"
        node1.node_type = "function"
        node1.depth = 1
        node1.expanded = True
        node1.children = [Mock(), Mock()]

        node2 = Mock()
        node2.identifier = "function2"
        node2.location = "/test/file.py:20"
        node2.node_type = "function"
        node2.depth = 1
        node2.expanded = False
        node2.children = []

        tree.nodes = [node1, node2]

        # Call method
        structure = self.controller._build_tree_structure(tree)

        # Assertions
        assert structure["tree_id"] == "test_tree"
        assert structure["context_name"] == "Test Tree"
        assert structure["max_depth"] == 3
        assert structure["current_depth"] == 2
        assert set(structure["expanded_areas"]) == {"area1", "area2"}
        assert set(structure["pruned_areas"]) == {"area3"}
        assert structure["node_count"] == 2
        assert len(structure["nodes"]) == 2
        assert structure["nodes"][0]["identifier"] == "function1"
        assert structure["nodes"][0]["expanded"] is True
        assert structure["nodes"][0]["children_count"] == 2

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_extract_code_snippets_no_tree(self):
        """Test _extract_code_snippets with no tree."""
        # Call method
        snippets = self.controller._extract_code_snippets(None, 1000)

        # Assertions
        assert snippets == []

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_extract_code_snippets_with_tree(self):
        """Test _extract_code_snippets with tree."""
        # Create mock tree with nodes
        tree = Mock()
        node1 = Mock()
        node1.identifier = "function1"
        node1.location = "/test/file.py:10"
        node1.node_type = "function"
        node1.depth = 1
        node1.content = "def function1():\n    return True"

        node2 = Mock()
        node2.identifier = "function2"
        node2.location = "/test/file.py:20"
        node2.node_type = "function"
        node2.depth = 1
        node2.content = "def function2():\n    return False"

        tree.nodes = [node1, node2]

        with patch("repomap_tool.core.config_service.get_config", return_value=200):
            # Call method
            snippets = self.controller._extract_code_snippets(tree, 1000)

        # Assertions
        assert len(snippets) == 2
        assert snippets[0]["identifier"] == "function1"
        assert snippets[0]["content"] == "def function1():\n    return True"
        assert snippets[0]["tokens_used"] > 0

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_extract_code_snippets_token_limit(self):
        """Test _extract_code_snippets respects token limit."""
        # Create mock tree with many nodes
        tree = Mock()
        tree.nodes = []
        for i in range(10):
            node = Mock()
            node.identifier = f"function{i}"
            node.location = f"/test/file.py:{i*10}"
            node.node_type = "function"
            node.depth = 1
            node.content = f"def function{i}():\n    return {i}" * 10  # Long content
            tree.nodes.append(node)

        with patch("repomap_tool.core.config_service.get_config", return_value=200):
            # Call method with low token limit
            snippets = self.controller._extract_code_snippets(tree, 100)

        # Assertions
        assert len(snippets) < 10  # Should be limited by tokens
        total_tokens = sum(snippet["tokens_used"] for snippet in snippets)
        assert total_tokens <= 100

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_build_session_stats_no_session(self):
        """Test _build_session_stats with no session."""
        # Call method
        stats = self.controller._build_session_stats(None)

        # Assertions
        assert stats == {}

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_build_session_stats_with_session(self):
        """Test _build_session_stats with session."""
        # Create mock session
        session = Mock()
        session.session_id = "test_session"
        session.project_path = "/test/project"
        session.current_focus = "tree_1"
        session.created_at = datetime(2024, 1, 15, 10, 0, 0)
        session.last_activity = datetime(2024, 1, 15, 11, 30, 0)

        # Create mock trees
        tree1 = Mock()
        tree1.nodes = [Mock(), Mock(), Mock()]
        tree1.expanded_areas = {"area1", "area2"}
        tree1.pruned_areas = {"area3"}

        tree2 = Mock()
        tree2.nodes = [Mock(), Mock()]
        tree2.expanded_areas = {"area4"}
        tree2.pruned_areas = set()

        session.exploration_trees = {"tree_1": tree1, "tree_2": tree2}

        # Call method
        stats = self.controller._build_session_stats(session)

        # Assertions
        assert stats["session_id"] == "test_session"
        assert stats["project_path"] == "/test/project"
        assert stats["tree_count"] == 2
        assert stats["total_nodes"] == 5  # 3 + 2
        assert stats["expanded_areas"] == 3  # 2 + 1
        assert stats["pruned_areas"] == 1  # 1 + 0
        assert stats["current_focus"] == "tree_1"
        assert stats["session_duration"] == 5400  # 1.5 hours in seconds

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_build_session_stats_string_dates(self):
        """Test _build_session_stats with string dates."""
        # Create mock session with string dates
        session = Mock()
        session.session_id = "test_session"
        session.project_path = "/test/project"
        session.current_focus = "tree_1"
        session.created_at = "2024-01-15T10:00:00"
        session.last_activity = "2024-01-15T11:30:00"
        session.exploration_trees = {}

        # Call method
        stats = self.controller._build_session_stats(session)

        # Assertions
        assert stats["session_duration"] == 5400  # 1.5 hours in seconds

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_cluster_search_results_error_handling(self):
        """Test _cluster_search_results handles errors gracefully."""
        # Create mock search results that will cause error
        result = Mock()
        result.file_path = None  # This will cause an error in getattr

        with patch("repomap_tool.core.config_service.get_config", return_value=5):
            # Call method
            clusters = self.controller._cluster_search_results([result], "test intent")

        # Assertions
        assert clusters == []

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_extract_entrypoints_error_handling(self):
        """Test _extract_entrypoints handles errors gracefully."""
        # Create mock tree that will cause error
        tree = Mock()
        mock_node = Mock()
        # Remove the required attributes to simulate error condition
        del mock_node.identifier
        del mock_node.location
        tree.nodes = [mock_node]

        with patch("repomap_tool.core.config_service.get_config", return_value=10):
            # Call method
            entrypoints = self.controller._extract_entrypoints(tree)

        # Assertions - the method should return empty list when nodes don't have required attributes
        assert entrypoints == []

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_create_exploration_session_error_handling(self):
        """Test _create_exploration_session handles errors gracefully."""
        # Mock session manager to raise exception
        self.mock_session_manager.persist_session.side_effect = Exception("Test error")

        # Call method and expect exception to be raised
        with pytest.raises(Exception, match="Test error"):
            self.controller._create_exploration_session(
                "test_session", "/test/project", []
            )

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_estimate_token_count_error_handling(self):
        """Test _estimate_token_count handles errors gracefully."""
        # Create mock trees that will cause error
        tree = Mock()
        tree.nodes = [Mock()]  # Mock without proper attributes

        with patch(
            "repomap_tool.core.config_service.get_config",
            side_effect=Exception("Test error"),
        ):
            # Call method
            token_count = self.controller._estimate_token_count([tree])

        # Assertions
        assert token_count == 1000  # Fallback value

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_build_tree_structure_error_handling(self):
        """Test _build_tree_structure handles errors gracefully."""
        # Create mock tree that will cause error
        tree = Mock()
        tree.tree_id = "test_tree"
        # Missing other required attributes

        # Call method
        structure = self.controller._build_tree_structure(tree)

        # Assertions
        assert structure == {}

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_extract_code_snippets_error_handling(self):
        """Test _extract_code_snippets handles errors gracefully."""
        # Create mock tree that will cause error
        tree = Mock()
        tree.nodes = [Mock()]  # Mock without proper attributes

        with patch(
            "repomap_tool.core.config_service.get_config",
            side_effect=Exception("Test error"),
        ):
            # Call method
            snippets = self.controller._extract_code_snippets(tree, 1000)

        # Assertions
        assert snippets == []

    @pytest.mark.skip(reason="Disabling tree/exploration tests")

    def test_build_session_stats_error_handling(self):
        """Test _build_session_stats handles errors gracefully."""
        # Create mock session that will cause error
        session = Mock()
        session.session_id = "test_session"
        session.project_path = "/test/project"
        session.current_focus = "tree_1"
        session.created_at = "invalid_date"  # Invalid date format
        session.last_activity = "invalid_date"
        session.exploration_trees = {}

        # Call method
        stats = self.controller._build_session_stats(session)

        # Assertions
        assert stats == {}  # Should return empty dict when there's an error
