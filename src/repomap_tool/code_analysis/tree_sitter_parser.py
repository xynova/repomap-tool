#!/usr/bin/env python3
"""
Tree-sitter parser for multi-language code analysis.

This module provides direct access to tree-sitter parsing capabilities,
providing detailed tag information including
imports, function calls, and definitions.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import tree_sitter
from grep_ast.tsl import get_language, get_parser
from grep_ast.parsers import filename_to_lang
from repomap_tool.code_analysis.models import CodeTag
from repomap_tool.protocols import QueryLoaderProtocol, TagCacheProtocol

from repomap_tool.core.logging_service import get_logger

logger = get_logger(__name__)
logger.debug("Attempting to import tree_sitter at module level.")


class TreeSitterParser:
    """Universal tree-sitter parser for all languages."""

    def __init__(
        self,
        project_root: Path,
        cache: TagCacheProtocol,
        query_loader: QueryLoaderProtocol,
    ):
        """Initialize the tree-sitter parser.

        Args:
            project_root: Root directory of the project for relative path resolution
            cache: Optional cache for tags.
            query_loader: An instance of QueryLoaderProtocol to load query strings.
        """
        if not project_root.is_absolute():
            raise ValueError("project_root must be an absolute path.")
        if cache is None:
            raise ValueError("Cache must be injected and cannot be None.")
        if query_loader is None:
            raise ValueError("QueryLoader must be injected and cannot be None.")

        self.project_root = project_root
        self._query_cache: Dict[str, str] = {}
        self.tag_cache = cache
        self.query_loader = query_loader

        # The custom_queries_dir is now managed by the QueryLoader, no need here.
        # The initial_query_string parameter is also removed.

    def _parse_file(self, file_path: str) -> List[CodeTag]:
        """Internal method for raw tree-sitter parsing without caching.

        Args:
            file_path: Path to the file to parse

        Returns:
            List of CodeTag objects
        """
        try:
            # Get language for the file
            lang = filename_to_lang(file_path)
            logger.debug(f"_parse_file: Detected language: {lang} for file: {file_path}")
            if not lang:
                logger.debug(f"No language detected for {file_path}")
                return []

            # Get parser and language
            parser = get_parser(lang)
            language = get_language(lang)
            logger.debug(f"_parse_file: Retrieved parser and language for {lang}. Language object: {language}")

            # Load query file using the injected QueryLoader
            query_scm = self.query_loader.load_query(lang)
            logger.debug(f"_parse_file: Loaded query SCM for {lang}. Query length: {len(query_scm) if query_scm else 0}")

            if not query_scm:
                logger.warning(f"_parse_file: No query SCM found for language {lang}.")
                return []

            logger.debug(f"_parse_file: Query SCM for {lang}:\n{query_scm}")

            query = tree_sitter.Query(language, query_scm)
            logger.debug(f"_parse_file: Successfully created query for {lang}.")

            # Read file content
            code_content = self._read_file(file_path)
            logger.debug(f"_parse_file: Read file content for {file_path}. Content length: {len(code_content) if code_content else 0}")
            if not code_content:
                logger.warning(f"_parse_file: Could not read file: {file_path}")
                return []

            # Parse with tree-sitter
            tree = parser.parse(bytes(code_content, "utf-8"))
            logger.debug(f"_parse_file: Parsed file into tree for {file_path}. Root node: {tree.root_node.type}")

            query_cursor = tree_sitter.QueryCursor(query)
            logger.debug(f"_parse_file: Created tree_sitter.QueryCursor object.")
            captures = query_cursor.captures(tree.root_node)
            logger.debug(f"_parse_file: QueryCursor.captures returned {len(list(captures))} entries.") # Convert to list for accurate count, but keep original iterable for the loop
            # print(f"DEBUG: Type of captures: {type(captures)}") # Removed debug print
            # print(f"DEBUG: First few captures: {list(captures)[:5]}") # Removed debug print
            tags = []

            # Process captures dictionary
            if isinstance(captures, dict):
                for tag_kind, nodes in captures.items():
                    logger.debug(f"_parse_file: Processing tag_kind: {tag_kind} with {len(nodes)} nodes.")
                    for node in nodes:
                        tags.append(
                            CodeTag(
                                name=node.text.decode("utf-8"),
                                kind=tag_kind,
                                line=node.start_point[0] + 1,
                                column=node.start_point[1],
                                file=file_path,
                                end_line=node.end_point[0] + 1,
                                end_column=node.end_point[1],
                            )
                        )
            else:
                logger.warning(f"_parse_file: Unexpected captures type: {type(captures)}. Expected dict.")

            logger.debug(f"_parse_file: Extracted {len(tags)} CodeTags from {file_path}")
            return tags

        except Exception as e:
            logger.error(f"Error parsing file {file_path} with tree-sitter: {e}")
            return []

    def get_tags(self, file_path: str, use_cache: bool = True) -> List[CodeTag]:
        """Get tags for a file, using cache if available

        Args:
            file_path: Path to the file to get tags for
            use_cache: Whether to use cache if available

        Returns:
            List of CodeTag objects
        """
        if use_cache and self.tag_cache:
            cached_tags = self.tag_cache.get_tags(file_path)
            if cached_tags is not None:
                logger.debug(f"Using cached tags for {file_path}")
                # Ensure cached_tags is a List[CodeTag]
                if isinstance(cached_tags, list):
                    return cached_tags
                else:
                    logger.warning(
                        f"Invalid cached tags type for {file_path}, falling back to parsing"
                    )

        # Parse file using internal _parse_file method
        tags = self._parse_file(file_path)

        # Cache results
        if use_cache and self.tag_cache:
            self.tag_cache.set_tags(file_path, tags)
            logger.debug(f"Cached {len(tags)} tags for {file_path}")

        return tags

    def parse_file_to_sexp(self, file_path: str) -> str:
        """Parses a file and returns its S-expression."""
        lang = filename_to_lang(file_path)
        parser = get_parser(lang)
        with open(file_path, 'rb') as f:
            tree = parser.parse(f.read())
        if tree is None or tree.root_node is None:
            logger.warning(f"Failed to parse file or root node is None for {file_path}")
            return ""
        return self._node_to_sexp(tree.root_node)

    def _node_to_sexp(self, node: tree_sitter.Node, indent: int = 0) -> str:
        """Recursively converts a tree-sitter node to an S-expression string.

        Args:
            node: The tree-sitter node to convert.
            indent: Current indentation level.

        Returns:
            S-expression string.
        """
        sexp_str = "" # Initialize an empty string
        prefix = "  " * indent

        # Check if node is named or a token
        if node.is_named:
            sexp_str += f"({node.type}"
        else:
            # For unnamed nodes (tokens), just print their text
            return f"\"{(node.text.decode('utf-8'))}\""

        # Add fields for named nodes
        for i, child in enumerate(node.children):
            field_name = node.field_name_for_child(i)
            child_sexp = self._node_to_sexp(child, indent + 1)
            if field_name:
                sexp_str += f"\n{prefix}  {field_name}: {child_sexp}"
            else:
                sexp_str += f"\n{prefix}  {child_sexp}"

        sexp_str += ")"
        return sexp_str

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
        if lang is None:
            return False
        
        # Check if query file exists without loading it to avoid warnings
        query_path = self.query_loader.custom_queries_dir / f"{lang}-tags.scm"
        return query_path.exists()
