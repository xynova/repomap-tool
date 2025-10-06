#!/usr/bin/env python3
"""
Script to consolidate logging setup across the codebase.

This script replaces all instances of `logging.getLogger(__name__)` with
`get_logger(__name__)` from the centralized logging service.
"""

import os
import re
import sys
from pathlib import Path

def replace_logging_in_file(file_path: Path) -> bool:
    """Replace logging setup in a single file.
    
    Args:
        file_path: Path to the file to process
        
    Returns:
        True if changes were made, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Skip files that already use the centralized logging
        if 'from ..core.logging_service import get_logger' in content:
            return False
        if 'from .logging_service import get_logger' in content:
            return False
        if 'get_logger(__name__)' in content:
            return False
            
        # Replace logger = logging.getLogger(__name__) with logger = get_logger(__name__)
        content = re.sub(
            r'logger = logging\.getLogger\(__name__\)',
            'logger = get_logger(__name__)',
            content
        )
        
        # Add import for get_logger if we made changes
        if content != original_content:
            # Determine the correct import path based on file location
            if 'src/repomap_tool/core/' in str(file_path):
                import_path = 'from .logging_service import get_logger'
            elif 'src/repomap_tool/' in str(file_path):
                import_path = 'from ..core.logging_service import get_logger'
            else:
                import_path = 'from repomap_tool.core.logging_service import get_logger'
            
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
        if replace_logging_in_file(file_path):
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
