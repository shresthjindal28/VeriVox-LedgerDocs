"""
Project entry point.

Run the AI PDF Server with uvicorn.

Usage:
    python run.py                    # Development mode with reload
    python run.py --prod             # Production mode
    python run.py --host 0.0.0.0     # Specify host
    python run.py --port 8080        # Specify port
"""

import argparse
import os
import sys

import uvicorn


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AI PDF Document Intelligence Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("HOST", "0.0.0.0"),
        help="Host to bind to",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", 8000)),
        help="Port to bind to",
    )

    parser.add_argument(
        "--prod",
        action="store_true",
        help="Run in production mode (no reload, multiple workers)",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=int(os.getenv("WORKERS", 1)),
        help="Number of worker processes (production only)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("LOG_LEVEL", "info").lower(),
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level",
    )

    return parser.parse_args()


def main():
    """Run the server."""
    args = parse_args()

    # Configuration
    config = {
        "app": "app.main:app",
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level,
    }

    if args.prod:
        # Production configuration
        config.update(
            {
                "reload": False,
                "workers": args.workers,
                "access_log": True,
                "loop": "uvloop",  # Faster event loop
                "http": "httptools",  # Faster HTTP parser
            }
        )
        print(f"Starting production server on {args.host}:{args.port}")
        print(f"Workers: {args.workers}")
    else:
        # Development configuration
        config.update(
            {
                "reload": True,
                "reload_dirs": ["app"],
                "access_log": True,
            }
        )
        print(f"Starting development server on {args.host}:{args.port}")
        print("Auto-reload enabled")

    print(f"API docs: http://{args.host}:{args.port}/docs")
    print("-" * 50)

    # Run server
    uvicorn.run(**config)


if __name__ == "__main__":
    main()
