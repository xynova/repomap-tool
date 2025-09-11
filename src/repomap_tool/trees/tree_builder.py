"""
Tree builder for exploration tree construction.

This module builds exploration trees from discovered entrypoints using existing
aider infrastructure for dependency analysis and tree structure creation.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from repomap_tool.models import Entrypoint, ExplorationTree, TreeNode
from repomap_tool.core import RepoMapService

logger = logging.getLogger(__name__)


class TreeBuilder:
    """Builds exploration trees from entrypoints using existing aider infrastructure."""

    def __init__(self, repo_map: RepoMapService):
        """Initialize tree builder.

        Args:
            repo_map: RepoMapService instance with aider infrastructure
        """
        self.repo_map = repo_map
        self.entrypoint_cache: Dict[str, Any] = {}  # Cache discovered entrypoints
        self.tree_cache: Dict[str, Any] = {}  # Cache built trees

        logger.debug("TreeBuilder initialized")

    def build_exploration_tree(
        self, entrypoint: Entrypoint, max_depth: int = 3
    ) -> ExplorationTree:
        """Build exploration tree from entrypoint.

        Args:
            entrypoint: Root entrypoint for the tree
            max_depth: Maximum tree depth

        Returns:
            ExplorationTree with hierarchical structure
        """
        cache_key = f"{entrypoint.identifier}_{max_depth}"
        if cache_key in self.tree_cache:
            logger.debug(f"Using cached tree for {entrypoint.identifier}")
            return self.tree_cache[cache_key]  # type: ignore

        logger.info(
            f"Building exploration tree for {entrypoint.identifier} (max_depth={max_depth})"
        )

        # Create tree structure
        tree = ExplorationTree(
            tree_id=f"tree_{entrypoint.identifier.lower().replace(' ', '_')}_{hash(entrypoint.location) % 10000:04d}",
            root_entrypoint=entrypoint,
            max_depth=max_depth,
        )

        # Build tree structure using existing aider infrastructure
        if hasattr(self.repo_map, "repo_map") and self.repo_map.repo_map:
            # Get tags and dependencies for this entrypoint
            tree_structure = self._build_tree_structure(entrypoint, max_depth)
            tree.tree_structure = tree_structure
        else:
            # Fallback: create simple tree structure
            tree.tree_structure = self._create_simple_tree_structure(entrypoint)

        # Cache the tree
        self.tree_cache[cache_key] = tree

        logger.info(
            f"Built tree {tree.tree_id} with {self._count_nodes(tree.tree_structure)} nodes"
        )
        return tree

    def build_exploration_tree_with_dependencies(
        self,
        entrypoint: Entrypoint,
        max_depth: int = 3,
        current_files: Optional[List[str]] = None,
    ) -> ExplorationTree:
        """Build exploration tree with dependency intelligence.

        Args:
            entrypoint: Root entrypoint for the tree
            max_depth: Maximum tree depth
            current_files: Currently focused files for context

        Returns:
            ExplorationTree with dependency-aware structure
        """
        cache_key = f"{entrypoint.identifier}_{max_depth}_dep"
        if cache_key in self.tree_cache:
            logger.debug(f"Using cached dependency tree for {entrypoint.identifier}")
            return self.tree_cache[cache_key]  # type: ignore

        logger.info(
            f"Building dependency-enhanced tree for {entrypoint.identifier} (max_depth={max_depth})"
        )

        # Create tree structure
        tree = ExplorationTree(
            tree_id=f"dep_tree_{entrypoint.identifier.lower().replace(' ', '_')}_{hash(entrypoint.location) % 10000:04d}",
            root_entrypoint=entrypoint,
            max_depth=max_depth,
        )

        # Build tree structure with dependency intelligence
        tree_structure = self._build_dependency_aware_tree_structure(
            entrypoint, max_depth, current_files
        )
        tree.tree_structure = tree_structure

        # Cache the tree
        self.tree_cache[cache_key] = tree

        logger.info(
            f"Built dependency tree {tree.tree_id} with {self._count_nodes(tree.tree_structure)} nodes"
        )
        return tree

    def _build_tree_structure(self, entrypoint: Entrypoint, max_depth: int) -> TreeNode:
        """Build hierarchical tree structure from entrypoint.

        Args:
            entrypoint: Root entrypoint
            max_depth: Maximum tree depth

        Returns:
            Root TreeNode with hierarchical structure
        """
        root = TreeNode(
            identifier=entrypoint.identifier,
            location=str(entrypoint.location),
            node_type="entrypoint",
            depth=0,
        )

        # Recursively build tree using aider's dependency information
        self._expand_node(root, entrypoint, max_depth, 0)

        return root

    def _build_dependency_aware_tree_structure(
        self,
        entrypoint: Entrypoint,
        max_depth: int,
        current_files: Optional[List[str]] = None,
    ) -> TreeNode:
        """Build hierarchical tree structure with dependency intelligence.

        Args:
            entrypoint: Root entrypoint
            max_depth: Maximum tree depth
            current_files: Currently focused files for context

        Returns:
            Root TreeNode with dependency-aware structure
        """
        root = TreeNode(
            identifier=entrypoint.identifier,
            location=str(entrypoint.location),
            node_type="entrypoint",
            depth=0,
        )

        # Add dependency centrality information to root node
        self._add_centrality_info(root, str(entrypoint.location))

        # Recursively build tree using dependency intelligence
        self._expand_node_with_dependencies(
            root, entrypoint, max_depth, 0, current_files
        )

        return root

    def _expand_node_with_dependencies(
        self,
        node: TreeNode,
        entrypoint: Entrypoint,
        max_depth: int,
        current_depth: int,
        current_files: Optional[List[str]] = None,
    ) -> None:
        """Expand a tree node using dependency intelligence.

        Args:
            node: TreeNode to expand
            entrypoint: Associated entrypoint
            max_depth: Maximum tree depth
            current_depth: Current depth in tree
            current_files: Currently focused files for context
        """
        if current_depth >= max_depth:
            logger.debug(f"Reached max depth {max_depth} for node {node.identifier}")
            return

        try:
            # Get dependency-aware related symbols
            related_symbols = self._get_dependency_aware_symbols(
                entrypoint, node, current_files
            )

            # Sort by importance (centrality + relevance)
            related_symbols = self._sort_by_importance(related_symbols, current_files)

            # Limit children based on depth and importance
            max_children = self._calculate_max_children(current_depth, max_depth)
            related_symbols = related_symbols[:max_children]

            for symbol in related_symbols:
                if self._should_add_as_child(symbol, node):
                    child = TreeNode(
                        identifier=symbol.get("name", "Unknown"),
                        location=self._get_symbol_location(
                            symbol, str(entrypoint.location)
                        ),
                        node_type=symbol.get("kind", "symbol"),
                        depth=current_depth + 1,
                    )

                    # Add dependency information to child
                    self._add_centrality_info(child, child.location)

                    child.parent = node
                    node.children.append(child)

                    # Recursively expand child if not at max depth
                    if current_depth + 1 < max_depth:
                        self._expand_node_with_dependencies(
                            child,
                            entrypoint,
                            max_depth,
                            current_depth + 1,
                            current_files,
                        )

        except Exception as e:
            logger.warning(f"Failed to expand node {node.identifier}: {e}")

    def _get_dependency_aware_symbols(
        self,
        entrypoint: Entrypoint,
        node: TreeNode,
        current_files: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get symbols with dependency intelligence.

        Args:
            entrypoint: Associated entrypoint
            node: Current tree node
            current_files: Currently focused files for context

        Returns:
            List of symbols with dependency information
        """
        try:
            # Get basic related symbols
            related_symbols = self._get_related_symbols(entrypoint, node)

            # Enhance with dependency information
            enhanced_symbols = []
            for symbol in related_symbols:
                enhanced_symbol = symbol.copy()

                # Add dependency centrality information
                symbol_location = self._get_symbol_location(
                    symbol, str(entrypoint.location)
                )
                if symbol_location:
                    centrality_info = self._get_centrality_info(symbol_location)
                    enhanced_symbol.update(centrality_info)

                # Add relevance score based on current context
                relevance_score = self._calculate_relevance_score(symbol, current_files)
                enhanced_symbol["relevance_score"] = relevance_score

                enhanced_symbols.append(enhanced_symbol)

            return enhanced_symbols

        except Exception as e:
            logger.warning(f"Failed to get dependency-aware symbols: {e}")
            return self._get_related_symbols(entrypoint, node)

    def _sort_by_importance(
        self, symbols: List[Dict[str, Any]], current_files: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Sort symbols by importance (centrality + relevance).

        Args:
            symbols: List of symbols to sort
            current_files: Currently focused files for context

        Returns:
            Sorted list of symbols by importance
        """

        def importance_score(symbol: Dict[str, Any]) -> float:
            # Combine centrality and relevance scores
            centrality = float(symbol.get("centrality_score", 0.0))
            relevance = float(symbol.get("relevance_score", 0.0))

            # Weighted combination (centrality 60%, relevance 40%)
            return centrality * 0.6 + relevance * 0.4

        return sorted(symbols, key=importance_score, reverse=True)

    def _calculate_max_children(self, current_depth: int, max_depth: int) -> int:
        """Calculate maximum number of children based on depth.

        Args:
            current_depth: Current depth in tree
            max_depth: Maximum tree depth

        Returns:
            Maximum number of children to add
        """
        # Decrease children as depth increases to prevent explosion
        base_children = 8
        depth_factor = max_depth - current_depth
        return max(3, min(base_children, base_children * depth_factor // max_depth))

    def _calculate_relevance_score(
        self, symbol: Dict[str, Any], current_files: Optional[List[str]] = None
    ) -> float:
        """Calculate relevance score based on current context.

        Args:
            symbol: Symbol to score
            current_files: Currently focused files for context

        Returns:
            Relevance score (0.0 to 1.0)
        """
        if not current_files:
            return 0.5  # Neutral score if no context

        symbol_location = symbol.get("location", "")
        if not symbol_location:
            return 0.0

        # Check if symbol is in current files
        for current_file in current_files:
            if current_file in symbol_location or symbol_location in current_file:
                return 1.0  # High relevance

        # Check for directory proximity
        symbol_dir = str(Path(symbol_location).parent)
        for current_file in current_files:
            current_dir = str(Path(current_file).parent)
            if symbol_dir == current_dir:
                return 0.8  # High relevance (same directory)
            elif symbol_dir in current_dir or current_dir in symbol_dir:
                return 0.6  # Medium relevance (related directory)

        return 0.3  # Low relevance

    def _get_centrality_info(self, file_path: str) -> Dict[str, Any]:
        """Get centrality information for a file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with centrality information
        """
        try:
            if (
                not hasattr(self.repo_map, "centrality_calculator")
                or not self.repo_map.centrality_calculator
            ):
                return {"centrality_score": 0.0, "centrality_rank": 0}

            centrality_scores = (
                self.repo_map.centrality_calculator.calculate_composite_importance()
            )
            centrality_score = centrality_scores.get(file_path, 0.0)

            # Calculate rank (higher score = lower rank number)
            sorted_scores = sorted(centrality_scores.values(), reverse=True)
            try:
                centrality_rank = sorted_scores.index(centrality_score) + 1
            except ValueError:
                centrality_rank = len(sorted_scores) + 1

            return {
                "centrality_score": centrality_score,
                "centrality_rank": centrality_rank,
            }

        except Exception as e:
            logger.warning(f"Failed to get centrality info for {file_path}: {e}")
            return {"centrality_score": 0.0, "centrality_rank": 0}

    def _add_centrality_info(self, node: TreeNode, file_path: str) -> None:
        """Add centrality information to a tree node.

        Args:
            node: TreeNode to enhance
            file_path: Path to the file
        """
        try:
            centrality_info = self._get_centrality_info(file_path)
            node.structural_info = {**node.structural_info, **centrality_info}
        except Exception as e:
            logger.warning(
                f"Failed to add centrality info to node {node.identifier}: {e}"
            )

    def _expand_node(
        self, node: TreeNode, entrypoint: Entrypoint, max_depth: int, current_depth: int
    ) -> None:
        """Expand a tree node by adding children.

        Args:
            node: TreeNode to expand
            entrypoint: Associated entrypoint
            max_depth: Maximum tree depth
            current_depth: Current depth in tree
        """
        if current_depth >= max_depth:
            logger.debug(f"Reached max depth {max_depth} for node {node.identifier}")
            return

        try:
            # Get dependencies and related symbols using existing infrastructure
            related_symbols = self._get_related_symbols(entrypoint, node)

            for symbol in related_symbols:
                if self._should_add_as_child(symbol, node):
                    child = TreeNode(
                        identifier=symbol.get("name", "Unknown"),
                        location=self._get_symbol_location(
                            symbol, str(entrypoint.location)
                        ),
                        node_type=symbol.get("kind", "symbol"),
                        depth=current_depth + 1,
                    )
                    child.parent = node
                    node.children.append(child)

                    # Recursively expand child if not at max depth
                    if current_depth + 1 < max_depth:
                        self._expand_node(
                            child, entrypoint, max_depth, current_depth + 1
                        )

        except Exception as e:
            logger.warning(f"Error expanding node {node.identifier}: {e}")

    def _get_related_symbols(
        self, entrypoint: Entrypoint, node: TreeNode
    ) -> List[Dict[str, Any]]:
        """Get symbols related to the current node.

        Args:
            entrypoint: Root entrypoint
            node: Current tree node

        Returns:
            List of related symbol dictionaries
        """
        try:
            # Try to use existing aider infrastructure
            if hasattr(self.repo_map, "repo_map") and self.repo_map.repo_map:
                # Get tags for the current node's file
                file_path = self._extract_file_path(node.location)
                if file_path and os.path.exists(file_path):
                    # Use aider's get_tags method if available
                    if hasattr(self.repo_map.repo_map, "get_tags"):
                        tags = self.repo_map.repo_map.get_tags(file_path, node.location)
                        return self._process_aider_tags(tags)

            # Fallback: return empty list
            return []

        except Exception as e:
            logger.debug(f"Error getting related symbols for {node.identifier}: {e}")
            return []

    def _process_aider_tags(self, tags: List) -> List[Dict[str, Any]]:
        """Process tags returned by aider infrastructure.

        Args:
            tags: Raw tags from aider

        Returns:
            Processed symbol dictionaries
        """
        processed_symbols = []

        for tag in tags:
            try:
                # Handle different tag formats
                if hasattr(tag, "name"):
                    symbol = {
                        "name": tag.name,
                        "kind": getattr(tag, "kind", "symbol"),
                        "file_path": getattr(tag, "file_path", ""),
                        "line_number": getattr(tag, "line_number", 0),
                    }
                    processed_symbols.append(symbol)
                elif isinstance(tag, dict):
                    processed_symbols.append(tag)
                elif isinstance(tag, str):
                    processed_symbols.append(
                        {
                            "name": tag,
                            "kind": "symbol",
                            "file_path": "",
                            "line_number": 0,
                        }
                    )

            except Exception as e:
                logger.debug(f"Error processing tag {tag}: {e}")
                continue

        return processed_symbols

    def _should_add_as_child(
        self, symbol: Dict[str, Any], parent_node: TreeNode
    ) -> bool:
        """Determine if a symbol should be added as a child of the parent node.

        Args:
            symbol: Symbol to evaluate
            parent_node: Potential parent node

        Returns:
            True if symbol should be added as child
        """
        # Don't add if it's the same as parent
        if symbol.get("name") == parent_node.identifier:
            return False

        # Don't add if it's already a child
        if any(
            child.identifier == symbol.get("name") for child in parent_node.children
        ):
            return False

        # Don't add if it's the parent's parent
        if parent_node.parent and symbol.get("name") == parent_node.parent.identifier:
            return False

        # Add if it's a reasonable symbol
        symbol_name = symbol.get("name", "")
        if symbol_name and len(symbol_name) > 1:
            return True

        return False

    def _get_symbol_location(self, symbol: Dict[str, Any], parent_location: str) -> str:
        """Get location string for a symbol.

        Args:
            symbol: Symbol dictionary
            parent_location: Parent node location

        Returns:
            Location string (file:line)
        """
        try:
            file_path = symbol.get("file_path", "")
            line_number = symbol.get("line_number", 0)

            if file_path and line_number:
                # Make path relative if possible
                if hasattr(self.repo_map, "config") and hasattr(
                    self.repo_map.config, "project_root"
                ):
                    try:
                        rel_path = os.path.relpath(
                            file_path, self.repo_map.config.project_root
                        )
                        return f"{rel_path}:{line_number}"
                    except ValueError:
                        return f"{file_path}:{line_number}"
                else:
                    return f"{file_path}:{line_number}"
            elif file_path:
                return file_path  # type: ignore
            else:
                # Use parent location as fallback
                return parent_location

        except Exception as e:
            logger.debug(f"Error getting symbol location: {e}")
            return parent_location

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

    def _create_simple_tree_structure(self, entrypoint: Entrypoint) -> TreeNode:
        """Create a simple tree structure when aider infrastructure is not available.

        Args:
            entrypoint: Root entrypoint

        Returns:
            Simple TreeNode structure
        """
        root = TreeNode(
            identifier=entrypoint.identifier,
            location=str(entrypoint.location),
            node_type="entrypoint",
            depth=0,
        )

        # Add some placeholder children to show the tree structure
        placeholder_children = [
            TreeNode(
                identifier=f"{entrypoint.identifier}Helper",
                location=str(entrypoint.location),
                node_type="function",
                depth=1,
            ),
            TreeNode(
                identifier=f"{entrypoint.identifier}Validator",
                location=str(entrypoint.location),
                node_type="function",
                depth=1,
            ),
        ]

        for child in placeholder_children:
            child.parent = root
            root.children.append(child)

        return root

    def _count_nodes(self, node: TreeNode) -> int:
        """Count total nodes in a tree.

        Args:
            node: Root node of the tree

        Returns:
            Total node count
        """
        count = 1  # Count this node

        for child in node.children:
            count += self._count_nodes(child)

        return count

    def clear_cache(self) -> None:
        """Clear the tree cache."""
        self.entrypoint_cache.clear()
        self.tree_cache.clear()
        logger.debug("Tree cache cleared")
