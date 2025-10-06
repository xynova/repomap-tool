"""
Advanced dependency graph with call graph integration.

This module extends the basic DependencyGraph with call graph analysis and
advanced dependency metrics for comprehensive code relationship analysis.
"""

import logging
from ..core.config_service import get_config
from ..core.logging_service import get_logger
from typing import List, Dict, Set, Optional, Any, Tuple
from collections import defaultdict, deque

from .dependency_graph import DependencyGraph
from .call_graph_builder import CallGraphBuilder
from .models import CallGraph, FunctionCall

logger = get_logger(__name__)


class AdvancedDependencyGraph(DependencyGraph):
    """Enhanced dependency graph with call graph integration and advanced metrics."""

    def __init__(self) -> None:
        """Initialize the advanced dependency graph."""
        super().__init__()
        self.call_graph: Optional[CallGraph] = None
        self.call_graph_builder = CallGraphBuilder()
        self.function_dependencies: Dict[str, Set[str]] = {}
        self.function_dependents: Dict[str, Set[str]] = {}
        self.centrality_scores: Dict[str, float] = {}

        logger.info("AdvancedDependencyGraph initialized")

    def integrate_call_graph(self, call_graph: CallGraph) -> None:
        """Integrate function call information into the dependency graph.

        Args:
            call_graph: CallGraph object to integrate
        """
        logger.info("Integrating call graph into dependency graph")

        self.call_graph = call_graph

        # Build function dependency maps
        self._build_function_dependency_maps()

        # Update dependency nodes with function information
        self._update_nodes_with_function_info()

        logger.info("Call graph integration complete")

    def _build_function_dependency_maps(self) -> None:
        """Build maps of function dependencies and dependents."""
        if not self.call_graph:
            return

        try:
            # Initialize maps
            self.function_dependencies = defaultdict(set)
            self.function_dependents = defaultdict(set)

            # Process all function calls
            for call in self.call_graph.function_calls:
                if call.caller != "unknown" and call.callee != "unknown":
                    # caller depends on callee
                    self.function_dependencies[call.caller].add(call.callee)
                    # callee is depended on by caller
                    self.function_dependents[call.callee].add(call.caller)

            logger.info(
                f"Built function dependency maps: {len(self.function_dependencies)} functions"
            )

        except Exception as e:
            logger.error(f"Error building function dependency maps: {e}")

    def _update_nodes_with_function_info(self) -> None:
        """Update dependency nodes with function information from call graph."""
        if not self.call_graph:
            return

        try:
            # Group functions by file
            file_functions = defaultdict(list)
            for func_name, file_path in self.call_graph.function_locations.items():
                file_functions[file_path].append(func_name)

            # Update each node with function information
            for file_path, node in self.nodes.items():
                if file_path in file_functions:
                    node.functions = file_functions[file_path]

                    # Calculate function-level metrics
                    node.structural_info = {
                        "function_count": len(node.functions),
                        "function_dependencies": self._get_file_function_dependencies(
                            file_path
                        ),
                        "function_dependents": self._get_file_function_dependents(
                            file_path
                        ),
                    }

            logger.info("Updated nodes with function information")

        except Exception as e:
            logger.error(f"Error updating nodes with function info: {e}")

    def _get_file_function_dependencies(self, file_path: str) -> List[str]:
        """Get all functions that functions in a file depend on."""
        if not self.call_graph or file_path not in self.nodes:
            return []

        dependencies = set()
        for func_name in self.nodes[file_path].functions:
            if func_name in self.function_dependencies:
                dependencies.update(self.function_dependencies[func_name])

        return list(dependencies)

    def _get_file_function_dependents(self, file_path: str) -> List[str]:
        """Get all functions that depend on functions in a file."""
        if not self.call_graph or file_path not in self.nodes:
            return []

        dependents = set()
        for func_name in self.nodes[file_path].functions:
            if func_name in self.function_dependents:
                dependents.update(self.function_dependents[func_name])

        return list(dependents)

    def calculate_transitive_dependencies(
        self, file_path: str, max_depth: int = get_config("MAX_DEPTH_LIMIT", 10)
    ) -> Set[str]:
        """Get all files transitively dependent on a given file.

        This enhanced version includes both import dependencies and function call dependencies.

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

            # Add import-based dependents
            for dependent in self.get_dependents(current_file):
                queue.append((dependent, depth + 1))

            # Add function-call-based dependents
            if self.call_graph:
                function_dependents = self._get_file_function_dependents(current_file)
                for func_name in function_dependents:
                    if func_name in self.call_graph.function_locations:
                        dependent_file = self.call_graph.function_locations[func_name]
                        if dependent_file != current_file:
                            queue.append((dependent_file, depth + 1))

        return visited - {file_path}  # Exclude the original file

    def calculate_transitive_dependents(
        self, file_path: str, max_depth: int = get_config("MAX_DEPTH_LIMIT", 10)
    ) -> Set[str]:
        """Get all files that a given file transitively depends on.

        This enhanced version includes both import dependencies and function call dependencies.

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

            # Add import-based dependencies
            for dependency in self.get_dependencies(current_file):
                queue.append((dependency, depth + 1))

            # Add function-call-based dependencies
            if self.call_graph:
                function_dependencies = self._get_file_function_dependencies(
                    current_file
                )
                for func_name in function_dependencies:
                    if func_name in self.call_graph.function_locations:
                        dependency_file = self.call_graph.function_locations[func_name]
                        if dependency_file != current_file:
                            queue.append((dependency_file, depth + 1))

        return visited - {file_path}  # Exclude the original file

    def calculate_dependency_depth(self, file_path: str) -> int:
        """Calculate how deep the dependency chain is for a file.

        This enhanced version considers both import and function call dependencies.

        Args:
            file_path: Path to the file

        Returns:
            Depth level (0 = no dependencies, higher = deeper in chain)
        """
        if file_path not in self.nodes:
            return 0

        try:
            # Find the longest path from any root to this file
            depths = []
            for root in self.get_root_nodes():
                try:
                    depth = self._calculate_path_depth(root, file_path)
                    depths.append(depth)
                except Exception:
                    continue

            return max(depths) if depths else 0

        except Exception as e:
            logger.debug(f"Error calculating dependency depth for {file_path}: {e}")
            return 0

    def _calculate_path_depth(
        self, start_file: str, end_file: str, max_depth: int = 20
    ) -> int:
        """Calculate the depth of a path between two files."""
        visited = set()
        queue = deque([(start_file, 0)])  # (file_path, depth)

        while queue:
            current_file, depth = queue.popleft()

            if current_file == end_file:
                return depth

            if depth > max_depth or current_file in visited:
                continue

            visited.add(current_file)

            # Add import-based dependencies
            for dependency in self.get_dependencies(current_file):
                queue.append((dependency, depth + 1))

            # Add function-call-based dependencies
            if self.call_graph:
                function_dependencies = self._get_file_function_dependencies(
                    current_file
                )
                for func_name in function_dependencies:
                    if func_name in self.call_graph.function_locations:
                        dependency_file = self.call_graph.function_locations[func_name]
                        if dependency_file != current_file:
                            queue.append((dependency_file, depth + 1))

        return 0  # No path found

    def find_dependency_clusters(self) -> List[List[str]]:
        """Find clusters of tightly coupled files.

        This enhanced version considers both import relationships and function call patterns.

        Returns:
            List of clusters, where each cluster is a list of file paths
        """
        try:
            # Get basic import-based clusters
            import_clusters = super().get_dependency_clusters()

            # Enhance with function call patterns
            enhanced_clusters = self._enhance_clusters_with_function_calls(
                import_clusters
            )

            logger.info(f"Found {len(enhanced_clusters)} enhanced dependency clusters")
            return enhanced_clusters

        except Exception as e:
            logger.error(f"Error finding dependency clusters: {e}")
            return []

    def _enhance_clusters_with_function_calls(
        self, import_clusters: List[List[str]]
    ) -> List[List[str]]:
        """Enhance import-based clusters with function call information."""
        if not self.call_graph:
            return import_clusters

        try:
            enhanced_clusters = []

            for cluster in import_clusters:
                enhanced_cluster = set(cluster)

                # Add files that have strong function call relationships
                for file_path in cluster:
                    # Find functions in this file
                    file_functions = self.nodes[file_path].functions

                    for func_name in file_functions:
                        # Add files that call these functions
                        if func_name in self.function_dependents:
                            for caller in self.function_dependents[func_name]:
                                if caller in self.call_graph.function_locations:
                                    caller_file = self.call_graph.function_locations[
                                        caller
                                    ]
                                    if caller_file not in enhanced_cluster:
                                        enhanced_cluster.add(caller_file)

                        # Add files that these functions call
                        if func_name in self.function_dependencies:
                            for callee in self.function_dependencies[func_name]:
                                if callee in self.call_graph.function_locations:
                                    callee_file = self.call_graph.function_locations[
                                        callee
                                    ]
                                    if callee_file not in enhanced_cluster:
                                        enhanced_cluster.add(callee_file)

                enhanced_clusters.append(list(enhanced_cluster))

            return enhanced_clusters

        except Exception as e:
            logger.error(f"Error enhancing clusters with function calls: {e}")
            return import_clusters

    def calculate_stability_metric(self, file_path: str) -> float:
        """Calculate how stable a file is.

        Stability = incoming_dependencies / (incoming + outgoing_dependencies)
        Higher values indicate more stable files (more incoming than outgoing deps).

        This enhanced version considers both import and function call dependencies.

        Args:
            file_path: Path to the file

        Returns:
            Stability metric between 0 and 1
        """
        if file_path not in self.nodes:
            return 0.0

        try:
            # Import-based metrics
            import_in_degree = len(self.get_dependents(file_path))
            import_out_degree = len(self.get_dependencies(file_path))

            # Function-call-based metrics
            func_in_degree = len(self._get_file_function_dependents(file_path))
            func_out_degree = len(self._get_file_function_dependencies(file_path))

            # Combined metrics
            total_in_degree = import_in_degree + func_in_degree
            total_out_degree = import_out_degree + func_out_degree
            total_degree = total_in_degree + total_out_degree

            if total_degree == 0:
                return 0.5  # Neutral stability for isolated files

            return total_in_degree / total_degree

        except Exception as e:
            logger.debug(f"Error calculating stability for {file_path}: {e}")
            return 0.0

    def get_function_coupling_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Calculate coupling metrics for each file based on function calls.

        Returns:
            Dictionary mapping file paths to coupling metrics
        """
        if not self.call_graph:
            return {}

        try:
            coupling_metrics = {}

            for file_path, node in self.nodes.items():
                file_functions = node.functions

                # Afferent coupling (functions that depend on this file)
                afferent_coupling = set()
                for func_name in file_functions:
                    if func_name in self.function_dependents:
                        afferent_coupling.update(self.function_dependents[func_name])

                # Efferent coupling (functions this file depends on)
                efferent_coupling = set()
                for func_name in file_functions:
                    if func_name in self.function_dependencies:
                        efferent_coupling.update(self.function_dependencies[func_name])

                coupling_metrics[file_path] = {
                    "afferent_coupling": len(afferent_coupling),
                    "efferent_coupling": len(efferent_coupling),
                    "total_coupling": len(afferent_coupling) + len(efferent_coupling),
                    "instability": len(efferent_coupling)
                    / max(len(afferent_coupling) + len(efferent_coupling), 1),
                }

            return coupling_metrics

        except Exception as e:
            logger.error(f"Error calculating function coupling metrics: {e}")
            return {}

    def identify_hotspots(self) -> List[str]:
        """Identify files that are dependency hotspots.

        Hotspots are files that have many incoming dependencies and are
        critical to the system's functioning.

        Returns:
            List of file paths that are hotspots
        """
        try:
            hotspots = []

            for file_path, node in self.nodes.items():
                # Calculate hotspot score based on multiple factors
                import_dependents = len(self.get_dependents(file_path))
                func_dependents = len(self._get_file_function_dependents(file_path))
                total_dependents = import_dependents + func_dependents

                # Consider a file a hotspot if it has many dependents
                if total_dependents >= 5:  # Threshold can be configurable
                    hotspots.append(file_path)

            # Sort by total dependents
            hotspots.sort(
                key=lambda x: len(self.get_dependents(x))
                + len(self._get_file_function_dependents(x)),
                reverse=True,
            )

            logger.info(f"Identified {len(hotspots)} dependency hotspots")
            return hotspots

        except Exception as e:
            logger.error(f"Error identifying hotspots: {e}")
            return []

    def suggest_refactoring_opportunities(self) -> List[Dict[str, Any]]:
        """Suggest files that might benefit from refactoring.

        Returns:
            List of refactoring opportunity dictionaries
        """
        try:
            opportunities = []

            for file_path, node in self.nodes.items():
                # Calculate various metrics
                import_dependents = len(self.get_dependents(file_path))
                import_dependencies = len(self.get_dependencies(file_path))
                func_dependents = len(self._get_file_function_dependents(file_path))
                func_dependencies = len(self._get_file_function_dependencies(file_path))

                total_incoming = import_dependents + func_dependents
                total_outgoing = import_dependencies + func_dependencies

                # Identify potential issues
                issues = []
                priority = "LOW"

                # High coupling
                if total_incoming + total_outgoing > 10:
                    issues.append("High coupling - many dependencies")
                    priority = "MEDIUM"

                # Many incoming dependencies (potential bottleneck)
                if total_incoming > 8:
                    issues.append("Many incoming dependencies - potential bottleneck")
                    priority = "HIGH"

                # Many outgoing dependencies (unstable)
                if total_outgoing > 6:
                    issues.append("Many outgoing dependencies - unstable")
                    priority = "MEDIUM"

                # Circular dependencies
                if file_path in [cycle[0] for cycle in self.find_cycles()]:
                    issues.append("Part of circular dependency")
                    priority = "HIGH"

                if issues:
                    opportunities.append(
                        {
                            "file_path": file_path,
                            "issues": issues,
                            "priority": priority,
                            "metrics": {
                                "import_dependents": import_dependents,
                                "import_dependencies": import_dependencies,
                                "func_dependents": func_dependents,
                                "func_dependencies": func_dependencies,
                                "total_incoming": total_incoming,
                                "total_outgoing": total_outgoing,
                            },
                        }
                    )

            # Sort by priority
            priority_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
            opportunities.sort(
                key=lambda x: priority_order.get(str(x["priority"]), 0), reverse=True
            )

            logger.info(f"Identified {len(opportunities)} refactoring opportunities")
            return opportunities

        except Exception as e:
            logger.error(f"Error suggesting refactoring opportunities: {e}")
            return []

    def get_enhanced_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics including call graph information.

        Returns:
            Dictionary with enhanced graph statistics
        """
        try:
            # Get base statistics
            base_stats = super().get_graph_statistics()

            # Add call graph statistics
            if self.call_graph:
                call_stats = self.call_graph_builder.get_call_statistics(
                    self.call_graph
                )
                base_stats.update(
                    {
                        "call_graph": call_stats,
                        "function_dependencies": len(self.function_dependencies),
                        "function_dependents": len(self.function_dependents),
                        "files_with_functions": len(
                            [n for n in self.nodes.values() if n.functions]
                        ),
                    }
                )

            # Add advanced metrics
            base_stats.update(
                {
                    "hotspots": len(self.identify_hotspots()),
                    "refactoring_opportunities": len(
                        self.suggest_refactoring_opportunities()
                    ),
                    "function_coupling_metrics": self.get_function_coupling_metrics(),
                }
            )

            return base_stats

        except Exception as e:
            logger.error(f"Error calculating enhanced graph statistics: {e}")
            return {}

    def build_call_graph(self, project_files: List[str]) -> None:
        """Build the call graph for the project.

        Args:
            project_files: List of file paths to analyze
        """
        logger.info("Building call graph for project")

        try:
            call_graph = self.call_graph_builder.build_call_graph(project_files)
            self.integrate_call_graph(call_graph)

        except Exception as e:
            logger.error(f"Error building call graph: {e}")

    def clear(self) -> None:
        """Clear the advanced dependency graph."""
        super().clear()
        self.call_graph = None
        self.function_dependencies.clear()
        self.function_dependents.clear()
        self.centrality_scores.clear()
        logger.info("Advanced dependency graph cleared")
