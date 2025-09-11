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
from typing import List, Dict, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import Import, FileImports, ProjectImports, ImportType

logger = logging.getLogger(__name__)


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
    """Parser for JavaScript/TypeScript import statements."""

    def extract_imports(self, file_content: str, file_path: str) -> List[Import]:
        """Extract JavaScript/TypeScript imports using regex patterns."""
        imports = []

        # Pattern for ES6 imports: import { name } from 'module'
        es6_pattern = r'import\s+(?:\{([^}]+)\}|\*|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]'

        # Pattern for CommonJS requires: const x = require('module')
        require_pattern = (
            r'(?:const|let|var)\s+\w+\s*=\s*require\s*\(\s*[\'"]([^\'"]+)[\'"]'
        )

        # Pattern for dynamic imports: import('module')
        dynamic_pattern = r'import\s*\(\s*[\'"]([^\'"]+)[\'"]'

        try:
            # Parse ES6 imports
            for match in re.finditer(es6_pattern, file_content):
                symbols_str = match.group(1)
                module = match.group(2)

                if symbols_str:
                    symbols = [s.strip() for s in symbols_str.split(",")]
                else:
                    symbols = []

                import_obj = Import(
                    module=module,
                    symbols=symbols,
                    is_relative=module.startswith("."),
                    import_type=(
                        ImportType.RELATIVE
                        if module.startswith(".")
                        else ImportType.ABSOLUTE
                    ),
                    line_number=self._get_line_number(file_content, match.start()),
                )
                imports.append(import_obj)

            # Parse CommonJS requires
            for match in re.finditer(require_pattern, file_content):
                module = match.group(1)
                import_obj = Import(
                    module=module,
                    is_relative=module.startswith("."),
                    import_type=(
                        ImportType.RELATIVE
                        if module.startswith(".")
                        else ImportType.ABSOLUTE
                    ),
                    line_number=self._get_line_number(file_content, match.start()),
                )
                imports.append(import_obj)

            # Parse dynamic imports
            for match in re.finditer(dynamic_pattern, file_content):
                module = match.group(1)
                import_obj = Import(
                    module=module,
                    is_relative=module.startswith("."),
                    import_type=(
                        ImportType.RELATIVE
                        if module.startswith(".")
                        else ImportType.ABSOLUTE
                    ),
                    line_number=self._get_line_number(file_content, match.start()),
                )
                imports.append(import_obj)

        except Exception as e:
            logger.error(f"Error parsing JavaScript file {file_path}: {e}")

        return imports

    def _get_line_number(self, content: str, position: int) -> Optional[int]:
        """Get line number for a given position in content."""
        try:
            return content[:position].count("\n") + 1
        except Exception:
            return None


class JavaImportParser(ImportParser):
    """Parser for Java import statements."""

    def extract_imports(self, file_content: str, file_path: str) -> List[Import]:
        """Extract Java imports using regex patterns."""
        imports = []

        # Pattern for Java imports: import java.util.List;
        import_pattern = r"import\s+([^;]+);"

        try:
            for match in re.finditer(import_pattern, file_content):
                module = match.group(1).strip()

                # Skip static imports for now
                if module.startswith("static "):
                    continue

                import_obj = Import(
                    module=module,
                    is_relative=False,
                    import_type=ImportType.ABSOLUTE,
                    line_number=self._get_line_number(file_content, match.start()),
                )
                imports.append(import_obj)

        except Exception as e:
            logger.error(f"Error parsing Java file {file_path}: {e}")

        return imports

    def _get_line_number(self, content: str, position: int) -> Optional[int]:
        """Get line number for a given position in content."""
        try:
            return content[:position].count("\n") + 1
        except Exception:
            return None


class GoImportParser(ImportParser):
    """Parser for Go import statements."""

    def extract_imports(self, file_content: str, file_path: str) -> List[Import]:
        """Extract Go imports using regex patterns."""
        imports = []

        # Pattern for Go imports: import "fmt"
        single_import_pattern = r'import\s+[\'"]([^\'"]+)[\'"]'

        # Pattern for grouped imports: import ( "fmt" "os" )
        grouped_import_pattern = r'import\s*\(\s*((?:[\'"][^\'"]+[\'"]\s*)+)\s*\)'

        try:
            # Parse single imports
            for match in re.finditer(single_import_pattern, file_content):
                module = match.group(1)

                import_obj = Import(
                    module=module,
                    is_relative=module.startswith("."),
                    import_type=(
                        ImportType.RELATIVE
                        if module.startswith(".")
                        else ImportType.ABSOLUTE
                    ),
                    line_number=self._get_line_number(file_content, match.start()),
                )
                imports.append(import_obj)

            # Parse grouped imports
            for match in re.finditer(grouped_import_pattern, file_content):
                imports_block = match.group(1)
                for import_match in re.finditer(r'[\'"]([^\'"]+)[\'"]', imports_block):
                    module = import_match.group(1)

                    import_obj = Import(
                        module=module,
                        is_relative=module.startswith("."),
                        import_type=(
                            ImportType.RELATIVE
                            if module.startswith(".")
                            else ImportType.ABSOLUTE
                        ),
                        line_number=self._get_line_number(file_content, match.start()),
                    )
                    imports.append(import_obj)

        except Exception as e:
            logger.error(f"Error parsing Go file {file_path}: {e}")

        return imports

    def _get_line_number(self, content: str, position: int) -> Optional[int]:
        """Get line number for a given position in content."""
        try:
            return content[:position].count("\n") + 1
        except Exception:
            return None


class ImportAnalyzer:
    """Main import analyzer that coordinates multi-language parsing."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize the import analyzer with language parsers."""
        self.project_root = project_root
        self.language_parsers: Dict[str, ImportParser] = {
            "py": PythonImportParser(),
            "js": JavaScriptImportParser(),
            "ts": JavaScriptImportParser(),  # TypeScript uses same parser
            "jsx": JavaScriptImportParser(),
            "tsx": JavaScriptImportParser(),
            "java": JavaImportParser(),
            "go": GoImportParser(),
        }

        # File extensions that should be analyzed
        self.analyzable_extensions = set(self.language_parsers.keys())

        logger.info(
            f"ImportAnalyzer initialized with {len(self.language_parsers)} language parsers for project: {self.project_root}"
        )

    def analyze_file_imports(self, file_path: str) -> FileImports:
        """Analyze a single file for imports."""

        full_path = file_path
        if self.project_root and not os.path.isabs(file_path):
            full_path = os.path.join(self.project_root, file_path)

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {full_path}")

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Get the appropriate parser
            parser = self.language_parsers[Path(file_path).suffix.lstrip(".")]
            imports = parser.extract_imports(content, file_path)

            # Resolve import paths
            resolved_imports = self._resolve_import_paths(imports, full_path)

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
        max_workers: int = 4,
        ignore_dirs: Optional[List[str]] = None,
        file_extensions: Optional[List[str]] = None,
    ) -> ProjectImports:
        """Analyze all supported files in a project for imports."""
        self.project_root = project_path  # Ensure project_root is set

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
        """Recursively get all files in a project directory, respecting .gitignore."""
        from ..core.file_scanner import parse_gitignore, should_ignore_file

        if file_extensions is None:
            file_extensions = list(self.analyzable_extensions)

        # Parse .gitignore file
        gitignore_path = Path(project_path) / ".gitignore"
        gitignore_patterns = parse_gitignore(gitignore_path)

        if gitignore_patterns:
            logger.info(
                f"Loaded {len(gitignore_patterns)} .gitignore patterns for import analysis"
            )

        all_files = []
        project_root_path = Path(project_path)

        for root, dirs, files in os.walk(project_path):
            # Filter out ignored directories using gitignore
            dirs[:] = [
                d
                for d in dirs
                if not should_ignore_file(
                    Path(root) / d, gitignore_patterns, project_root_path
                )
            ]

            for file in files:
                file_path = Path(root) / file

                # Check if file should be ignored based on gitignore
                if should_ignore_file(file_path, gitignore_patterns, project_root_path):
                    logger.debug(f"Ignoring file (gitignore): {file_path}")
                    continue

                # Check file extension
                if any(file.endswith(f".{ext}") for ext in file_extensions):
                    # Get relative path from project root
                    rel_path = file_path.relative_to(project_root_path)
                    all_files.append(str(rel_path))

        return all_files

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
