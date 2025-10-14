"""
Smart spell checker service using codespell for programming context.

This module provides intelligent spell correction functionality using
codespell, which is specifically designed for programming and code contexts.
"""

from typing import List, Tuple, Optional, Set
import subprocess
import tempfile
import os

from ..core.logging_service import get_logger

logger = get_logger(__name__)


class SpellCheckerService:
    """
    Smart spell checker service optimized for programming terms.

    Uses codespell, which is specifically designed for programming contexts
    and provides much better suggestions for code-related typos.
    """

    def __init__(self, custom_dictionary: Optional[Set[str]] = None):
        """
        Initialize the spell checker service.

        Args:
            custom_dictionary: Optional set of custom words to add to the dictionary
        """
        self.custom_dictionary = custom_dictionary or set()

        # Check if codespell is available
        self.codespell_available = self._check_codespell_availability()

        if self.codespell_available:
            logger.debug(
                "SpellCheckerService initialized with codespell (programming-optimized)"
            )
        else:
            logger.warning(
                "codespell not available, falling back to basic spellchecking"
            )

    def _check_codespell_availability(self) -> bool:
        """
        Check if codespell is available on the system.

        Returns:
            True if codespell is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["codespell", "--version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _run_codespell(self, text: str) -> List[str]:
        """
        Run codespell on the given text and return suggestions.

        Args:
            text: Text to check for spelling errors

        Returns:
            List of correction suggestions from codespell
        """
        if not self.codespell_available:
            return []

        suggestions = []

        try:
            # Create a temporary file with the text
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                f.write(text)
                temp_file = f.name

            # Run codespell
            result = subprocess.run(
                ["codespell", temp_file], capture_output=True, text=True, timeout=10
            )

            # Parse the output
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if "==>" in line:
                        # Extract suggestions from lines like:
                        # /tmp/file.txt:1: seach ==> search, each, reach, teach, beach
                        parts = line.split("==>")
                        if len(parts) == 2:
                            suggestions_text = parts[1].strip()
                            # Split by comma and clean up
                            for suggestion in suggestions_text.split(","):
                                clean_suggestion = suggestion.strip()
                                if clean_suggestion:
                                    suggestions.append(clean_suggestion)

            # Clean up
            os.unlink(temp_file)

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.warning(f"codespell failed: {e}")

        return suggestions

    def suggest_corrections(self, query: str, max_suggestions: int = 3) -> List[str]:
        """
        Suggest corrected versions of a query using codespell.

        Args:
            query: Original query with potential typos
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of suggested corrected queries (up to max_suggestions)
        """
        if not self.codespell_available:
            return []

        # Get suggestions from codespell
        codespell_suggestions = self._run_codespell(query)

        if not codespell_suggestions:
            return []

        # Create corrected versions of the query
        suggestions = []
        words = query.split()

        # Strategy 1: Use the first (best) suggestion for each word
        corrected_words = []
        suggestion_index = 0

        for word in words:
            clean_word = "".join(c for c in word if c.isalnum()).lower()
            if not clean_word:
                corrected_words.append(word)
                continue

            # Check if this word has a suggestion
            if suggestion_index < len(codespell_suggestions):
                # Use the first suggestion for this word
                corrected_words.append(codespell_suggestions[suggestion_index])
                suggestion_index += 1
            else:
                corrected_words.append(word)

        # Add the full correction
        if corrected_words != words:
            full_correction = " ".join(corrected_words)
            if full_correction != query:
                suggestions.append(full_correction)

        # Strategy 2: Try individual word corrections
        for suggestion in codespell_suggestions[:max_suggestions]:
            # Find which word this suggestion replaces
            for i, word in enumerate(words):
                clean_word = "".join(c for c in word if c.isalnum()).lower()
                if clean_word and suggestion != clean_word:
                    # Create a partial correction
                    partial_words = words.copy()
                    partial_words[i] = suggestion
                    partial_correction = " ".join(partial_words)

                    if (
                        partial_correction not in suggestions
                        and partial_correction != query
                    ):
                        suggestions.append(partial_correction)
                    break

        return suggestions[:max_suggestions]

    def check_spelling(self, text: str) -> Tuple[bool, List[str]]:
        """
        Check if text has spelling errors and return corrections.

        Args:
            text: Text to check for spelling errors

        Returns:
            Tuple of (has_errors, corrections) where:
            - has_errors: True if there are spelling errors
            - corrections: List of corrected words
        """
        if not self.codespell_available:
            return False, text.split()

        # Get suggestions from codespell
        suggestions = self._run_codespell(text)

        if not suggestions:
            return False, text.split()

        # Create corrected version
        words = text.split()
        corrected_words = []
        suggestion_index = 0

        for word in words:
            clean_word = "".join(c for c in word if c.isalnum()).lower()
            if not clean_word:
                corrected_words.append(word)
                continue

            # Use suggestion if available
            if suggestion_index < len(suggestions):
                corrected_words.append(suggestions[suggestion_index])
                suggestion_index += 1
            else:
                corrected_words.append(word)

        has_errors = corrected_words != words
        return has_errors, corrected_words

    def get_did_you_mean_suggestions(self, query: str) -> List[str]:
        """
        Get "Did you mean" suggestions for a query.

        Args:
            query: Query that might have typos

        Returns:
            List of "Did you mean" suggestions
        """
        suggestions = self.suggest_corrections(query)

        if not suggestions:
            return []

        # Format as "Did you mean" suggestions
        did_you_mean = []
        for suggestion in suggestions:
            did_you_mean.append(f"Did you mean: '{suggestion}'?")

        return did_you_mean

    def auto_correct_query(self, query: str) -> str:
        """
        Automatically correct a query if a clear correction is available.

        Args:
            query: Query to auto-correct

        Returns:
            Corrected query or original if no clear correction
        """
        suggestions = self.suggest_corrections(query, max_suggestions=1)
        if suggestions:
            return suggestions[0]
        return query
