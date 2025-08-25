#!/usr/bin/env python3
# external_repomap.py

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import aider components
try:
    from aider.repomap import RepoMap
    from aider.special import filter_important_files
    from aider.dump import dump
except ImportError as e:
    logger.error(f"Failed to import aider components: {e}")
    logger.error("Make sure aider is installed: pip install aider")
    sys.exit(1)

# Import fuzzy matching
try:
    from fuzzy_matcher import FuzzyMatcher
    fuzzy_matcher_available = True
except ImportError as e:
    logger.error(f"Failed to import fuzzy_matcher: {e}")
    logger.error("Make sure fuzzywuzzy and python-Levenshtein are installed")
    fuzzy_matcher_available = False

# Import adaptive semantic matching
try:
    from adaptive_semantic_matcher import AdaptiveSemanticMatcher
    adaptive_semantic_available = True
except ImportError as e:
    logger.error(f"Failed to import adaptive_semantic_matcher: {e}")
    adaptive_semantic_available = False

class DockerRepoMap:
    def __init__(self, project_root, map_tokens=4096, cache_dir=None, verbose=True, 
                 fuzzy_match=False, fuzzy_threshold=70, fuzzy_strategies=None,
                 adaptive_semantic=False, semantic_threshold=0.1):
        self.project_root = Path(project_root).resolve()
        self.map_tokens = map_tokens
        self.cache_dir = Path(cache_dir) if cache_dir else self.project_root
        self.verbose = verbose
        
        # Fuzzy matching configuration
        self.fuzzy_match = fuzzy_match
        self.fuzzy_threshold = fuzzy_threshold
        self.fuzzy_strategies = fuzzy_strategies or ['prefix', 'substring', 'levenshtein']
        
        # Adaptive semantic matching configuration
        self.adaptive_semantic = adaptive_semantic
        self.semantic_threshold = semantic_threshold
        
        # Initialize fuzzy matcher
        if self.fuzzy_match and fuzzy_matcher_available:
            self.fuzzy_matcher = FuzzyMatcher(
                threshold=fuzzy_threshold,
                strategies=self.fuzzy_strategies,
                verbose=verbose
            )
            logger.info(f"Initialized FuzzyMatcher with threshold={fuzzy_threshold}, strategies={self.fuzzy_strategies}")
        
        # Initialize adaptive semantic matcher
        if self.adaptive_semantic and adaptive_semantic_available:
            self.semantic_matcher = AdaptiveSemanticMatcher(verbose=verbose)
            logger.info(f"Initialized AdaptiveSemanticMatcher with threshold={semantic_threshold}")
        elif self.adaptive_semantic and not adaptive_semantic_available:
            logger.warning("Adaptive semantic matching requested but not available")
            self.adaptive_semantic = False
        
        # Create mock objects
        self.mock_model, self.mock_io = self._create_mocks()
        
        # Initialize RepoMap
        self.repo_map = RepoMap(
            map_tokens=map_tokens,
            root=str(self.project_root),
            main_model=self.mock_model,
            io=self.mock_io,
            verbose=verbose,
            refresh="auto"
        )
        
        logger.info(f"Initialized RepoMap for {self.project_root}")
        logger.info(f"Cache directory: {self.cache_dir}")
    
    def _create_mocks(self):
        """Create mock objects for aider dependencies"""
        
        class MockModel:
            def __init__(self, map_tokens):
                self.map_tokens = map_tokens
                self.info = {"max_input_tokens": 8192}
            
            def token_count(self, text):
                # Simple token approximation
                return len(text) // 4
            
            def get_repo_map_tokens(self):
                return self.map_tokens
        
        class MockIO:
            def __init__(self, verbose=True):
                self.verbose = verbose
            
            def read_text(self, fname):
                try:
                    with open(fname, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    if self.verbose:
                        logger.warning(f"Error reading {fname}: {e}")
                    return None
            
            def tool_output(self, msg):
                if self.verbose:
                    logger.info(f"[INFO] {msg}")
            
            def tool_warning(self, msg):
                logger.warning(f"[WARN] {msg}")
            
            def tool_error(self, msg):
                logger.error(f"[ERROR] {msg}")
        
        return MockModel(self.map_tokens), MockIO(self.verbose)
    
    def get_source_files(self, extensions=None):
        """Get all source files from the project"""
        if extensions is None:
            extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.scala']
        
        source_files = []
        exclude_dirs = {'.git', 'node_modules', '__pycache__', 'build', 'dist', 'venv', '.venv', 'target', 'bin', 'obj'}
        
        logger.info(f"Scanning for files with extensions: {extensions}")
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    source_files.append(file_path)
        
        logger.info(f"Found {len(source_files)} source files")
        return source_files
    
    def generate_repo_map(self, chat_files=None, mentioned_fnames=None, mentioned_idents=None, force_refresh=False):
        """Generate repo map for the project"""
        if chat_files is None:
            chat_files = []
        if mentioned_fnames is None:
            mentioned_fnames = set()
        if mentioned_idents is None:
            mentioned_idents = set()
        
        # Apply fuzzy matching to mentioned identifiers
        original_idents = mentioned_idents.copy()
        if mentioned_idents and self.fuzzy_match:
            logger.info("=== Applying Fuzzy Matching ===")
            mentioned_idents = self.get_fuzzy_ident_matches(mentioned_idents)
            logger.info("=== Fuzzy Matching Complete ===")
        
        all_files = self.get_source_files()
        other_files = [f for f in all_files if f not in chat_files]
        
        logger.info(f"Generating repo map for {len(all_files)} files (chat: {len(chat_files)}, other: {len(other_files)})")
        logger.info(f"Mentioned files: {mentioned_fnames}")
        logger.info(f"Original identifiers: {original_idents}")
        logger.info(f"Identifiers after fuzzy matching: {mentioned_idents}")
        
        try:
            repo_content = self.repo_map.get_repo_map(
                chat_files=chat_files,
                other_files=other_files,
                mentioned_fnames=mentioned_fnames,
                mentioned_idents=mentioned_idents,
                force_refresh=force_refresh
            )
            
            if repo_content:
                logger.info(f"Generated repo map with {len(repo_content)} characters")
                return repo_content
            else:
                logger.warning("No repo map generated")
                return None
                
        except Exception as e:
            logger.error(f"Error generating repo map: {e}")
            return None
    
    def get_cache_stats(self):
        """Get cache statistics"""
        try:
            cache_path = self.project_root / self.repo_map.TAGS_CACHE_DIR
            if cache_path.exists():
                cache_size = sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file())
                cache_files = len(list(cache_path.rglob('*')))
                
                return {
                    "cache_path": str(cache_path),
                    "cache_size_bytes": cache_size,
                    "cache_size_mb": round(cache_size / (1024 * 1024), 2),
                    "cache_files": cache_files,
                    "exists": True,
                    "last_modified": datetime.fromtimestamp(cache_path.stat().st_mtime).isoformat()
                }
            else:
                return {"exists": False}
        except Exception as e:
            return {"error": str(e)}
    
    def clear_cache(self):
        """Clear the cache"""
        try:
            cache_path = self.project_root / self.repo_map.TAGS_CACHE_DIR
            if cache_path.exists():
                import shutil
                shutil.rmtree(cache_path)
                logger.info(f"Cleared cache at {cache_path}")
            else:
                logger.info("No cache to clear")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_all_identifiers_from_repo(self) -> set:
        """Extract all identifiers from the parsed codebase"""
        all_identifiers = set()
        
        try:
            # Get all source files
            source_files = self.get_source_files()
            
            for file_path in source_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract function and class names using regex
                    # This is a simplified approach - in a full implementation,
                    # we'd use tree-sitter parsing like the main RepoMap
                    
                    # Function definitions
                    import re
                    func_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
                    class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:\(]'
                    
                    func_matches = re.findall(func_pattern, content)
                    class_matches = re.findall(class_pattern, content)
                    
                    all_identifiers.update(func_matches)
                    all_identifiers.update(class_matches)
                    
                except Exception as e:
                    if self.verbose:
                        logger.debug(f"Error processing {file_path}: {e}")
                    continue
            
            if self.verbose:
                logger.info(f"Extracted {len(all_identifiers)} identifiers from codebase")
            
        except Exception as e:
            logger.error(f"Error extracting identifiers: {e}")
        
        return all_identifiers
    
    def get_fuzzy_ident_matches(self, query_idents: set) -> set:
        """Get fuzzy matches and adaptive semantic matches for the given identifiers"""
        if not query_idents:
            return query_idents
        
        # Get all identifiers from the codebase
        all_identifiers = self.get_all_identifiers_from_repo()
        
        if not all_identifiers:
            logger.warning("No identifiers found in codebase for matching")
            return query_idents
        
        # Initialize matches set
        all_matches = set()
        original_queries = query_idents.copy()
        
        # Perform fuzzy matching if enabled
        if self.fuzzy_match and hasattr(self, 'fuzzy_matcher'):
            fuzzy_matches = set()
            for query in original_queries:
                matches = self.fuzzy_matcher.match_identifiers(query, all_identifiers)
                
                if self.verbose:
                    logger.info(f"Fuzzy matches for '{query}':")
                    for ident, score in matches[:5]:  # Show top 5 matches
                        logger.info(f"  - {ident} (score: {score})")
                
                # Add matched identifiers to the set
                for ident, score in matches:
                    fuzzy_matches.add(ident)
            
            all_matches.update(fuzzy_matches)
            
            if self.verbose:
                logger.info(f"Fuzzy matches found: {fuzzy_matches}")
        
        # Perform adaptive semantic matching if enabled
        if self.adaptive_semantic and hasattr(self, 'semantic_matcher'):
            # Learn from the codebase
            self.semantic_matcher.learn_from_identifiers(all_identifiers)
            
            semantic_matches = set()
            for query in original_queries:
                matches = self.semantic_matcher.find_semantic_matches(query, all_identifiers, self.semantic_threshold)
                
                if self.verbose:
                    logger.info(f"Semantic matches for '{query}':")
                    for ident, score in matches[:5]:  # Show top 5 matches
                        logger.info(f"  - {ident} (score: {score:.3f})")
                
                # Add matched identifiers to the set
                for ident, score in matches:
                    semantic_matches.add(ident)
            
            all_matches.update(semantic_matches)
            
            if self.verbose:
                logger.info(f"Semantic matches found: {semantic_matches}")
        
        # Combine original queries with all matches
        combined_matches = query_idents.union(all_matches)
        
        if self.verbose:
            logger.info(f"Original identifiers: {original_queries}")
            logger.info(f"All matches found: {all_matches}")
            logger.info(f"Combined identifiers: {combined_matches}")
        
        return combined_matches
    
    def save_repo_map(self, repo_content, output_file=None):
        """Save repo map to file"""
        if not repo_content:
            logger.warning("No repo content to save")
            return None
        
        if output_file is None:
            output_file = self.project_root / "repo_map.txt"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(repo_content)
            
            logger.info(f"Repo map saved to: {output_file}")
            return str(output_file)
        except Exception as e:
            logger.error(f"Error saving repo map: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description='Generate repo map using aider')
    parser.add_argument('project_path', help='Path to the project directory')
    parser.add_argument('--map-tokens', type=int, default=4096, help='Token budget for repo map (default: 4096)')
    parser.add_argument('--output', '-o', help='Output file path (default: repo_map.txt in project root)')
    parser.add_argument('--cache-stats', action='store_true', help='Show cache statistics')
    parser.add_argument('--clear-cache', action='store_true', help='Clear the cache')
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh of repo map')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # New dynamic parameters
    parser.add_argument('--chat-files', help='Comma-separated list of files currently in chat')
    parser.add_argument('--mentioned-files', help='Comma-separated list of mentioned files')
    parser.add_argument('--mentioned-idents', help='Comma-separated list of mentioned identifiers')
    
    # Fuzzy matching parameters
    parser.add_argument('--fuzzy-match', action='store_true', 
                       help='Enable fuzzy matching for mentioned identifiers')
    parser.add_argument('--fuzzy-threshold', type=int, default=70,
                       help='Similarity threshold for fuzzy matching (0-100, default: 70)')
    parser.add_argument('--fuzzy-strategies', 
                       help='Comma-separated list of fuzzy matching strategies (prefix,substring,levenshtein,word)')
    
    # Adaptive semantic matching parameters
    parser.add_argument('--adaptive-semantic', action='store_true',
                       help='Enable adaptive semantic matching for mentioned identifiers')
    parser.add_argument('--semantic-threshold', type=float, default=0.1,
                       help='Similarity threshold for semantic matching (0.0-1.0, default: 0.1)')
    
    args = parser.parse_args()
    
    # Parse fuzzy strategies
    fuzzy_strategies = None
    if args.fuzzy_strategies:
        fuzzy_strategies = [s.strip() for s in args.fuzzy_strategies.split(',')]
    
    # Initialize RepoMap
    repo_map = DockerRepoMap(
        project_root=args.project_path,
        map_tokens=args.map_tokens,
        verbose=args.verbose,
        fuzzy_match=args.fuzzy_match,
        fuzzy_threshold=args.fuzzy_threshold,
        fuzzy_strategies=fuzzy_strategies,
        adaptive_semantic=args.adaptive_semantic,
        semantic_threshold=args.semantic_threshold
    )
    
    # Handle cache operations
    if args.cache_stats:
        stats = repo_map.get_cache_stats()
        print(json.dumps(stats, indent=2))
        return
    
    if args.clear_cache:
        repo_map.clear_cache()
        return
    
    # Parse dynamic parameters
    chat_files = []
    if args.chat_files:
        chat_files = [f.strip() for f in args.chat_files.split(',') if f.strip()]
    
    mentioned_fnames = set()
    if args.mentioned_files:
        mentioned_fnames = {f.strip() for f in args.mentioned_files.split(',') if f.strip()}
    
    mentioned_idents = set()
    if args.mentioned_idents:
        mentioned_idents = {i.strip() for i in args.mentioned_idents.split(',') if i.strip()}
    
    # Generate repo map
    repo_content = repo_map.generate_repo_map(
        chat_files=chat_files,
        mentioned_fnames=mentioned_fnames,
        mentioned_idents=mentioned_idents,
        force_refresh=args.force_refresh
    )
    
    if repo_content:
        # Save to file
        output_file = repo_map.save_repo_map(repo_content, args.output)
        
        if output_file:
            print(f"Repo map generated successfully: {output_file}")
            print(f"Content length: {len(repo_content)} characters")
            print(f"Estimated tokens: {len(repo_content) // 4}")
        else:
            print("Failed to save repo map")
            sys.exit(1)
    else:
        print("Failed to generate repo map")
        sys.exit(1)

if __name__ == '__main__':
    main()
