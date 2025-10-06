#!/usr/bin/env python3
"""
Script to consolidate hardcoded configuration values across the codebase.

This script identifies and replaces common hardcoded values with calls to
the centralized configuration service.
"""

import os
import re
import sys
from pathlib import Path

# Common hardcoded values to replace
CONFIG_REPLACEMENTS = [
    # Thresholds
    (r'threshold.*=.*0\.7', 'threshold = get_config("FUZZY_THRESHOLD", 0.7)'),
    (r'threshold.*=.*0\.3', 'threshold = get_config("SEMANTIC_THRESHOLD", 0.3)'),
    (r'threshold.*=.*0\.1', 'threshold = get_config("HYBRID_THRESHOLD", 0.1)'),
    
    # Max workers
    (r'max_workers.*=.*4', 'max_workers = get_config("MAX_WORKERS", 4)'),
    
    # Timeouts
    (r'timeout.*=.*30', 'timeout = get_config("ANALYSIS_TIMEOUT", 30)'),
    (r'timeout.*=.*5', 'timeout = get_config("MIN_TIMEOUT", 5)'),
    (r'timeout.*=.*120', 'timeout = get_config("MAX_TIMEOUT", 120)'),
    
    # Limits
    (r'limit.*=.*5', 'limit = get_config("DEFAULT_LIMIT", 5)'),
    (r'limit.*=.*10', 'limit = get_config("MAX_LIMIT", 10)'),
    (r'limit.*=.*50', 'limit = get_config("MAX_RESULTS", 50)'),
    (r'limit.*=.*100', 'limit = get_config("MAX_SEARCH_RESULTS", 100)'),
    
    # Max tokens
    (r'max_tokens.*=.*4000', 'max_tokens = get_config("MAX_TOKENS", 4000)'),
    (r'max_tokens.*=.*1000', 'max_tokens = get_config("MIN_TOKENS", 1000)'),
    (r'max_tokens.*=.*8000', 'max_tokens = get_config("MAX_TOKENS_LIMIT", 8000)'),
    
    # Cache settings
    (r'cache_size.*=.*1000', 'cache_size = get_config("CACHE_SIZE", 1000)'),
    (r'ttl.*=.*3600', 'ttl = get_config("CACHE_TTL", 3600)'),
    
    # Depth settings
    (r'max_depth.*=.*3', 'max_depth = get_config("MAX_DEPTH", 3)'),
    (r'max_depth.*=.*10', 'max_depth = get_config("MAX_DEPTH_LIMIT", 10)'),
    
    # Snippet settings
    (r'max_lines.*=.*10', 'max_lines = get_config("SNIPPET_MAX_LINES", 10)'),
    (r'max_snippets.*=.*3', 'max_snippets = get_config("MAX_SNIPPETS_PER_FILE", 3)'),
    
    # PageRank settings
    (r'alpha.*=.*0\.85', 'alpha = get_config("PAGERANK_ALPHA", 0.85)'),
    (r'max_iter.*=.*100', 'max_iter = get_config("PAGERANK_MAX_ITER", 100)'),
    (r'max_iter.*=.*1000', 'max_iter = get_config("EIGENVECTOR_MAX_ITER", 1000)'),
]

def add_config_import(content: str, file_path: Path) -> str:
    """Add config service import to file content.
    
    Args:
        content: File content
        file_path: Path to the file
        
    Returns:
        Updated content with import added
    """
    # Skip if already imported
    if 'from ..core.config_service import get_config' in content:
        return content
    if 'from .config_service import get_config' in content:
        return content
    if 'get_config(' in content and 'import get_config' not in content:
        # Determine the correct import path based on file location
        if 'src/repomap_tool/core/' in str(file_path):
            import_path = 'from .config_service import get_config'
        elif 'src/repomap_tool/' in str(file_path):
            import_path = 'from ..core.config_service import get_config'
        else:
            import_path = 'from repomap_tool.core.config_service import get_config'
        
        # Add import after existing imports
        import_pattern = r'(import logging\n)'
        if re.search(import_pattern, content):
            content = re.sub(
                import_pattern,
                f'\\1{import_path}\n',
                content
            )
        else:
            # Add at the beginning if no logging import found
            content = f'{import_path}\n{content}'
    
    return content

def replace_config_in_file(file_path: Path) -> bool:
    """Replace hardcoded config values in a single file.
    
    Args:
        file_path: Path to the file to process
        
    Returns:
        True if changes were made, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = False
        
        # Apply each replacement pattern
        for pattern, replacement in CONFIG_REPLACEMENTS:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made = True
        
        # Add config import if we made changes
        if changes_made:
            content = add_config_import(content, file_path)
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False
    
    return False

def main():
    """Main function to process all Python files."""
    # Get the project root
    project_root = Path(__file__).parent.parent
    src_dir = project_root / 'src' / 'repomap_tool'
    
    if not src_dir.exists():
        print(f"Error: {src_dir} does not exist")
        sys.exit(1)
    
    # Find all Python files
    python_files = list(src_dir.rglob('*.py'))
    
    print(f"Found {len(python_files)} Python files to process")
    
    changed_files = []
    for file_path in python_files:
        if replace_config_in_file(file_path):
            changed_files.append(file_path)
            print(f"Updated: {file_path.relative_to(project_root)}")
    
    print(f"\nProcessed {len(python_files)} files")
    print(f"Updated {len(changed_files)} files")
    
    if changed_files:
        print("\nUpdated files:")
        for file_path in changed_files:
            print(f"  - {file_path.relative_to(project_root)}")

if __name__ == '__main__':
    main()
