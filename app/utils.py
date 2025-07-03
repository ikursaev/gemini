"""Utility functions for the Gemini CLI application."""

import logging
from pathlib import Path
from typing import Tuple

from google import genai

from app.config import settings

logger = logging.getLogger(__name__)


async def count_tokens(client: genai.Client, model: str, contents: list) -> int:
    """
    Count tokens for given content.

    Args:
        client: Gemini client instance
        model: Model name
        contents: List of content to count tokens for

    Returns:
        Number of tokens
    """
    try:
        result = await client.aio.models.count_tokens(
            model=model,
            contents=contents,
        )
        return result
    except Exception as e:
        logger.error(f"Error counting tokens: {e}")
        return 0


def cleanup_file(file_path: str | Path) -> bool:
    """
    Safely clean up a file.

    Args:
        file_path: Path to the file to remove

    Returns:
        True if file was successfully removed, False otherwise
    """
    try:
        Path(file_path).unlink(missing_ok=True)
        logger.info(f"Cleaned up file: {file_path}")
        return True
    except Exception as e:
        logger.warning(f"Failed to cleanup file {file_path}: {e}")
        return False


def validate_file_size(file_size: int) -> Tuple[bool, str]:
    """
    Validate file size against maximum allowed size.

    Args:
        file_size: Size of the file in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    if file_size == 0:
        return False, "Empty file uploaded"

    if file_size > settings.MAX_FILE_SIZE:
        return False, f"File size {file_size} exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"

    return True, ""


def validate_mime_type(mime_type: str) -> Tuple[bool, str]:
    """
    Validate MIME type against supported types.

    Args:
        mime_type: MIME type to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    supported_types = ["application/pdf", "image/jpeg", "image/png", "image/gif", "image/bmp", "image/tiff"]

    if mime_type == "application/pdf":
        return True, ""

    if mime_type.startswith("image/"):
        return True, ""

    return False, f"Unsupported file type: {mime_type}. Supported types: {supported_types}"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size_float = float(size_bytes)
    while size_float >= 1024 and i < len(size_names) - 1:
        size_float /= 1024.0
        i += 1

    return f"{size_float:.1f} {size_names[i]}"
