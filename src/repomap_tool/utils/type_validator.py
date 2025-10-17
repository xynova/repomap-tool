"""
Runtime type validation utilities.

This module provides runtime type validation for data structures
to ensure type safety at runtime.
"""

import logging
from ..core.logging_service import get_logger
from typing import Any, Dict, List, Optional
from repomap_tool.models import ProjectMap, Tag, FileData # Import from models

logger = get_logger(__name__)


def validate_project_map(data: Optional[Dict[str, Any]]) -> ProjectMap:
    """
    Validate and convert project map data to structured format.

    Args:
        data: Raw project map data

    Returns:
        Validated ProjectMap structure

    Raises:
        ValueError: If data structure is invalid
    """
    if data is None:
        return ProjectMap(tags=None, identifiers=None, files=None)

    if not isinstance(data, dict):
        raise ValueError("Project map data must be a dictionary")

    # Validate and extract tags
    tags = None
    if "tags" in data and data["tags"] is not None:
        if not isinstance(data["tags"], list):
            raise ValueError("Tags must be a list")
        tags = []
        for tag in data["tags"]:
            # Handle both dict and object formats
            if isinstance(tag, dict):
                validated_tag = Tag(
                    name=tag["name"],
                    type=tag.get("type", None),
                    file=tag.get("file", ""),
                    line=tag.get("line", 0),
                )
            else:
                # Handle object format
                validated_tag = Tag(
                    name=tag.name,
                    type=getattr(tag, "kind", None),
                    file=tag.file,
                    line=tag.line,
                )
            tags.append(validated_tag)

    # Validate and extract identifiers
    identifiers = None
    if "identifiers" in data and data["identifiers"] is not None:
        if not isinstance(data["identifiers"], (list, set, tuple)):
            raise ValueError("Identifiers must be a list, set, or tuple")
        identifiers = list(data["identifiers"])

    # Validate and extract files
    files = None
    if "files" in data and data["files"] is not None:
        if not isinstance(data["files"], dict):
            raise ValueError("Files must be a dictionary")
        files = {}
        for file_path, file_data in data["files"].items():
            if isinstance(file_data, dict):
                validated_file_data = FileData(
                    identifiers=file_data.get("identifiers"),
                    tags=file_data.get("tags"),
                    content=file_data.get("content"),
                )
                files[file_path] = validated_file_data

    return ProjectMap(tags=tags, identifiers=identifiers, files=files)


def validate_identifier_set(identifiers: Any) -> List[str]:
    """
    Validate and convert identifiers to a list of strings.

    Args:
        identifiers: Raw identifiers data

    Returns:
        List of validated identifier strings

    Raises:
        ValueError: If identifiers are invalid
    """
    if identifiers is None:
        return []

    if isinstance(identifiers, str):
        return [identifiers]

    if isinstance(identifiers, (list, set, tuple)):
        validated = []
        for identifier in identifiers:
            if isinstance(identifier, str):
                validated.append(identifier)
            else:
                validated.append(str(identifier))
        return validated

    raise ValueError("Identifiers must be a string, list, set, or tuple")


def validate_cache_stats(stats: Any) -> Dict[str, Any]:
    """
    Validate cache statistics data.

    Args:
        stats: Raw cache statistics

    Returns:
        Validated cache statistics dictionary

    Raises:
        ValueError: If statistics are invalid
    """
    if not isinstance(stats, dict):
        raise ValueError("Cache statistics must be a dictionary")

    required_keys = ["cache_size", "hits", "misses", "hit_rate_percent"]
    for key in required_keys:
        if key not in stats:
            raise ValueError(f"Cache statistics missing required key: {key}")

    return stats


def validate_match_result(match: Any) -> tuple[str, int]:
    """
    Validate a match result tuple.

    Args:
        match: Raw match result

    Returns:
        Validated (identifier, score) tuple

    Raises:
        ValueError: If match result is invalid
    """
    if not isinstance(match, (list, tuple)) or len(match) != 2:
        raise ValueError("Match result must be a tuple or list with 2 elements")

    identifier, score = match

    if not isinstance(identifier, str):
        raise ValueError("Match identifier must be a string")

    if not isinstance(score, (int, float)):
        raise ValueError("Match score must be a number")

    return (identifier, int(score))


def validate_config_dict(config_dict: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate configuration dictionary structure.

    Args:
        config_dict: Raw configuration dictionary

    Returns:
        Validated configuration dictionary

    Raises:
        ValueError: If configuration is invalid
    """
    if config_dict is None:
        raise ValueError("Configuration dictionary cannot be None")

    if not isinstance(config_dict, dict):
        raise ValueError("Configuration must be a dictionary")

    # Validate required fields
    required_fields = ["project_root"]
    for field in required_fields:
        if field not in config_dict:
            raise ValueError(f"Configuration missing required field: {field}")

    return config_dict


def safe_validate_project_map(data: Optional[Dict[str, Any]]) -> ProjectMap:
    """
    Safely validate project map data with graceful degradation.

    Args:
        data: Raw project map data

    Returns:
        Validated ProjectMap structure or empty structure on error
    """
    try:
        return validate_project_map(data)
    except (ValueError, TypeError) as e:
        logger.error(f"Failed to validate project map: {e}")
        return ProjectMap(tags=None, identifiers=None, files=None)


def safe_validate_identifier_set(identifiers: Any) -> List[str]:
    """
    Safely validate identifiers with graceful degradation.

    Args:
        identifiers: Raw identifiers data

    Returns:
        List of validated identifier strings or empty list on error
    """
    try:
        return validate_identifier_set(identifiers)
    except (ValueError, TypeError) as e:
        logger.error(f"Failed to validate identifiers: {e}")
        return []


def log_type_validation_errors(
    data: Any, expected_type: str, context: str = ""
) -> None:
    """
    Log type validation errors for debugging.

    Args:
        data: The data that failed validation
        expected_type: The expected type
        context: Additional context for the error
    """
    actual_type = type(data).__name__
    logger.warning(
        f"Type validation failed in {context}: "
        f"expected {expected_type}, got {actual_type}"
    )
