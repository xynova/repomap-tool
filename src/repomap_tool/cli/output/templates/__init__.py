"""
Template system for RepoMap-Tool CLI output formatting.

This module provides a comprehensive template system for generating
consistent and configurable output across all CLI commands.
"""

from .engine import TemplateEngine, TemplateEngineFactory
from .registry import DefaultTemplateRegistry
from .config import TemplateConfig, TemplateOptions
from .loader import TemplateLoader, FileTemplateLoader

__all__ = [
    "TemplateEngine",
    "TemplateEngineFactory",
    "DefaultTemplateRegistry",
    "TemplateConfig",
    "TemplateOptions",
    "TemplateLoader",
    "FileTemplateLoader",
]
