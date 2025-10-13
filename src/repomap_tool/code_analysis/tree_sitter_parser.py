#!/usr/bin/env python3
"""
Tree-sitter parser for multi-language code analysis.

This module provides direct access to tree-sitter parsing capabilities,
bypassing aider's filtering to get detailed tag information including
imports, function calls, and definitions.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from grep_ast import filename_to_lang
from grep_ast.tsl import get_language, get_parser

from repomap_tool.core.logging_service import get_logger

logger = get_logger(__name__)


class TreeSitterParser:
    """Universal tree-sitter parser for all languages."""

    def __init__(
        self,
        project_root: Optional[str] = None,
        custom_queries_dir: Optional[str] = None,
    ):
        """Initialize the tree-sitter parser.

        Args:
            project_root: Root directory of the project for relative path resolution
            custom_queries_dir: Directory containing custom query files (.scm).
                              Defaults to code_analysis/queries/ directory
        """
        self.project_root = project_root or "."
        self._query_cache: Dict[str, str] = {}

        # Set custom queries directory - use package resources for reliable access
        if custom_queries_dir is None:
            # Try to use package resources first (works in Docker)
            try:
                import pkg_resources
                self.custom_queries_dir = Path(pkg_resources.resource_filename(
                    "repomap_tool.code_analysis", "queries"
                ))
                logger.debug(f"Using package resource queries directory: {self.custom_queries_dir}")
                # Verify the directory exists and has query files
                if not self.custom_queries_dir.exists():
                    raise FileNotFoundError(f"Package resource directory does not exist: {self.custom_queries_dir}")
                query_files = list(self.custom_queries_dir.glob("*.scm"))
                if not query_files:
                    raise FileNotFoundError(f"No .scm query files found in: {self.custom_queries_dir}")
                logger.debug(f"Found {len(query_files)} query files in package resources")
            except Exception as e:
                logger.debug(f"Could not use package resources for queries: {e}")
                # Fallback to file-based path
                self.custom_queries_dir = Path(__file__).parent / "queries"
                logger.debug(f"Using file-based queries directory: {self.custom_queries_dir}")
                # Verify fallback directory
                if not self.custom_queries_dir.exists():
                    logger.warning(f"Fallback queries directory does not exist: {self.custom_queries_dir}")
        else:
            self.custom_queries_dir = Path(custom_queries_dir)

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse file and return ALL tree-sitter tags (unfiltered).

        Args:
            file_path: Path to the file to parse

        Returns:
            List of tag dictionaries with detailed information
        """
        try:
            # Get language for the file
            lang = filename_to_lang(file_path)
            if not lang:
                logger.debug(f"No language detected for {file_path}")
                return []

            # Get parser and language
            parser = get_parser(lang)
            language = get_language(lang)

            # Load query file
            query_scm = self._load_query(lang)
            if not query_scm:
                logger.warning(f"No query file found for language: {lang}")
                return []

            # Read file content
            code = self._read_file(file_path)
            if not code:
                logger.warning(f"Could not read file: {file_path}")
                return []

            # Parse with tree-sitter
            tree = parser.parse(bytes(code, "utf-8"))
            query = language.query(query_scm)
            captures = query.captures(tree.root_node)

            # Extract ALL tags WITHOUT filtering
            tags = []

            # Handle different capture formats
            if hasattr(captures, "items"):
                # Dictionary format: {tag_name: [nodes]}
                for tag_kind, nodes in captures.items():
                    for node in nodes:
                        tags.append(
                            {
                                "name": node.text.decode("utf-8"),
                                "kind": tag_kind,  # Keep full kind: name.definition.class, etc.
                                "line": node.start_point[0]
                                + 1,  # Convert to 1-based line numbers
                                "column": node.start_point[1],
                                "file": file_path,
                                "end_line": node.end_point[0] + 1,
                                "end_column": node.end_point[1],
                            }
                        )
            else:
                # List format: [(node, tag_kind), ...]
                for capture in captures:
                    if len(capture) == 2:
                        node, tag_kind = capture
                        tags.append(
                            {
                                "name": node.text.decode("utf-8"),
                                "kind": tag_kind,  # Keep full kind: name.definition.class, etc.
                                "line": node.start_point[0]
                                + 1,  # Convert to 1-based line numbers
                                "column": node.start_point[1],
                                "file": file_path,
                                "end_line": node.end_point[0] + 1,
                                "end_column": node.end_point[1],
                            }
                        )
                    else:
                        logger.debug(f"Unexpected capture format: {capture}")

            logger.debug(f"Parsed {len(tags)} tags from {file_path}")
            
            # Associate comments with code elements
            tags_with_comments = self._associate_comments_with_code(tags, tree.root_node, code)
            return tags_with_comments

        except Exception as e:
            logger.error(f"Error parsing file {file_path} with tree-sitter: {e}")
            return []

    def _load_query(self, lang: str) -> Optional[str]:
        """Load the .scm query file for this language.

        Args:
            lang: Language identifier

        Returns:
            Query string or None if not found
        """
        if lang in self._query_cache:
            return self._query_cache[lang]

        logger.debug(f"Loading query for language: {lang}")
        logger.debug(f"Custom queries directory: {self.custom_queries_dir}")

        # 1. Check custom queries directory FIRST
        custom_query_path = self.custom_queries_dir / f"{lang}-tags.scm"
        logger.debug(f"Looking for custom query at: {custom_query_path}")
        if custom_query_path.exists():
            try:
                query_content = custom_query_path.read_text()
                self._query_cache[lang] = query_content
                logger.debug(f"Using custom query file: {custom_query_path}")
                return query_content
            except Exception as e:
                logger.debug(f"Could not load custom query for {lang}: {e}")
        else:
            logger.debug(f"Custom query file does not exist: {custom_query_path}")

        # 2. Fall back to aider's query files
        try:
            from aider.queries import get_scm_fname

            query_path = get_scm_fname(lang)
            logger.debug(f"Looking for aider query at: {query_path}")
            if query_path and query_path.exists():
                query_content = query_path.read_text()
                self._query_cache[lang] = query_content
                logger.debug(f"Using aider query file: {query_path}")
                return str(query_content)
        except Exception as e:
            logger.debug(f"Could not load aider query for {lang}: {e}")

        # 3. Fallback: try to find query files directly
        try:
            import pkg_resources

            query_path = pkg_resources.resource_filename(
                "aider.queries.tree-sitter-language-pack", f"{lang}-tags.scm"
            )
            logger.debug(f"Looking for pkg_resources query at: {query_path}")
            if os.path.exists(query_path):
                with open(query_path, "r") as f:
                    query_content = f.read()
                    self._query_cache[lang] = query_content
                    logger.debug(f"Using pkg_resources query file: {query_path}")
                    return query_content
        except Exception as e:
            logger.debug(f"Could not load pkg_resources query for {lang}: {e}")

        logger.warning(f"No query file found for language: {lang}")
        return None

    def _associate_comments_with_code(self, tags: List[Dict], root_node: Any, code: str) -> List[Dict]:
        """Associate comments with nearest code elements.
        
        Args:
            tags: List of parsed tags
            root_node: Tree-sitter root node
            code: Source code content
            
        Returns:
            Tags with associated comments
        """
        try:
            # Find all comment nodes in the tree
            comment_nodes = []
            self._find_comment_nodes(root_node, comment_nodes)
            
            # Associate comments with nearest code elements
            for tag in tags:
                tag['comment'] = self._find_nearest_comment(tag, comment_nodes, code)
            
            return tags
        except Exception as e:
            logger.warning(f"Error associating comments: {e}")
            return tags

    def _find_comment_nodes(self, node: Any, comment_nodes: List[Dict]) -> None:
        """Recursively find all comment nodes in the tree.
        
        Args:
            node: Current tree-sitter node
            comment_nodes: List to store comment nodes
        """
        try:
            if hasattr(node, 'type') and node.type in ['comment', 'line_comment', 'block_comment']:
                comment_text = node.text.decode('utf-8') if hasattr(node, 'text') else ""
                comment_nodes.append({
                    'text': comment_text,
                    'line': node.start_point[0] + 1,
                    'column': node.start_point[1],
                    'end_line': node.end_point[0] + 1,
                    'end_column': node.end_point[1]
                })
            
            # Recursively check children
            if hasattr(node, 'children'):
                for child in node.children:
                    self._find_comment_nodes(child, comment_nodes)
        except Exception as e:
            logger.debug(f"Error finding comment nodes: {e}")

    def _find_nearest_comment(self, tag: Dict, comment_nodes: List[Dict], code: str) -> Optional[str]:
        """Find the nearest comment for a code element.
        
        Args:
            tag: Code element tag
            comment_nodes: List of comment nodes
            code: Source code content
            
        Returns:
            Associated comment text or None
        """
        try:
            tag_line = tag.get('line', 0)
            if tag_line <= 0:
                return None
            
            # Find comments within 5 lines before the tag
            nearest_comment = None
            min_distance = float('inf')
            
            for comment in comment_nodes:
                comment_line = comment.get('line', 0)
                if comment_line <= 0:
                    continue
                
                # Only consider comments before the tag (within 5 lines)
                if comment_line < tag_line and (tag_line - comment_line) <= 5:
                    distance = tag_line - comment_line
                    if distance < min_distance:
                        min_distance = distance
                        nearest_comment = comment
            
            if nearest_comment:
                # Clean comment text
                comment_text = nearest_comment['text'].strip()
                # Remove comment markers
                comment_text = self._clean_comment_text(comment_text)
                return comment_text if comment_text else None
            
            return None
        except Exception as e:
            logger.debug(f"Error finding nearest comment: {e}")
            return None

    def _clean_comment_text(self, comment_text: str) -> str:
        """Clean comment text by removing markers.
        
        Args:
            comment_text: Raw comment text
            
        Returns:
            Cleaned comment text
        """
        try:
            # Remove common comment markers
            comment_text = comment_text.strip()
            
            # Python: # comment
            if comment_text.startswith('#'):
                comment_text = comment_text[1:].strip()
            
            # JavaScript/Java: // comment
            elif comment_text.startswith('//'):
                comment_text = comment_text[2:].strip()
            
            # Block comments: /* comment */
            elif comment_text.startswith('/*') and comment_text.endswith('*/'):
                comment_text = comment_text[2:-2].strip()
            
            # JSDoc: /** comment */
            elif comment_text.startswith('/**') and comment_text.endswith('*/'):
                comment_text = comment_text[3:-2].strip()
                # Remove JSDoc markers
                comment_text = comment_text.replace('*', '').strip()
            
            return comment_text
        except Exception as e:
            logger.debug(f"Error cleaning comment text: {e}")
            return comment_text

    def _read_file(self, file_path: str) -> Optional[str]:
        """Read file content safely.

        Args:
            file_path: Path to the file

        Returns:
            File content or None if error
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages.

        Returns:
            List of supported language identifiers
        """
        # Common languages supported by tree-sitter
        return [
            "python",
            "javascript",
            "typescript",
            "java",
            "go",
            "rust",
            "cpp",
            "c",
            "csharp",
            "php",
            "ruby",
            "swift",
            "kotlin",
            "scala",
            "haskell",
            "ocaml",
            "elixir",
            "clojure",
            "lua",
        ]

    def is_language_supported(self, file_path: str) -> bool:
        """Check if a file's language is supported.

        Args:
            file_path: Path to the file

        Returns:
            True if language is supported
        """
        lang = filename_to_lang(file_path)
        return lang is not None and self._load_query(lang) is not None
