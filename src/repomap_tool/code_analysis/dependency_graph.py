"""
Dependency graph representation and analysis.

This module provides the core dependency graph structure and algorithms for analyzing
code dependencies across a project.
"""

import logging
from dataclasses import asdict
from ..core.config_service import get_config
from ..core.logging_service import get_logger
import networkx as nx
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple, Any
from collections import defaultdict, deque

from .models import DependencyNode, Import, FileImports, ProjectImports
from .import_analyzer import ImportAnalyzer

logger = get_logger(__name__)


class DependencyGraph:
    """Main dependency graph representation using NetworkX."""

    def __init__(self, import_analyzer: Optional[Any] = None) -> None:
        """Initialize an empty dependency graph.

        Args:
            import_analyzer: ImportAnalyzer instance (required dependency)
        """
        # Validate required dependency
        if import_analyzer is None:
            raise ValueError("ImportAnalyzer must be injected - no fallback allowed")

        self.graph = nx.DiGraph()
        self.nodes: Dict[str, DependencyNode] = {}
        self.import_analyzer = import_analyzer
        self.project_path: Optional[str] = None
        self.construction_time: Optional[float] = None

        logger.debug("DependencyGraph initialized")

    def build_graph(self, project_imports: ProjectImports) -> None:
        """Build the dependency graph from a ProjectImports object."""
        logger.debug(
            f"Building dependency graph from ProjectImports for {project_imports.project_path}"
        )

        # Set project path for path resolution
        self.project_path = project_imports.project_path

        # Update import analyzer with project root for proper import resolution
        self.import_analyzer.project_root = project_imports.project_path

        # Clear existing graph
        self.graph.clear()
        self.nodes.clear()

        # Add nodes
        for file_path in project_imports.files.keys():
            self._add_node(file_path)

        # Add edges
        for file_path, file_imports in project_imports.files.items():
            if file_path not in self.nodes:
                continue

            node = self.nodes[file_path]
            node.imports = [
                imp.module
                for imp in file_imports.imports
                if imp.resolved_path and imp.module
            ]
            node.language = file_imports.language or "unknown"

            for imp in file_imports.imports:
                if imp.resolved_path:
                    # Use absolute resolved path directly for node lookup
                    resolved_path = imp.resolved_path
                    if resolved_path in self.nodes:
                        self.graph.add_edge(file_path, resolved_path)
                        if self.nodes[resolved_path].imported_by is None:
                            self.nodes[resolved_path].imported_by = []
                        # At this point, imported_by is guaranteed to be a list
                        imported_by = self.nodes[resolved_path].imported_by
                        assert imported_by is not None  # Type assertion for MyPy
                        imported_by.append(file_path)

            logger.debug(
                f"Graph built: {len(self.nodes)} nodes, {len(self.graph.edges)} edges"
            )

    def _add_node(self, file_path: str) -> None:
        """Add a single node to the graph."""
        try:
            node = DependencyNode(
                file_path=file_path, language=Path(file_path).suffix.lstrip(".")
            )
            self.nodes[file_path] = node
            self.graph.add_node(file_path, **asdict(node))
        except Exception as e:
            logger.error(f"Error adding node for {file_path}: {e}")

    def _validate_files(self, project_files: List[str]) -> None:
        """Validate that all files exist and are accessible."""
        valid_files = []
        for file_path in project_files:
            try:
                path = Path(file_path)
                if path.exists() and path.is_file():
                    valid_files.append(file_path)
                else:
                    logger.warning(f"File does not exist or is not a file: {file_path}")
            except Exception as e:
                logger.warning(f"Error validating file {file_path}: {e}")

        if len(valid_files) != len(project_files):
            logger.warning(
                f"Filtered {len(project_files) - len(valid_files)} invalid files"
            )

        # Update project files to only valid ones
        project_files[:] = valid_files

    def _add_edges(self, project_imports: ProjectImports) -> None:
        """Add dependency edges based on import analysis."""
        logger.info("Adding dependency edges to graph")

        # Build edges from import relationships
        if project_imports.file_imports:
            for file_path, file_imports in project_imports.file_imports.items():
                if file_path not in self.nodes:
                    continue

                # Update node with import information
                node = self.nodes[file_path]
                node.imports = [
                    imp.module
                    for imp in file_imports.imports
                    if imp.resolved_path and imp.module
                ]
                node.language = file_imports.language or "unknown"

                # Add edges for each resolved import
                for imp in file_imports.imports:
                    if imp.resolved_path and imp.resolved_path in self.nodes:
                        # Add edge: file_path -> resolved_path (file_path depends on resolved_path)
                        resolved_path = imp.resolved_path
                        self.graph.add_edge(file_path, resolved_path)

                        # Update imported_by lists
                        if self.nodes[resolved_path].imported_by is None:
                            self.nodes[resolved_path].imported_by = []
                        # At this point, imported_by is guaranteed to be a list
                        imported_by = self.nodes[resolved_path].imported_by
                        assert imported_by is not None  # Type assertion for MyPy
                        imported_by.append(file_path)

        logger.info(f"Added {len(self.graph.edges)} dependency edges")

    def _validate_graph_integrity(self) -> None:
        """Validate the constructed graph for integrity issues."""
        logger.info("Validating graph integrity")

        # Check for orphaned nodes
        connected_nodes = set()
        for source, target in self.graph.edges():
            connected_nodes.add(source)
            connected_nodes.add(target)

        orphaned = set(self.nodes.keys()) - connected_nodes
        if orphaned:
            logger.warning(
                f"Found {len(orphaned)} orphaned nodes: {list(orphaned)[:5]}..."
            )

        # Check for self-references
        self_refs = [(s, t) for s, t in self.graph.edges() if s == t]
        if self_refs:
            logger.warning(f"Found {len(self_refs)} self-references")

        # Check for disconnected components
        if not nx.is_weakly_connected(self.graph):
            components = list(nx.weakly_connected_components(self.graph))
            logger.info(f"Graph has {len(components)} disconnected components")
            for i, component in enumerate(components):
                logger.debug(f"Component {i}: {len(component)} nodes")

    def add_file(self, file_path: str) -> None:
        """Add a single file to the dependency graph.

        Args:
            file_path: Path to the file to add
        """
        if file_path in self.nodes:
            logger.debug(f"File {file_path} already in graph")
            return

        try:
            # Create node
            node = DependencyNode(file_path=file_path, language="python")
            self.nodes[file_path] = node
            self.graph.add_node(file_path, **asdict(node))

            # Analyze imports and add edges
            file_imports = self.import_analyzer.analyze_file_imports(file_path)

            # Update node with import information
            node.imports = [
                imp.module
                for imp in file_imports.imports
                if imp.resolved_path and imp.module
            ]
            node.language = file_imports.language or "unknown"

            # Add edges
            for imp in file_imports.imports:
                if imp.resolved_path and imp.resolved_path in self.nodes:
                    # Edge direction: imported_file → importing_file (so predecessors give dependencies)
                    resolved_path = imp.resolved_path
                    self.graph.add_edge(resolved_path, file_path)
                    if self.nodes[resolved_path].imported_by is None:
                        self.nodes[resolved_path].imported_by = []
                    # At this point, imported_by is guaranteed to be a list
                    imported_by = self.nodes[resolved_path].imported_by
                    assert imported_by is not None  # Type assertion for MyPy
                    imported_by.append(file_path)

            logger.info(f"Added file {file_path} to dependency graph")

        except Exception as e:
            logger.error(f"Error adding file {file_path}: {e}")

    def remove_file(self, file_path: str) -> None:
        """Remove a file from the dependency graph.

        Args:
            file_path: Path to the file to remove
        """
        if file_path not in self.nodes:
            logger.debug(f"File {file_path} not in graph")
            return

        try:
            # Remove edges
            self.graph.remove_node(file_path)

            # Remove from our node collection
            del self.nodes[file_path]

            # Update imported_by lists in other nodes
            for node in self.nodes.values():
                if node.imported_by and file_path in node.imported_by:
                    node.imported_by.remove(file_path)

            logger.info(f"Removed file {file_path} from dependency graph")

        except Exception as e:
            logger.error(f"Error removing file {file_path}: {e}")

    def get_dependencies(self, file_path: str) -> List[str]:
        """Get files that a given file depends on.

        Args:
            file_path: Path to the file

        Returns:
            List of file paths that this file imports
        """
        if file_path not in self.nodes:
            return []

        return list(self.graph.predecessors(file_path))

    def get_dependents(self, file_path: str) -> List[str]:
        """Get files that depend on a given file.

        Args:
            file_path: Path to the file

        Returns:
            List of file paths that import this file
        """
        if file_path not in self.nodes:
            return []

        return list(self.graph.successors(file_path))

    def get_transitive_dependencies(
        self, file_path: str, max_depth: int = get_config("MAX_DEPTH_LIMIT", 10)
    ) -> Set[str]:
        """Get all files transitively dependent on a given file.

        Args:
            file_path: Path to the file
            max_depth: Maximum depth to traverse

        Returns:
            Set of all file paths in the dependency chain
        """
        if file_path not in self.nodes:
            return set()

        visited = set()
        queue = deque([(file_path, 0)])  # (file_path, depth)

        while queue:
            current_file, depth = queue.popleft()

            if depth > max_depth or current_file in visited:
                continue

            visited.add(current_file)

            # Add dependents to queue
            for dependent in self.get_dependents(current_file):
                queue.append((dependent, depth + 1))

        return visited - {file_path}  # Exclude the original file

    def get_transitive_dependents(
        self, file_path: str, max_depth: int = get_config("MAX_DEPTH_LIMIT", 10)
    ) -> Set[str]:
        """Get all files that a given file transitively depends on.

        Args:
            file_path: Path to the file
            max_depth: Maximum depth to traverse

        Returns:
            Set of all file paths in the dependency chain
        """
        if file_path not in self.nodes:
            return set()

        visited = set()
        queue = deque([(file_path, 0)])  # (file_path, depth)

        while queue:
            current_file, depth = queue.popleft()

            if depth > max_depth or current_file in visited:
                continue

            visited.add(current_file)

            # Add dependencies to queue
            for dependency in self.get_dependencies(current_file):
                queue.append((dependency, depth + 1))

        return visited - {file_path}  # Exclude the original file

    def find_cycles(self) -> List[List[str]]:
        """Find circular dependencies in the graph.

        Returns:
            List of cycles, where each cycle is a list of file paths
        """
        try:
            cycles = list(nx.simple_cycles(self.graph))
            logger.debug(f"Found {len(cycles)} circular dependency cycles")
            return cycles
        except Exception as e:
            logger.error(f"Error finding cycles: {e}")
            return []

    def get_leaf_nodes(self) -> List[str]:
        """Get files that have no outgoing dependencies.

        Returns:
            List of file paths that are leaf nodes
        """
        return [node for node in self.graph.nodes() if self.graph.out_degree(node) == 0]

    def get_root_nodes(self) -> List[str]:
        """Get files that have no incoming dependencies.

        Returns:
            List of file paths that are root nodes
        """
        return [node for node in self.graph.nodes() if self.graph.in_degree(node) == 0]

    def get_dependency_depth(self, file_path: str) -> int:
        """Calculate the depth of a file in the dependency chain.

        Args:
            file_path: Path to the file

        Returns:
            Depth level (0 = no dependencies, higher = deeper in chain)
        """
        if file_path not in self.nodes:
            return 0

        # Use NetworkX's shortest path length to calculate depth
        try:
            # Find the longest path from any root to this file
            depths = []
            for root in self.get_root_nodes():
                try:
                    depth = nx.shortest_path_length(self.graph, root, file_path)
                    depths.append(depth)
                except nx.NetworkXNoPath:
                    continue

            return max(depths) if depths else 0

        except Exception as e:
            logger.debug(f"Error calculating depth for {file_path}: {e}")
            return 0

    def get_dependency_clusters(self) -> List[List[str]]:
        """Find clusters of tightly coupled files.

        Returns:
            List of clusters, where each cluster is a list of file paths
        """
        try:
            # Use NetworkX's strongly connected components
            clusters = list(nx.strongly_connected_components(self.graph))

            # Filter out single-node clusters
            meaningful_clusters = [cluster for cluster in clusters if len(cluster) > 1]

            logger.info(f"Found {len(meaningful_clusters)} dependency clusters")
            return meaningful_clusters

        except Exception as e:
            logger.error(f"Error finding dependency clusters: {e}")
            return []

    def calculate_stability_metric(self, file_path: str) -> float:
        """Calculate a stability metric for a file.

        Stability = incoming_dependencies / (incoming + outgoing_dependencies)
        Higher values indicate more stable files (more incoming than outgoing deps).

        Args:
            file_path: Path to the file

        Returns:
            Stability metric between 0 and 1
        """
        if file_path not in self.nodes:
            return 0.0

        try:
            in_degree = self.graph.in_degree(file_path)
            out_degree = self.graph.out_degree(file_path)
            total_degree = in_degree + out_degree

            if total_degree == 0:
                return 0.5  # Neutral stability for isolated files

            return float(in_degree / total_degree)

        except Exception as e:
            logger.debug(f"Error calculating stability for {file_path}: {e}")
            return 0.0

    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the dependency graph.

        Returns:
            Dictionary with graph statistics
        """
        try:
            stats = {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.graph.edges),
                "leaf_nodes": len(self.get_leaf_nodes()),
                "root_nodes": len(self.get_root_nodes()),
                "cycles": len(self.find_cycles()),
                "clusters": len(self.get_dependency_clusters()),
                "is_connected": nx.is_weakly_connected(self.graph),
                "is_dag": nx.is_directed_acyclic_graph(self.graph),
                "average_in_degree": sum(
                    self.graph.in_degree(node) for node in self.graph.nodes()
                )
                / max(len(self.nodes), 1),
                "average_out_degree": sum(
                    self.graph.out_degree(node) for node in self.graph.nodes()
                )
                / max(len(self.nodes), 1),
            }

            # Language distribution
            language_counts: Dict[str, int] = defaultdict(int)
            for node in self.nodes.values():
                lang = node.language or "unknown"
                language_counts[lang] += 1
            stats["language_distribution"] = dict(language_counts)

            return stats

        except Exception as e:
            logger.error(f"Error calculating graph statistics: {e}")
            return {}

    def export_to_networkx(self) -> nx.DiGraph:
        """Export the dependency graph as a NetworkX DiGraph.

        Returns:
            NetworkX directed graph object
        """
        return self.graph.copy()

    def import_from_networkx(self, graph: nx.DiGraph) -> None:
        """Import a dependency graph from a NetworkX DiGraph.

        Args:
            graph: NetworkX directed graph to import
        """
        try:
            self.graph = graph.copy()
            self.nodes = {}

            # Reconstruct nodes from graph data
            for node, data in self.graph.nodes(data=True):
                if "file_path" in data:
                    self.nodes[node] = DependencyNode(**data)
                else:
                    # Create basic node if data is incomplete
                    self.nodes[node] = DependencyNode(file_path=node, language="python")

            logger.info(
                f"Imported graph with {len(self.nodes)} nodes and {len(self.graph.edges)} edges"
            )

        except Exception as e:
            logger.error(f"Error importing graph: {e}")

    def clear(self) -> None:
        """Clear the dependency graph."""
        self.graph.clear()
        self.nodes.clear()
        self.project_path = None
        logger.info("Dependency graph cleared")
