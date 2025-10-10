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
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize the tree-sitter parser.
        
        Args:
            project_root: Root directory of the project for relative path resolution
        """
        self.project_root = project_root or "."
        self._query_cache: Dict[str, str] = {}
    
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
            if hasattr(captures, 'items'):
                # Dictionary format: {tag_name: [nodes]}
                for tag_kind, nodes in captures.items():
                    for node in nodes:
                        tags.append({
                            'name': node.text.decode("utf-8"),
                            'kind': tag_kind,  # Keep full kind: name.definition.class, etc.
                            'line': node.start_point[0] + 1,  # Convert to 1-based line numbers
                            'column': node.start_point[1],
                            'file': file_path,
                            'end_line': node.end_point[0] + 1,
                            'end_column': node.end_point[1],
                        })
            else:
                # List format: [(node, tag_kind), ...]
                for capture in captures:
                    if len(capture) == 2:
                        node, tag_kind = capture
                        tags.append({
                            'name': node.text.decode("utf-8"),
                            'kind': tag_kind,  # Keep full kind: name.definition.class, etc.
                            'line': node.start_point[0] + 1,  # Convert to 1-based line numbers
                            'column': node.start_point[1],
                            'file': file_path,
                            'end_line': node.end_point[0] + 1,
                            'end_column': node.end_point[1],
                        })
                    else:
                        logger.debug(f"Unexpected capture format: {capture}")
            
            logger.debug(f"Parsed {len(tags)} tags from {file_path}")
            return tags
            
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
        
        try:
            # Use aider's query files
            from aider.queries import get_scm_fname
            query_path = get_scm_fname(lang)
            if query_path and query_path.exists():
                query_content = query_path.read_text()
                self._query_cache[lang] = query_content
                return query_content
        except Exception as e:
            logger.debug(f"Could not load query for {lang}: {e}")
        
        # Fallback: try to find query files directly
        try:
            import pkg_resources
            query_path = pkg_resources.resource_filename(
                'aider.queries.tree-sitter-language-pack', 
                f'{lang}-tags.scm'
            )
            if os.path.exists(query_path):
                with open(query_path, 'r') as f:
                    query_content = f.read()
                    self._query_cache[lang] = query_content
                    return query_content
        except Exception as e:
            logger.debug(f"Could not load fallback query for {lang}: {e}")
        
        # Direct path fallback
        try:
            query_path = f"/Users/hector/Xynova/ai/repomap-tool/.venv/lib/python3.11/site-packages/aider/queries/tree-sitter-language-pack/{lang}-tags.scm"
            if os.path.exists(query_path):
                with open(query_path, 'r') as f:
                    query_content = f.read()
                    self._query_cache[lang] = query_content
                    return query_content
        except Exception as e:
            logger.debug(f"Could not load direct query for {lang}: {e}")
        
        return None
    
    def _read_file(self, file_path: str) -> Optional[str]:
        """Read file content safely.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File content or None if error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
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
            'python', 'javascript', 'typescript', 'java', 'go', 'rust',
            'cpp', 'c', 'csharp', 'php', 'ruby', 'swift', 'kotlin',
            'scala', 'haskell', 'ocaml', 'elixir', 'clojure', 'lua'
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
