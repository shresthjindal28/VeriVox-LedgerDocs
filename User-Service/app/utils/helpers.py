"""
Utility functions and helpers for the User Service.
"""

import logging
import sys
from typing import Optional
from datetime import datetime

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging with structlog.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if log_level == "DEBUG" else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.utcnow()


def mask_email(email: str) -> str:
    """
    Mask email for logging (privacy).
    
    Example: john.doe@example.com -> j***e@example.com
    """
    if not email or "@" not in email:
        return "***"
    
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """
    Mask phone number for logging (privacy).
    
    Example: +1234567890 -> +1***7890
    """
    if not phone or len(phone) < 8:
        return "***"
    
    return phone[:3] + "***" + phone[-4:]


def validate_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    import re
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(value))
