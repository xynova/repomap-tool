"""
Template configuration models for RepoMap-Tool CLI.

This module defines the configuration models for template rendering,
including template options, styling preferences, and output formatting.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class TemplateOptions(BaseModel):
    """Configuration options for template rendering."""

    use_emojis: bool = Field(
        default=True, description="Whether to use emojis in output"
    )
    use_hierarchical_structure: bool = Field(
        default=True, description="Whether to use hierarchical tree structure"
    )
    include_line_numbers: bool = Field(
        default=True, description="Whether to include line numbers in output"
    )
    include_centrality_scores: bool = Field(
        default=True, description="Whether to include centrality scores"
    )
    include_impact_risk: bool = Field(
        default=True, description="Whether to include impact risk information"
    )
    max_critical_lines: int = Field(
        default=3, ge=1, le=10, description="Maximum number of critical lines to show"
    )
    max_dependencies: int = Field(
        default=3, ge=1, le=10, description="Maximum number of dependencies to show"
    )
    compression_level: str = Field(
        default="medium", description="Compression level for output"
    )
    max_width: int = Field(
        default=120, ge=40, le=200, description="Maximum width for output lines"
    )
    indent_size: int = Field(
        default=2, ge=1, le=8, description="Indentation size for hierarchical output"
    )

    @field_validator("compression_level")
    @classmethod
    def validate_compression_level(cls, v: str) -> str:
        """Validate compression level."""
        valid_levels = ["low", "medium", "high", "minimal"]
        if v not in valid_levels:
            raise ValueError(f"Compression level must be one of {valid_levels}")
        return v


class TemplateConfig(BaseModel):
    """Configuration for template rendering."""

    template_name: Optional[str] = Field(
        default=None, description="Name of the template to use"
    )
    template_path: Optional[str] = Field(
        default=None, description="Path to custom template file"
    )
    options: TemplateOptions = Field(
        default_factory=TemplateOptions, description="Template rendering options"
    )
    custom_variables: Dict[str, Any] = Field(
        default_factory=dict, description="Custom variables for template rendering"
    )
    format_style: str = Field(
        default="rich", description="Format style (rich, plain, minimal)"
    )

    @field_validator("format_style")
    @classmethod
    def validate_format_style(cls, v: str) -> str:
        """Validate format style."""
        valid_styles = ["rich", "plain", "minimal", "compact"]
        if v not in valid_styles:
            raise ValueError(f"Format style must be one of {valid_styles}")
        return v

    def get_template_context(self) -> Dict[str, Any]:
        """Get template rendering context."""
        context = {
            "options": self.options.model_dump(),
            "custom_variables": self.custom_variables,
            "format_style": self.format_style,
        }
        return context

    @classmethod
    def create_config(
        cls,
        template_name: Optional[str] = None,
        use_emojis: bool = True,
        use_hierarchical_structure: bool = True,
        include_line_numbers: bool = True,
        include_centrality_scores: bool = True,
        include_impact_risk: bool = True,
        max_critical_lines: int = 3,
        max_dependencies: int = 3,
        compression_level: str = "medium",
        format_style: str = "rich",
        **custom_variables: Any,
    ) -> TemplateConfig:
        """Create a template configuration with specified options."""
        options = TemplateOptions(
            use_emojis=use_emojis,
            use_hierarchical_structure=use_hierarchical_structure,
            include_line_numbers=include_line_numbers,
            include_centrality_scores=include_centrality_scores,
            include_impact_risk=include_impact_risk,
            max_critical_lines=max_critical_lines,
            max_dependencies=max_dependencies,
            compression_level=compression_level,
        )

        return cls(
            template_name=template_name,
            options=options,
            format_style=format_style,
            custom_variables=custom_variables,
        )
