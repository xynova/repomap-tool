"""
LLM Optimization Package for RepoMap Tool.

This package provides LLM-optimized output formatting, critical line extraction,
token optimization, and hierarchical structuring to maximize the value of repomap
output within LLM context window limitations.

Core Components:
- CriticalLineExtractor: Extracts the most important lines from functions/classes
- HierarchicalFormatter: Formats output in LLM-friendly hierarchical structure
- TokenOptimizer: Optimizes output for maximum information per token
- SignatureEnhancer: Enhances function signatures with type information
- ContextSelector: Selects most relevant context based on token budget
- OutputTemplates: LLM-optimized output templates
"""

from .critical_line_extractor import CriticalLineExtractor
from .hierarchical_formatter import HierarchicalFormatter
from .token_optimizer import TokenOptimizer
from .signature_enhancer import SignatureEnhancer
from .context_selector import ContextSelector
from .output_templates import OutputTemplates

__all__ = [
    # Core classes
    "CriticalLineExtractor",
    "HierarchicalFormatter", 
    "TokenOptimizer",
    "SignatureEnhancer",
    "ContextSelector",
    "OutputTemplates",
]

__version__ = "0.1.0"
