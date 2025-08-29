#!/usr/bin/env python3
"""
core.py - Core Docker RepoMap functionality with Pydantic models

This module provides the main DockerRepoMap class refactored to use Pydantic
for configuration management, validation, and structured data handling.
"""

import os
import sys
import re
import fnmatch
import time
import logging
from pathlib import Path
from typing import List, Set, Dict, Any, Optional, Tuple
from datetime import datetime

# Import Pydantic models
from .models import (
    RepoMapConfig,
    MatchResult,
    SearchRequest,
    SearchResponse,
    ProjectInfo,
)

# Import aider components
try:
    from aider.repomap import RepoMap

except ImportError as e:
    logging.error(f"Failed to import aider components: {e}")
    logging.error("Make sure aider is installed: pip install aider")
    sys.exit(1)

# Import aider components
try:
    from aider.repomap import RepoMap
    AIDER_AVAILABLE = True
except ImportError as e:
    logging.error(f"Failed to import aider components: {e}")
    logging.error("Make sure aider-chat is installed: pip install aider-chat")
    AIDER_AVAILABLE = False

# Import matchers
try:
    from .matchers.fuzzy_matcher import FuzzyMatcher
    from .matchers.adaptive_semantic_matcher import AdaptiveSemanticMatcher
    from .matchers.hybrid_matcher import HybridMatcher

    MATCHERS_AVAILABLE = True
except ImportError as e:
    logging.error(f"Failed to import matchers: {e}")
    MATCHERS_AVAILABLE = False


def parse_gitignore(gitignore_path: Path) -> List[str]:
    """
    Parse a .gitignore file and return list of patterns.
    
    Args:
        gitignore_path: Path to .gitignore file
        
    Returns:
        List of gitignore patterns
    """
    patterns = []
    if not gitignore_path.exists():
        return patterns
        
    try:
        with open(gitignore_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    patterns.append(line)
    except Exception as e:
        logging.warning(f"Failed to read .gitignore file {gitignore_path}: {e}")
    
    return patterns


def should_ignore_file(file_path: Path, gitignore_patterns: List[str], project_root: Path) -> bool:
    """
    Check if a file should be ignored based on .gitignore patterns.
    
    Args:
        file_path: Path to the file to check
        gitignore_patterns: List of .gitignore patterns
        project_root: Root directory of the project
        
    Returns:
        True if file should be ignored, False otherwise
    """
    if not gitignore_patterns:
        return False
        
    # Get relative path from project root
    try:
        rel_path = file_path.relative_to(project_root)
    except ValueError:
        # File is not under project root
        return False
    
    rel_path_str = str(rel_path)
    
    for pattern in gitignore_patterns:
        # Handle directory patterns (ending with /)
        if pattern.endswith('/'):
            dir_pattern = pattern[:-1]
            if rel_path_str.startswith(dir_pattern + '/') or rel_path_str == dir_pattern:
                return True
        
        # Handle file patterns
        elif pattern.startswith('*'):
            # Wildcard pattern
            if fnmatch.fnmatch(rel_path_str, pattern):
                return True
        else:
            # Exact match or prefix match
            if rel_path_str == pattern or rel_path_str.startswith(pattern + '/'):
                return True
    
    return False


class DockerRepoMap:
    """
    Enhanced Docker RepoMap with Pydantic configuration and structured data handling.

    This class provides code analysis and identifier matching capabilities
    with improved configuration management using Pydantic models.
    """

    def __init__(self, config: RepoMapConfig):
        """
        Initialize Docker RepoMap with validated configuration.

        Args:
            config: Validated RepoMapConfig instance
        """
        self.config = config
        self.logger = self._setup_logging()

        # Initialize components
        self.repo_map: Optional[Any] = None
        self.fuzzy_matcher: Optional[FuzzyMatcher] = None
        self.semantic_matcher: Optional[AdaptiveSemanticMatcher] = None
        self.hybrid_matcher: Optional[HybridMatcher] = None

        # Initialize the system
        self._initialize_components()

        self.logger.info(f"Initialized DockerRepoMap for {self.config.project_root}")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging based on configuration."""
        logger = logging.getLogger(__name__)

        # Set log level
        level = getattr(logging, self.config.log_level)
        logger.setLevel(level)

        # Create handler if none exists
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _initialize_components(self) -> None:
        """Initialize all components based on configuration."""
        if AIDER_AVAILABLE:
            # Create real aider components
            from aider.io import InputOutput
            from aider.models import Model
            
            # Create a simple IO object
            self.io = InputOutput()
            
            # Create a simple Model object
            from aider.models import DEFAULT_MODEL_NAME
            self.model = Model(DEFAULT_MODEL_NAME)
            
            # Initialize RepoMap with real implementation
            self.repo_map = RepoMap(
                map_tokens=self.config.map_tokens,
                root=str(self.config.project_root),
                main_model=self.model,
                io=self.io,
                verbose=self.config.verbose,
                refresh="auto" if self.config.refresh_cache else "no",
            )
        else:
            # Fallback to standalone implementation
            self.repo_map = StandaloneRepoMap(
                project_root=str(self.config.project_root),
                verbose=self.config.verbose
            )

        # Initialize matchers if available
        if MATCHERS_AVAILABLE:
            self._initialize_matchers()
        else:
            self.logger.warning("Matchers not available - matching features disabled")

    def _initialize_matchers(self) -> None:
        """Initialize matching components."""
        # Initialize fuzzy matcher
        if self.config.fuzzy_match.enabled:
            self.fuzzy_matcher = FuzzyMatcher(
                threshold=self.config.fuzzy_match.threshold,
                strategies=self.config.fuzzy_match.strategies,
                cache_results=self.config.fuzzy_match.cache_results,
                verbose=self.config.verbose,
            )
            self.logger.info(f"Initialized FuzzyMatcher: {self.config.fuzzy_match}")

        # Initialize semantic matcher
        if self.config.semantic_match.enabled:
            self.semantic_matcher = AdaptiveSemanticMatcher(verbose=self.config.verbose)
            self.logger.info(
                f"Initialized SemanticMatcher: {self.config.semantic_match}"
            )

        # Initialize hybrid matcher if both are enabled
        if self.config.fuzzy_match.enabled and self.config.semantic_match.enabled:
            self.hybrid_matcher = HybridMatcher(
                fuzzy_threshold=self.config.fuzzy_match.threshold,
                semantic_threshold=self.config.semantic_match.threshold,
                verbose=self.config.verbose,
            )
            self.logger.info("Initialized HybridMatcher")

    def _create_mocks(self) -> Tuple[Any, Any]:
        """Create mock objects for aider dependencies."""

        class MockModel:
            def __init__(self, map_tokens: int):
                self.map_tokens = map_tokens
                self.info = {"max_input_tokens": 8192}

            def __call__(self, *args: Any, **kwargs: Any) -> str:
                return "Mock response"

            def token_count(self, text: str) -> int:
                # Simple token estimation
                return len(text.split())

        class MockIO:
            def __init__(self) -> None:
                self.tool_error_messages: List[str] = []
                self.tool_call_messages: List[str] = []

            def add_tool_error(self, message: str) -> None:
                self.tool_error_messages.append(message)

            def add_tool_call(self, message: str) -> None:
                self.tool_call_messages.append(message)

            def tool_error(self, message: str) -> None:
                self.tool_error_messages.append(message)

            def tool_warning(self, message: str) -> None:
                # Mock warning method
                pass

            def tool_output(self, message: str) -> None:
                # Mock output method
                pass

        return MockModel(self.config.map_tokens), MockIO()

    def _create_mock_repo_map(self) -> Any:
        """Create a mock RepoMap object with required methods."""

        class MockRepoMap:
            def __init__(self, config: Any) -> None:
                self.config = config
                self.root = str(config.project_root)
                self.map_tokens = config.map_tokens
                self.verbose = config.verbose

            def get_map(self) -> Dict[str, Any]:
                """Return a mock project map with sample identifiers."""
                # Create a mock project map with sample data
                mock_map = {
                    "files": {
                        "main.py": {
                            "identifiers": ["hello_world", "main", "print"],
                            "content": "def hello_world():\n    print('Hello, World!')",
                        },
                        "utils.py": {
                            "identifiers": [
                                "process_data",
                                "validate_input",
                                "format_output",
                            ],
                            "content": "def process_data(data):\n    return data.upper()",
                        },
                    },
                    "identifiers": [
                        "hello_world",
                        "main",
                        "print",
                        "process_data",
                        "validate_input",
                        "format_output",
                    ],
                    "stats": {
                        "total_files": 2,
                        "total_identifiers": 6,
                        "file_types": {"python": 2},
                    },
                }
                return mock_map

        return MockRepoMap(self.config)

    def _extract_identifiers(self, project_map: Any) -> Set[str]:
        """Extract all identifiers from the project map.

        This method handles multiple project map formats:
        - String: Real aider RepoMap returns a formatted string
        - Dictionary: Mock/standalone implementation returns structured data
        - None/Empty: Handle gracefully
        """
        identifiers: Set[str] = set()

        # Handle None or empty project_map
        if not project_map:
            return identifiers

        # Handle string format (real aider RepoMap)
        if isinstance(project_map, str):
            # Extract identifiers from the string using regex
            import re
            # Look for function/class definitions and variable names
            patterns = [
                r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:\(]',
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*[^=]',  # Variable assignments
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)',  # Function calls
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, project_map)
                identifiers.update(matches)
            
            return identifiers

        # Handle dictionary format (mock/standalone implementation)
        if isinstance(project_map, dict):
            # Handle Tag objects from aider (new format)
            if "tags" in project_map and project_map["tags"] is not None:
                for tag in project_map["tags"]:
                    if hasattr(tag, 'name') and tag.name:
                        identifiers.add(tag.name)
            
            # Check if project_map has top-level identifiers key
            if "identifiers" in project_map and project_map["identifiers"] is not None:
                # Ensure identifiers is iterable
                if isinstance(project_map["identifiers"], (list, set, tuple)):
                    identifiers.update(project_map["identifiers"])
                else:
                    self.logger.warning(
                        f"Unexpected identifiers type: {type(project_map['identifiers'])}"
                    )

            # Also check for file-based identifiers (complex structure)
            for file_path, file_data in project_map.items():
                if isinstance(file_data, dict) and "identifiers" in file_data:
                    if isinstance(file_data["identifiers"], (list, set, tuple)):
                        identifiers.update(file_data["identifiers"])

        return identifiers

    def _get_project_files(self) -> List[str]:
        """Get list of project files, respecting .gitignore patterns."""
        try:
            # Parse .gitignore file
            gitignore_path = self.config.project_root / ".gitignore"
            gitignore_patterns = parse_gitignore(gitignore_path)
            
            if gitignore_patterns:
                self.logger.info(f"Loaded {len(gitignore_patterns)} .gitignore patterns")
            
            files = []
            for root, dirs, filenames in os.walk(self.config.project_root):
                # Filter out ignored directories
                dirs[:] = [d for d in dirs if not should_ignore_file(
                    Path(root) / d, gitignore_patterns, self.config.project_root
                )]
                
                for filename in filenames:
                    file_path = Path(root) / filename
                    
                    # Check if file should be ignored
                    if should_ignore_file(file_path, gitignore_patterns, self.config.project_root):
                        if self.config.verbose:
                            self.logger.debug(f"Ignoring file (gitignore): {file_path}")
                        continue
                    
                    # Only include supported file types
                    if filename.endswith((".py", ".js", ".java", ".cpp", ".c", ".h")):
                        files.append(str(file_path))
            
            if self.config.verbose:
                self.logger.info(f"Found {len(files)} files after .gitignore filtering")
            
            return files
        except Exception as e:
            self.logger.error(f"Error scanning project files: {e}")
            return []

    def _analyze_file_types(self) -> Dict[str, int]:
        """Analyze file types in the project."""
        files = self._get_project_files()
        file_types: Dict[str, int] = {}
        for file_path in files:
            ext = file_path.split(".")[-1] if "." in file_path else "unknown"
            file_types[ext] = file_types.get(ext, 0) + 1
        return file_types

    def _analyze_identifier_types(self, identifiers: Set[str]) -> Dict[str, int]:
        """Analyze types of identifiers in the project."""
        types = {
            "functions": 0,
            "classes": 0,
            "variables": 0,
            "constants": 0,
            "other": 0,
        }

        # Handle None or empty identifiers
        if not identifiers:
            return types

        for identifier in identifiers:
            # Skip None or non-string identifiers
            if not identifier or not isinstance(identifier, str):
                continue

            try:
                if identifier.isupper():
                    types["constants"] += 1
                elif identifier[0].isupper():
                    types["classes"] += 1
                elif identifier.endswith("()"):
                    types["functions"] += 1
                elif identifier.islower():
                    types["variables"] += 1
                else:
                    types["other"] += 1
            except (IndexError, AttributeError) as e:
                self.logger.warning(f"Error analyzing identifier '{identifier}': {e}")
                types["other"] += 1

        return types

    def _get_cache_size(self) -> Optional[int]:
        """Get cache size in bytes."""
        if self.config.cache_dir:
            try:
                cache_path = Path(self.config.cache_dir)
                return sum(
                    f.stat().st_size for f in cache_path.rglob("*") if f.is_file()
                )
            except Exception:
                return None
        return None

    def _fuzzy_search(
        self, request: SearchRequest, identifiers: Set[str]
    ) -> List[MatchResult]:
        """Perform fuzzy search."""
        if not self.fuzzy_matcher:
            return []

        # Use specified strategies or default
        strategies = request.strategies or self.config.fuzzy_match.strategies

        # Get matches
        matches = self.fuzzy_matcher.match_identifiers(request.query, identifiers)

        # Convert to MatchResult objects
        results = []
        for identifier, score in matches:
            if score >= request.threshold * 100:  # Convert threshold to percentage
                result = MatchResult(
                    identifier=identifier,
                    score=score / 100.0,  # Normalize to 0.0-1.0
                    strategy="fuzzy",
                    match_type="fuzzy",
                    metadata={"strategies": strategies},
                )
                results.append(result)

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def _semantic_search(
        self, request: SearchRequest, identifiers: Set[str]
    ) -> List[MatchResult]:
        """Perform semantic search."""
        if not self.semantic_matcher:
            return []

        # Learn from identifiers first
        self.semantic_matcher.learn_from_identifiers(identifiers)

        # Get matches
        matches = self.semantic_matcher.find_semantic_matches(
            request.query, identifiers, threshold=request.threshold
        )

        # Convert to MatchResult objects
        results = []
        for identifier, score in matches:
            # Normalize score to ensure it's within 0.0-1.0 range
            normalized_score = max(0.0, min(1.0, score))
            result = MatchResult(
                identifier=identifier,
                score=normalized_score,
                strategy="semantic",
                match_type="semantic",
                metadata={"tfidf_score": score},
            )
            results.append(result)

        return results

    def _hybrid_search(
        self, request: SearchRequest, identifiers: Set[str]
    ) -> List[MatchResult]:
        """Perform hybrid search."""
        if not self.hybrid_matcher:
            return []

        # Get matches
        matches = self.hybrid_matcher.find_hybrid_matches(
            request.query, identifiers, threshold=request.threshold
        )

        # Convert to MatchResult objects
        results = []
        for identifier, score, component_scores in matches:
            # Determine the best strategy from component scores
            best_strategy = max(component_scores.items(), key=lambda x: x[1])[0]
            result = MatchResult(
                identifier=identifier,
                score=score,
                strategy=best_strategy,
                match_type="hybrid",
                metadata={"hybrid_score": score, "component_scores": component_scores},
            )
            results.append(result)

        return results

    def _basic_search(
        self, request: SearchRequest, identifiers: Set[str]
    ) -> List[MatchResult]:
        """Perform basic string search as fallback."""
        results = []
        query_lower = request.query.lower()

        for identifier in identifiers:
            if query_lower in identifier.lower():
                score = len(query_lower) / len(identifier)
                if score >= request.threshold:
                    result = MatchResult(
                        identifier=identifier,
                        score=score,
                        strategy="substring",
                        match_type="fuzzy",
                        metadata={"basic_match": True},
                    )
                    results.append(result)

        return results

    def analyze_project(self) -> ProjectInfo:
        """
        Analyze the project and return structured information.

        Returns:
            ProjectInfo with analysis results
        """
        start_time = time.time()

        try:
            # Get project files first
            project_files = self._get_project_files()
            if not project_files:
                # If no files found, return empty analysis
                return ProjectInfo(
                    project_root=str(self.config.project_root),
                    total_files=0,
                    total_identifiers=0,
                    file_types={},
                    identifier_types={
                        "variables": 0,
                        "functions": 0,
                        "classes": 0,
                        "constants": 0,
                        "other": 0,
                    },
                    analysis_time_ms=0,
                    cache_size_bytes=self._get_cache_size(),
                    last_updated=datetime.now(),
                )

            # Get project tags using real RepoMap method with actual files
            all_tags = []
            if self.repo_map is not None:
                for file_path in project_files:
                    rel_fname = str(Path(file_path).relative_to(self.config.project_root))
                    try:
                        tags = self.repo_map.get_tags(file_path, rel_fname)
                        if tags:
                            all_tags.extend(tags)
                    except Exception as e:
                        if self.config.verbose:
                            self.logger.warning(f"Failed to get tags for {rel_fname}: {e}")
            
            # Convert tags to a format that _extract_identifiers can handle
            project_map = {"tags": all_tags} if all_tags else {}

            # Extract identifiers
            all_identifiers = self._extract_identifiers(project_map)

            # Analyze file types
            file_types = self._analyze_file_types()

            # Analyze identifier types
            identifier_types = self._analyze_identifier_types(all_identifiers)

            analysis_time = (time.time() - start_time) * 1000

            # Create project info
            project_info = ProjectInfo(
                project_root=str(self.config.project_root),
                total_files=len(self._get_project_files()),
                total_identifiers=len(all_identifiers),
                file_types=file_types,
                identifier_types=identifier_types,
                analysis_time_ms=analysis_time,
                cache_size_bytes=self._get_cache_size(),
                last_updated=datetime.now(),
            )

            self.logger.info(f"Project analysis complete: {project_info}")
            return project_info

        except Exception as e:
            self.logger.error(f"Project analysis failed: {e}")
            raise

    def search_identifiers(self, request: SearchRequest) -> SearchResponse:
        """
        Search for identifiers using the specified matching strategy.

        Args:
            request: SearchRequest with query and parameters

        Returns:
            SearchResponse with match results
        """
        start_time = time.time()

        try:
            # Get project files first
            project_files = self._get_project_files()
            if not project_files:
                # If no files found, return empty results
                return SearchResponse(
                    query=request.query,
                    match_type=request.match_type,
                    threshold=request.threshold,
                    total_results=0,
                    results=[],
                    search_time_ms=0,
                    cache_hit=False,
                    metadata={
                        "strategies_used": request.strategies or [],
                        "include_context": request.include_context,
                    },
                )

            # Get all identifiers using real RepoMap method with actual files
            all_tags = []
            if self.repo_map is not None:
                for file_path in project_files:
                    rel_fname = str(Path(file_path).relative_to(self.config.project_root))
                    try:
                        tags = self.repo_map.get_tags(file_path, rel_fname)
                        if tags:
                            all_tags.extend(tags)
                    except Exception as e:
                        if self.config.verbose:
                            self.logger.warning(f"Failed to get tags for {rel_fname}: {e}")
            
            # Convert tags to a format that _extract_identifiers can handle
            project_map = {"tags": all_tags} if all_tags else {}
            all_identifiers = self._extract_identifiers(project_map)

            # Perform search based on match type
            if request.match_type == "fuzzy" and self.fuzzy_matcher:
                results = self._fuzzy_search(request, all_identifiers)
            elif request.match_type == "semantic" and self.semantic_matcher:
                results = self._semantic_search(request, all_identifiers)
            elif request.match_type == "hybrid" and self.hybrid_matcher:
                results = self._hybrid_search(request, all_identifiers)
            else:
                # Fallback to basic search
                results = self._basic_search(request, all_identifiers)

            # Limit results
            results = results[: request.max_results]

            search_time = (time.time() - start_time) * 1000

            response = SearchResponse(
                query=request.query,
                match_type=request.match_type,
                threshold=request.threshold,
                total_results=len(results),
                results=results,
                search_time_ms=search_time,
                cache_hit=False,  # TODO: Implement cache checking
                metadata={
                    "strategies_used": request.strategies or [],
                    "include_context": request.include_context,
                },
            )

            self.logger.info(
                f"Search completed: {len(results)} results in {search_time:.2f}ms"
            )
            return response

        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            raise

    def get_config(self) -> RepoMapConfig:
        """Get current configuration."""
        return self.config

    def update_config(self, new_config: RepoMapConfig) -> None:
        """Update configuration and reinitialize components."""
        self.config = new_config
        self._initialize_components()
        self.logger.info("Configuration updated and components reinitialized")

    def export_config(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        return self.config.model_dump()

    def import_config(self, config_dict: Dict[str, Any]) -> None:
        """Import configuration from dictionary."""
        new_config = RepoMapConfig(**config_dict)
        self.update_config(new_config)
