#!/usr/bin/env python3
"""
Backfill document_ownership for existing documents.

Run this script to register existing documents in the vector store
with a user so they appear on the dashboard.

Usage:
    python -m scripts.backfill_document_ownership <USER_ID>

Example:
    python -m scripts.backfill_document_ownership "550e8400-e29b-41d4-a716-446655440000"

Get your USER_ID from: Supabase Dashboard > Authentication > Users, or from the JWT 'sub' claim.
"""

import asyncio
import os
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from dotenv import load_dotenv

load_dotenv()

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8001")


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    user_id = sys.argv[1].strip()
    if not user_id:
        print("Error: USER_ID is required")
        sys.exit(1)

    # Import here to load app config
    from app.services.vector_service import vector_store

    docs = await vector_store.list_documents()
    if not docs:
        print("No documents found in vector store.")
        sys.exit(0)

    print(f"Found {len(docs)} document(s). Registering ownership for user {user_id}...")

    async with httpx.AsyncClient(timeout=10.0) as client:
        for doc in docs:
            try:
                resp = await client.post(
                    f"{USER_SERVICE_URL}/internal/documents/{doc.document_id}/ownership",
                    params={"user_id": user_id, "filename": doc.filename},
                )
                if resp.status_code == 200:
                    print(f"  ✓ {doc.filename} ({doc.document_id})")
                else:
                    print(f"  ✗ {doc.filename}: {resp.status_code} - {resp.text[:100]}")
            except Exception as e:
                print(f"  ✗ {doc.filename}: {e}")

    print("Done. Refresh your dashboard.")


if __name__ == "__main__":
    asyncio.run(main())
