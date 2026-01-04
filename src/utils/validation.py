"""Data validation utilities."""

from pathlib import Path

import structlog

from src.models.visa import ContentData

logger = structlog.get_logger()


def validate_content_json(file_path: Path) -> bool:
    """Validate content JSON file against schema.

    Checks:
    - JSON is valid and matches ContentData schema
    - Required fields are non-empty
    - At least one section is extracted
    - Total text length exceeds minimum threshold

    Args:
        file_path: Path to JSON file

    Returns:
        True if valid, False otherwise
    """
    try:
        # Load and validate with Pydantic
        content = ContentData.from_json_file(file_path)

        # Check required fields
        if not content.source_url:
            logger.warning(
                "validation_failed",
                file=file_path.name,
                reason="missing_source_url",
            )
            return False

        if not content.title:
            logger.warning(
                "validation_failed",
                file=file_path.name,
                reason="missing_title",
            )
            return False

        # Check sections
        if len(content.sections) == 0:
            logger.warning(
                "validation_failed",
                file=file_path.name,
                reason="no_sections_extracted",
            )
            return False

        # Check total text length
        total_text = sum(len(s.content) for s in content.sections)
        if total_text < 100:
            logger.warning(
                "validation_failed",
                file=file_path.name,
                reason="text_too_short",
                length=total_text,
            )
            return False

        return True

    except Exception as e:
        logger.error(
            "validation_failed",
            file=file_path.name,
            reason="exception",
            error=str(e),
        )
        return False


def validate_all_files(directory: Path) -> dict:
    """Validate all JSON files in a directory.

    Args:
        directory: Directory containing JSON files

    Returns:
        Dictionary with validation statistics
    """
    json_files = list(directory.glob("*.json"))

    stats = {
        "total": len(json_files),
        "valid": 0,
        "invalid": 0,
        "errors": [],
    }

    for file_path in json_files:
        if validate_content_json(file_path):
            stats["valid"] += 1
        else:
            stats["invalid"] += 1
            stats["errors"].append(file_path.name)

    return stats
