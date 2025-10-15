"""
Import analyzer for dependency analysis.

This module provides multi-language import parsing capabilities to extract import
statements from various programming languages and build a comprehensive view of
project dependencies.
"""

import os
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
    """Parser for Python import statements using tree-sitter."""

    def __init__(self, tree_sitter_parser: Optional[Any] = None) -> None:
        """Initialize with tree-sitter parser.

        Args:
            tree_sitter_parser: TreeSitterParser instance for parsing
        """
        super().__init__()
        self.tree_sitter_parser = tree_sitter_parser

    def extract_imports(self, file_content: str, file_path: str) -> List[Import]:
        """Extract Python imports using tree-sitter parsing."""
        imports = []

        if not self.tree_sitter_parser:
            logger.warning("No tree-sitter parser available - cannot extract imports")
            return []

        try:
            # Get all tags from tree-sitter
            tags = self.tree_sitter_parser.get_tags(file_path, use_cache=True)

            # Look for import-related tags
            for tag in tags:
                # All tags are now CodeTag objects
                kind = tag.kind

                # Handle import statements
                if "import" in kind.lower():
                    # Parse import details from the tag
                    import_obj = self._parse_import_tag(tag, file_path)
                    if import_obj:
                        imports.append(import_obj)

            logger.debug(
                f"Tree-sitter extracted {len(imports)} imports from {file_path}"
            )

        except Exception as e:
            logger.error(f"Error extracting Python imports from {file_path}: {e}")
            return []

        # Log debug message if no imports found (this is normal for files without imports)
        if not imports:
            logger.debug(
                f"No imports found via tree-sitter for {file_path} - file may not contain imports"
            )

        return imports

    def _parse_import_tag(self, tag: Any, file_path: str) -> Optional[Import]:
        """Parse a single import tag into Import object.

        Args:
            tag: Tree-sitter tag (CodeTag object or dict)
            file_path: Path to the file

        Returns:
            Import object or None if parsing fails
        """
        try:
            # All tags are now CodeTag objects
            module = tag.name
            line_number = tag.line

            return Import(
                module=module,
                alias=None,
                is_relative=False,  # Simplified - could parse from tag details
                import_type=ImportType.ABSOLUTE,
                line_number=line_number,
            )
        except Exception as e:
            logger.debug(f"Error parsing import tag {tag}: {e}")
            return None


class JavaScriptImportParser(ImportParser):
    """Parser for JavaScript/TypeScript import statements using tree-sitter."""

    def __init__(self, tree_sitter_parser: Optional[Any] = None) -> None:
        """Initialize with TreeSitterParser."""
        super().__init__()
        self.tree_sitter_parser = tree_sitter_parser

    def extract_imports(self, file_content: str, file_path: str) -> List[Import]:
        """Extract JavaScript/TypeScript imports using tree-sitter parsing."""
        imports = []

        if not self.tree_sitter_parser:
            logger.warning("No tree-sitter parser available - cannot extract imports")
            return []

        try:
            # Use tree-sitter to parse the file
            tags = self.tree_sitter_parser.get_tags(file_path, use_cache=True)

            # Extract imports from tree-sitter tags
            for tag in tags:
                if tag.kind in [
                    "import.statement",
                    "import.named",
                    "import.default",
                    "import.namespace",
                    "import.type",
                    "require.statement",
                    "require.var",
                ]:
                    import_obj = self._parse_import_tag(tag, file_path)
                    if import_obj:
                        imports.append(import_obj)

        except Exception as e:
            logger.error(f"Error extracting JavaScript imports from {file_path}: {e}")
            return []

        # Log warning if tree-sitter returns no imports (might indicate query issue)
        if not imports:
            logger.warning(
                f"No imports found via tree-sitter for {file_path} - check query file"
            )

        return imports

    def _parse_import_tag(self, tag: Any, file_path: str) -> Optional[Import]:
        """Parse a single import tag from tree-sitter."""
        try:
            # All tags are now CodeTag objects
            kind = tag.get("kind")
            name = tag.get("name")
            line = tag.get("line")
            source = getattr(tag, "source", "")

            # Handle different import types
            if kind in [
                "import.statement",
                "import.named",
                "import.default",
                "import.namespace",
            ]:
                # Extract module from source
                if source:
                    module = source.strip("'\"")
                    is_relative = module.startswith(".")

                    return Import(
                        module=module,
                        is_relative=is_relative,
                        import_type=(
                            ImportType.RELATIVE if is_relative else ImportType.ABSOLUTE
                        ),
                        line_number=line or 0,
                    )

            elif kind in ["require.statement", "require.var"]:
                # Handle CommonJS requires
                if source:
                    module = source.strip("'\"")
                    is_relative = module.startswith(".")

                    return Import(
                        module=module,
                        is_relative=is_relative,
                        import_type=(
                            ImportType.RELATIVE if is_relative else ImportType.ABSOLUTE
                        ),
                        line_number=line or 0,
                    )

            return None

        except Exception as e:
            logger.error(f"Error parsing import tag: {e}")
            return None


class JavaImportParser(ImportParser):
    """Parser for Java import statements using tree-sitter."""

    def __init__(self, tree_sitter_parser: Optional[Any] = None) -> None:
        """Initialize with TreeSitterParser."""
        super().__init__()
        self.tree_sitter_parser = tree_sitter_parser

    def extract_imports(self, file_content: str, file_path: str) -> List[Import]:
        """Extract Java imports using tree-sitter parsing."""
        imports = []

        if not self.tree_sitter_parser:
            logger.warning("No tree-sitter parser available - cannot extract imports")
            return []

        try:
            # Use tree-sitter to parse the file
            tags = self.tree_sitter_parser.get_tags(file_path, use_cache=True)

            # Extract imports from tree-sitter tags
            for tag in tags:
                if tag.kind in ["import.statement", "import.static"]:
                    import_obj = self._parse_import_tag(tag, file_path)
                    if import_obj:
                        imports.append(import_obj)

        except Exception as e:
            logger.error(f"Error extracting Java imports from {file_path}: {e}")
            return []

        # Log warning if tree-sitter returns no imports (might indicate query issue)
        if not imports:
            logger.warning(
                f"No imports found via tree-sitter for {file_path} - check query file"
            )

        return imports

    def _parse_import_tag(self, tag: dict, file_path: str) -> Optional[Import]:
        """Parse a single import tag from tree-sitter."""
        try:
            kind = tag.get("kind")
            name = tag.get("name")
            line = tag.get("line")

            # Handle import statements
            if kind == "import.statement":
                # Extract module name
                if name:
                    return Import(
                        module=name,
                        symbols=[],
                        is_relative=False,  # Java imports are always absolute
                        import_type=ImportType.ABSOLUTE,
                        line_number=line or 0,
                    )

            elif kind == "import.static":
                # Handle static imports
                if name:
                    return Import(
                        module=name,
                        symbols=[],
                        is_relative=False,
                        import_type=ImportType.ABSOLUTE,
                        line_number=line or 0,
                    )

            return None

        except Exception as e:
            logger.error(f"Error parsing import tag: {e}")
            return None


class GoImportParser(ImportParser):
    """Parser for Go import statements using tree-sitter."""

    def __init__(self, tree_sitter_parser: Optional[Any] = None) -> None:
        """Initialize with TreeSitterParser."""
        super().__init__()
        self.tree_sitter_parser = tree_sitter_parser

    def extract_imports(self, file_content: str, file_path: str) -> List[Import]:
        """Extract Go imports using tree-sitter parsing."""
        imports = []

        if not self.tree_sitter_parser:
            logger.warning("No tree-sitter parser available - cannot extract imports")
            return []

        try:
            # Use tree-sitter to parse the file
            tags = self.tree_sitter_parser.get_tags(file_path, use_cache=True)

            # Extract imports from tree-sitter tags
            for tag in tags:
                if tag.kind in ["import.single", "import.grouped"]:
                    import_obj = self._parse_import_tag(tag, file_path)
                    if import_obj:
                        imports.append(import_obj)

        except Exception as e:
            logger.error(f"Error extracting Go imports from {file_path}: {e}")
            return []

        # Log warning if tree-sitter returns no imports (might indicate query issue)
        if not imports:
            logger.warning(
                f"No imports found via tree-sitter for {file_path} - check query file"
            )

        return imports

    def _parse_import_tag(self, tag: dict, file_path: str) -> Optional[Import]:
        """Parse a single import tag from tree-sitter."""
        try:
            kind = tag.get("kind")
            path = tag.get("rel_fname") or tag.get("file")
            line = tag.get("line")

            # Handle import statements
            if kind in ["import.single", "import.grouped"]:
                if path:
                    module = path.strip("'\"")
                    is_relative = module.startswith(".")

                    return Import(
                        module=module,
                        symbols=[],
                        is_relative=is_relative,
                        import_type=(
                            ImportType.RELATIVE if is_relative else ImportType.ABSOLUTE
                        ),
                        line_number=line or 0,
                    )

            return None

        except Exception as e:
            logger.error(f"Error parsing import tag: {e}")
            return None


class CSharpImportParser(ImportParser):
    """Parser for C# using directives using tree-sitter."""

    def __init__(self, tree_sitter_parser: Optional[Any] = None) -> None:
        """Initialize with TreeSitterParser."""
        super().__init__()
        self.tree_sitter_parser = tree_sitter_parser

    def extract_imports(self, file_content: str, file_path: str) -> List[Import]:
        """Extract C# using directives using tree-sitter parsing."""
        imports = []

        if not self.tree_sitter_parser:
            logger.warning("No tree-sitter parser available - cannot extract imports")
            return []

        try:
            # Use tree-sitter to parse the file
            tags = self.tree_sitter_parser.get_tags(file_path, use_cache=True)

            # Extract imports from tree-sitter tags
            for tag in tags:
                if tag.kind in [
                    "using.directive",
                    "using.static",
                    "using.alias",
                    "using.global",
                ]:
                    import_obj = self._parse_import_tag(tag, file_path)
                    if import_obj:
                        imports.append(import_obj)

        except Exception as e:
            logger.error(f"Error extracting C# imports from {file_path}: {e}")
            return []

        # Log warning if tree-sitter returns no imports (might indicate query issue)
        if not imports:
            logger.warning(
                f"No imports found via tree-sitter for {file_path} - check query file"
            )

        return imports

    def _parse_import_tag(self, tag: dict, file_path: str) -> Optional[Import]:
        """Parse a single import tag from tree-sitter."""
        try:
            kind = tag.get("kind")
            name = tag.get("name")
            line = tag.get("line")

            # Handle using directives
            if kind in [
                "using.directive",
                "using.static",
                "using.alias",
                "using.global",
            ]:
                if name:
                    return Import(
                        module=name,
                        symbols=[],
                        is_relative=False,  # C# using directives are always absolute
                        import_type=ImportType.ABSOLUTE,
                        line_number=line or 0,
                    )

            return None

        except Exception as e:
            logger.error(f"Error parsing import tag: {e}")
            return None


class ImportAnalyzer:
    """Main import analyzer that coordinates multi-language parsing."""

    def __init__(
        self,
        project_root: Optional[str] = None,
        tree_sitter_parser: Optional[Any] = None,
    ) -> None:
        """Initialize the import analyzer with language parsers."""
        # Validate required dependency
        if tree_sitter_parser is None:
            raise ValueError("TreeSitterParser must be injected - no fallback allowed")
        
        # Ensure project_root is always a string, not a ConfigurationOption
        self.project_root = str(project_root) if project_root is not None else None
        self.tree_sitter_parser = tree_sitter_parser

        # All parsers use TreeSitterParser - no regex fallbacks
        self.language_parsers: Dict[str, ImportParser] = {
            "py": PythonImportParser(tree_sitter_parser=tree_sitter_parser),
            "js": JavaScriptImportParser(tree_sitter_parser=tree_sitter_parser),
            "ts": JavaScriptImportParser(
                tree_sitter_parser=tree_sitter_parser
            ),  # TypeScript uses same parser
            "jsx": JavaScriptImportParser(tree_sitter_parser=tree_sitter_parser),
            "tsx": JavaScriptImportParser(tree_sitter_parser=tree_sitter_parser),
            "java": JavaImportParser(tree_sitter_parser=tree_sitter_parser),
            "go": GoImportParser(tree_sitter_parser=tree_sitter_parser),
            "cs": CSharpImportParser(
                tree_sitter_parser=tree_sitter_parser
            ),  # NEW: C# support
        }

        # File extensions that should be analyzed
        from .file_filter import FileFilter

        self.analyzable_extensions = FileFilter.get_analyzable_extensions()

        logger.debug(
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
            max_workers = get_config("MAX_WORKERS", 4)

        all_files = self._get_all_files(project_path, ignore_dirs, file_extensions)
        project_imports = ProjectImports(files={}, project_path=project_path)

        # Filter to only analyzable files
        analyzable_files = [
            f
            for f in all_files
            if Path(f).suffix.lstrip(".") in self.analyzable_extensions
        ]

        logger.debug(
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

        project_imports = ProjectImports(project_path=project_path, files=file_imports)

        logger.debug(
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
        from .file_discovery_service import create_file_discovery_service

        # Use centralized file discovery service
        file_discovery = create_file_discovery_service(project_path)
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
            # Check if this is a known external library that shouldn't be resolved locally
            if self._is_external_library(module):
                logger.debug(f"Skipping external library import: {module}")
                return None

            # If we have a project root, try to resolve within the project
            if self.project_root:
                project_root = Path(self.project_root)
                module_parts = module.split(".")

                # Try to find the module within the project
                for ext in self.analyzable_extensions:
                    # Try as a file: module.py
                    candidate_path = (
                        project_root
                        / "src"
                        / "/".join(module_parts)
                        / f"{module_parts[-1]}.{ext}"
                    )
                    if candidate_path.exists():
                        return candidate_path

                    # Try as a directory with __init__.py
                    candidate_dir = project_root / "src" / "/".join(module_parts)
                    init_file = candidate_dir / f"__init__.{ext}"
                    if init_file.exists():
                        return init_file

                    # Try without the last part (for imports like 'repomap_tool.cli' -> 'repomap_tool/cli/__init__.py')
                    if len(module_parts) > 1:
                        candidate_dir = (
                            project_root / "src" / "/".join(module_parts[:-1])
                        )
                        init_file = candidate_dir / f"__init__.{ext}"
                        if init_file.exists():
                            return init_file

            # Fallback: try to find the module relative to the current file
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

    def _is_external_library(self, module: str) -> bool:
        """Check if a module is a known external library that shouldn't be resolved locally."""
        # Common external libraries that should not be resolved to local files
        external_libraries = {
            "rich",
            "click",
            "typing",
            "pathlib",
            "os",
            "sys",
            "json",
            "logging",
            "collections",
            "itertools",
            "functools",
            "operator",
            "re",
            "datetime",
            "time",
            "random",
            "math",
            "statistics",
            "decimal",
            "fractions",
            "numpy",
            "pandas",
            "matplotlib",
            "requests",
            "urllib",
            "http",
            "socket",
            "threading",
            "multiprocessing",
            "asyncio",
            "concurrent",
            "subprocess",
            "shutil",
            "tempfile",
            "glob",
            "fnmatch",
            "linecache",
            "pickle",
            "copy",
            "weakref",
            "gc",
            "traceback",
            "warnings",
            "contextlib",
            "abc",
            "enum",
            "dataclasses",
            "typing_extensions",
            "pydantic",
            "fastapi",
            "flask",
            "django",
            "sqlalchemy",
            "pytest",
            "unittest",
            "doctest",
            "pdb",
            "profile",
            "cProfile",
            "timeit",
            "dis",
            "inspect",
            "ast",
            "tokenize",
            "keyword",
            "token",
            "symbol",
            "parser",
            "compiler",
            "py_compile",
            "compileall",
            "pyclbr",
            "tabnanny",
            "trace",
            "distutils",
            "setuptools",
            "pip",
            "wheel",
            "venv",
            "virtualenv",
            "conda",
            "poetry",
            "pipenv",
            "pyenv",
            "black",
            "flake8",
            "mypy",
            "pylint",
            "bandit",
            "safety",
            "coverage",
            "pytest",
            "tox",
            "pre-commit",
            "isort",
            "autopep8",
        }

        # Get the top-level module name
        top_level = module.split(".")[0]
        return top_level in external_libraries

    def _is_same_file(self, candidate_path: Path, file_dir: Path) -> bool:
        """Check if the candidate path is the same as the file being analyzed."""
        try:
            # Get the current file being analyzed from the file_dir
            # This is a bit of a hack since we don't have direct access to the current file
            # We'll check if the candidate path is in the same directory and has a common name
            # that might indicate it's the same file

            # For now, we'll be conservative and only skip if it's clearly the same file
            # This prevents the rich.console -> console.py self-reference issue
            return False  # Let's be conservative and not skip anything for now

        except Exception as e:
            logger.debug(f"Error checking if same file: {e}")
            return False

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
