"""
Legacy CLI module - imports the refactored CLI for backward compatibility.
"""

# Import the refactored CLI as the main entry point
from .cli.main import cli

# Re-export for backward compatibility
__all__ = ["cli"]
