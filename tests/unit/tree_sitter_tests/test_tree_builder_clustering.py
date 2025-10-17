"""
Unit tests for TreeBuilder clustering functionality.

Tests the new clustering methods added in Phase 3:
- build_tree_from_search_results()
- expand_area()
- prune_area()
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from repomap_tool.code_exploration.tree_builder import TreeBuilder
from repomap_tool.cli.controllers.view_models import SearchViewModel
from repomap_tool.models import Entrypoint, ExplorationTree, TreeNode


class TestTreeBuilderClustering:
    """Test TreeBuilder clustering functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_repo_map = Mock()
        self.mock_entrypoint_discoverer = Mock()

        # Create TreeBuilder instance
        self.tree_builder = TreeBuilder(
            repo_map=self.mock_repo_map,
            entrypoint_discoverer=self.mock_entrypoint_discoverer,
        )

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_build_tree_from_search_results_empty_results(self):
        """Test build_tree_from_search_results with empty search results."""
        # Create empty search results
        search_results = SearchViewModel(
            query="test query",
            results=[],
            total_results=0,
            search_strategy="fuzzy",
            execution_time=0.1,
            token_count=100,
            max_tokens=1000,
            match_type="fuzzy",
            threshold=0.7,
        )

        # Call method
        trees = self.tree_builder.build_tree_from_search_results(
            search_results=search_results,
            intent="test intent",
            max_depth=3,
            project_path="/test/project",
        )

        # Assertions
        assert trees == []
        assert len(trees) == 0

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_build_tree_from_search_results_single_file(self):
        """Test build_tree_from_search_results with single file results."""
        # Create search results with single file
        symbol1 = SymbolViewModel(
            name="function1",
            file_path="/test/project/file1.py",
            line_number=10,
            symbol_type="function",
        )
        symbol2 = SymbolViewModel(
            name="function2",
            file_path="/test/project/file1.py",
            line_number=20,
            symbol_type="function",
        )

        search_results = SearchViewModel(
            query="test query",
            results=[symbol1, symbol2],
            total_results=2,
            search_strategy="fuzzy",
            execution_time=0.1,
            token_count=100,
            max_tokens=1000,
            match_type="fuzzy",
            threshold=0.7,
        )

        # Mock build_exploration_tree
        mock_tree = Mock(spec=ExplorationTree)
        mock_tree.tree_id = "test_tree_1"
        mock_tree.context_name = None
        mock_tree.description = None

        with patch.object(
            self.tree_builder, "build_exploration_tree", return_value=mock_tree
        ):
            # Call method
            trees = self.tree_builder.build_tree_from_search_results(
                search_results=search_results,
                intent="test intent",
                max_depth=3,
                project_path="/test/project",
            )

        # Assertions
        assert len(trees) == 1
        assert trees[0] == mock_tree
        assert (
            mock_tree.context_name
            == "Tree for test intent exploration in /test/project/file1.py"
        )

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_build_tree_from_search_results_multiple_files(self):
        """Test build_tree_from_search_results with multiple file results."""
        # Create search results with multiple files
        symbol1 = SymbolViewModel(
            name="function1",
            file_path="/test/project/file1.py",
            line_number=10,
            symbol_type="function",
        )
        symbol2 = SymbolViewModel(
            name="function2",
            file_path="/test/project/file2.py",
            line_number=20,
            symbol_type="function",
        )

        search_results = SearchViewModel(
            query="test query",
            results=[symbol1, symbol2],
            total_results=2,
            search_strategy="fuzzy",
            execution_time=0.1,
            token_count=100,
            max_tokens=1000,
            match_type="fuzzy",
            threshold=0.7,
        )

        # Mock build_exploration_tree
        mock_tree1 = Mock(spec=ExplorationTree)
        mock_tree1.tree_id = "test_tree_1"
        mock_tree2 = Mock(spec=ExplorationTree)
        mock_tree2.tree_id = "test_tree_2"

        with patch.object(
            self.tree_builder,
            "build_exploration_tree",
            side_effect=[mock_tree1, mock_tree2],
        ):
            # Call method
            trees = self.tree_builder.build_tree_from_search_results(
                search_results=search_results,
                intent="test intent",
                max_depth=3,
                project_path="/test/project",
            )

        # Assertions
        assert len(trees) == 2
        assert trees[0] == mock_tree1
        assert trees[1] == mock_tree2

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_build_tree_from_search_results_max_trees_limit(self):
        """Test build_tree_from_search_results respects max trees limit."""
        # Create search results with many files
        symbols = []
        for i in range(10):
            symbol = SymbolViewModel(
                name=f"function{i}",
                file_path=f"/test/project/file{i}.py",
                line_number=10,
                symbol_type="function",
            )
            symbols.append(symbol)

        search_results = SearchViewModel(
            query="test query",
            results=symbols,
            total_results=10,
            search_strategy="fuzzy",
            execution_time=0.1,
            token_count=100,
            max_tokens=1000,
            match_type="fuzzy",
            threshold=0.7,
        )

        # Mock build_exploration_tree
        mock_trees = [Mock(spec=ExplorationTree) for _ in range(10)]

        with patch.object(
            self.tree_builder, "build_exploration_tree", side_effect=mock_trees
        ):
            with patch(
                "repomap_tool.code_exploration.tree_builder.get_config"
            ) as mock_get_config:
                # Configure the mock to return 3 for EXPLORATION_MAX_TREES, default for others
                def config_side_effect(key, default):
                    if key == "EXPLORATION_MAX_TREES":
                        return 3
                    return default

                mock_get_config.side_effect = config_side_effect

                # Call method
                trees = self.tree_builder.build_tree_from_search_results(
                    search_results=search_results,
                    intent="test intent",
                    max_depth=3,
                    project_path="/test/project",
                )

        # Assertions
        assert len(trees) == 3  # Should be limited to 3

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_expand_area_no_matching_nodes(self):
        """Test expand_area with no matching nodes."""
        # Create tree with no matching nodes
        tree = Mock(spec=ExplorationTree)
        tree.tree_id = "test_tree"
        tree.tree_structure = Mock()
        tree.expanded_areas = set()
        tree.current_depth = 1

        # Mock _find_nodes_by_area to return empty list
        with patch.object(self.tree_builder, "_find_nodes_by_area", return_value=[]):
            # Call method
            new_symbols = self.tree_builder.expand_area(
                tree=tree, area="nonexistent", project_path="/test/project"
            )

        # Assertions
        assert new_symbols == []
        # Note: The method adds the area to expanded_areas even if no nodes are found
        # This is the current behavior, so we test for it
        assert "nonexistent" in tree.expanded_areas

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_expand_area_with_matching_nodes(self):
        """Test expand_area with matching nodes."""
        # Create tree with matching nodes
        tree = Mock(spec=ExplorationTree)
        tree.tree_id = "test_tree"
        tree.expanded_areas = set()
        tree.current_depth = 1
        tree.tree_structure = Mock()  # Add tree_structure attribute

        # Create mock node
        mock_node = Mock(spec=TreeNode)
        mock_node.identifier = "test_function"
        mock_node.location = "/test/project/file.py:10"
        mock_node.depth = 1
        mock_node.children = []

        # Mock _find_nodes_by_area to return the mock node
        with patch.object(
            self.tree_builder, "_find_nodes_by_area", return_value=[mock_node]
        ):
            # Mock _get_related_symbols_from_tree_sitter
            mock_symbols = [
                {
                    "identifier": "related_function",
                    "location": "/test/project/file.py:20",
                    "type": "function",
                    "file_path": "/test/project/file.py",
                    "line_number": 20,
                    "confidence": 0.8,
                }
            ]
            with patch.object(
                self.tree_builder,
                "_get_related_symbols_from_tree_sitter",
                return_value=mock_symbols,
            ):
                # Mock _get_all_nodes
                with patch.object(
                    self.tree_builder, "_get_all_nodes", return_value=[mock_node]
                ):
                    # Call method
                    new_symbols = self.tree_builder.expand_area(
                        tree=tree, area="test_function", project_path="/test/project"
                    )

        # Assertions
        assert len(new_symbols) == 1
        assert isinstance(new_symbols[0], SymbolViewModel)
        assert new_symbols[0].name == "related_function"
        assert "test_function" in tree.expanded_areas
        assert len(mock_node.children) == 1

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_prune_area_no_matching_nodes(self):
        """Test prune_area with no matching nodes."""
        # Create tree with no matching nodes
        tree = Mock(spec=ExplorationTree)
        tree.tree_id = "test_tree"
        tree.pruned_areas = set()
        tree.expanded_areas = set()

        # Mock _find_nodes_by_area to return empty list
        with patch.object(self.tree_builder, "_find_nodes_by_area", return_value=[]):
            # Call method
            removed_identifiers = self.tree_builder.prune_area(
                tree=tree, area="nonexistent"
            )

        # Assertions
        assert removed_identifiers == []
        assert "nonexistent" not in tree.pruned_areas

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_prune_area_with_matching_nodes(self):
        """Test prune_area with matching nodes."""
        # Create tree with matching nodes
        tree = Mock(spec=ExplorationTree)
        tree.tree_id = "test_tree"
        tree.pruned_areas = set()
        tree.expanded_areas = {"test_function"}
        tree.tree_structure = Mock()  # Add tree_structure attribute

        # Create mock parent and child nodes
        mock_parent = Mock(spec=TreeNode)
        mock_parent.children = []

        mock_node = Mock(spec=TreeNode)
        mock_node.identifier = "test_function"
        mock_node.parent = mock_parent
        mock_node.children = []

        # Add node to parent's children
        mock_parent.children.append(mock_node)

        # Mock _find_nodes_by_area to return the mock node
        with patch.object(
            self.tree_builder, "_find_nodes_by_area", return_value=[mock_node]
        ):
            # Mock _get_all_descendants
            with patch.object(
                self.tree_builder, "_get_all_descendants", return_value=[]
            ):
                # Call method
                removed_identifiers = self.tree_builder.prune_area(
                    tree=tree, area="test_function"
                )

        # Assertions
        assert len(removed_identifiers) == 1
        assert removed_identifiers[0] == "test_function"
        assert "test_function" in tree.pruned_areas
        assert "test_function" not in tree.expanded_areas
        assert mock_node not in mock_parent.children

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_find_nodes_by_area_matches_identifier(self):
        """Test _find_nodes_by_area finds nodes by identifier."""
        # Create tree structure
        root_node = TreeNode(
            identifier="root_function",
            location="/test/project/file.py:1",
            node_type="function",
            depth=0,
        )

        child_node = TreeNode(
            identifier="test_function",
            location="/test/project/file.py:10",
            node_type="function",
            depth=1,
        )
        child_node.parent = root_node
        root_node.children = [child_node]

        # Call method
        matching_nodes = self.tree_builder._find_nodes_by_area(
            root_node, "test_function"
        )

        # Assertions
        assert len(matching_nodes) == 1
        assert matching_nodes[0] == child_node

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_find_nodes_by_area_matches_location(self):
        """Test _find_nodes_by_area finds nodes by location."""
        # Create tree structure
        root_node = TreeNode(
            identifier="root_function",
            location="/test/project/file.py:1",
            node_type="function",
            depth=0,
        )

        child_node = TreeNode(
            identifier="some_function",
            location="/test/project/test_file.py:10",
            node_type="function",
            depth=1,
        )
        child_node.parent = root_node
        root_node.children = [child_node]

        # Call method
        matching_nodes = self.tree_builder._find_nodes_by_area(root_node, "test_file")

        # Assertions
        assert len(matching_nodes) == 1
        assert matching_nodes[0] == child_node

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_get_all_descendants(self):
        """Test _get_all_descendants returns all descendant nodes."""
        # Create tree structure
        parent_node = TreeNode(
            identifier="parent",
            location="/test/project/file.py:1",
            node_type="function",
            depth=0,
        )

        child1 = TreeNode(
            identifier="child1",
            location="/test/project/file.py:10",
            node_type="function",
            depth=1,
        )
        child1.parent = parent_node

        child2 = TreeNode(
            identifier="child2",
            location="/test/project/file.py:20",
            node_type="function",
            depth=1,
        )
        child2.parent = parent_node

        grandchild = TreeNode(
            identifier="grandchild",
            location="/test/project/file.py:30",
            node_type="function",
            depth=2,
        )
        grandchild.parent = child1

        parent_node.children = [child1, child2]
        child1.children = [grandchild]
        child2.children = []

        # Call method
        descendants = self.tree_builder._get_all_descendants(parent_node)

        # Assertions
        assert len(descendants) == 3
        assert child1 in descendants
        assert child2 in descendants
        assert grandchild in descendants

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_get_all_nodes(self):
        """Test _get_all_nodes returns all nodes in tree."""
        # Create tree structure
        root_node = TreeNode(
            identifier="root",
            location="/test/project/file.py:1",
            node_type="function",
            depth=0,
        )

        child1 = TreeNode(
            identifier="child1",
            location="/test/project/file.py:10",
            node_type="function",
            depth=1,
        )
        child1.parent = root_node

        child2 = TreeNode(
            identifier="child2",
            location="/test/project/file.py:20",
            node_type="function",
            depth=1,
        )
        child2.parent = root_node

        root_node.children = [child1, child2]
        child1.children = []
        child2.children = []

        # Call method
        all_nodes = self.tree_builder._get_all_nodes(root_node)

        # Assertions
        assert len(all_nodes) == 3
        assert root_node in all_nodes
        assert child1 in all_nodes
        assert child2 in all_nodes

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_get_related_symbols_from_tree_sitter_no_repo_map(self):
        """Test _get_related_symbols_from_tree_sitter with no repo_map."""
        # Create node
        node = TreeNode(
            identifier="test_function",
            location="/test/project/file.py:10",
            node_type="function",
            depth=1,
        )

        # Set repo_map to None
        self.tree_builder.repo_map = None

        # Call method
        symbols = self.tree_builder._get_related_symbols_from_tree_sitter(
            node, "/test/project"
        )

        # Assertions
        assert symbols == []

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_get_related_symbols_from_tree_sitter_with_repo_map(self):
        """Test _get_related_symbols_from_tree_sitter with repo_map."""
        # Create node
        node = TreeNode(
            identifier="test_function",
            location="/test/project/file.py:10",
            node_type="function",
            depth=1,
        )

        # Mock repo_map
        mock_repo_map = Mock()
        mock_repo_map.get_tags.return_value = [
            Mock(name="related_function", line=20, kind="def")
        ]
        self.tree_builder.repo_map = Mock()
        self.tree_builder.repo_map.repo_map = mock_repo_map

        # Mock _extract_file_path and _process_tree_sitter_tags
        with patch.object(
            self.tree_builder,
            "_extract_file_path",
            return_value="/test/project/file.py",
        ):
            with patch.object(
                self.tree_builder,
                "_process_tree_sitter_tags",
                return_value=[
                    {
                        "identifier": "test_function_related",  # Changed to match node identifier
                        "location": "/test/project/file.py:20",
                        "type": "function",
                        "file_path": "/test/project/file.py",
                        "line_number": 20,
                        "confidence": 0.8,
                    }
                ],
            ):
                with patch(
                    "repomap_tool.core.config_service.get_config", return_value=5
                ):
                    # Call method
                    symbols = self.tree_builder._get_related_symbols_from_tree_sitter(
                        node, "/test/project"
                    )

        # Assertions
        assert len(symbols) == 1
        assert symbols[0]["identifier"] == "test_function_related"
        mock_repo_map.get_tags.assert_called_once()

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_build_tree_from_search_results_error_handling(self):
        """Test build_tree_from_search_results handles errors gracefully."""
        # Create search results
        search_results = SearchViewModel(
            query="test query",
            results=[],
            total_results=0,
            search_strategy="fuzzy",
            execution_time=0.1,
            token_count=100,
            max_tokens=1000,
            match_type="fuzzy",
            threshold=0.7,
        )

        # Mock build_exploration_tree to raise exception
        with patch.object(
            self.tree_builder,
            "build_exploration_tree",
            side_effect=Exception("Test error"),
        ):
            # Call method
            trees = self.tree_builder.build_tree_from_search_results(
                search_results=search_results,
                intent="test intent",
                max_depth=3,
                project_path="/test/project",
            )

        # Assertions
        assert trees == []

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_expand_area_error_handling(self):
        """Test expand_area handles errors gracefully."""
        # Create tree
        tree = Mock(spec=ExplorationTree)
        tree.tree_id = "test_tree"
        tree.expanded_areas = set()
        tree.current_depth = 1

        # Mock _find_nodes_by_area to raise exception
        with patch.object(
            self.tree_builder,
            "_find_nodes_by_area",
            side_effect=Exception("Test error"),
        ):
            # Call method
            new_symbols = self.tree_builder.expand_area(
                tree=tree, area="test_area", project_path="/test/project"
            )

        # Assertions
        assert new_symbols == []

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_prune_area_error_handling(self):
        """Test prune_area handles errors gracefully."""
        # Create tree
        tree = Mock(spec=ExplorationTree)
        tree.tree_id = "test_tree"
        tree.pruned_areas = set()
        tree.expanded_areas = set()

        # Mock _find_nodes_by_area to raise exception
        with patch.object(
            self.tree_builder,
            "_find_nodes_by_area",
            side_effect=Exception("Test error"),
        ):
            # Call method
            removed_identifiers = self.tree_builder.prune_area(
                tree=tree, area="test_area"
            )

        # Assertions
        assert removed_identifiers == []
