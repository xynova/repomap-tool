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
        return unique_entrypoints
    
    def _get_project_symbols(self, project_path: str) -> List[Dict[str, Any]]:
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
    
    def _discover_semantic_entrypoints(self, intent: str, symbols: List[Dict[str, Any]], project_path: str) -> List[Entrypoint]:
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
            for symbol in symbols:
                # Extract symbol identifier
                symbol_id = self._extract_symbol_identifier(symbol)
                if not symbol_id:
                    continue
                
                # Calculate semantic similarity
                similarity = self.semantic_matcher.calculate_similarity(intent, symbol_id)
                
                if similarity >= self.semantic_threshold:
                    # Get semantic categories for this symbol
                    categories = self._get_semantic_categories(symbol_id)
                    
                    # Create entrypoint
                    entrypoint = Entrypoint(
                        identifier=symbol_id,
                        location=self._get_symbol_location(symbol, project_path),
                        score=similarity,
                        categories=categories,
                        structural_context=self._get_structural_context(symbol)
                    )
                    entrypoints.append(entrypoint)
                    
        except Exception as e:
            logger.error(f"Error in semantic entrypoint discovery: {e}")
        
        return entrypoints
    
    def _discover_fuzzy_entrypoints(self, intent: str, symbols: List[Dict[str, Any]], project_path: str) -> List[Entrypoint]:
        """Discover entrypoints using fuzzy matching.
        
        Args:
            intent: User intent description
            symbols: List of project symbols
            project_path: Project path
            
        Returns:
            List of fuzzy-matched entrypoints
        """
        entrypoints = []
        
        try:
            # Use existing fuzzy matcher to find similar symbols
            symbol_identifiers = [self._extract_symbol_identifier(s) for s in symbols if self._extract_symbol_identifier(s)]
            
            if not symbol_identifiers:
                return []
            
            # Find fuzzy matches
            fuzzy_matches = self.fuzzy_matcher.find_similar(intent, symbol_identifiers)
            
            for match in fuzzy_matches:
                if match.score >= self.fuzzy_threshold:
                    # Find the original symbol data
                    symbol_data = next((s for s in symbols if self._extract_symbol_identifier(s) == match.identifier), None)
                    
                    if symbol_data:
                        # Create entrypoint
                        entrypoint = Entrypoint(
                            identifier=match.identifier,
                            location=self._get_symbol_location(symbol_data, project_path),
                            score=match.score / 100.0,  # Convert percentage to 0-1 scale
                            categories=[],  # Fuzzy matching doesn't provide categories
                            structural_context=self._get_structural_context(symbol_data)
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
