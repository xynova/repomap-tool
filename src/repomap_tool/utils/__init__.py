"""
Utility modules for repomap-tool.

This package contains utility functions and helpers.
"""

from .type_validator import (
    validate_project_map,
    validate_identifier_set,
    validate_cache_stats,
    validate_match_result,
    validate_config_dict,
    safe_validate_project_map,
    safe_validate_identifier_set,
    log_type_validation_errors,
)
from .file_validator import (
    FileValidator,
    validate_path,
    safe_read_text,
    safe_write_text,
    safe_create_directory,
)

__all__ = [
    "validate_project_map",
    "validate_identifier_set",
    "validate_cache_stats",
    "validate_match_result",
    "validate_config_dict",
    "safe_validate_project_map",
    "safe_validate_identifier_set",
    "log_type_validation_errors",
    "FileValidator",
    "validate_path",
    "safe_read_text",
    "safe_write_text",
    "safe_create_directory",
]
