"""
Tree mapper for generating repomaps from exploration trees.

This module generates focused, useful repomaps from current tree exploration state,
providing the output interface for tree-based exploration.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from repomap_tool.models import ExplorationTree, TreeNode
from repomap_tool.core import RepoMapService

logger = logging.getLogger(__name__)


class TreeMapper:
    """Generates repomaps from current tree exploration state."""

    def __init__(self, repo_map: RepoMapService):
        """Initialize tree mapper.

        Args:
            repo_map: RepoMapService instance
        """
        self.repo_map = repo_map

        logger.debug("TreeMapper initialized")

    def generate_tree_map(
        self, tree: ExplorationTree, include_code: bool = True
    ) -> str:
        """Generate repomap from current tree state.

        Args:
            tree: Exploration tree to map
            include_code: Whether to include code snippets

        Returns:
            Formatted repomap string
        """
        if not tree.tree_structure:
            return "❌ Tree structure not available"

        output = []

        # Header
        output.append(f"🌳 Exploration Tree: {tree.context_name}")
        output.append(f"📍 Root: {tree.root_entrypoint.identifier}")
        output.append(f"🎯 Confidence: {tree.confidence:.2f}")
        output.append(f"📊 Nodes: {self._count_nodes(tree.tree_structure)}")
        output.append("")

        # Generate hierarchical tree representation
        tree_repr = self._generate_tree_representation(
            tree.tree_structure, include_code
        )
        output.append(tree_repr)

        # Show expansion/pruning history
        if tree.expanded_areas:
            output.append(f"\n✅ Expanded areas: {', '.join(tree.expanded_areas)}")

        if tree.pruned_areas:
            output.append(f"✂️ Pruned areas: {', '.join(tree.pruned_areas)}")

        # Show available expansion points
        expansion_points = self._find_expansion_opportunities(tree)
        if expansion_points:
            output.append(f"\n🔍 Available expansions:")
            for point in expansion_points:
                output.append(
                    f'  • {point} - expand with: repomap-tool expand "{point}"'
                )

        return "\n".join(output)

    def _generate_tree_representation(
        self, node: TreeNode, include_code: bool, prefix: str = ""
    ) -> str:
        """Generate hierarchical tree representation.

        Args:
            node: Root node of the tree
            include_code: Whether to include code snippets
            prefix: Prefix for indentation

        Returns:
            Formatted tree representation
        """
        output = []

        # Current node
        node_line = f"{prefix}├── {node.identifier}"

        if node.location and node.location != "unknown:0":
            node_line += f" ({node.location})"

        if node.node_type != "entrypoint":
            node_line += f" [{node.node_type}]"

        output.append(node_line)

        # Code snippet if requested
        if include_code and node.node_type in ["function", "class"]:
            code_snippet = self._get_code_snippet(node)
            if code_snippet:
                output.append(f"{prefix}│   └── {code_snippet}")

        # Recursively add children
        for i, child in enumerate(node.children):
            child_prefix = prefix + ("│   " if i < len(node.children) - 1 else "    ")
            child_output = self._generate_tree_representation(
                child, include_code, child_prefix
            )
            output.append(child_output)

        return "\n".join(output)

    def _get_code_snippet(self, node: TreeNode) -> Optional[str]:
        """Get relevant code snippet for tree node.

        Args:
            node: TreeNode to get code for

        Returns:
            Code snippet or None
        """
        try:
            # Use existing repo_map infrastructure to get code details
            if hasattr(self.repo_map, "repo_map") and self.repo_map.repo_map:
                file_path = self._extract_file_path(node.location)
                if file_path and os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()

                        # Find the function/class definition
                        for i, line in enumerate(lines):
                            if node.identifier in line and (
                                "def " in line
                                or "class " in line
                                or "async def " in line
                            ):
                                # Get a few lines of context
                                start_line = max(0, i - 1)
                                end_line = min(len(lines), i + 3)
                                context_lines = lines[start_line:end_line]

                                # Clean up and format
                                snippet = "".join(context_lines).strip()
                                if len(snippet) > 100:
                                    snippet = snippet[:97] + "..."

                                return snippet

        except Exception as e:
            logger.debug(f"Error getting code snippet for {node.identifier}: {e}")

        return None

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

    def _find_expansion_opportunities(self, tree: ExplorationTree) -> List[str]:
        """Find areas in the tree that could be expanded.

        Args:
            tree: Tree to analyze

        Returns:
            List of expansion opportunities
        """
        if not tree.tree_structure:
            return []

        opportunities = []

        # Find unexpanded nodes that could be interesting
        unexpanded_nodes = self._find_unexpanded_nodes(tree.tree_structure)

        for node in unexpanded_nodes:
            # Suggest expansion based on node characteristics
            if node.node_type in ["function", "class"] and node.depth < tree.max_depth:
                opportunities.append(node.identifier.lower().replace("_", " "))

            # Suggest expansion based on location patterns
            if "validation" in node.location.lower():
                opportunities.append("validation")
            elif "error" in node.location.lower():
                opportunities.append("error_handling")
            elif "auth" in node.location.lower():
                opportunities.append("authentication")
            elif "db" in node.location.lower() or "database" in node.location.lower():
                opportunities.append("database")

        # Remove duplicates and limit results
        unique_opportunities = list(set(opportunities))[:5]
        return unique_opportunities

    def _find_unexpanded_nodes(self, node: TreeNode) -> List[TreeNode]:
        """Find all unexpanded nodes in the tree.

        Args:
            node: Root node to search from

        Returns:
            List of unexpanded nodes
        """
        unexpanded = []

        if not node.expanded:
            unexpanded.append(node)

        for child in node.children:
            unexpanded.extend(self._find_unexpanded_nodes(child))

        return unexpanded

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

    def generate_tree_summary(self, tree: ExplorationTree) -> str:
        """Generate a summary of the tree.

        Args:
            tree: Tree to summarize

        Returns:
            Summary string
        """
        if not tree.tree_structure:
            return "Tree structure not available"

        summary = []
        summary.append(f"📋 Tree Summary: {tree.context_name}")
        summary.append(f"   Root: {tree.root_entrypoint.identifier}")
        summary.append(f"   Confidence: {tree.confidence:.2f}")
        summary.append(f"   Total Nodes: {self._count_nodes(tree.tree_structure)}")
        summary.append(f"   Max Depth: {tree.max_depth}")
        summary.append(f"   Expanded Areas: {len(tree.expanded_areas)}")
        summary.append(f"   Pruned Areas: {len(tree.pruned_areas)}")

        # Node type breakdown
        node_types = self._analyze_node_types(tree.tree_structure)
        if node_types:
            summary.append("   Node Types:")
            for node_type, count in sorted(node_types.items()):
                summary.append(f"     • {node_type}: {count}")

        return "\n".join(summary)

    def _analyze_node_types(self, node: TreeNode) -> Dict[str, int]:
        """Analyze the distribution of node types in the tree.

        Args:
            node: Root node to analyze

        Returns:
            Dictionary mapping node types to counts
        """
        node_types: Dict[str, int] = {}

        def count_types(n: TreeNode) -> None:
            node_type = n.node_type
            node_types[node_type] = node_types.get(node_type, 0) + 1

            for child in n.children:
                count_types(child)

        count_types(node)
        return node_types

    def generate_export_format(
        self, tree: ExplorationTree, format_type: str = "json"
    ) -> str:
        """Generate tree in export format.

        Args:
            tree: Tree to export
            format_type: Export format (json, yaml, etc.)

        Returns:
            Exported tree string
        """
        if format_type.lower() == "json":
            return self._export_as_json(tree)
        elif format_type.lower() == "yaml":
            return self._export_as_yaml(tree)
        else:
            return f"Unsupported export format: {format_type}"

    def _export_as_json(self, tree: ExplorationTree) -> str:
        """Export tree as JSON.

        Args:
            tree: Tree to export

        Returns:
            JSON string
        """
        import json

        try:
            # Convert tree to serializable format
            export_data = {
                "tree_id": tree.tree_id,
                "context_name": tree.context_name,
                "root_entrypoint": {
                    "identifier": tree.root_entrypoint.identifier,
                    "location": tree.root_entrypoint.location,
                    "score": tree.root_entrypoint.score,
                },
                "max_depth": tree.max_depth,
                "confidence": tree.confidence,
                "created_at": tree.created_at.isoformat(),
                "last_modified": tree.last_modified.isoformat(),
                "expanded_areas": list(tree.expanded_areas),
                "pruned_areas": list(tree.pruned_areas),
                "tree_structure": (
                    self._serialize_tree_node(tree.tree_structure)
                    if tree.tree_structure
                    else None
                ),
            }

            return json.dumps(export_data, indent=2)

        except Exception as e:
            logger.error(f"Error exporting tree as JSON: {e}")
            return f"Error exporting tree: {e}"

    def _export_as_yaml(self, tree: ExplorationTree) -> str:
        """Export tree as YAML.

        Args:
            tree: Tree to export

        Returns:
            YAML string
        """
        try:
            import yaml

            # Convert tree to serializable format (same as JSON)
            export_data = {
                "tree_id": tree.tree_id,
                "context_name": tree.context_name,
                "root_entrypoint": {
                    "identifier": tree.root_entrypoint.identifier,
                    "location": tree.root_entrypoint.location,
                    "score": tree.root_entrypoint.score,
                },
                "max_depth": tree.max_depth,
                "confidence": tree.confidence,
                "created_at": tree.created_at.isoformat(),
                "last_modified": tree.last_modified.isoformat(),
                "expanded_areas": list(tree.expanded_areas),
                "pruned_areas": list(tree.pruned_areas),
                "tree_structure": (
                    self._serialize_tree_node(tree.tree_structure)
                    if tree.tree_structure
                    else None
                ),
            }

            return yaml.dump(export_data, default_flow_style=False, indent=2)

        except ImportError:
            return "YAML export requires PyYAML package"
        except Exception as e:
            logger.error(f"Error exporting tree as YAML: {e}")
            return f"Error exporting tree: {e}"

    def _serialize_tree_node(self, node: TreeNode) -> Dict[str, Any]:
        """Serialize TreeNode for export.

        Args:
            node: TreeNode to serialize

        Returns:
            Serialized node dictionary
        """
        if not node:
            return {}

        serialized = {
            "identifier": node.identifier,
            "location": node.location,
            "node_type": node.node_type,
            "depth": node.depth,
            "expanded": node.expanded,
            "structural_info": node.structural_info,
            "children": [self._serialize_tree_node(child) for child in node.children],
        }

        return serialized
