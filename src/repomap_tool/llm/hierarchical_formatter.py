"""
Hierarchical formatter for LLM-optimized output.

This module formats code analysis output in a hierarchical structure
that's easy for LLMs to parse and understand.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SymbolInfo:
    """Information about a code symbol for formatting."""
    name: str
    file_path: str
    line_number: int
    symbol_type: str  # function, class, method, etc.
    signature: Optional[str] = None
    critical_lines: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    centrality_score: Optional[float] = None
    impact_risk: Optional[float] = None


class HierarchicalFormatter:
    """Formats output in LLM-friendly hierarchical structure."""
    
    def __init__(self):
        self.indentation_level = 0
        self.max_depth = 4
        self.use_unicode = True  # Use Unicode symbols for better visual hierarchy
    
    def format_file_hierarchy(self, file_analysis: Dict[str, Any]) -> str:
        """Format file analysis in hierarchical structure.
        
        Args:
            file_analysis: Dictionary containing file analysis data
            
        Returns:
            Formatted hierarchical string
        """
        output = []
        
        # File header
        file_path = file_analysis.get('file_path', 'unknown')
        line_number = file_analysis.get('line_number', 0)
        output.append(f"{file_path}:{line_number}:")
        
        # File-level information
        if 'imports' in file_analysis:
            imports = file_analysis['imports']
            if imports:
                output.append(f"├── imports: {', '.join(imports[:5])}")
                if len(imports) > 5:
                    output.append(f"│   ... and {len(imports) - 5} more")
        
        # Symbols in the file
        symbols = file_analysis.get('symbols', [])
        for i, symbol in enumerate(symbols):
            is_last = i == len(symbols) - 1
            symbol_output = self._format_symbol(symbol, is_last)
            output.extend(symbol_output)
        
        # Dependencies
        dependencies = file_analysis.get('dependencies', [])
        if dependencies:
            output.append(f"└── dependencies: {', '.join(dependencies[:3])}")
            if len(dependencies) > 3:
                output.append(f"    ... and {len(dependencies) - 3} more")
        
        return "\n".join(output)
    
    def format_symbol_hierarchy(self, symbols: List[SymbolInfo]) -> str:
        """Format symbols with proper hierarchy.
        
        Args:
            symbols: List of SymbolInfo objects
            
        Returns:
            Hierarchically formatted string
        """
        if not symbols:
            return "No symbols found"
        
        output = []
        
        for i, symbol in enumerate(symbols):
            is_last = i == len(symbols) - 1
            symbol_output = self._format_symbol(symbol, is_last)
            output.extend(symbol_output)
        
        return "\n".join(output)
    
    def _format_symbol(self, symbol: Dict[str, Any], is_last: bool) -> List[str]:
        """Format a single symbol with proper hierarchy.
        
        Args:
            symbol: SymbolInfo object or dictionary to format
            is_last: Whether this is the last symbol at this level
            
        Returns:
            List of formatted lines for the symbol
        """
        output = []
        
        # Symbol header
        prefix = "└──" if is_last else "├──"
        name = symbol.get('name', 'unknown')
        header = f"{prefix} {name}"
        
        # Add signature if available
        signature = symbol.get('signature', '')
        if signature:
            header += f": {signature}"
        
        # Add centrality and impact information
        centrality_score = symbol.get('centrality_score')
        if centrality_score is not None:
            header += f" [Centrality: {centrality_score:.2f}]"
        
        impact_risk = symbol.get('impact_risk')
        if impact_risk is not None:
            risk_level = "HIGH" if impact_risk > 0.7 else "MEDIUM" if impact_risk > 0.4 else "LOW"
            header += f" ⚠️ {risk_level}"
        
        output.append(header)
        
        # Critical lines
        critical_lines = symbol.get('critical_lines', [])
        if critical_lines:
            for j, line in enumerate(critical_lines[:3]):  # Limit to top 3
                is_last_line = j == len(critical_lines[:3]) - 1
                line_prefix = "    └──" if is_last_line else "    ├──"
                output.append(f"{line_prefix} Critical: {line.strip()}")
        
        # Dependencies
        dependencies = symbol.get('dependencies', [])
        if dependencies:
            deps = ", ".join(dependencies[:3])  # Limit dependencies
            if len(dependencies) > 3:
                deps += f" (+{len(dependencies) - 3} more)"
            output.append(f"    └── Dependencies: {deps}")
        
        return output
    
    def create_llm_structure(self, project_analysis: Dict[str, Any]) -> str:
        """Create overall LLM-optimized structure.
        
        Args:
            project_analysis: Dictionary containing project analysis data
            
        Returns:
            Complete LLM-optimized structure
        """
        output = []
        
        # Project header
        project_name = project_analysis.get('project_name', 'Unknown Project')
        total_files = project_analysis.get('total_files', 0)
        total_symbols = project_analysis.get('total_symbols', 0)
        
        output.append(f"🧠 LLM-Optimized Repomap: {project_name}")
        output.append("=" * 60)
        output.append(f"📊 Summary: {total_files} files, {total_symbols} symbols")
        output.append("")
        
        # Files organized by module/package
        files_by_module = project_analysis.get('files_by_module', {})
        for module, files in files_by_module.items():
            output.append(f"📁 {module}/")
            
            for i, file_info in enumerate(files):
                is_last = i == len(files) - 1
                file_output = self._format_file_summary(file_info, is_last)
                output.extend(file_output)
            
            output.append("")  # Empty line between modules
        
        return "\n".join(output)
    
    def _format_file_summary(self, file_info: Dict[str, Any], is_last: bool) -> List[str]:
        """Format a file summary in the hierarchy.
        
        Args:
            file_info: Dictionary containing file information
            is_last: Whether this is the last file in the module
            
        Returns:
            List of formatted lines for the file
        """
        output = []
        
        prefix = "    └──" if is_last else "    ├──"
        file_path = file_info.get('file_path', 'unknown')
        symbol_count = file_info.get('symbol_count', 0)
        centrality = file_info.get('centrality_score', 0.0)
        
        # Format file line
        file_line = f"{prefix} {file_path}"
        if symbol_count > 0:
            file_line += f" ({symbol_count} symbols)"
        if centrality > 0.0:
            file_line += f" [Centrality: {centrality:.2f}]"
        
        output.append(file_line)
        
        # Add key symbols if available
        key_symbols = file_info.get('key_symbols', [])
        if key_symbols:
            for j, symbol in enumerate(key_symbols[:2]):  # Limit to top 2
                is_last_symbol = j == len(key_symbols[:2]) - 1
                symbol_prefix = "        └──" if is_last_symbol else "        ├──"
                output.append(f"{symbol_prefix} {symbol}")
        
        return output
    
    def format_with_budget_constraints(
        self, 
        content: str, 
        max_lines: int = 50,
        max_depth: int = 3
    ) -> str:
        """Format content with budget constraints for token optimization.
        
        Args:
            content: Raw content to format
            max_lines: Maximum number of lines to include
            max_depth: Maximum depth of hierarchy
            
        Returns:
            Budget-constrained formatted content
        """
        lines = content.split('\n')
        
        if len(lines) <= max_lines:
            return content
        
        # Truncate while preserving hierarchy
        truncated_lines = []
        current_depth = 0
        
        for line in lines:
            if len(truncated_lines) >= max_lines - 2:  # Leave room for truncation message
                break
            
            # Count indentation level
            indent_level = len(line) - len(line.lstrip())
            if indent_level > max_depth * 2:  # 2 spaces per level
                continue  # Skip deeply nested content
            
            truncated_lines.append(line)
            current_depth = max(current_depth, indent_level // 2)
        
        # Add truncation message
        truncated_lines.append("")
        truncated_lines.append(f"... truncated at {max_lines} lines, depth {current_depth}")
        
        return "\n".join(truncated_lines)
    
    def add_visual_enhancements(self, content: str) -> str:
        """Add visual enhancements for better LLM parsing.
        
        Args:
            content: Raw formatted content
            
        Returns:
            Enhanced content with visual markers
        """
        if not self.use_unicode:
            return content
        
        # Add emojis and visual markers for better LLM understanding
        enhanced = content
        
        # File markers
        enhanced = enhanced.replace("📁", "📁")
        enhanced = enhanced.replace("📊", "📊")
        
        # Symbol markers
        enhanced = enhanced.replace("├──", "├──")
        enhanced = enhanced.replace("└──", "└──")
        
        # Add importance indicators
        enhanced = enhanced.replace("Critical:", "💡 Critical:")
        enhanced = enhanced.replace("Dependencies:", "🔗 Dependencies:")
        enhanced = enhanced.replace("imports:", "📦 imports:")
        
        return enhanced
