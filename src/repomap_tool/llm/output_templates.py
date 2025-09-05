"""
Output templates for code analysis results.

This module provides configurable output templates for different
types of content with user-controlled formatting options.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TemplateConfig:
    """Configuration for output templates."""

    use_emojis: bool = True
    use_hierarchical_structure: bool = True
    include_line_numbers: bool = True
    include_centrality_scores: bool = True
    include_impact_risk: bool = True
    max_critical_lines: int = 3
    max_dependencies: int = 3
    compression_level: str = "medium"


class OutputTemplates:
    """Configurable output templates for different content types."""

    def __init__(self, config: Optional[TemplateConfig] = None):
        self.config = config or TemplateConfig()
        self.templates = self._load_templates()

    def apply_template(
        self, symbol: Dict[str, Any], template_type: str = "function"
    ) -> str:
        """Apply LLM-optimized template to symbol.

        Args:
            symbol: Symbol data to format
            template_type: Type of template to apply

        Returns:
            Formatted string using appropriate template
        """
        try:
            if template_type == "function":
                return self._apply_function_template(symbol)
            elif template_type == "class":
                return self._apply_class_template(symbol)
            elif template_type == "file":
                return self._apply_file_template(symbol)
            elif template_type == "project":
                return self._apply_project_template(symbol)
            else:
                return self._apply_generic_template(symbol)

        except Exception as e:
            logger.error(f"Error applying template {template_type}: {e}")
            return self._apply_fallback_template(symbol)

    def _apply_function_template(self, symbol: Dict[str, Any]) -> str:
        """Apply function-specific template."""
        output = []

        # Function header with enhanced signature
        name = symbol.get("name", "unknown_function")
        file_path = symbol.get("file_path", "unknown")
        line_number = symbol.get("line_number", 0)

        if self.config.include_line_numbers:
            header = f"{file_path}:{line_number}:"
        else:
            header = f"{file_path}:"

        output.append(header)

        # Function signature
        signature = symbol.get("signature", "")
        if signature:
            output.append(f"├── {name}: {signature}")
        else:
            output.append(f"├── {name}")

        # Centrality and impact information
        if self.config.include_centrality_scores:
            centrality = symbol.get("centrality_score", 0)
            if centrality > 0:
                output.append(f"│   📊 Centrality: {centrality:.2f}")

        if self.config.include_impact_risk:
            impact_risk = symbol.get("impact_risk", 0)
            if impact_risk > 0:
                risk_level = (
                    "HIGH"
                    if impact_risk > 0.7
                    else "MEDIUM" if impact_risk > 0.4 else "LOW"
                )
                output.append(f"│   ⚠️  Impact Risk: {risk_level} ({impact_risk:.2f})")

        # Critical implementation lines
        critical_lines = symbol.get("critical_lines", [])
        if critical_lines:
            for i, line in enumerate(critical_lines[: self.config.max_critical_lines]):
                is_last = i == len(critical_lines[: self.config.max_critical_lines]) - 1
                prefix = "    └──" if is_last else "    ├──"

                if self.config.use_emojis:
                    output.append(f"{prefix} 💡 Critical: {line.strip()}")
                else:
                    output.append(f"{prefix} Critical: {line.strip()}")

        # Usage examples
        usage_examples = symbol.get("usage_examples", [])
        if usage_examples:
            for i, example in enumerate(usage_examples[:2]):
                is_last = i == len(usage_examples[:2]) - 1
                prefix = "    └──" if is_last else "    ├──"

                if self.config.use_emojis:
                    output.append(f"{prefix} 📞 Usage: {example}")
                else:
                    output.append(f"{prefix} Usage: {example}")

        # Dependencies
        dependencies = symbol.get("dependencies", [])
        if dependencies:
            deps = ", ".join(dependencies[: self.config.max_dependencies])
            if len(dependencies) > self.config.max_dependencies:
                deps += f" (+{len(dependencies) - self.config.max_dependencies} more)"

            if self.config.use_emojis:
                output.append(f"    └── 🔗 Dependencies: {deps}")
            else:
                output.append(f"    └── Dependencies: {deps}")

        return "\n".join(output)

    def _apply_class_template(self, symbol: Dict[str, Any]) -> str:
        """Apply class-specific template."""
        output = []

        # Class header
        name = symbol.get("name", "unknown_class")
        file_path = symbol.get("file_path", "unknown")
        line_number = symbol.get("line_number", 0)

        if self.config.include_line_numbers:
            header = f"{file_path}:{line_number}:"
        else:
            header = f"{file_path}:"

        output.append(header)

        # Class definition
        signature = symbol.get("signature", "")
        if signature:
            output.append(f"├── {name}: {signature}")
        else:
            output.append(f"├── {name}")

        # Centrality and impact information
        if self.config.include_centrality_scores:
            centrality = symbol.get("centrality_score", 0)
            if centrality > 0:
                output.append(f"│   📊 Centrality: {centrality:.2f}")

        # Methods and attributes (if available)
        methods = symbol.get("methods", [])
        if methods:
            for i, method in enumerate(methods[:3]):
                is_last = i == len(methods[:3]) - 1
                prefix = "    └──" if is_last else "    ├──"
                output.append(f"{prefix} {method}")

        # Dependencies
        dependencies = symbol.get("dependencies", [])
        if dependencies:
            deps = ", ".join(dependencies[: self.config.max_dependencies])
            if len(dependencies) > self.config.max_dependencies:
                deps += f" (+{len(dependencies) - self.config.max_dependencies} more)"

            if self.config.use_emojis:
                output.append(f"    └── 🔗 Dependencies: {deps}")
            else:
                output.append(f"    └── Dependencies: {deps}")

        return "\n".join(output)

    def _apply_file_template(self, symbol: Dict[str, Any]) -> str:
        """Apply file-specific template."""
        output = []

        # File header
        file_path = symbol.get("file_path", "unknown")
        line_number = symbol.get("line_number", 0)

        if self.config.include_line_numbers:
            header = f"{file_path}:{line_number}:"
        else:
            header = f"{file_path}:"

        output.append(header)

        # File-level information
        imports = symbol.get("imports", [])
        if imports:
            if self.config.use_emojis:
                output.append(f"├── 📦 imports: {', '.join(imports[:5])}")
            else:
                output.append(f"├── imports: {', '.join(imports[:5])}")

            if len(imports) > 5:
                output.append(f"│   ... and {len(imports) - 5} more")

        # Symbols in the file
        symbols = symbol.get("symbols", [])
        if symbols:
            for i, sym in enumerate(symbols[:5]):
                is_last = i == len(symbols[:5]) - 1
                prefix = "    └──" if is_last else "    ├──"
                output.append(f"{prefix} {sym.get('name', 'unknown')}")

            if len(symbols) > 5:
                output.append(f"    ... and {len(symbols) - 5} more symbols")

        # Dependencies
        dependencies = symbol.get("dependencies", [])
        if dependencies:
            deps = ", ".join(dependencies[: self.config.max_dependencies])
            if len(dependencies) > self.config.max_dependencies:
                deps += f" (+{len(dependencies) - self.config.max_dependencies} more)"

            if self.config.use_emojis:
                output.append(f"└── 🔗 dependencies: {deps}")
            else:
                output.append(f"└── dependencies: {deps}")

        return "\n".join(output)

    def _apply_project_template(self, symbol: Dict[str, Any]) -> str:
        """Apply project-level template."""
        output = []

        # Project header
        project_name = symbol.get("project_name", "Unknown Project")
        total_files = symbol.get("total_files", 0)
        total_symbols = symbol.get("total_symbols", 0)

        if self.config.use_emojis:
            output.append(f"🧠 LLM-Optimized Repomap: {project_name}")
        else:
            output.append(f"LLM-Optimized Repomap: {project_name}")

        output.append("=" * 60)

        if self.config.use_emojis:
            output.append(f"📊 Summary: {total_files} files, {total_symbols} symbols")
        else:
            output.append(f"Summary: {total_files} files, {total_symbols} symbols")

        output.append("")

        # Files organized by module/package
        files_by_module = symbol.get("files_by_module", {})
        for module, files in files_by_module.items():
            if self.config.use_emojis:
                output.append(f"📁 {module}/")
            else:
                output.append(f"{module}/")

            for i, file_info in enumerate(files):
                is_last = i == len(files) - 1
                prefix = "    └──" if is_last else "    ├──"

                file_path = file_info.get("file_path", "unknown")
                symbol_count = file_info.get("symbol_count", 0)
                centrality = file_info.get("centrality_score", 0)

                file_line = f"{prefix} {file_path}"
                if symbol_count > 0:
                    file_line += f" ({symbol_count} symbols)"
                if centrality > 0:
                    file_line += f" [Centrality: {centrality:.2f}]"

                output.append(file_line)

            output.append("")  # Empty line between modules

        return "\n".join(output)

    def _apply_generic_template(self, symbol: Dict[str, Any]) -> str:
        """Apply generic template for unknown symbol types."""
        output = []

        # Basic header
        name = symbol.get("name", "unknown")
        file_path = symbol.get("file_path", "unknown")
        line_number = symbol.get("line_number", 0)

        if self.config.include_line_numbers:
            header = f"{file_path}:{line_number}:"
        else:
            header = f"{file_path}:"

        output.append(header)
        output.append(f"├── {name}")

        # Add available information
        for key, value in symbol.items():
            if key in ["name", "file_path", "line_number"]:
                continue

            if isinstance(value, list) and value:
                if len(value) <= 3:
                    output.append(f"│   └── {key}: {', '.join(str(v) for v in value)}")
                else:
                    output.append(
                        f"│   └── {key}: {', '.join(str(v) for v in value[:3])} (+{len(value) - 3} more)"
                    )
            elif value:
                output.append(f"│   └── {key}: {value}")

        return "\n".join(output)

    def _apply_fallback_template(self, symbol: Dict[str, Any]) -> str:
        """Apply fallback template when other templates fail."""
        return f"Error formatting {symbol.get('name', 'unknown')} from {symbol.get('file_path', 'unknown')}"

    def _load_templates(self) -> Dict[str, Any]:
        """Load templates for different content types."""
        return {
            "function_template": self._load_function_template(),
            "class_template": self._load_class_template(),
            "file_template": self._load_file_template(),
            "project_template": self._load_project_template(),
        }

    def _load_function_template(self) -> str:
        """Load function template."""
        return """
{file_path}:{line_number}:
├── {name}: {signature}
│   📊 Centrality: {centrality}
│   ⚠️  Impact Risk: {impact_risk}
{critical_lines}
{usage_examples}
    └── 🔗 Dependencies: {dependencies}
"""

    def _load_class_template(self) -> str:
        """Load class template."""
        return """
{file_path}:{line_number}:
├── {name}: {signature}
│   📊 Centrality: {centrality}
{methods}
    └── 🔗 Dependencies: {dependencies}
"""

    def _load_file_template(self) -> str:
        """Load file template."""
        return """
{file_path}:{line_number}:
├── 📦 imports: {imports}
{symbols}
└── 🔗 dependencies: {dependencies}
"""

    def _load_project_template(self) -> str:
        """Load project template."""
        return """
🧠 LLM-Optimized Repomap: {project_name}
============================================================
📊 Summary: {total_files} files, {total_symbols} symbols

{modules}
"""

    @classmethod
    def create_config(
        cls,
        use_emojis: bool = True,
        use_hierarchical_structure: bool = True,
        include_line_numbers: bool = True,
        include_centrality_scores: bool = True,
        include_impact_risk: bool = True,
        max_critical_lines: int = 3,
        max_dependencies: int = 3,
        compression_level: str = "medium",
    ) -> TemplateConfig:
        """Create a template configuration with specified options."""
        return TemplateConfig(
            use_emojis=use_emojis,
            use_hierarchical_structure=use_hierarchical_structure,
            include_line_numbers=include_line_numbers,
            include_centrality_scores=include_centrality_scores,
            include_impact_risk=include_impact_risk,
            max_critical_lines=max_critical_lines,
            max_dependencies=max_dependencies,
            compression_level=compression_level,
        )

    def format_project_summary(self, project_data: Dict[str, Any]) -> str:
        """Format a complete project summary using the configured templates.

        Args:
            project_data: Project analysis data

        Returns:
            Formatted project summary
        """
        if not self.config.use_hierarchical_structure:
            return self._format_flat_summary(project_data)

        return self._format_hierarchical_summary(project_data)

    def _format_flat_summary(self, project_data: Dict[str, Any]) -> str:
        """Format project summary in flat structure."""
        lines = []

        # Project header
        lines.append(f"Project: {project_data.get('project_root', 'Unknown')}")
        lines.append(f"Files: {project_data.get('total_files', 0)}")
        lines.append(f"Identifiers: {project_data.get('total_identifiers', 0)}")

        # File types
        if project_data.get("file_types"):
            lines.append("\nFile Types:")
            for ext, count in project_data["file_types"].items():
                lines.append(f"  {ext}: {count}")

        # Identifier types
        if project_data.get("identifier_types"):
            lines.append("\nIdentifier Types:")
            for id_type, count in project_data["identifier_types"].items():
                lines.append(f"  {id_type}: {count}")

        return "\n".join(lines)

    def _format_hierarchical_summary(self, project_data: Dict[str, Any]) -> str:
        """Format project summary in hierarchical structure."""
        lines = []

        # Project header with emojis if enabled
        emoji_prefix = "📁 " if self.config.use_emojis else ""
        lines.append(
            f"{emoji_prefix}Project: {project_data.get('project_root', 'Unknown')}"
        )
        lines.append(f"├── Files: {project_data.get('total_files', 0)}")
        lines.append(f"└── Identifiers: {project_data.get('total_identifiers', 0)}")

        # File types
        if project_data.get("file_types"):
            emoji_prefix = "📄 " if self.config.use_emojis else ""
            lines.append(f"\n{emoji_prefix}File Types:")
            for ext, count in project_data["file_types"].items():
                lines.append(f"  ├── {ext}: {count}")

        # Identifier types
        if project_data.get("identifier_types"):
            emoji_prefix = "🏷️ " if self.config.use_emojis else ""
            lines.append(f"\n{emoji_prefix}Identifier Types:")
            for id_type, count in project_data["identifier_types"].items():
                lines.append(f"  ├── {id_type}: {count}")

        return "\n".join(lines)
