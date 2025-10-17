"""
Exploration Controller for RepoMap-Tool CLI.

This module contains the ExplorationController that orchestrates
tree discovery and exploration operations.
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from repomap_tool.core.logging_service import get_logger
from repomap_tool.core.config_service import get_config

from .base_controller import BaseController
from .view_models import (
    ControllerConfig,
    ExplorationViewModel,
    TreeClusterViewModel,
    TreeFocusViewModel,
    TreeExpansionViewModel,
    TreePruningViewModel,
    TreeMappingViewModel,
    TreeListingViewModel,
    SessionStatusViewModel,
)

if TYPE_CHECKING:
    from repomap_tool.models import SymbolViewModel

logger = get_logger(__name__)


class ExplorationController(BaseController):
    """Controller for exploration operations."""

    def __init__(
        self,
        search_controller: Any,  # SearchController
        session_manager: Any,  # SessionManager
        tree_builder: Any,  # TreeBuilder
        config: Optional[ControllerConfig] = None,
    ) -> None:
        """Initialize the ExplorationController.

        Args:
            search_controller: SearchController for intent-based discovery
            session_manager: SessionManager for session operations
            tree_builder: TreeBuilder for constructing exploration trees
            config: Controller configuration
        """
        super().__init__(config)

        # Validate dependencies
        if search_controller is None:
            raise ValueError("SearchController must be injected - no fallback allowed")
        if session_manager is None:
            raise ValueError("SessionManager must be injected - no fallback allowed")
        if tree_builder is None:
            raise ValueError("TreeBuilder must be injected - no fallback allowed")

        self.search_controller = search_controller
        self.session_manager = session_manager
        self.tree_builder = tree_builder

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the controller's main operation."""
        # This will be implemented by specific methods
        pass

    def start_exploration(
        self,
        intent: str,
        project_path: str,
        max_depth: int = 3,
        max_tokens: int = 4000,
    ) -> ExplorationViewModel:
        """Start new exploration session with intent.

        Args:
            intent: Natural language intent for exploration
            project_path: Path to the project being explored
            max_depth: Maximum depth for exploration trees
            max_tokens: Maximum tokens for output

        Returns:
            ExplorationViewModel with discovered trees
        """
        start_time = time.time()

        try:
            # Create session ID from intent
            session_id = self._create_session_id_from_intent(intent)

            # Use search controller to discover relevant code
            from repomap_tool.models import SearchRequest

            search_request = SearchRequest(
                query=intent,
                max_results=get_config("EXPLORATION_MAX_RESULTS", 50),
            )
            search_results = self.search_controller.execute(search_request)

            # Cluster results into exploration trees
            tree_clusters = self._cluster_search_results(search_results, intent)

            # Build exploration trees
            trees = []
            confidence_scores = {}

            for cluster in tree_clusters:
                # Convert cluster results to SearchViewModel format
                results_list = cluster.get("results", [])
                # Create a SearchViewModel from the results list
                from repomap_tool.cli.controllers.view_models import SearchViewModel

                search_results = SearchViewModel(
                    query=intent,
                    results=results_list,
                    total_results=len(results_list),
                    search_strategy="hybrid",
                    execution_time=0.0,
                    token_count=0,
                    max_tokens=4000,
                )
                cluster_trees = self.tree_builder.build_tree_from_search_results(
                    search_results=search_results,
                    intent=intent,
                    max_depth=max_depth,
                    project_path=project_path,
                )

                # Process each tree in the cluster
                for tree in cluster_trees:
                    # Create tree cluster view model
                    tree_cluster_vm = TreeClusterViewModel(
                        tree_id=tree.tree_id,
                        context_name=cluster.get("file_path", "Unknown"),
                        confidence=cluster.get("relevance_score", 0.5),
                        entrypoints=[],  # TODO: Extract entrypoints from tree
                        total_nodes=1,  # Single node per cluster
                        max_depth=tree.max_depth,
                        root_file=cluster.get("file_path", "Unknown"),
                        description=f"Cluster for {cluster.get('file_path', 'Unknown')}",
                    )

                    trees.append(tree_cluster_vm)
                    confidence_scores[tree.tree_id] = cluster.get(
                        "relevance_score", 0.5
                    )

            # Create exploration session
            self._create_exploration_session(
                session_id=session_id,
                project_path=project_path,
                trees=trees,
            )

            execution_time = time.time() - start_time

            return ExplorationViewModel(
                session_id=session_id,
                project_path=project_path,
                intent=intent,
                trees=trees,
                total_trees=len(trees),
                confidence_scores=confidence_scores,
                token_count=self._estimate_token_count(trees) if trees else 0,
                max_tokens=max_tokens,
                execution_time=execution_time,
                discovery_strategy="hybrid",
            )

        except Exception as e:
            self.logger.error(f"Error starting exploration: {e}")
            raise

    def focus_tree(self, session_id: str, tree_id: str) -> TreeFocusViewModel:
        """Focus on specific exploration tree.

        Args:
            session_id: Session ID
            tree_id: Tree ID to focus on

        Returns:
            TreeFocusViewModel with focused tree information
        """
        try:
            # Get session and tree
            session = self.session_manager.get_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            tree = session.get_tree(tree_id)
            if not tree:
                raise ValueError(f"Tree {tree_id} not found in session {session_id}")

            # Set as current focus
            session.set_current_focus(tree_id)
            self.session_manager.save_session(session)

            return TreeFocusViewModel(
                tree_id=tree_id,
                context_name=tree.context_name,
                current_focus=True,
                tree_structure=self._build_tree_structure(tree),
                expanded_areas=tree.expanded_areas,
                pruned_areas=tree.pruned_areas,
                total_nodes=1 if tree.tree_structure else 0,
                max_depth=tree.max_depth,
            )

        except Exception as e:
            self.logger.error(f"Error focusing tree: {e}")
            raise

    def expand_tree(
        self, session_id: str, tree_id: str, area: str
    ) -> TreeExpansionViewModel:
        """Expand specific area of exploration tree.

        Args:
            session_id: Session ID
            tree_id: Tree ID to expand
            area: Area to expand

        Returns:
            TreeExpansionViewModel with expansion results
        """
        try:
            # Get session and tree
            session = self.session_manager.get_session(session_id)
            tree = session.get_tree(tree_id)

            # Expand the specified area
            new_nodes = self.tree_builder.expand_area(
                tree=tree,
                area=area,
                project_path=session.project_path,
            )

            # Update session
            self.session_manager.save_session(session)

            return TreeExpansionViewModel(
                tree_id=tree_id,
                expanded_area=area,
                new_nodes=new_nodes,
                total_nodes=len(tree.nodes),
                expansion_depth=tree.current_depth,
                confidence_score=tree.confidence,
            )

        except Exception as e:
            self.logger.error(f"Error expanding tree: {e}")
            raise

    def prune_tree(
        self, session_id: str, tree_id: str, area: str, reason: str = "User requested"
    ) -> TreePruningViewModel:
        """Prune specific area of exploration tree.

        Args:
            session_id: Session ID
            tree_id: Tree ID to prune
            area: Area to prune
            reason: Reason for pruning

        Returns:
            TreePruningViewModel with pruning results
        """
        try:
            # Get session and tree
            session = self.session_manager.get_session(session_id)

            # Resolve "current" to actual tree ID
            if tree_id == "current":
                if not session.current_focus:
                    raise ValueError(f"No current focus set in session {session_id}")
                tree_id = session.current_focus

            tree = session.get_tree(tree_id)

            # Prune the specified area
            removed_nodes = self.tree_builder.prune_area(tree, area)

            # Update session
            self.session_manager.save_session(session)

            return TreePruningViewModel(
                tree_id=tree_id,
                pruned_area=area,
                removed_nodes=removed_nodes,
                remaining_nodes=len(tree.nodes),
                pruning_reason=reason,
            )

        except Exception as e:
            self.logger.error(f"Error pruning tree: {e}")
            raise

    def map_tree(
        self,
        session_id: str,
        tree_id: str,
        include_code: bool = False,
        max_tokens: int = 4000,
    ) -> TreeMappingViewModel:
        """Generate map from current tree state.

        Args:
            session_id: Session ID
            tree_id: Tree ID to map
            include_code: Whether to include code snippets
            max_tokens: Maximum tokens for output

        Returns:
            TreeMappingViewModel with tree map
        """
        try:
            # Get session and tree
            session = self.session_manager.get_session(session_id)

            # Resolve "current" to actual tree ID
            if tree_id == "current":
                if not session.current_focus:
                    raise ValueError(f"No current focus set in session {session_id}")
                tree_id = session.current_focus

            tree = session.get_tree(tree_id)

            # Build tree structure
            tree_structure = self._build_tree_structure(tree)

            # Extract code snippets if requested
            code_snippets = []
            if include_code:
                code_snippets = self._extract_code_snippets(tree, max_tokens)

            return TreeMappingViewModel(
                tree_id=tree_id,
                tree_structure=tree_structure,
                total_nodes=len(tree.nodes),
                max_depth=tree.max_depth,
                include_code=include_code,
                code_snippets=code_snippets,
                token_count=self._estimate_token_count([tree]) if tree else 0,
                max_tokens=max_tokens,
            )

        except Exception as e:
            self.logger.error(f"Error mapping tree: {e}")
            raise

    def list_trees(self, session_id: str) -> TreeListingViewModel:
        """List all exploration trees in the session.

        Args:
            session_id: Session ID

        Returns:
            TreeListingViewModel with tree list
        """
        try:
            # Get session
            session = self.session_manager.get_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            # Convert trees to view models
            trees = []
            for tree in session.exploration_trees.values():
                tree_cluster_vm = TreeClusterViewModel(
                    tree_id=tree.tree_id,
                    context_name=tree.context_name,
                    confidence=tree.confidence,
                    entrypoints=self._extract_entrypoints(tree),
                    total_nodes=len(tree.nodes),
                    max_depth=tree.max_depth,
                    root_file=tree.root_entrypoint.file_path,
                    description=tree.description,
                )
                trees.append(tree_cluster_vm)

            return TreeListingViewModel(
                session_id=session_id,
                trees=trees,
                total_trees=len(trees),
                current_focus=session.current_focus,
            )

        except Exception as e:
            self.logger.error(f"Error listing trees: {e}")
            raise

    def get_session_status(self, session_id: str) -> SessionStatusViewModel:
        """Get current exploration session status.

        Args:
            session_id: Session ID

        Returns:
            SessionStatusViewModel with session status
        """
        try:
            # Get session
            session = self.session_manager.get_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            return SessionStatusViewModel(
                session_id=session_id,
                project_path=session.project_path,
                total_trees=len(session.exploration_trees),
                current_focus=session.current_focus,
                created_at=session.created_at.isoformat(),
                last_activity=session.last_activity.isoformat(),
                session_stats=self._build_session_stats(session),
            )

        except Exception as e:
            self.logger.error(f"Error getting session status: {e}")
            raise

    def _create_session_id_from_intent(self, intent: str) -> str:
        """Create session ID from intent."""
        import re

        # Get date component (MMDD format)
        date_str = datetime.now().strftime("%m%d")

        # Normalize query: lowercase, replace spaces with underscores, remove special chars
        normalized = re.sub(r"[^\w\s]", "", intent.lower().strip())
        normalized = re.sub(r"\s+", "_", normalized)

        # Truncate if too long (keep it readable)
        if len(normalized) > 20:
            normalized = normalized[:20]

        return f"{date_str}_{normalized}"

    def _cluster_search_results(self, search_results: Any, intent: str) -> List[Any]:
        """Cluster search results into exploration trees."""
        try:
            from repomap_tool.core.config_service import get_config
            from repomap_tool.core.logging_service import get_logger

            logger = get_logger(__name__)
            max_clusters = get_config("EXPLORATION_MAX_CLUSTERS", 5)

            if (
                not search_results
                or not hasattr(search_results, "results")
                or len(search_results.results) == 0
            ):
                return []

            # Get the actual results list from SearchViewModel
            results_list = search_results.results

            # Group results by file path for clustering
            file_groups: Dict[str, List[Any]] = {}
            for result in results_list:
                file_path = getattr(result, "file_path", None)
                if file_path:
                    if file_path not in file_groups:
                        file_groups[file_path] = []
                    file_groups[file_path].append(result)

            # Create clusters based on file groups and intent
            clusters = []
            for file_path, results in list(file_groups.items())[:max_clusters]:
                # Create a cluster for this file group
                cluster = {
                    "file_path": file_path,
                    "results": results,
                    "intent": intent,
                    "cluster_type": "file_based",
                    "relevance_score": (
                        len(results) / len(results_list) if results_list else 0
                    ),
                }
                clusters.append(cluster)

            logger.debug(
                f"Created {len(clusters)} clusters from {len(results_list)} search results"
            )
            return clusters

        except Exception as e:
            self.logger.error(f"Error clustering search results: {e}")
            return []

    def _extract_entrypoints(self, tree: Any) -> List[Dict[str, Any]]:
        """Extract entrypoints from tree using tree-sitter RepoMap."""
        try:
            from repomap_tool.core.config_service import get_config
            from repomap_tool.core.logging_service import get_logger

            logger = get_logger(__name__)
            max_entrypoints = get_config("EXPLORATION_MAX_ENTRYPOINTS", 10)

            if not tree or not hasattr(tree, "nodes"):
                return []

            entrypoints = []

            # Extract entrypoints from tree nodes
            for node in tree.nodes[:max_entrypoints]:
                if hasattr(node, "identifier") and hasattr(node, "location"):
                    entrypoint = {
                        "identifier": node.identifier,
                        "location": node.location,
                        "type": getattr(node, "node_type", "unknown"),
                        "depth": getattr(node, "depth", 0),
                        "relevance_score": getattr(node, "relevance_score", 0.5),
                    }
                    entrypoints.append(entrypoint)

            # Sort by relevance score (highest first)
            entrypoints.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

            logger.debug(f"Extracted {len(entrypoints)} entrypoints from tree")
            return entrypoints

        except Exception as e:
            self.logger.error(f"Error extracting entrypoints: {e}")
            return []

    def _create_exploration_session(
        self, session_id: str, project_path: str, trees: List[TreeClusterViewModel]
    ) -> None:
        """Create exploration session with trees."""
        try:
            from repomap_tool.core.logging_service import get_logger
            from repomap_tool.models import ExplorationSession, ExplorationTree

            logger = get_logger(__name__)

            # Create new exploration session
            session = ExplorationSession(
                session_id=session_id,
                project_path=project_path,
                exploration_trees={},
                current_focus=None,
                # created_at and last_activity will be set by model default_factory
            )

            # Add trees to session
            for i, tree_cluster in enumerate(trees):
                tree_id = f"tree_{i+1}"

                # Create exploration tree from cluster
                # Create a mock entrypoint for the tree
                from repomap_tool.models import Entrypoint

                mock_entrypoint = Entrypoint(
                    identifier=f"root_{tree_id}",
                    file_path=Path("/mock/path"),
                    score=0.5,
                )

                exploration_tree = ExplorationTree(
                    tree_id=tree_id,
                    root_entrypoint=mock_entrypoint,
                    context_name=getattr(tree_cluster, "context_name", f"Tree {i+1}"),
                    expanded_areas=set(),
                    pruned_areas=set(),
                    max_depth=getattr(tree_cluster, "max_depth", 3),
                )

                session.add_tree(exploration_tree)

            # Set first tree as current focus if available
            if trees:
                session.set_current_focus("tree_1")

            # Save session
            self.session_manager.persist_session(session)

            logger.info(
                f"Created exploration session {session_id} with {len(trees)} trees"
            )

        except Exception as e:
            self.logger.error(f"Error creating exploration session: {e}")
            raise

    def _estimate_token_count(self, trees: List[Any]) -> int:
        """Estimate token count for trees."""
        try:
            from repomap_tool.core.config_service import get_config
            from repomap_tool.core.logging_service import get_logger

            logger = get_logger(__name__)
            base_tokens_per_node = get_config("EXPLORATION_TOKENS_PER_NODE", 50)

            if not trees or trees is None:
                return 0

            total_tokens = 0

            for tree in trees:
                if hasattr(tree, "nodes"):
                    # Estimate tokens based on number of nodes
                    node_count = len(tree.nodes)
                    tree_tokens = node_count * base_tokens_per_node

                    # Add overhead for tree structure
                    tree_overhead = get_config("EXPLORATION_TREE_OVERHEAD", 100)
                    total_tokens += tree_tokens + tree_overhead
                else:
                    # Fallback estimation
                    total_tokens += get_config("EXPLORATION_FALLBACK_TOKENS", 200)

            logger.debug(f"Estimated {total_tokens} tokens for {len(trees)} trees")
            return total_tokens

        except Exception as e:
            self.logger.error(f"Error estimating token count: {e}")
            return 1000  # Fallback value

    def _build_tree_structure(self, tree: Any) -> Dict[str, Any]:
        """Build tree structure representation."""
        try:
            from repomap_tool.core.logging_service import get_logger

            logger = get_logger(__name__)

            if not tree:
                return {}

            structure: Dict[str, Any] = {
                "tree_id": getattr(tree, "tree_id", "unknown"),
                "context_name": getattr(tree, "context_name", "Unknown Tree"),
                "max_depth": getattr(tree, "max_depth", 0),
                "current_depth": getattr(tree, "current_depth", 0),
                "expanded_areas": list(getattr(tree, "expanded_areas", set())),
                "pruned_areas": list(getattr(tree, "pruned_areas", set())),
                "node_count": 0,
                "nodes": [],
            }

            # Process tree nodes
            if hasattr(tree, "nodes") and tree.nodes:
                structure["node_count"] = len(tree.nodes)

                for node in tree.nodes:
                    node_data = {
                        "identifier": getattr(node, "identifier", "unknown"),
                        "location": getattr(node, "location", "unknown"),
                        "type": getattr(node, "node_type", "unknown"),
                        "depth": getattr(node, "depth", 0),
                        "expanded": getattr(node, "expanded", False),
                        "children_count": len(getattr(node, "children", [])),
                    }
                    structure["nodes"].append(node_data)

            logger.debug(
                f"Built tree structure for {structure['tree_id']} with {structure['node_count']} nodes"
            )
            return structure

        except Exception as e:
            self.logger.error(f"Error building tree structure: {e}")
            return {}

    def _extract_code_snippets(
        self, tree: Any, max_tokens: int
    ) -> List[Dict[str, Any]]:
        """Extract code snippets from tree with token limits."""
        try:
            from repomap_tool.core.config_service import get_config
            from repomap_tool.core.logging_service import get_logger

            logger = get_logger(__name__)
            snippet_token_limit = get_config("EXPLORATION_SNIPPET_TOKEN_LIMIT", 200)

            if not tree or not hasattr(tree, "nodes"):
                return []

            snippets = []
            current_tokens: float = 0.0

            # Extract snippets from tree nodes
            for node in tree.nodes:
                if current_tokens >= max_tokens:
                    break

                # Create snippet from node
                snippet = {
                    "identifier": getattr(node, "identifier", "unknown"),
                    "location": getattr(node, "location", "unknown"),
                    "type": getattr(node, "node_type", "unknown"),
                    "depth": getattr(node, "depth", 0),
                    "content": getattr(node, "content", ""),
                    "tokens_used": snippet_token_limit,
                }

                # Estimate tokens for this snippet
                snippet_tokens = (
                    len(snippet["content"].split()) * 1.3
                )  # Rough estimation
                snippet["tokens_used"] = int(snippet_tokens)

                if current_tokens + snippet_tokens <= max_tokens:
                    snippets.append(snippet)
                    current_tokens += snippet_tokens
                else:
                    # Truncate content to fit remaining tokens
                    remaining_tokens = max_tokens - current_tokens
                    if remaining_tokens > 50:  # Only add if meaningful
                        snippet["content"] = snippet["content"][
                            : int(remaining_tokens * 4)
                        ]  # Rough char to token ratio
                        snippet["tokens_used"] = remaining_tokens
                        snippets.append(snippet)
                    break

            logger.debug(
                f"Extracted {len(snippets)} code snippets using {current_tokens} tokens"
            )
            return snippets

        except Exception as e:
            self.logger.error(f"Error extracting code snippets: {e}")
            return []

    def _build_session_stats(self, session: Any) -> Dict[str, Any]:
        """Build session statistics."""
        try:
            from repomap_tool.core.logging_service import get_logger

            logger = get_logger(__name__)

            if not session:
                return {}

            stats: Dict[str, Any] = {
                "session_id": getattr(session, "session_id", "unknown"),
                "project_path": getattr(session, "project_path", "unknown"),
                "tree_count": 0,
                "total_nodes": 0,
                "expanded_areas": 0,
                "pruned_areas": 0,
                "current_focus": getattr(session, "current_focus", None),
                "created_at": getattr(session, "created_at", None),
                "last_activity": getattr(session, "last_activity", None),
                "session_duration": 0,
            }

            # Calculate tree statistics
            if hasattr(session, "exploration_trees"):
                stats["tree_count"] = len(session.exploration_trees)

                for tree in session.exploration_trees.values():
                    if hasattr(tree, "nodes"):
                        stats["total_nodes"] += len(tree.nodes)
                    if hasattr(tree, "expanded_areas"):
                        stats["expanded_areas"] += len(tree.expanded_areas)
                    if hasattr(tree, "pruned_areas"):
                        stats["pruned_areas"] += len(tree.pruned_areas)

            # Calculate session duration
            if stats["created_at"] and stats["last_activity"]:
                if isinstance(stats["created_at"], str):
                    created_at: datetime = datetime.fromisoformat(
                        stats["created_at"].replace("Z", "+00:00")
                    )
                else:
                    created_at = stats["created_at"]

                if isinstance(stats["last_activity"], str):
                    last_activity: datetime = datetime.fromisoformat(
                        stats["last_activity"].replace("Z", "+00:00")
                    )
                else:
                    last_activity = stats["last_activity"]

                duration = last_activity - created_at
                stats["session_duration"] = int(duration.total_seconds())

            logger.debug(
                f"Built session stats for {stats['session_id']}: {stats['tree_count']} trees, {stats['total_nodes']} nodes"
            )
            return stats

        except Exception as e:
            self.logger.error(f"Error building session stats: {e}")
            return {}
