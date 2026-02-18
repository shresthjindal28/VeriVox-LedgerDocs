#!/usr/bin/env python3
"""
Entry point for the User Service.
Run with: python run.py
"""

import uvicorn

from app.core.config import settings


def main():
    """Run the User Service with uvicorn."""
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )


if __name__ == "__main__":
    main()
