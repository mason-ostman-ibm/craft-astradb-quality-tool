"""Input validation utilities."""

import os
from pathlib import Path
from typing import Optional


def validate_similarity_threshold(threshold: float) -> bool:
    """
    Validate similarity threshold value.

    Args:
        threshold: Similarity threshold (0.0 to 1.0).

    Returns:
        True if valid.

    Raises:
        ValueError: If threshold is out of range.
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError(
            f"Similarity threshold must be between 0.0 and 1.0, got {threshold}"
        )
    return True


def validate_file_path(file_path: str, must_exist: bool = False) -> Path:
    """
    Validate and convert file path to Path object.

    Args:
        file_path: File path string.
        must_exist: Whether the file must already exist.

    Returns:
        Path object.

    Raises:
        ValueError: If path is invalid or doesn't exist when required.
    """
    path = Path(file_path)
    
    if must_exist and not path.exists():
        raise ValueError(f"File does not exist: {file_path}")
    
    return path


def validate_positive_integer(value: int, name: str = "value") -> bool:
    """
    Validate that a value is a positive integer.

    Args:
        value: Integer value to validate.
        name: Name of the parameter for error messages.

    Returns:
        True if valid.

    Raises:
        ValueError: If value is not positive.
    """
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value}")
    return True


def validate_document_id(doc_id: str) -> bool:
    """
    Validate document ID format.

    Args:
        doc_id: Document ID string.

    Returns:
        True if valid.

    Raises:
        ValueError: If ID is empty or invalid.
    """
    if not doc_id or not doc_id.strip():
        raise ValueError("Document ID cannot be empty")
    return True


def validate_export_format(format_type: str) -> bool:
    """
    Validate export format type.

    Args:
        format_type: Format type (json, csv).

    Returns:
        True if valid.

    Raises:
        ValueError: If format is not supported.
    """
    valid_formats = ["json", "csv"]
    if format_type.lower() not in valid_formats:
        raise ValueError(
            f"Invalid export format: {format_type}. "
            f"Supported formats: {', '.join(valid_formats)}"
        )
    return True


def validate_merge_strategy(strategy: str) -> bool:
    """
    Validate merge strategy.

    Args:
        strategy: Merge strategy name.

    Returns:
        True if valid.

    Raises:
        ValueError: If strategy is not supported.
    """
    valid_strategies = [
        "keep_first",
        "keep_last",
        "longest_answer",
        "shortest_answer",
        "most_recent",
        "manual",
    ]
    if strategy.lower() not in valid_strategies:
        raise ValueError(
            f"Invalid merge strategy: {strategy}. "
            f"Supported strategies: {', '.join(valid_strategies)}"
        )
    return True


def validate_quality_threshold(threshold: int) -> bool:
    """
    Validate quality score threshold.

    Args:
        threshold: Quality score (0-100).

    Returns:
        True if valid.

    Raises:
        ValueError: If threshold is out of range.
    """
    if not 0 <= threshold <= 100:
        raise ValueError(
            f"Quality threshold must be between 0 and 100, got {threshold}"
        )
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.

    Args:
        filename: Original filename.

    Returns:
        Sanitized filename.
    """
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed"
    
    return filename


def validate_date_format(date_string: str) -> bool:
    """
    Validate date string format (ISO 8601).

    Args:
        date_string: Date string to validate.

    Returns:
        True if valid.

    Raises:
        ValueError: If date format is invalid.
    """
    from datetime import datetime
    
    try:
        datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return True
    except ValueError:
        raise ValueError(
            f"Invalid date format: {date_string}. "
            "Expected ISO 8601 format (e.g., 2024-01-15T10:30:00Z)"
        )
