"""
Tree manager for exploration tree operations.

This module manages tree state, expansion, pruning, and focus operations,
providing the core functionality for tree manipulation within sessions.
"""

import logging
from ..core.logging_service import get_logger
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

from repomap_tool.models import ExplorationTree, TreeNode, ExplorationSession
from repomap_tool.core import RepoMapService
from repomap_tool.code_exploration.session_manager import SessionManager
from repomap_tool.code_exploration.tree_builder import TreeBuilder

logger = get_logger(__name__)


class TreeManager:
    """Manages tree state, expansion, pruning, and focus operations."""

    def __init__(
        self,
        repo_map: RepoMapService,
        session_manager: Optional[Any] = None,
        tree_builder: Optional[Any] = None,
    ):
        """Initialize tree manager with injected dependencies.

        Args:
            repo_map: RepoMapService instance
            session_manager: Session manager instance (injected)
            tree_builder: Tree builder instance (injected)
        """
        self.repo_map = repo_map

        # Use injected dependencies - no fallback
        if session_manager is None:
            raise ValueError("SessionManager must be injected - no fallback allowed")
        if tree_builder is None:
            raise ValueError("TreeBuilder must be injected - no fallback allowed")

        self.session_manager = session_manager
        self.tree_builder = tree_builder

        logger.debug("TreeManager initialized")

    def focus_tree(self, session_id: str, tree_id: str) -> bool:
        """Set focus to specific tree (stateful within session).

        Args:
            session_id: Session ID
            tree_id: Tree ID to focus on

        Returns:
            True if focus was set successfully
        """
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found")
                return False

            if tree_id not in session.exploration_trees:
                logger.warning(f"Tree {tree_id} not found in session {session_id}")
                return False

            session.current_focus = tree_id
            session.last_activity = datetime.now()
            self.session_manager.persist_session(session)

            logger.info(f"Focused on tree {tree_id} in session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error setting focus to tree {tree_id}: {e}")
            return False

    def expand_tree(
        self, session_id: str, expansion_area: str, tree_id: Optional[str] = None
    ) -> bool:
        """Expand tree in specific area.

        Args:
            session_id: Session ID
            expansion_area: Area to expand (e.g., "password_validation")
            tree_id: Tree ID (uses current focus if not specified)

        Returns:
            True if expansion was successful
        """
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found")
                return False

            target_tree_id = tree_id or session.current_focus
            if not target_tree_id:
                logger.warning(
                    f"No tree specified and no current focus in session {session_id}"
                )
                return False

            if target_tree_id not in session.exploration_trees:
                logger.warning(
                    f"Tree {target_tree_id} not found in session {session_id}"
                )
                return False

            tree = session.exploration_trees[target_tree_id]

            # Find expansion point in tree
            expansion_node = self._find_expansion_point(tree, expansion_area)
            if expansion_node:
                # Expand this node using existing aider infrastructure
                self._expand_tree_node(expansion_node, tree)
                tree.expanded_areas.add(expansion_area)
                tree.last_modified = datetime.now()

                # Persist session
                self.session_manager.persist_session(session)

                logger.info(f"Expanded tree {target_tree_id} in area: {expansion_area}")
                return True
            else:
                logger.warning(
                    f"Expansion area '{expansion_area}' not found in tree {target_tree_id}"
                )
                return False

        except Exception as e:
            logger.error(f"Error expanding tree in area {expansion_area}: {e}")
            return False

    def prune_tree(
        self, session_id: str, prune_area: str, tree_id: Optional[str] = None
    ) -> bool:
        """Remove branch from tree.

        Args:
            session_id: Session ID
            prune_area: Area to prune (e.g., "logging")
            tree_id: Tree ID (uses current focus if not specified)

        Returns:
            True if pruning was successful
        """
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found")
                return False

            target_tree_id = tree_id or session.current_focus
            if not target_tree_id:
                logger.warning(
                    f"No tree specified and no current focus in session {session_id}"
                )
                return False

            if target_tree_id not in session.exploration_trees:
                logger.warning(
                    f"Tree {target_tree_id} not found in session {session_id}"
                )
                return False

            tree = session.exploration_trees[target_tree_id]

            # Find and remove branch
            if self._prune_tree_branch(tree, prune_area):
                tree.pruned_areas.add(prune_area)
                tree.last_modified = datetime.now()

                # Persist session
                self.session_manager.persist_session(session)

                logger.info(f"Pruned tree {target_tree_id} in area: {prune_area}")
                return True
            else:
                logger.warning(
                    f"Prune area '{prune_area}' not found in tree {target_tree_id}"
                )
                return False

        except Exception as e:
            logger.error(f"Error pruning tree in area {prune_area}: {e}")
            return False

    def get_tree_state(
        self, session_id: str, tree_id: Optional[str] = None
    ) -> Optional[ExplorationTree]:
        """Get current tree state.

        Args:
            session_id: Session ID
            tree_id: Tree ID (uses current focus if not specified)

        Returns:
            Current tree or None if not found
        """
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                return None

            target_tree_id = tree_id or session.current_focus
            if not target_tree_id:
                return None

            if target_tree_id in session.exploration_trees:
                tree: ExplorationTree = session.exploration_trees[target_tree_id]
                return tree

            return None

        except Exception as e:
            logger.error(f"Error getting tree state: {e}")
            return None

    def list_trees(self, session_id: str) -> List[Dict[str, Any]]:
        """List all trees in a session.

        Args:
            session_id: Session ID

        Returns:
            List of tree information dictionaries
        """
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                return []

            trees_info = []
            for tree_id, tree in session.exploration_trees.items():
                tree_info = {
                    "tree_id": tree_id,
                    "context_name": tree.context_name,
                    "root_entrypoint": tree.root_entrypoint.identifier,
                    "confidence": tree.confidence,
                    "node_count": (
                        self._count_nodes(tree.tree_structure)
                        if tree.tree_structure
                        else 0
                    ),
                    "expanded_areas": list(tree.expanded_areas),
                    "pruned_areas": list(tree.pruned_areas),
                    "is_focused": tree_id == session.current_focus,
                    "created_at": tree.created_at,
                    "last_modified": tree.last_modified,
                }
                trees_info.append(tree_info)

            return trees_info

        except Exception as e:
            logger.error(f"Error listing trees: {e}")
            return []

    def _find_expansion_point(
        self, tree: ExplorationTree, expansion_area: str
    ) -> Optional[TreeNode]:
        """Find a node in the tree that matches the expansion area.

        Args:
            tree: Tree to search in
            expansion_area: Area to expand

        Returns:
            TreeNode to expand or None if not found
        """
        if not tree.tree_structure:
            return None

        # Search for nodes that match the expansion area
        matching_nodes = self._search_tree_nodes(tree.tree_structure, expansion_area)

        if matching_nodes:
            # Return the first matching node that hasn't been expanded
            for node in matching_nodes:
                if not node.expanded:
                    return node

        # If no unexpanded nodes found, return the first matching node
        return matching_nodes[0] if matching_nodes else None

    def _search_tree_nodes(self, node: TreeNode, search_term: str) -> List[TreeNode]:
        """Search for nodes in the tree that match a search term.

        Args:
            node: Root node to search from
            search_term: Term to search for

        Returns:
            List of matching nodes
        """
        matching_nodes = []

        # Check if current node matches
        if self._node_matches_search(node, search_term):
            matching_nodes.append(node)

        # Recursively search children
        for child in node.children:
            matching_nodes.extend(self._search_tree_nodes(child, search_term))

        return matching_nodes

    def _node_matches_search(self, node: TreeNode, search_term: str) -> bool:
        """Check if a node matches the search term.

        Args:
            node: TreeNode to check
            search_term: Term to search for

        Returns:
            True if node matches search term
        """
        search_lower = search_term.lower()

        # Check identifier
        if search_lower in node.identifier.lower():
            return True

        # Check node type
        if search_lower in node.node_type.lower():
            return True

        # Check location
        if search_lower in node.location.lower():
            return True

        return False

    def _expand_tree_node(self, node: TreeNode, tree: ExplorationTree) -> None:
        """Expand a specific tree node using aider infrastructure.

        Args:
            node: Node to expand
            tree: Tree containing the node
        """
        try:
            # Use existing repo_map to get dependencies and build sub-tree
            if (
                hasattr(self.repo_map, "repo_map")
                and self.repo_map.repo_map
                and node.depth < tree.max_depth
            ):
                # Get more detailed information about this node
                file_path = self._extract_file_path(node.location)
                if file_path and os.path.exists(file_path):
                    # Use aider's get_tags method if available
                    if hasattr(self.repo_map.repo_map, "get_tags"):
                        tags = self.repo_map.repo_map.get_tags(file_path, node.location)

                        # Add children nodes based on dependencies/calls
                        for tag in tags:
                            if hasattr(tag, "name") and tag.name != node.identifier:
                                child = TreeNode(
                                    identifier=tag.name,
                                    location=f"{node.location}",  # Same file for now
                                    node_type=(
                                        "function"
                                        if hasattr(tag, "kind")
                                        and tag.kind == "function"
                                        else "symbol"
                                    ),
                                    depth=node.depth + 1,
                                )
                                child.parent = node
                                node.children.append(child)

                        node.expanded = True
                        logger.debug(
                            f"Expanded node {node.identifier} with {len(node.children)} children"
                        )

        except Exception as e:
            logger.warning(f"Error expanding node {node.identifier}: {e}")

    def _prune_tree_branch(self, tree: ExplorationTree, prune_area: str) -> bool:
        """Remove a branch from the tree.

        Args:
            tree: Tree to prune
            prune_area: Area to prune

        Returns:
            True if pruning was successful
        """
        if not tree.tree_structure:
            return False

        # Find nodes to prune
        nodes_to_prune = self._search_tree_nodes(tree.tree_structure, prune_area)

        if not nodes_to_prune:
            return False

        # Remove matching nodes from their parents
        for node in nodes_to_prune:
            if node.parent:
                node.parent.children = [
                    child for child in node.parent.children if child != node
                ]
                logger.debug(
                    f"Pruned node {node.identifier} from parent {node.parent.identifier}"
                )

        return True

    def _extract_file_path(self, location: str) -> Optional[str]:
        """Extract file path from location string.

        Args:
            location: Location string (file:line)

        Returns:
            File path or None
        """
        try:
            if ":" in location:
                file_path = location.split(":")[0]
            else:
                file_path = location

            # Resolve to absolute path if possible
            if hasattr(self.repo_map, "config") and hasattr(
                self.repo_map.config, "project_root"
            ):
                abs_path = os.path.join(self.repo_map.config.project_root, file_path)
                if os.path.exists(abs_path):
                    return abs_path

            return file_path

        except Exception as e:
            logger.debug(f"Error extracting file path from {location}: {e}")
            return None

    def _count_nodes(self, node: TreeNode) -> int:
        """Count total nodes in a tree.

        Args:
            node: Root node of the tree

        Returns:
            Total node count
        """
        if not node:
            return 0

        count = 1  # Count this node

        for child in node.children:
            count += self._count_nodes(child)

        return count
