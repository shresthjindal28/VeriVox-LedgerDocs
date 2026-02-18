#!/usr/bin/env python3
"""
Entry point for the API Gateway.
Run with: python run.py
"""

import uvicorn

from app.config import settings


def main():
    """Run the API Gateway with uvicorn."""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    Study With Me - API Gateway               ║
╠══════════════════════════════════════════════════════════════╣
║  Gateway:      http://{settings.HOST}:{settings.PORT:<5}                            ║
║  PDF Service:  {settings.PDF_SERVICE_URL:<45} ║
║  User Service: {settings.USER_SERVICE_URL:<45} ║
║  Docs:         http://localhost:{settings.PORT}/docs                       ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )


if __name__ == "__main__":
    main()
