"""
Entry point for running the CLI as a module.

This allows running: python -m repomap_tool.cli
"""

from .main import cli

if __name__ == "__main__":
    cli()
