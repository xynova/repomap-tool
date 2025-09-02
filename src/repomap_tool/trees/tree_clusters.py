"""
Tree clustering engine for entrypoint organization.

This module groups discovered entrypoints into logical clusters with meaningful titles,
leveraging existing semantic analysis to create human-readable context names.
"""

import logging
from collections import Counter
from typing import List, Dict, Optional
from uuid import uuid4

from repomap_tool.models import Entrypoint, TreeCluster
from repomap_tool.matchers.semantic_matcher import DomainSemanticMatcher

logger = logging.getLogger(__name__)


class TreeClusterer:
    """Groups entrypoints into logical clusters with meaningful titles."""
    
    def __init__(self, semantic_matcher: Optional[DomainSemanticMatcher] = None):
        """Initialize tree clusterer.
        
        Args:
            semantic_matcher: Semantic matcher for category extraction
        """
        self.semantic_matcher = semantic_matcher
        self.context_patterns = self._load_context_patterns()
        
        logger.debug("TreeClusterer initialized")
    
    def cluster_entrypoints(self, entrypoints: List[Entrypoint]) -> List[TreeCluster]:
        """Group entrypoints into logical clusters.
        
        Args:
            entrypoints: List of discovered entrypoints
            
        Returns:
            List of tree clusters with meaningful titles
        """
        if not entrypoints:
            logger.warning("No entrypoints to cluster")
            return []
        
        logger.info(f"Clustering {len(entrypoints)} entrypoints into logical groups")
        
        # Group entrypoints by primary semantic category
        clusters = self._group_by_primary_category(entrypoints)
        
        # Create tree clusters with meaningful titles
        tree_clusters = []
        for context, cluster_entrypoints in clusters.items():
            cluster = TreeCluster(
                context_name=self._generate_context_name(cluster_entrypoints),
                entrypoints=cluster_entrypoints,
                confidence=self._calculate_cluster_confidence(cluster_entrypoints),
                tree_id=self._generate_tree_id(context, cluster_entrypoints)
            )
            tree_clusters.append(cluster)
        
        # Sort by confidence
        tree_clusters.sort(key=lambda x: x.confidence, reverse=True)
        
        logger.info(f"Created {len(tree_clusters)} clusters")
        return tree_clusters
    
    def _group_by_primary_category(self, entrypoints: List[Entrypoint]) -> Dict[str, List[Entrypoint]]:
        """Group entrypoints by their primary semantic category.
        
        Args:
            entrypoints: List of entrypoints to group
            
        Returns:
            Dictionary mapping categories to entrypoint lists
        """
        clusters = {}
        
        for entrypoint in entrypoints:
            # Get primary category from entrypoint
            primary_category = self._get_primary_category(entrypoint)
            
            if primary_category not in clusters:
                clusters[primary_category] = []
            
            clusters[primary_category].append(entrypoint)
        
        return clusters
    
    def _get_primary_category(self, entrypoint: Entrypoint) -> str:
        """Get the primary semantic category for an entrypoint.
        
        Args:
            entrypoint: Entrypoint to categorize
            
        Returns:
            Primary category name
        """
        # Use existing categories if available
        if entrypoint.categories:
            return entrypoint.categories[0]
        
        # Fallback to path-based classification
        return self._classify_from_path(entrypoint.location)
    
    def _classify_from_path(self, file_path: str) -> str:
        """Classify entrypoint based on file path.
        
        Args:
            file_path: File path to classify
            
        Returns:
            Inferred category
        """
        path_lower = file_path.lower()
        
        # Path-based category mapping
        path_mappings = {
            "auth": "authentication",
            "error": "error_handling", 
            "api": "api_development",
            "db": "database",
            "database": "database",
            "cache": "caching",
            "security": "security",
            "validation": "validation",
            "file": "file_operations",
            "network": "network",
            "performance": "performance",
            "test": "testing",
            "config": "configuration",
            "util": "utilities",
            "helper": "utilities",
            "service": "services",
            "controller": "api_development",
            "model": "database",
            "view": "frontend",
            "component": "frontend"
        }
        
        for keyword, category in path_mappings.items():
            if keyword in path_lower:
                return category
        
        # Default category
        return "general"
    
    def _generate_context_name(self, entrypoints: List[Entrypoint]) -> str:
        """Generate meaningful title from entrypoints using semantic analysis.
        
        Args:
            entrypoints: List of entrypoints in the cluster
            
        Returns:
            Human-readable context name
        """
        if not entrypoints:
            return "Code Components"
        
        # Step 1: Collect semantic categories from all entrypoints
        all_categories = []
        for entrypoint in entrypoints:
            # Use existing categories if available
            if entrypoint.categories:
                all_categories.extend(entrypoint.categories)
            
            # Add path-based context
            path_context = self._extract_path_context(entrypoint.location)
            if path_context:
                all_categories.append(path_context)
        
        # Step 2: Count category frequencies
        category_counts = Counter(all_categories)
        
        # Step 3: Generate title from dominant categories
        return self._format_title_from_categories(category_counts)
    
    def _extract_path_context(self, file_path: str) -> Optional[str]:
        """Extract semantic context from file path.
        
        Args:
            file_path: File path to analyze
            
        Returns:
            Extracted context or None
        """
        path_mappings = {
            "auth": "authentication",
            "error": "error_handling",
            "api": "api_development", 
            "db": "database",
            "database": "database",
            "cache": "caching",
            "security": "security",
            "validation": "validation",
            "file": "file_operations",
            "network": "network",
            "performance": "performance"
        }
        
        path_lower = file_path.lower()
        for keyword, category in path_mappings.items():
            if keyword in path_lower:
                return category
        
        return None
    
    def _format_title_from_categories(self, category_counts: Counter) -> str:
        """Format human-readable title from semantic categories.
        
        Args:
            category_counts: Counter of category frequencies
            
        Returns:
            Formatted title
        """
        if not category_counts:
            return "Code Components"
        
        # Get top 2 most frequent categories
        top_categories = category_counts.most_common(2)
        primary = top_categories[0][0]
        secondary = top_categories[1][0] if len(top_categories) > 1 else None
        
        # Title generation rules based on category combinations
        title_rules = {
            ("authentication", "error_handling"): "Auth Error Handling",
            ("authentication", "validation"): "Auth Validation", 
            ("authentication", "api_development"): "Auth API Flow",
            ("database", "api_development"): "Database API",
            ("database", "performance"): "Database Optimization",
            ("api_development", "error_handling"): "API Error Handling",
            ("security", "validation"): "Security Validation",
            ("network", "api_development"): "Network API",
            ("file_operations", "data_processing"): "File Processing",
            ("caching", "performance"): "Cache Optimization",
            ("frontend", "authentication"): "Frontend Auth",
            ("frontend", "validation"): "Frontend Validation",
            ("services", "authentication"): "Auth Services",
            ("services", "database"): "Database Services",
            ("utilities", "validation"): "Validation Utils"
        }
        
        # Try specific combination first
        if secondary:
            combination_key = (primary, secondary)
            if combination_key in title_rules:
                return title_rules[combination_key]
        
        # Fallback to single category formatting
        single_category_rules = {
            "authentication": "Authentication Flow",
            "error_handling": "Error Handling",
            "database": "Database Components", 
            "api_development": "API Endpoints",
            "security": "Security Components",
            "validation": "Validation Logic",
            "file_operations": "File Operations",
            "network": "Network Components",
            "caching": "Caching Layer",
            "performance": "Performance Components",
            "frontend": "Frontend Components",
            "services": "Service Layer",
            "utilities": "Utility Functions",
            "testing": "Test Components",
            "configuration": "Configuration"
        }
        
        if primary in single_category_rules:
            return single_category_rules[primary]
        
        # Final fallback - make it readable
        return f"{primary.replace('_', ' ').title()} Components"
    
    def _calculate_cluster_confidence(self, entrypoints: List[Entrypoint]) -> float:
        """Calculate confidence score for a cluster.
        
        Args:
            entrypoints: List of entrypoints in the cluster
            
        Returns:
            Confidence score (0.0-1.0)
        """
        if not entrypoints:
            return 0.0
        
        # Calculate average score of entrypoints
        total_score = sum(ep.score for ep in entrypoints)
        avg_score = total_score / len(entrypoints)
        
        # Boost confidence for larger clusters (more evidence)
        size_boost = min(len(entrypoints) * 0.1, 0.3)
        
        # Boost confidence for consistent categories
        category_consistency = self._calculate_category_consistency(entrypoints)
        
        confidence = min(avg_score + size_boost + category_consistency, 1.0)
        return round(confidence, 2)
    
    def _calculate_category_consistency(self, entrypoints: List[Entrypoint]) -> float:
        """Calculate how consistent the categories are within a cluster.
        
        Args:
            entrypoints: List of entrypoints in the cluster
            
        Returns:
            Consistency score (0.0-0.2)
        """
        if len(entrypoints) <= 1:
            return 0.0
        
        # Count categories across all entrypoints
        all_categories = []
        for entrypoint in entrypoints:
            if entrypoint.categories:
                all_categories.extend(entrypoint.categories)
        
        if not all_categories:
            return 0.0
        
        # Calculate category diversity
        unique_categories = len(set(all_categories))
        total_categories = len(all_categories)
        
        # Lower diversity = higher consistency
        diversity_ratio = unique_categories / total_categories
        consistency = (1.0 - diversity_ratio) * 0.2
        
        return round(consistency, 2)
    
    def _generate_tree_id(self, context: str, entrypoints: List[Entrypoint]) -> str:
        """Generate unique tree ID for the cluster.
        
        Args:
            context: Primary category context
            entrypoints: List of entrypoints in the cluster
            
        Returns:
            Unique tree identifier
        """
        # Create readable prefix from context
        context_prefix = context.replace('_', '').lower()
        
        # Add unique suffix
        unique_suffix = str(uuid4().hex[:8])
        
        return f"{context_prefix}_{unique_suffix}"
    
    def _load_context_patterns(self) -> Dict:
        """Load context pattern rules for title generation.
        
        Returns:
            Dictionary of context patterns
        """
        # This could be loaded from a configuration file in the future
        return {
            "authentication": ["auth", "login", "user", "password", "session"],
            "error_handling": ["error", "exception", "fail", "invalid", "warning"],
            "database": ["db", "database", "query", "model", "schema"],
            "api_development": ["api", "endpoint", "route", "controller", "service"],
            "validation": ["validate", "check", "verify", "test", "assert"],
            "security": ["security", "encrypt", "hash", "token", "permission"],
            "performance": ["performance", "optimize", "speed", "cache", "async"]
        }
