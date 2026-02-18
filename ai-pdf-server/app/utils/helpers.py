"""Reusable helper utilities."""

import hashlib
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import aiofiles
import structlog

from app.core.config import settings


# ============================================================
# ID Generation
# ============================================================


def generate_document_id() -> str:
    """Generate a unique document ID using UUID4."""
    return str(uuid.uuid4())


def generate_chunk_id(document_id: str, page_number: int, chunk_index: int) -> str:
    """
    Generate a deterministic chunk ID.

    Args:
        document_id: The parent document ID
        page_number: Page number where chunk originates
        chunk_index: Index of the chunk within the page

    Returns:
        Deterministic chunk ID string
    """
    return f"{document_id}_p{page_number}_c{chunk_index}"


# ============================================================
# Hashing
# ============================================================


def compute_sha256(data: bytes) -> str:
    """
    Compute SHA-256 hash of byte data.

    Args:
        data: Bytes to hash

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(data).hexdigest()


def verify_hash(data: bytes, expected_hash: str) -> bool:
    """
    Verify data against expected hash.

    Args:
        data: Bytes to verify
        expected_hash: Expected SHA-256 hash

    Returns:
        True if hashes match, False otherwise
    """
    computed = compute_sha256(data)
    return computed.lower() == expected_hash.lower()


# ============================================================
# File Operations
# ============================================================


async def save_file_async(path: Path, content: bytes) -> None:
    """
    Save content to file asynchronously.

    Args:
        path: Path to save file
        content: Bytes to write
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "wb") as f:
        await f.write(content)


async def read_file_async(path: Path) -> bytes:
    """
    Read file content asynchronously.

    Args:
        path: Path to read from

    Returns:
        File contents as bytes
    """
    async with aiofiles.open(path, "rb") as f:
        return await f.read()


async def delete_file_async(path: Path) -> bool:
    """
    Delete a file asynchronously.

    Args:
        path: Path to delete

    Returns:
        True if deleted, False if not found
    """
    try:
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception:
        return False


async def save_json_async(path: Path, data: Dict[str, Any]) -> None:
    """
    Save dictionary as JSON file asynchronously.

    Args:
        path: Path to save JSON file
        data: Dictionary to serialize
    """
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, indent=2, default=str)
    async with aiofiles.open(path, "w") as f:
        await f.write(content)


async def load_json_async(path: Path) -> Optional[Dict[str, Any]]:
    """
    Load JSON file asynchronously.

    Args:
        path: Path to JSON file

    Returns:
        Dictionary from JSON or None if not found
    """
    import json

    if not path.exists():
        return None

    async with aiofiles.open(path, "r") as f:
        content = await f.read()
        return json.loads(content)


# ============================================================
# Logging Configuration
# ============================================================


def setup_logging() -> structlog.BoundLogger:
    """
    Configure structured logging for the application.

    Returns:
        Configured logger instance
    """
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            (
                structlog.processors.JSONRenderer()
                if settings.LOG_FORMAT == "json"
                else structlog.dev.ConsoleRenderer()
            ),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )

    return structlog.get_logger()


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a logger instance.

    Args:
        name: Optional logger name

    Returns:
        Configured logger
    """
    return structlog.get_logger(name)


# ============================================================
# Text Processing
# ============================================================


def clean_text(text: str) -> str:
    """
    Clean and normalize text content.

    Args:
        text: Raw text to clean

    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    import re

    text = re.sub(r"\s+", " ", text)
    # Remove control characters except newlines
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    return text.strip()


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


# ============================================================
# Timestamp Utilities
# ============================================================


def get_utc_timestamp() -> datetime:
    """Get current UTC timestamp."""
    return datetime.utcnow()


def format_timestamp(dt: datetime) -> str:
    """Format datetime to ISO string."""
    return dt.isoformat()


# Initialize default logger
logger = get_logger("ai-pdf-server")
