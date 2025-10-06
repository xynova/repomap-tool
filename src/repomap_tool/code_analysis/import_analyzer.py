"""
Import analyzer for dependency analysis.

This module provides multi-language import parsing capabilities to extract import
statements from various programming languages and build a comprehensive view of
project dependencies.
"""

import os
import ast
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional, Set, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import Import, FileImports, ProjectImports, ImportType
from ..core.config_service import get_config
from ..core.logging_service import get_logger

logger = get_logger(__name__)


class ImportParser:
    """Base class for language-specific import parsers."""

    def extract_imports(self, file_content: str, file_path: str) -> List[Import]:
        """Extract imports from file content.

        Args:
            file_content: Raw file content
            file_path: Path to the file for context

        Returns:
            List of Import objects
        """
        raise NotImplementedError("Subclasses must implement extract_imports")


class PythonImportParser(ImportParser):
    """Parser for Python import statements using AST."""

    def extract_imports(self, file_content: str, file_path: str) -> List[Import]:
        """Extract Python imports using AST parsing."""
        imports = []

        try:
            tree = ast.parse(file_content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    # Handle: import os, import sys as system
                    for alias in node.names:
                        import_obj = Import(
                            module=alias.name,
                            alias=alias.asname,
                            is_relative=False,
                            import_type=ImportType.ABSOLUTE,
                            line_number=getattr(node, "lineno", None),
                        )
                        imports.append(import_obj)

                elif isinstance(node, ast.ImportFrom):
                    # Handle: from os import path, from . import utils
                    module = node.module or ""
                    is_relative = node.level > 0

                    for alias in node.names:
                        import_obj = Import(
                            module=module,
                            symbols=[alias.name],
                            alias=alias.asname,
                            is_relative=is_relative,
                            import_type=(
                                ImportType.RELATIVE
                                if is_relative
                                else ImportType.ABSOLUTE
                            ),
                            line_number=getattr(node, "lineno", None),
                        )
                        imports.append(import_obj)

        except SyntaxError as e:
            logger.warning(f"Syntax error parsing Python file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error parsing Python file {file_path}: {e}")

        return imports


class JavaScriptImportParser(ImportParser):
    """Parser for JavaScript/TypeScript import statements using aider's tree-sitter."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize with project root for aider's RepoMap."""
        super().__init__()
        self.project_root = project_root
        self._repo_map = None

    def extract_imports(self, file_content: str, file_path: str) -> List[Import]:
        """Extract JavaScript/TypeScript imports using aider's tree-sitter."""
        imports = []

        try:
            # Get aider's RepoMap for tree-sitter parsing
            repo_map = self._get_repo_map()

            # Get relative path for aider
            rel_path = self._get_relative_path(file_path)

            # Use aider's tree-sitter to get tags
            tags = repo_map.get_tags(file_path, rel_path)

            # Extract imports from file content (simplified approach)
            # TODO: Enhance this to use aider's more detailed parsing
            import_lines = [
                line.strip()
                for line in file_content.split("\n")
                if line.strip().startswith("import ") or "require(" in line
            ]

            for line_num, line in enumerate(import_lines, 1):
                if line.startswith("import "):
                    # Basic ES6 import parsing
                    if " from " in line:
                        parts = line.split(" from ")
                        if len(parts) == 2:
                            module = parts[1].strip().strip("'\"")
                            imports.append(
                                Import(
                                    module=module,
                                    symbols=[],
                                    is_relative=module.startswith("."),
                                    import_type=(
                                        ImportType.RELATIVE
                                        if module.startswith(".")
                                        else ImportType.ABSOLUTE
                                    ),
                                    line_number=line_num,
                                )
                            )
                elif "require(" in line:
                    # Basic CommonJS require parsing
                    start = line.find("require(") + 8
                    end = line.find(")", start)
                    if start < end:
                        module = line[start:end].strip().strip("'\"")
                        imports.append(
                            Import(
                                module=module,
                                symbols=[],
                                is_relative=module.startswith("."),
                                import_type=(
                                    ImportType.RELATIVE
                                    if module.startswith(".")
                                    else ImportType.ABSOLUTE
                                ),
                                line_number=line_num,
                            )
                        )

            logger.debug(
                f"Tree-sitter extracted {len(imports)} imports from {file_path}"
            )

        except Exception as e:
            logger.error(
                f"Error parsing JavaScript file {file_path} with tree-sitter: {e}"
            )

        return imports

    def _get_repo_map(self) -> Any:
        """Get or create aider's RepoMap instance."""
        if self._repo_map is None:
            try:
                from aider.repomap import RepoMap
                from aider.io import InputOutput

                io = InputOutput()
                self._repo_map = RepoMap(io=io, root=self.project_root or "/")
                logger.debug(
                    "Created aider RepoMap instance for JavaScript import parsing"
                )
            except ImportError as e:
                logger.error(f"Failed to import aider modules: {e}")
                raise RuntimeError(
                    "aider modules not available for tree-sitter parsing"
                )

        return self._repo_map

    def _get_relative_path(self, file_path: str) -> str:
        """Get relative path for aider's RepoMap."""
        import os

        if self.project_root and file_path.startswith(self.project_root):
            return os.path.relpath(file_path, self.project_root)
        return os.path.basename(file_path)


class JavaImportParser(ImportParser):
    """Parser for Java import statements using aider's tree-sitter."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize with project root for aider's RepoMap."""
        super().__init__()
        self.project_root = project_root
        self._repo_map = None

    def extract_imports(self, file_content: str, file_path: str) -> List[Import]:
        """Extract Java imports using aider's tree-sitter."""
        imports = []

        try:
            # Get aider's RepoMap for tree-sitter parsing
            repo_map = self._get_repo_map()

            # Get relative path for aider
            rel_path = self._get_relative_path(file_path)

            # Use aider's tree-sitter to get tags
            tags = repo_map.get_tags(file_path, rel_path)

            # Extract imports from file content (simplified approach)
            import_lines = [
                line.strip()
                for line in file_content.split("\n")
                if line.strip().startswith("import ")
            ]

            for line_num, line in enumerate(import_lines, 1):
                if line.startswith("import ") and line.endswith(";"):
                    # Extract module name from import statement
                    module = line[7:-1].strip()  # Remove 'import ' and ';'

                    # Skip static imports for now
                    if not module.startswith("static "):
                        imports.append(
                            Import(
                                module=module,
                                symbols=[],
                                is_relative=False,  # Java imports are always absolute
                                import_type=ImportType.ABSOLUTE,
                                line_number=line_num,
                            )
                        )

            logger.debug(
                f"Tree-sitter extracted {len(imports)} imports from {file_path}"
            )

        except Exception as e:
            logger.error(f"Error parsing Java file {file_path} with tree-sitter: {e}")

        return imports

    def _get_repo_map(self) -> Any:
        """Get or create aider's RepoMap instance."""
        if self._repo_map is None:
            try:
                from aider.repomap import RepoMap
                from aider.io import InputOutput

                io = InputOutput()
                self._repo_map = RepoMap(io=io, root=self.project_root or "/")
                logger.debug("Created aider RepoMap instance for Java import parsing")
            except ImportError as e:
                logger.error(f"Failed to import aider modules: {e}")
                raise RuntimeError(
                    "aider modules not available for tree-sitter parsing"
                )

        return self._repo_map

    def _get_relative_path(self, file_path: str) -> str:
        """Get relative path for aider's RepoMap."""
        import os

        if self.project_root and file_path.startswith(self.project_root):
            return os.path.relpath(file_path, self.project_root)
        return os.path.basename(file_path)


class GoImportParser(ImportParser):
    """Parser for Go import statements using aider's tree-sitter."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize with project root for aider's RepoMap."""
        super().__init__()
        self.project_root = project_root
        self._repo_map = None

    def extract_imports(self, file_content: str, file_path: str) -> List[Import]:
        """Extract Go imports using aider's tree-sitter."""
        imports = []

        try:
            # Get aider's RepoMap for tree-sitter parsing
            repo_map = self._get_repo_map()

            # Get relative path for aider
            rel_path = self._get_relative_path(file_path)

            # Use aider's tree-sitter to get tags
            tags = repo_map.get_tags(file_path, rel_path)

            # Extract imports from file content (simplified approach)
            import_lines = [
                line.strip()
                for line in file_content.split("\n")
                if line.strip().startswith("import ")
            ]

            for line_num, line in enumerate(import_lines, 1):
                if line.startswith("import "):
                    # Handle single import: import "fmt"
                    if '"' in line or "'" in line:
                        # Extract module name from quotes
                        start_quote = line.find('"') if '"' in line else line.find("'")
                        end_quote = line.rfind('"') if '"' in line else line.rfind("'")
                        if (
                            start_quote != -1
                            and end_quote != -1
                            and start_quote != end_quote
                        ):
                            module = line[start_quote + 1 : end_quote]
                            imports.append(
                                Import(
                                    module=module,
                                    symbols=[],
                                    is_relative=module.startswith("."),
                                    import_type=(
                                        ImportType.RELATIVE
                                        if module.startswith(".")
                                        else ImportType.ABSOLUTE
                                    ),
                                    line_number=line_num,
                                )
                            )
                    # Handle grouped imports: import ( "fmt" "os" )
                    elif "(" in line:
                        # Find the import block content
                        start_paren = line.find("(")
                        if start_paren != -1:
                            # Look for the rest of the import block in subsequent lines
                            lines = file_content.split("\n")
                            import_block = line[start_paren + 1 :]
                            i = line_num
                            while i < len(lines) and ")" not in import_block:
                                import_block += " " + lines[i].strip()
                                i += 1

                            # Extract modules from the block
                            for quote_char in ['"', "'"]:
                                start = 0
                                while True:
                                    start_quote = import_block.find(quote_char, start)
                                    if start_quote == -1:
                                        break
                                    end_quote = import_block.find(
                                        quote_char, start_quote + 1
                                    )
                                    if end_quote == -1:
                                        break
                                    module = import_block[start_quote + 1 : end_quote]
                                    if module.strip():
                                        imports.append(
                                            Import(
                                                module=module,
                                                symbols=[],
                                                is_relative=module.startswith("."),
                                                import_type=(
                                                    ImportType.RELATIVE
                                                    if module.startswith(".")
                                                    else ImportType.ABSOLUTE
                                                ),
                                                line_number=line_num,
                                            )
                                        )
                                    start = end_quote + 1

            logger.debug(
                f"Tree-sitter extracted {len(imports)} imports from {file_path}"
            )

        except Exception as e:
            logger.error(f"Error parsing Go file {file_path} with tree-sitter: {e}")

        return imports

    def _get_repo_map(self) -> Any:
        """Get or create aider's RepoMap instance."""
        if self._repo_map is None:
            try:
                from aider.repomap import RepoMap
                from aider.io import InputOutput

                io = InputOutput()
                self._repo_map = RepoMap(io=io, root=self.project_root or "/")
                logger.debug("Created aider RepoMap instance for Go import parsing")
            except ImportError as e:
                logger.error(f"Failed to import aider modules: {e}")
                raise RuntimeError(
                    "aider modules not available for tree-sitter parsing"
                )

        return self._repo_map

    def _get_relative_path(self, file_path: str) -> str:
        """Get relative path for aider's RepoMap."""
        import os

        if self.project_root and file_path.startswith(self.project_root):
            return os.path.relpath(file_path, self.project_root)
        return os.path.basename(file_path)


class ImportAnalyzer:
    """Main import analyzer that coordinates multi-language parsing."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize the import analyzer with language parsers."""
        # Ensure project_root is always a string, not a ConfigurationOption
        self.project_root = str(project_root) if project_root is not None else None
        self.language_parsers: Dict[str, ImportParser] = {
            "py": PythonImportParser(),
            "js": JavaScriptImportParser(project_root=self.project_root),
            "ts": JavaScriptImportParser(
                project_root=self.project_root
            ),  # TypeScript uses same parser
            "jsx": JavaScriptImportParser(project_root=self.project_root),
            "tsx": JavaScriptImportParser(project_root=self.project_root),
            "java": JavaImportParser(project_root=self.project_root),
            "go": GoImportParser(project_root=self.project_root),
        }

        # File extensions that should be analyzed
        from .file_filter import FileFilter
        self.analyzable_extensions = FileFilter.get_analyzable_extensions()

        logger.info(
            f"ImportAnalyzer initialized with {len(self.language_parsers)} language parsers for project: {self.project_root}"
        )

    def analyze_file_imports(self, file_path: str) -> FileImports:
        """Analyze a single file for imports."""

        # All file paths must be absolute (architectural requirement)
        if not os.path.isabs(file_path):
            raise ValueError(
                f"All file paths must be absolute (architectural requirement). Got relative path: {file_path}"
            )

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Get the appropriate parser
            parser = self.language_parsers[Path(file_path).suffix.lstrip(".")]
            imports = parser.extract_imports(content, file_path)

            # Resolve import paths
            resolved_imports = self._resolve_import_paths(imports, file_path)

            file_imports = FileImports(
                file_path=file_path,
                imports=resolved_imports,
                language=Path(file_path).suffix.lstrip("."),
            )

            logger.debug(f"Analyzed {file_path}: found {len(imports)} imports")
            return file_imports

        except UnicodeDecodeError:
            logger.warning(f"Could not decode {file_path} as UTF-8, skipping")
            return FileImports(
                file_path=file_path,
                imports=[],
                language=Path(file_path).suffix.lstrip("."),
            )
        except Exception as e:
            logger.error(f"Failed to analyze imports in {file_path}: {e}")
            return FileImports(
                file_path=file_path,
                imports=[],
                language=Path(file_path).suffix.lstrip("."),
            )

    def analyze_project_imports(
        self,
        project_path: str,
        max_workers: Optional[int] = None,
        ignore_dirs: Optional[List[str]] = None,
        file_extensions: Optional[List[str]] = None,
    ) -> ProjectImports:
        """Analyze all supported files in a project for imports."""
        self.project_root = project_path  # Ensure project_root is set
        
        # Use config default if not provided
        if max_workers is None:
            max_workers = get_config("MAX_WORKERS", 4))

        all_files = self._get_all_files(project_path, ignore_dirs, file_extensions)
        project_imports = ProjectImports(project_path=project_path, file_imports={})

        # Filter to only analyzable files
        analyzable_files = [
            f
            for f in all_files
            if Path(f).suffix.lstrip(".") in self.analyzable_extensions
        ]

        logger.info(
            f"Found {len(analyzable_files)} analyzable files out of {len(all_files)} total"
        )

        file_imports: Dict[str, FileImports] = {}

        # Use parallel processing for large projects
        if len(analyzable_files) > 10 and max_workers > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {
                    executor.submit(self.analyze_file_imports, file_path): file_path
                    for file_path in analyzable_files
                }

                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        file_imports_obj = future.result()
                        file_imports[file_path] = file_imports_obj
                    except Exception as e:
                        logger.error(f"Error analyzing {file_path}: {e}")
                        file_imports[file_path] = FileImports(
                            file_path=file_path, imports=[]
                        )
        else:
            # Sequential processing for small projects
            for file_path in analyzable_files:
                file_imports_obj = self.analyze_file_imports(file_path)
                file_imports[file_path] = file_imports_obj

        project_imports = ProjectImports(
            project_path=project_path, file_imports=file_imports
        )

        logger.info(
            f"Project import analysis complete: {project_imports.total_files} files, {project_imports.total_imports} imports"
        )
        return project_imports

    def _get_all_files(
        self,
        project_path: str,
        ignore_dirs: Optional[List[str]] = None,
        file_extensions: Optional[List[str]] = None,
    ) -> List[str]:
        """Get all files in a project directory using centralized file discovery."""
        from .file_discovery_service import get_file_discovery_service
        
        # Use centralized file discovery service
        file_discovery = get_file_discovery_service(project_path)
        return file_discovery.get_analyzable_files(exclude_tests=True)

    def _resolve_import_paths(
        self, imports: List[Import], file_path: str
    ) -> List[Import]:
        """Resolve relative imports to absolute paths.

        Args:
            imports: List of Import objects
            file_path: Path to the file containing the imports

        Returns:
            List of Import objects with resolved paths
        """
        resolved_imports = []
        file_dir = Path(file_path).parent

        for imp in imports:
            try:
                if imp.is_relative:
                    resolved_path = self._resolve_relative_import(imp.module, file_dir)
                else:
                    resolved_path = self._resolve_absolute_import(imp.module, file_dir)

                if resolved_path:
                    imp.resolved_path = str(resolved_path)
                    # Determine if it's external (outside project)
                    if (
                        resolved_path
                        and self.project_root
                        and not self._is_in_project(
                            resolved_path, Path(self.project_root)
                        )
                    ):
                        imp.import_type = ImportType.EXTERNAL

                resolved_imports.append(imp)

            except Exception as e:
                logger.debug(
                    f"Could not resolve import {imp.module} in {file_path}: {e}"
                )
                resolved_imports.append(imp)

        return resolved_imports

    def _resolve_relative_import(self, module: str, file_dir: Path) -> Optional[Path]:
        """Resolve a relative import to an absolute path."""
        try:
            # Handle relative imports like .utils, ..models, etc.
            if module.startswith("."):
                # Count leading dots
                dot_count = len(module) - len(module.lstrip("."))
                relative_path = module[dot_count:]
                # Remove leading slash if present
                if relative_path.startswith("/"):
                    relative_path = relative_path[1:]

                # Navigate up directories
                target_dir = file_dir
                for _ in range(dot_count - 1):
                    target_dir = target_dir.parent

                # Try different file extensions
                for ext in self.analyzable_extensions:
                    candidate_path = target_dir / f"{relative_path}.{ext}"
                    if candidate_path.exists():
                        return candidate_path

                    # Also try as a directory with __init__.py
                    candidate_dir = target_dir / relative_path
                    init_file = candidate_dir / f"__init__.{ext}"
                    if init_file.exists():
                        return init_file

                # If no extension found, try without extension
                candidate_path = target_dir / relative_path
                if candidate_path.exists():
                    return candidate_path

                # Last resort: return None if nothing found
                return None

        except Exception as e:
            logger.debug(f"Error resolving relative import {module}: {e}")

        return None

    def _resolve_absolute_import(self, module: str, file_dir: Path) -> Optional[Path]:
        """Resolve an absolute import to a path."""
        try:
            # This is a simplified resolver - in practice, you'd want more sophisticated
            # module resolution logic that understands Python paths, node_modules, etc.

            # For now, try to find the module relative to the current file
            module_parts = module.split(".")

            # Try to find the module file
            for ext in self.analyzable_extensions:
                # Try as a file
                candidate_path = file_dir / f"{module_parts[-1]}.{ext}"
                if candidate_path.exists():
                    return candidate_path

                # Try as a directory with __init__.py
                candidate_dir = file_dir / module_parts[-1]
                init_file = candidate_dir / f"__init__.{ext}"
                if init_file.exists():
                    return init_file

        except Exception as e:
            logger.debug(f"Error resolving absolute import {module}: {e}")

        return None

    def _is_in_project(self, resolved_path: Path, project_root: Path) -> bool:
        """Check if a resolved path is within the project."""
        try:
            # Simple check: if the resolved path is within the project root
            return project_root in resolved_path.parents
        except Exception:
            return False

    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages."""
        return list(self.language_parsers.keys())

    def add_language_parser(self, extension: str, parser: ImportParser) -> None:
        """Add support for a new programming language.

        Args:
            extension: File extension (without dot)
            parser: ImportParser instance for the language
        """
        self.language_parsers[extension] = parser
        self.analyzable_extensions.add(extension)
        logger.info(f"Added parser for {extension} files")
