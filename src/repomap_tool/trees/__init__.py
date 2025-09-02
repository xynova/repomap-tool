"""
Tree-based exploration functionality for repomap-tool.

This package provides intelligent code exploration using tree-based navigation
and session management for focused code analysis.
"""

from .session_manager import SessionManager, ExplorationSession
from .discovery_engine import EntrypointDiscoverer
from .tree_builder import TreeBuilder
from .tree_clusters import TreeClusterer
from .tree_manager import TreeManager
from .tree_mapper import TreeMapper

__all__ = [
    "SessionManager",
    "ExplorationSession", 
    "EntrypointDiscoverer",
    "TreeBuilder",
    "TreeClusterer",
    "TreeManager",
    "TreeMapper"
]
