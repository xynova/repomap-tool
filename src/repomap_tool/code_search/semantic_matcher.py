#!/usr/bin/env python3
"""
semantic_matcher.py - Simple semantic matching using domain-specific dictionaries

This module provides semantic matching capabilities without external LLMs by using
predefined semantic mappings for programming concepts.
"""

import re
import logging
from ..core.config_service import get_config
from ..core.logging_service import get_logger
from typing import Dict, List, Set, Tuple, Optional

# Configure logging
logger = get_logger(__name__)


class DomainSemanticMatcher:
    """
    A simple semantic matcher using domain-specific dictionaries for programming concepts.

    This approach uses predefined semantic mappings to categorize and match
    programming identifiers based on their functional meaning.
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize the semantic matcher with programming domain mappings.

        Args:
            verbose: Whether to log semantic matching details
        """
        self.verbose = verbose
        self.enabled = True  # Add enabled attribute for compatibility

        # Define semantic mappings for programming concepts
        self.semantic_mappings = {
            "authentication": [
                "auth",
                "login",
                "signin",
                "signout",
                "logout",
                "authenticate",
                "verify",
                "validate",
                "password",
                "credential",
                "token",
                "session",
                "user",
                "identity",
                "authorize",
                "permission",
                "access",
                "secure",
                "oauth",
                "jwt",
                "bearer",
                "refresh",
                "expire",
                "revoke",
            ],
            "data_processing": [
                "process",
                "transform",
                "convert",
                "parse",
                "format",
                "serialize",
                "deserialize",
                "encode",
                "decode",
                "filter",
                "sort",
                "aggregate",
                "map",
                "reduce",
                "extract",
                "load",
                "save",
                "import",
                "export",
                "migrate",
                "backup",
                "restore",
                "sync",
                "merge",
                "split",
            ],
            "configuration": [
                "config",
                "setting",
                "option",
                "parameter",
                "env",
                "environment",
                "preference",
                "property",
                "attribute",
                "flag",
                "switch",
                "toggle",
                "default",
                "override",
                "customize",
                "init",
                "setup",
                "bootstrap",
            ],
            "api_development": [
                "api",
                "endpoint",
                "route",
                "handler",
                "controller",
                "service",
                "request",
                "response",
                "method",
                "action",
                "operation",
                "call",
                "invoke",
                "execute",
                "trigger",
                "dispatch",
                "delegate",
                "proxy",
            ],
            "database": [
                "db",
                "database",
                "query",
                "select",
                "insert",
                "update",
                "delete",
                "table",
                "record",
                "row",
                "column",
                "field",
                "schema",
                "index",
                "constraint",
                "foreign",
                "primary",
                "unique",
                "transaction",
                "commit",
                "rollback",
                "connection",
                "pool",
                "migration",
                "seed",
            ],
            "testing": [
                "test",
                "spec",
                "mock",
                "stub",
                "fixture",
                "assert",
                "verify",
                "check",
                "validate",
                "expect",
                "should",
                "describe",
                "it",
                "before",
                "after",
                "setup",
                "teardown",
                "coverage",
                "unit",
                "integration",
                "e2e",
                "acceptance",
                "regression",
            ],
            "file_operations": [
                "file",
                "read",
                "write",
                "open",
                "close",
                "save",
                "load",
                "upload",
                "download",
                "upload",
                "stream",
                "buffer",
                "path",
                "directory",
                "folder",
                "create",
                "delete",
                "move",
                "copy",
                "rename",
                "exists",
                "size",
                "type",
                "extension",
            ],
            "network": [
                "http",
                "https",
                "url",
                "uri",
                "request",
                "response",
                "client",
                "server",
                "socket",
                "connection",
                "port",
                "host",
                "domain",
                "ip",
                "dns",
                "proxy",
                "gateway",
                "router",
                "firewall",
            ],
            "logging": [
                "log",
                "logger",
                "debug",
                "info",
                "warn",
                "error",
                "fatal",
                "trace",
                "level",
                "output",
                "console",
                "file",
                "syslog",
                "format",
                "timestamp",
                "message",
                "context",
                "metadata",
            ],
            "caching": [
                "cache",
                "memoize",
                "store",
                "retrieve",
                "get",
                "set",
                "put",
                "delete",
                "clear",
                "expire",
                "ttl",
                "lru",
                "redis",
                "memcached",
                "invalidate",
                "refresh",
                "update",
                "hit",
                "miss",
            ],
            "validation": [
                "validate",
                "verify",
                "check",
                "assert",
                "ensure",
                "require",
                "sanitize",
                "clean",
                "filter",
                "escape",
                "encode",
                "decode",
                "format",
                "normalize",
                "standardize",
                "compliance",
                "rule",
            ],
            "error_handling": [
                "error",
                "exception",
                "catch",
                "throw",
                "raise",
                "handle",
                "recover",
                "fallback",
                "retry",
                "timeout",
                "abort",
                "cancel",
                "rollback",
                "cleanup",
                "finally",
                "ensure",
                "safe",
            ],
            "security": [
                "security",
                "encrypt",
                "decrypt",
                "hash",
                "salt",
                "sign",
                "verify",
                "certificate",
                "key",
                "secret",
                "password",
                "token",
                "permission",
                "role",
                "access",
                "audit",
                "compliance",
            ],
            "performance": [
                "performance",
                "optimize",
                "speed",
                "fast",
                "slow",
                "benchmark",
                "profile",
                "measure",
                "time",
                "duration",
                "latency",
                "throughput",
                "memory",
                "cpu",
                "resource",
                "efficient",
                "bottleneck",
            ],
        }

        # Create reverse mapping for quick lookup
        self.reverse_mappings = {}
        for category, terms in self.semantic_mappings.items():
            for term in terms:
                self.reverse_mappings[term.lower()] = category

        if self.verbose:
            logger.info(
                f"Initialized DomainSemanticMatcher with {len(self.semantic_mappings)} categories"
            )

    def split_identifier(self, identifier: str) -> List[str]:
        """
        Split an identifier into words (camelCase, snake_case, kebab-case, etc.).

        Args:
            identifier: The identifier to split

        Returns:
            List of words from the identifier
        """
        if not identifier:
            return []

        # Handle different naming conventions
        # camelCase -> ['camel', 'Case']
        # snake_case -> ['snake', 'case']
        # kebab-case -> ['kebab', 'case']
        # PascalCase -> ['Pascal', 'Case']

        # Split by underscores and hyphens first
        parts = re.split(r"[_-]", identifier)

        # Then split camelCase and PascalCase
        words = []
        for part in parts:
            if part:
                # Split camelCase: "camelCase" -> ["camel", "Case"]
                camel_parts = re.findall(
                    r"[A-Z]?[a-z]+|[A-Z]{2,}(?=[A-Z][a-z]|\b|\d)|\d+", part
                )
                words.extend(camel_parts)

        return [word.lower() for word in words if word]

    def get_semantic_category(self, identifier: str) -> Optional[str]:
        """
        Get the semantic category for an identifier.

        Args:
            identifier: The identifier to categorize

        Returns:
            The semantic category or None if not found
        """
        words = self.split_identifier(identifier)

        for word in words:
            if word in self.reverse_mappings:
                return self.reverse_mappings[word]

        return None

    def get_semantic_categories(self, identifier: str) -> List[str]:
        """
        Get all semantic categories that match an identifier.

        Args:
            identifier: The identifier to categorize

        Returns:
            List of matching semantic categories
        """
        words = self.split_identifier(identifier)
        categories = set()

        for word in words:
            if word in self.reverse_mappings:
                categories.add(self.reverse_mappings[word])

        return list(categories)

    def semantic_similarity(self, query: str, identifier: str) -> float:
        """
        Calculate semantic similarity between query and identifier.

        Args:
            query: The search query
            identifier: The identifier to compare against

        Returns:
            Similarity score between 0.0 and 1.0
        """
        query_categories = set(self.get_semantic_categories(query))
        identifier_categories = set(self.get_semantic_categories(identifier))

        if not query_categories or not identifier_categories:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(query_categories.intersection(identifier_categories))
        union = len(query_categories.union(identifier_categories))

        if union == 0:
            return 0.0

        similarity = intersection / union

        # Boost similarity for exact category matches
        if query_categories == identifier_categories:
            similarity = min(1.0, similarity + 0.3)

        return similarity

    def find_semantic_matches(
        self,
        query: str,
        all_identifiers: Set[str],
        threshold: float = get_config("SEMANTIC_THRESHOLD", 0.3),
    ) -> List[Tuple[str, float]]:
        """
        Find semantic matches for a query among all identifiers.

        Args:
            query: The search query
            all_identifiers: Set of all available identifiers
            threshold: Minimum similarity threshold (0.0 to 1.0)

        Returns:
            List of (identifier, similarity_score) tuples, sorted by score
        """
        matches = []

        for identifier in all_identifiers:
            similarity = self.semantic_similarity(query, identifier)

            if similarity >= threshold:
                matches.append((identifier, similarity))

        # Sort by similarity score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)

        if self.verbose:
            logger.debug(f"Semantic matches for '{query}' (threshold: {threshold}):")
            for identifier, score in matches[:5]:
                logger.debug(f"  - {identifier} (similarity: {score:.2f})")

        return matches

    def get_category_statistics(self, all_identifiers: Set[str]) -> Dict[str, int]:
        """
        Get statistics about semantic categories in the codebase.

        Args:
            all_identifiers: Set of all identifiers in the codebase

        Returns:
            Dictionary mapping category names to counts
        """
        category_counts: Dict[str, int] = {}

        for identifier in all_identifiers:
            categories = self.get_semantic_categories(identifier)
            for category in categories:
                category_counts[category] = category_counts.get(category, 0) + 1

        return category_counts

    def suggest_categories(self, identifier: str) -> List[str]:
        """
        Suggest semantic categories for an identifier.

        Args:
            identifier: The identifier to suggest categories for

        Returns:
            List of suggested semantic categories
        """
        return self.get_semantic_categories(identifier)

    def get_related_terms(self, category: str) -> List[str]:
        """
        Get all terms related to a semantic category.

        Args:
            category: The semantic category

        Returns:
            List of related terms
        """
        return self.semantic_mappings.get(category, [])

    def add_custom_mapping(self, category: str, terms: List[str]) -> None:
        """
        Add custom semantic mapping for a category.

        Args:
            category: The semantic category name
            terms: List of terms that belong to this category
        """
        if category not in self.semantic_mappings:
            self.semantic_mappings[category] = []

        self.semantic_mappings[category].extend(terms)

        # Update reverse mappings
        for term in terms:
            self.reverse_mappings[term.lower()] = category

        if self.verbose:
            logger.info(
                f"Added custom mapping for category '{category}' with {len(terms)} terms"
            )
