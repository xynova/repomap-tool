"""
Import-related utility functions.

This module provides utilities for working with imports, including module name
conversion, import matching, and cross-file relationship analysis.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

from .models import Import, CrossFileRelationship

logger = logging.getLogger(__name__)


class ImportUtils:
    """Utility class for import-related operations."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize import utilities.

        Args:
            project_root: Root path of the project for resolving relative imports
        """
        # Ensure project_root is always a string, not a ConfigurationOption
        self.project_root = str(project_root) if project_root is not None else None

    def file_path_to_module_name(self, file_path: str) -> Optional[str]:
        """Convert a file path to its corresponding Python module name.

        Args:
            file_path: Path to the Python file

        Returns:
            Module name or None if conversion fails
        """
        try:
            if not self.project_root:
                # Fallback to simple stem extraction if no project root
                return Path(file_path).stem

            # Convert to absolute path
            abs_file_path = Path(file_path).resolve()
            abs_project_root = Path(str(self.project_root)).resolve()

            # Check if the file is within the project root
            try:
                relative_path = abs_file_path.relative_to(abs_project_root)
            except ValueError:
                # File is not within project root
                return Path(file_path).stem

            # Convert path to module name
            module_parts = []
            is_init_file = False

            for part in relative_path.parts:
                if part == "__init__.py":
                    # Handle __init__.py files - the module is the parent directory
                    is_init_file = True
                    break
                elif part.endswith(".py"):
                    # Remove .py extension
                    module_parts.append(part[:-3])
                else:
                    module_parts.append(part)

            # Join parts with dots
            if is_init_file:
                # For __init__.py files, the module name is the parent directory path
                module_name = ".".join(module_parts)
            else:
                module_name = ".".join(module_parts)

            return module_name if module_name else None

        except Exception as e:
            logger.debug(f"Error converting file path to module name: {e}")
            return None

    def is_import_of_file(self, import_obj: Import, target_file: str) -> bool:
        """Check if an import refers to a specific file.

        Args:
            import_obj: Import object to check
            target_file: Target file path to check against

        Returns:
            True if the import refers to the target file
        """
        try:
            # Get the module name that the target file represents
            target_module = self.file_path_to_module_name(target_file)
            if not target_module:
                return False

            # Check if the import matches the target module
            import_module = import_obj.module

            # Handle exact matches
            if import_module == target_module:
                return True

            # Handle cases where the import is a parent package of the target
            # e.g., import "my_package" matches file "my_package/__init__.py"
            if target_module.startswith(import_module + "."):
                return True

            # Handle cases where the import is a submodule of the target
            # e.g., import "my_package.utils" matches file "my_package/utils.py"
            if import_module.startswith(target_module + "."):
                return True

            # Handle relative imports
            if import_obj.is_relative:
                # For relative imports, we need to resolve them relative to the importing file
                # This is more complex and would require the importing file context
                # For now, we'll do a simple check
                relative_module = import_module.lstrip(".")
                if relative_module == target_module or target_module.endswith(
                    "." + relative_module
                ):
                    return True

            return False

        except Exception as e:
            logger.debug(f"Error in _is_import_of_file: {e}")
            return False

    def find_import_relationships(
        self, source_file: str, target_files: List[str], imports: List[Import]
    ) -> List[CrossFileRelationship]:
        """Find relationships between files based on imports.

        Args:
            source_file: Source file path
            target_files: List of target file paths to check
            imports: List of imports from the source file

        Returns:
            List of CrossFileRelationship objects
        """
        relationships = []

        # Pre-compute which imports match which target files to avoid nested loops
        import_matches = {}
        for import_obj in imports:
            matching_files = []
            for target_file in target_files:
                if self.is_import_of_file(import_obj, target_file):
                    matching_files.append(target_file)
            if matching_files:
                import_matches[import_obj] = matching_files

        # Build relationships from pre-computed matches
        for import_obj, matching_files in import_matches.items():
            for target_file in matching_files:
                relationship = CrossFileRelationship(
                    source_file=source_file,
                    target_file=target_file,
                    relationship_type="import",
                    line_number=import_obj.line_number or 0,
                    details=f"Imports from {import_obj.module}",
                )
                relationships.append(relationship)

        return relationships

    def get_imported_modules(self, imports: List[Import]) -> Set[str]:
        """Get a set of all imported module names.

        Args:
            imports: List of Import objects

        Returns:
            Set of module names
        """
        return {imp.module for imp in imports if imp.module}

    def get_imported_symbols(self, imports: List[Import]) -> Set[str]:
        """Get a set of all imported symbols.

        Args:
            imports: List of Import objects

        Returns:
            Set of symbol names
        """
        symbols = set()
        for imp in imports:
            symbols.update(imp.symbols)
        return symbols

    def categorize_imports(self, imports: List[Import]) -> dict:
        """Categorize imports by type.

        Args:
            imports: List of Import objects

        Returns:
            Dictionary with categorized imports
        """
        categories: Dict[str, List[Import]] = {
            "absolute": [],
            "relative": [],
            "standard_library": [],
            "third_party": [],
            "local": [],
        }

        for imp in imports:
            if imp.is_relative:
                categories["relative"].append(imp)
            else:
                categories["absolute"].append(imp)

                # Try to categorize further (simplified)
                if imp.module and not imp.module.startswith("."):
                    if "." not in imp.module:  # Likely standard library
                        categories["standard_library"].append(imp)
                    elif self.project_root and self._is_local_module(imp.module):
                        categories["local"].append(imp)
                    else:
                        categories["third_party"].append(imp)

        return categories

    def _is_local_module(self, module_name: str) -> bool:
        """Check if a module is likely a local project module.

        Args:
            module_name: Module name to check

        Returns:
            True if the module appears to be local
        """
        if not self.project_root:
            return False

        # Simple heuristic: check if the module path exists in the project
        try:
            module_path = Path(str(self.project_root)) / module_name.replace(".", "/")
            return module_path.exists() or (module_path.with_suffix(".py")).exists()
        except Exception:
            return False
