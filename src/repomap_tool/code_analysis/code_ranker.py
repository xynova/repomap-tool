#!/usr/bin/env python3
"""
PageRank-based code importance ranking.

This module implements a PageRank algorithm inspired by aider's approach
for ranking code elements by importance and relevance.
"""

from __future__ import annotations

import math
import os
from collections import defaultdict, Counter
from typing import List, Dict, Set, Optional, Any

import networkx as nx

from repomap_tool.core.logging_service import get_logger

logger = get_logger(__name__)


class CodeRanker:
    """PageRank-based code importance ranking (inspired by aider)."""

    def rank_tags(
        self,
        all_tags: List[Dict[str, Any]],
        context_files: Optional[Set[str]] = None,
        mentioned_identifiers: Optional[Set[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Rank tags by importance using PageRank algorithm.

        Args:
            all_tags: List of all tags from tree-sitter parsing
            context_files: Set of files in current context (higher priority)
            mentioned_identifiers: Set of mentioned identifiers (higher priority)

        Returns:
            List of tags with rank scores, sorted by importance
        """
        if not all_tags:
            return []

        try:
            # Build dependency graph
            G = self._build_graph(all_tags)

            if G.number_of_nodes() == 0:
                logger.warning("No nodes in dependency graph")
                return all_tags

            # Create personalization vector
            personalization = self._build_personalization(
                all_tags, context_files or set(), mentioned_identifiers or set()
            )

            # Apply smart weights (aider's heuristics)
            self._apply_weights(
                G, all_tags, context_files or set(), mentioned_identifiers or set()
            )

            # Run PageRank
            if personalization:
                ranked = nx.pagerank(
                    G,
                    weight="weight",
                    personalization=personalization,
                    dangling=personalization,
                )
            else:
                ranked = nx.pagerank(G, weight="weight")

            # Distribute rank to definitions
            ranked_tags = self._distribute_rank(G, ranked, all_tags)

            logger.debug(f"Ranked {len(ranked_tags)} tags using PageRank")
            return ranked_tags

        except Exception as e:
            logger.error(f"Error in PageRank calculation: {e}")
            # Return original tags if ranking fails
            return all_tags

    def _build_graph(self, tags: List[Dict[str, Any]]) -> nx.MultiDiGraph:
        """Build dependency graph from tags.

        Args:
            tags: List of parsed tags

        Returns:
            NetworkX MultiDiGraph representing code dependencies
        """
        G = nx.MultiDiGraph()

        # Organize tags by file and identifier
        defines = defaultdict(set)  # identifier -> set of files
        references = defaultdict(list)  # identifier -> list of files

        for tag in tags:
            file_path = tag.file
            name = tag.name
            kind = tag.kind

            if "definition" in kind:
                defines[name].add(file_path)
            elif "reference" in kind:
                references[name].append(file_path)

        # Build edges: referencer -> definer
        for ident in defines.keys():
            if ident not in references:
                # No references, add self-edge to prevent isolated nodes
                for definer in defines[ident]:
                    G.add_edge(definer, definer, weight=0.1, ident=ident)
                continue

            # Add edges from referencers to definers
            for referencer, num_refs in Counter(references[ident]).items():
                for definer in defines[ident]:
                    # Scale down high-frequency references to prevent domination
                    weight = math.sqrt(num_refs)
                    G.add_edge(referencer, definer, weight=weight, ident=ident)

        logger.debug(
            f"Built graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges"
        )
        return G

    def _apply_weights(
        self,
        G: nx.MultiDiGraph,
        tags: List[Dict[str, Any]],
        context_files: Set[str],
        mentioned_identifiers: Set[str],
    ) -> None:
        """Apply smart weights to graph edges (aider's heuristics).

        Args:
            G: The dependency graph
            tags: List of all tags
            context_files: Files in current context
            mentioned_identifiers: Mentioned identifiers
        """
        for u, v, data in G.edges(data=True):
            ident = data.get("ident", "")
            weight = data.get("weight", 1.0)

            # Apply multipliers based on aider's heuristics

            # Mentioned identifiers are important
            if mentioned_identifiers and ident in mentioned_identifiers:
                weight *= 10

            # Long, well-named identifiers are important
            is_snake = ("_" in ident) and any(c.isalpha() for c in ident)
            is_camel = any(c.isupper() for c in ident) and any(
                c.islower() for c in ident
            )
            if (is_snake or is_camel) and len(ident) >= 8:
                weight *= 10

            # Private identifiers are less important
            if ident.startswith("_"):
                weight *= 0.1

            # Context files are very important
            if context_files and u in context_files:
                weight *= 50

            # Over-defined identifiers are less important
            if len([t for t in tags if t.name == ident and "definition" in t.kind]) > 5:
                weight *= 0.1

            data["weight"] = weight

    def _build_personalization(
        self,
        tags: List[Dict[str, Any]],
        context_files: Set[str],
        mentioned_identifiers: Set[str],
    ) -> Dict[str, float]:
        """Build personalization vector for PageRank.

        Args:
            tags: List of all tags
            context_files: Files in current context
            mentioned_identifiers: Mentioned identifiers

        Returns:
            Personalization dictionary mapping files to scores
        """
        personalization: Dict[str, float] = {}

        # Get all unique files
        files = set(tag.file for tag in tags)
        if not files:
            return personalization

        base_score = 100 / len(files)

        for file_path in files:
            score = 0.0

            # Context files get high personalization
            if context_files and file_path in context_files:
                score += base_score

            # Files with mentioned identifiers
            if mentioned_identifiers:
                file_tags = [t for t in tags if t.file == file_path]
                file_idents = set(t.name for t in file_tags)
                if file_idents.intersection(mentioned_identifiers):
                    score = max(score, base_score)

            if score > 0:
                personalization[file_path] = score

        logger.debug(f"Created personalization for {len(personalization)} files")
        return personalization

    def _distribute_rank(
        self, G: nx.MultiDiGraph, ranked: Dict[str, float], tags: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Distribute PageRank scores to individual tags.

        Args:
            G: The dependency graph
            ranked: PageRank scores for files
            tags: List of all tags

        Returns:
            List of tags with rank scores, sorted by importance
        """
        # Distribute rank from files to their tags
        ranked_tags = []

        for tag in tags:
            file_path = tag.file
            tag_rank = ranked.get(file_path, 0.0)

            ranked_tags.append({**tag, "rank": tag_rank})

        # Sort by rank (highest first)
        ranked_tags.sort(key=lambda x: x["rank"], reverse=True)

        return ranked_tags

    def get_top_ranked_tags(
        self, ranked_tags: List[Dict[str, Any]], limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get top-ranked tags.

        Args:
            ranked_tags: List of ranked tags
            limit: Maximum number of tags to return

        Returns:
            Top-ranked tags
        """
        return ranked_tags[:limit]
