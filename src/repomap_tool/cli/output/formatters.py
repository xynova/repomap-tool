"""
Output formatting utilities for RepoMap-Tool CLI.

This module contains legacy formatter functions that have been replaced by the new
OutputManager and formatter protocol system. This file is kept for backward
compatibility but the functions are no longer used.
"""

# This file is deprecated and kept only for backward compatibility.
# All output formatting is now handled by the OutputManager and formatter protocols
# in the new output architecture.

# The legacy functions have been removed as they are no longer used by any CLI commands.
# All output is now handled through:
# - OutputManager (src/repomap_tool/cli/output/manager.py)
# - Standard formatters (src/repomap_tool/cli/output/standard_formatters.py)
# - Template system (src/repomap_tool/cli/output/templates/)
