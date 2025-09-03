"""
Entrypoint discovery engine for tree exploration.

This module discovers relevant code entry points using existing semantic and fuzzy matching
capabilities, providing the foundation for building exploration trees.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from repomap_tool.models import Entrypoint
from repomap_tool.core import DockerRepoMap
from repomap_tool.matchers.semantic_matcher import DomainSemanticMatcher
from repomap_tool.matchers.fuzzy_matcher import FuzzyMatcher

# Phase 2: Dependency analysis integration
from repomap_tool.dependencies import (
    ImportAnalyzer, 
    DependencyGraph, 
    CentralityCalculator,
    ImpactAnalyzer
)

logger = logging.getLogger(__name__)


class EntrypointDiscoverer:
    """Discovers relevant entrypoints using existing semantic/fuzzy matching."""
    
    def __init__(self, repo_map: DockerRepoMap):
        """Initialize entrypoint discoverer.
        
        Args:
            repo_map: DockerRepoMap instance with semantic/fuzzy matchers
        """
        self.repo_map = repo_map
        self.semantic_matcher = getattr(repo_map, 'semantic_matcher', None) or getattr(repo_map, 'domain_semantic_matcher', None)
        self.fuzzy_matcher = getattr(repo_map, 'fuzzy_matcher', None)
        
        # Use semantic matcher threshold from config if available
        if hasattr(repo_map, 'config') and hasattr(repo_map.config, 'trees'):
            self.semantic_threshold = repo_map.config.trees.entrypoint_threshold
        else:
            self.semantic_threshold = 0.6
            
        # Fuzzy matching threshold (70% similarity)
        self.fuzzy_threshold = 0.7
        
        # Phase 2: Initialize dependency analysis components
        self.import_analyzer = ImportAnalyzer()
        self.dependency_graph = DependencyGraph()
        self.centrality_calculator = None  # Will be initialized when needed
        self.impact_analyzer = None  # Will be initialized when needed
        
        logger.debug(f"EntrypointDiscoverer initialized with semantic_threshold={self.semantic_threshold}, fuzzy_threshold={self.fuzzy_threshold}")
    
    def discover_entrypoints(self, project_path: str, intent: str) -> List[Entrypoint]:
        """Find relevant entrypoints using existing semantic/fuzzy matching.
        
        Args:
            project_path: Path to the project to analyze
            intent: User intent description (e.g., "authentication bugs")
            
        Returns:
            List of relevant entrypoints with scores
        """
        logger.info(f"Discovering entrypoints for intent: '{intent}' in {project_path}")
        
        # Get all project symbols using existing infrastructure
        all_symbols = self._get_project_symbols(project_path)
        if not all_symbols:
            logger.warning(f"No symbols found in project {project_path}")
            return []
        
        relevant_entrypoints = []
        
        # Use existing semantic matching to find relevant symbols
        if self.semantic_matcher and self.semantic_matcher.enabled:
            semantic_entrypoints = self._discover_semantic_entrypoints(intent, all_symbols, project_path)
            relevant_entrypoints.extend(semantic_entrypoints)
            logger.debug(f"Found {len(semantic_entrypoints)} entrypoints via semantic matching")
        
        # Use existing fuzzy matching for additional matches
        if self.fuzzy_matcher and self.fuzzy_matcher.enabled:
            fuzzy_entrypoints = self._discover_fuzzy_entrypoints(intent, all_symbols, project_path)
            relevant_entrypoints.extend(fuzzy_entrypoints)
            logger.debug(f"Found {len(fuzzy_entrypoints)} entrypoints via fuzzy matching")
        
        # Remove duplicates and sort by score
        unique_entrypoints = self._deduplicate_entrypoints(relevant_entrypoints)
        unique_entrypoints.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"Discovered {len(unique_entrypoints)} unique entrypoints")
        
        # Phase 2: Enhance entrypoints with dependency analysis
        if unique_entrypoints:
            self._enhance_entrypoints_with_dependencies(unique_entrypoints, project_path)
        
        return unique_entrypoints
    
    def _get_project_symbols(self, project_path: str) -> List[str]:
        """Get all project symbols using existing infrastructure.
        
        Args:
            project_path: Project path to analyze
            
        Returns:
            List of symbol dictionaries
        """
        try:
            # Use existing repo_map to get symbols
            if hasattr(self.repo_map, 'get_tags'):
                symbols = self.repo_map.get_tags()
                logger.debug(f"Retrieved {len(symbols)} symbols from repo_map")
                return symbols
            
            # Fallback: try to get symbols from search engine
            elif hasattr(self.repo_map, 'search_engine'):
                # This would need to be implemented based on existing search engine
                logger.debug("Using search engine fallback for symbol discovery")
                return []
            
            else:
                logger.warning("No symbol discovery method available in repo_map")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get project symbols: {e}")
            return []
    
    def _discover_semantic_entrypoints(self, intent: str, symbols: List[str], project_path: str) -> List[Entrypoint]:
        """Discover entrypoints using semantic matching.
        
        Args:
            intent: User intent description
            symbols: List of project symbols
            project_path: Project path
            
        Returns:
            List of semantically relevant entrypoints
        """
        entrypoints = []
        
        try:
            for symbol_id in symbols:
                if not symbol_id:
                    continue
                
                # Calculate semantic similarity
                similarity = self.semantic_matcher.semantic_similarity(intent, symbol_id)
                
                if similarity >= self.semantic_threshold:
                    # Get semantic categories for this symbol
                    categories = self._get_semantic_categories(symbol_id)
                    
                    # Create entrypoint
                    entrypoint = Entrypoint(
                        identifier=symbol_id,
                        location=self._get_symbol_location_from_string(symbol_id, project_path),
                        score=similarity,
                        categories=categories,
                        structural_context=self._get_structural_context_from_string(symbol_id)
                    )
                    entrypoints.append(entrypoint)
                    
        except Exception as e:
            logger.error(f"Error in semantic entrypoint discovery: {e}")
        
        return entrypoints
    
    def _discover_fuzzy_entrypoints(self, intent: str, symbols: List[str], project_path: str) -> List[Entrypoint]:
        """Discover entrypoints using fuzzy matching.
        
        Args:
            intent: User intent description
            symbols: List of project symbols (strings)
            project_path: Project path
            
        Returns:
            List of fuzzy-matched entrypoints
        """
        entrypoints = []
        
        try:
            # Use existing fuzzy matcher to find similar symbols
            if not symbols:
                return []
            
            # Find fuzzy matches
            fuzzy_matches = self.fuzzy_matcher.match_identifiers(intent, set(symbols))
            
            for identifier, score in fuzzy_matches:
                if score >= self.fuzzy_threshold:
                    # Create entrypoint
                    entrypoint = Entrypoint(
                        identifier=identifier,
                        location=self._get_symbol_location_from_string(identifier, project_path),
                        score=score / 100.0,  # Convert percentage to 0-1 scale
                        categories=[],  # Fuzzy matching doesn't provide categories
                        structural_context=self._get_structural_context_from_string(identifier)
                    )
                    entrypoints.append(entrypoint)
                        
        except Exception as e:
            logger.error(f"Error in fuzzy entrypoint discovery: {e}")
        
        return entrypoints
    
    def _extract_symbol_identifier(self, symbol: Dict[str, Any]) -> Optional[str]:
        """Extract identifier from symbol data.
        
        Args:
            symbol: Symbol dictionary from repo_map
            
        Returns:
            Symbol identifier or None
        """
        # Try different possible keys for symbol identifier
        for key in ['name', 'identifier', 'symbol', 'function', 'class']:
            if key in symbol and symbol[key]:
                return str(symbol[key])
        
        # If symbol is a string, use it directly
        if isinstance(symbol, str):
            return symbol
        
        logger.debug(f"Could not extract identifier from symbol: {symbol}")
        return None
    
    def _get_symbol_location(self, symbol: Dict[str, Any], project_path: str) -> str:
        """Get file location for symbol.
        
        Args:
            symbol: Symbol dictionary
            project_path: Project path
            
        Returns:
            File path and line number (file:line)
        """
        try:
            # Try to get file path and line number
            file_path = symbol.get('file_path', '')
            line_number = symbol.get('line_number', '')
            
            if file_path and line_number:
                # Make path relative to project
                rel_path = os.path.relpath(file_path, project_path)
                return f"{rel_path}:{line_number}"
            elif file_path:
                rel_path = os.path.relpath(file_path, project_path)
                return rel_path
            else:
                return "unknown:0"
                
        except Exception as e:
            logger.debug(f"Error getting symbol location: {e}")
            return "unknown:0"
    
    def _get_symbol_location_from_string(self, identifier: str, project_path: str) -> str:
        """Get file location for a string identifier.
        
        Args:
            identifier: String identifier (e.g., "src/file.py")
            project_path: Project path
            
        Returns:
            File path and line number (file:line)
        """
        try:
            # Attempt to find the file in the project_path
            for root, _, files in os.walk(project_path):
                for file in files:
                    if file.endswith(identifier):
                        # Construct a dummy line number if not available
                        return f"{os.path.join(root, file)}:0"
            return "unknown:0"
        except Exception as e:
            logger.debug(f"Error getting symbol location from string '{identifier}': {e}")
            return "unknown:0"

    def _get_semantic_categories(self, symbol_id: str) -> List[str]:
        """Get semantic categories for symbol using existing semantic matcher.
        
        Args:
            symbol_id: Symbol identifier
            
        Returns:
            List of semantic categories
        """
        try:
            if hasattr(self.semantic_matcher, 'get_semantic_categories'):
                categories = self.semantic_matcher.get_semantic_categories(symbol_id)
                if categories:
                    return categories
        except Exception as e:
            logger.debug(f"Error getting semantic categories for {symbol_id}: {e}")
        
        # Fallback: extract categories from symbol name
        return self._extract_categories_from_name(symbol_id)
    
    def _extract_categories_from_name(self, symbol_id: str) -> List[str]:
        """Extract semantic categories from symbol name as fallback.
        
        Args:
            symbol_id: Symbol identifier
            
        Returns:
            List of inferred categories
        """
        categories = []
        symbol_lower = symbol_id.lower()
        
        # Simple pattern matching for common categories
        if any(word in symbol_lower for word in ['auth', 'login', 'user', 'password']):
            categories.append('authentication')
        
        if any(word in symbol_lower for word in ['error', 'exception', 'fail', 'invalid']):
            categories.append('error_handling')
        
        if any(word in symbol_lower for word in ['db', 'database', 'query', 'model']):
            categories.append('database')
        
        if any(word in symbol_lower for word in ['api', 'endpoint', 'route', 'controller']):
            categories.append('api_development')
        
        if any(word in symbol_lower for word in ['validate', 'check', 'verify']):
            categories.append('validation')
        
        if any(word in symbol_lower for word in ['cache', 'redis', 'memcached']):
            categories.append('caching')
        
        if any(word in symbol_lower for word in ['security', 'encrypt', 'hash']):
            categories.append('security')
        
        if any(word in symbol_lower for word in ['file', 'upload', 'download']):
            categories.append('file_operations')
        
        if any(word in symbol_lower for word in ['network', 'http', 'socket']):
            categories.append('network')
        
        if any(word in symbol_lower for word in ['performance', 'optimize', 'speed']):
            categories.append('performance')
        
        return categories
    
    def _get_structural_context(self, symbol: Dict[str, Any]) -> Dict[str, Any]:
        """Get structural context information for symbol.
        
        Args:
            symbol: Symbol dictionary
            
        Returns:
            Structural context dictionary
        """
        context = {}
        
        try:
            # Extract available structural information
            if 'kind' in symbol:
                context['type'] = symbol['kind']
            
            if 'scope' in symbol:
                context['scope'] = symbol['scope']
            
            if 'dependencies' in symbol:
                context['dependencies'] = symbol['dependencies']
            
            if 'complexity' in symbol:
                context['complexity'] = symbol['complexity']
            
            if 'lines' in symbol:
                context['line_count'] = symbol['lines']
                
        except Exception as e:
            logger.debug(f"Error getting structural context: {e}")
        
        return context
    
    def _get_structural_context_from_string(self, identifier: str) -> Dict[str, Any]:
        """Get structural context information for a string identifier.
        
        Args:
            identifier: String identifier (e.g., "src/file.py")
            
        Returns:
            Structural context dictionary
        """
        context = {}
        try:
            # Attempt to find the file in a dummy project path
            dummy_project_path = "." # Use current directory as a placeholder
            for root, _, files in os.walk(dummy_project_path):
                for file in files:
                    if file.endswith(identifier):
                        # Construct a dummy line number if not available
                        return {"file_path": os.path.join(root, file), "line_number": "0"}
            return {"file_path": "unknown", "line_number": "0"}
        except Exception as e:
            logger.debug(f"Error getting structural context from string '{identifier}': {e}")
            return {"file_path": "unknown", "line_number": "0"}
    
    def _deduplicate_entrypoints(self, entrypoints: List[Entrypoint]) -> List[Entrypoint]:
        """Remove duplicate entrypoints based on identifier and location.
        
        Args:
            entrypoints: List of entrypoints to deduplicate
            
        Returns:
            List of unique entrypoints
        """
        seen = set()
        unique = []
        
        for entrypoint in entrypoints:
            # Create unique key from identifier and location
            key = (entrypoint.identifier, entrypoint.location)
            
            if key not in seen:
                seen.add(key)
                unique.append(entrypoint)
            else:
                # Keep the one with higher score
                existing = next(ep for ep in unique if (ep.identifier, ep.location) == key)
                if entrypoint.score > existing.score:
                    unique.remove(existing)
                    unique.append(entrypoint)
        
        return unique

    def _enhance_entrypoints_with_dependencies(self, entrypoints: List[Entrypoint], project_path: str) -> None:
        """Enhance entrypoints with dependency analysis information.
        
        Args:
            entrypoints: List of entrypoints to enhance
            project_path: Project path for dependency analysis
        """
        try:
            logger.info("Enhancing entrypoints with dependency analysis")
            
            # Build dependency graph for the project
            self._build_project_dependency_graph(project_path)
            
            # Initialize centrality calculator and impact analyzer if not already done
            if self.centrality_calculator is None:
                self.centrality_calculator = CentralityCalculator(self.dependency_graph)
            
            if self.impact_analyzer is None:
                self.impact_analyzer = ImpactAnalyzer(self.dependency_graph)
            
            # Enhance each entrypoint with dependency metrics
            for entrypoint in entrypoints:
                self._enhance_single_entrypoint(entrypoint, project_path)
                
            logger.info(f"Enhanced {len(entrypoints)} entrypoints with dependency information")
            
        except Exception as e:
            logger.error(f"Error enhancing entrypoints with dependencies: {e}")
    
    def _build_project_dependency_graph(self, project_path: str) -> None:
        """Build dependency graph for the entire project.
        
        Args:
            project_path: Project path to analyze
        """
        try:
            logger.info(f"Building dependency graph for project: {project_path}")
            
            # Get project files first
            from repomap_tool.core.file_scanner import get_project_files
            project_files = get_project_files(project_path, verbose=False)
            
            # Analyze project imports
            project_imports = self.import_analyzer.analyze_project_imports(project_files)
            
            # Build dependency graph
            self.dependency_graph.build_graph(project_files)
            
            logger.info(f"Built dependency graph with {len(self.dependency_graph.nodes)} nodes and {len(self.dependency_graph.graph.edges)} edges")
            
        except Exception as e:
            logger.error(f"Error building dependency graph: {e}")
    
    def _enhance_single_entrypoint(self, entrypoint: Entrypoint, project_path: str) -> None:
        """Enhance a single entrypoint with dependency metrics.
        
        Args:
            entrypoint: Entrypoint to enhance
            project_path: Project path for context
        """
        try:
            # Extract file path from location
            file_path = self._extract_file_path_from_location(entrypoint.location, project_path)
            if not file_path:
                return
            
            # Get dependency centrality score
            centrality_scores = self.centrality_calculator.calculate_composite_importance()
            if file_path in centrality_scores:
                entrypoint.dependency_centrality = centrality_scores[file_path]
            
            # Get import and dependency counts
            dependents = self.dependency_graph.get_dependents(file_path)
            dependencies = self.dependency_graph.get_dependencies(file_path)
            
            entrypoint.import_count = len(dependents)
            entrypoint.dependency_count = len(dependencies)
            
            # Calculate impact risk
            impact_report = self.impact_analyzer.analyze_change_impact(file_path)
            if impact_report:
                entrypoint.impact_risk = impact_report.overall_risk_score
                
                # Calculate refactoring priority based on impact risk and centrality
                if entrypoint.dependency_centrality is not None:
                    entrypoint.refactoring_priority = (
                        entrypoint.impact_risk * 0.4 + 
                        entrypoint.dependency_centrality * 0.6
                    )
            
        except Exception as e:
            logger.debug(f"Error enhancing entrypoint {entrypoint.identifier}: {e}")
    
    def _extract_file_path_from_location(self, location: str, project_path: str) -> Optional[str]:
        """Extract file path from entrypoint location.
        
        Args:
            location: Entrypoint location (e.g., "src/file.py:123")
            project_path: Project root path
            
        Returns:
            Absolute file path or None if extraction fails
        """
        try:
            # Handle location format: "file.py:123" or "src/file.py:123"
            if ':' in location:
                file_part = location.split(':')[0]
            else:
                file_part = location
            
            # Construct absolute path
            absolute_path = os.path.join(project_path, file_part)
            
            # Normalize path
            normalized_path = os.path.normpath(absolute_path)
            
            # Verify file exists
            if os.path.isfile(normalized_path):
                return normalized_path
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting file path from location '{location}': {e}")
            return None
