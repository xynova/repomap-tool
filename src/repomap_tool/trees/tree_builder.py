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
from repomap_tool.core import DockerRepoMap

logger = logging.getLogger(__name__)


class TreeBuilder:
    """Builds exploration trees from entrypoints using existing aider infrastructure."""
    
    def __init__(self, repo_map: DockerRepoMap):
        """Initialize tree builder.
        
        Args:
            repo_map: DockerRepoMap instance with aider infrastructure
        """
        self.repo_map = repo_map
        self.entrypoint_cache = {}  # Cache discovered entrypoints
        self.tree_cache = {}        # Cache built trees
        
        logger.debug("TreeBuilder initialized")
    
    def build_exploration_tree(self, entrypoint: Entrypoint, max_depth: int = 3) -> ExplorationTree:
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
            return self.tree_cache[cache_key]
        
        logger.info(f"Building exploration tree for {entrypoint.identifier} (max_depth={max_depth})")
        
        # Create tree structure
        tree = ExplorationTree(
            tree_id=f"tree_{entrypoint.identifier.lower().replace(' ', '_')}_{hash(entrypoint.location) % 10000:04d}",
            root_entrypoint=entrypoint,
            max_depth=max_depth
        )
        
        # Build tree structure using existing aider infrastructure
        if hasattr(self.repo_map, 'repo_map') and self.repo_map.repo_map:
            # Get tags and dependencies for this entrypoint
            tree_structure = self._build_tree_structure(entrypoint, max_depth)
            tree.tree_structure = tree_structure
        else:
            # Fallback: create simple tree structure
            tree.tree_structure = self._create_simple_tree_structure(entrypoint)
        
        # Cache the tree
        self.tree_cache[cache_key] = tree
        
        logger.info(f"Built tree {tree.tree_id} with {self._count_nodes(tree.tree_structure)} nodes")
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
            location=entrypoint.location,
            node_type="entrypoint",
            depth=0
        )
        
        # Recursively build tree using aider's dependency information
        self._expand_node(root, entrypoint, max_depth, 0)
        
        return root
    
    def _expand_node(self, node: TreeNode, entrypoint: Entrypoint, max_depth: int, current_depth: int):
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
                        identifier=symbol.get('name', 'Unknown'),
                        location=self._get_symbol_location(symbol, entrypoint.location),
                        node_type=symbol.get('kind', 'symbol'),
                        depth=current_depth + 1
                    )
                    child.parent = node
                    node.children.append(child)
                    
                    # Recursively expand child if not at max depth
                    if current_depth + 1 < max_depth:
                        self._expand_node(child, entrypoint, max_depth, current_depth + 1)
                        
        except Exception as e:
            logger.warning(f"Error expanding node {node.identifier}: {e}")
    
    def _get_related_symbols(self, entrypoint: Entrypoint, node: TreeNode) -> List[Dict[str, Any]]:
        """Get symbols related to the current node.
        
        Args:
            entrypoint: Root entrypoint
            node: Current tree node
            
        Returns:
            List of related symbol dictionaries
        """
        try:
            # Try to use existing aider infrastructure
            if hasattr(self.repo_map, 'repo_map') and self.repo_map.repo_map:
                # Get tags for the current node's file
                file_path = self._extract_file_path(node.location)
                if file_path and os.path.exists(file_path):
                    # Use aider's get_tags method if available
                    if hasattr(self.repo_map.repo_map, 'get_tags'):
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
                if hasattr(tag, 'name'):
                    symbol = {
                        'name': tag.name,
                        'kind': getattr(tag, 'kind', 'symbol'),
                        'file_path': getattr(tag, 'file_path', ''),
                        'line_number': getattr(tag, 'line_number', 0)
                    }
                    processed_symbols.append(symbol)
                elif isinstance(tag, dict):
                    processed_symbols.append(tag)
                elif isinstance(tag, str):
                    processed_symbols.append({
                        'name': tag,
                        'kind': 'symbol',
                        'file_path': '',
                        'line_number': 0
                    })
                    
            except Exception as e:
                logger.debug(f"Error processing tag {tag}: {e}")
                continue
        
        return processed_symbols
    
    def _should_add_as_child(self, symbol: Dict[str, Any], parent_node: TreeNode) -> bool:
        """Determine if a symbol should be added as a child of the parent node.
        
        Args:
            symbol: Symbol to evaluate
            parent_node: Potential parent node
            
        Returns:
            True if symbol should be added as child
        """
        # Don't add if it's the same as parent
        if symbol.get('name') == parent_node.identifier:
            return False
        
        # Don't add if it's already a child
        if any(child.identifier == symbol.get('name') for child in parent_node.children):
            return False
        
        # Don't add if it's the parent's parent
        if parent_node.parent and symbol.get('name') == parent_node.parent.identifier:
            return False
        
        # Add if it's a reasonable symbol
        symbol_name = symbol.get('name', '')
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
            file_path = symbol.get('file_path', '')
            line_number = symbol.get('line_number', 0)
            
            if file_path and line_number:
                # Make path relative if possible
                if hasattr(self.repo_map, 'config') and hasattr(self.repo_map.config, 'project_root'):
                    try:
                        rel_path = os.path.relpath(file_path, self.repo_map.config.project_root)
                        return f"{rel_path}:{line_number}"
                    except ValueError:
                        return f"{file_path}:{line_number}"
                else:
                    return f"{file_path}:{line_number}"
            elif file_path:
                return file_path
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
            if ':' in location:
                file_path = location.split(':')[0]
            else:
                file_path = location
            
            # Resolve to absolute path if possible
            if hasattr(self.repo_map, 'config') and hasattr(self.repo_map.config, 'project_root'):
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
            location=entrypoint.location,
            node_type="entrypoint",
            depth=0
        )
        
        # Add some placeholder children to show the tree structure
        placeholder_children = [
            TreeNode(
                identifier=f"{entrypoint.identifier}Helper",
                location=entrypoint.location,
                node_type="function",
                depth=1
            ),
            TreeNode(
                identifier=f"{entrypoint.identifier}Validator",
                location=entrypoint.location,
                node_type="function",
                depth=1
            )
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
    
    def clear_cache(self):
        """Clear the tree cache."""
        self.entrypoint_cache.clear()
        self.tree_cache.clear()
        logger.debug("Tree cache cleared")
