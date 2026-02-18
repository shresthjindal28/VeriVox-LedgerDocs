"""Security and integrity verification utilities.

This module provides blockchain-ready document integrity verification.
The hash storage is designed to be easily migrated to blockchain storage.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from app.core.config import settings
from app.utils.helpers import (
    compute_sha256,
    get_logger,
    load_json_async,
    read_file_async,
    save_json_async,
)

logger = get_logger(__name__)


@dataclass
class HashRecord:
    """
    Blockchain-ready hash record.

    This structure is designed to be easily stored on a blockchain.
    """

    document_id: str
    sha256_hash: str
    filename: str
    timestamp: str
    file_size_bytes: int
    # Placeholder for future blockchain integration
    blockchain_tx_id: Optional[str] = None
    blockchain_confirmed: bool = False


class IntegrityService:
    """
    Service for document integrity verification.

    Provides SHA-256 hashing and verification with a structure
    ready for blockchain integration.
    """

    def __init__(self, hash_store_path: Optional[Path] = None):
        """
        Initialize integrity service.

        Args:
            hash_store_path: Path to hash store file
        """
        self.hash_store_path = hash_store_path or (settings.METADATA_DIR / "hash_store.json")
        self._cache: Dict[str, HashRecord] = {}

    async def _load_store(self) -> Dict[str, dict]:
        """Load hash store from disk."""
        data = await load_json_async(self.hash_store_path)
        return data or {}

    async def _save_store(self, store: Dict[str, dict]) -> None:
        """Save hash store to disk."""
        await save_json_async(self.hash_store_path, store)

    async def register_document(
        self,
        document_id: str,
        sha256_hash: str,
        filename: str,
        file_size_bytes: int,
    ) -> HashRecord:
        """
        Register a document's hash for integrity tracking.

        Args:
            document_id: Unique document identifier
            sha256_hash: SHA-256 hash of document content
            filename: Original filename
            file_size_bytes: Size of document in bytes

        Returns:
            Created HashRecord
        """
        record = HashRecord(
            document_id=document_id,
            sha256_hash=sha256_hash,
            filename=filename,
            timestamp=datetime.utcnow().isoformat(),
            file_size_bytes=file_size_bytes,
        )

        # Store in cache
        self._cache[document_id] = record

        # Persist to disk
        store = await self._load_store()
        store[document_id] = {
            "document_id": record.document_id,
            "sha256_hash": record.sha256_hash,
            "filename": record.filename,
            "timestamp": record.timestamp,
            "file_size_bytes": record.file_size_bytes,
            "blockchain_tx_id": record.blockchain_tx_id,
            "blockchain_confirmed": record.blockchain_confirmed,
        }
        await self._save_store(store)

        logger.info(
            "Document hash registered",
            document_id=document_id,
            hash=sha256_hash[:16] + "...",
        )

        return record

    async def get_document_hash(self, document_id: str) -> Optional[str]:
        """
        Retrieve stored hash for a document.

        Args:
            document_id: Document ID

        Returns:
            SHA-256 hash or None if not found
        """
        # Check cache first
        if document_id in self._cache:
            return self._cache[document_id].sha256_hash

        # Load from disk
        store = await self._load_store()
        if document_id in store:
            return store[document_id]["sha256_hash"]

        return None

    async def get_hash_record(self, document_id: str) -> Optional[HashRecord]:
        """
        Get complete hash record for a document.

        Args:
            document_id: Document ID

        Returns:
            HashRecord or None if not found
        """
        # Check cache first
        if document_id in self._cache:
            return self._cache[document_id]

        # Load from disk
        store = await self._load_store()
        if document_id in store:
            data = store[document_id]
            record = HashRecord(
                document_id=data["document_id"],
                sha256_hash=data["sha256_hash"],
                filename=data["filename"],
                timestamp=data["timestamp"],
                file_size_bytes=data["file_size_bytes"],
                blockchain_tx_id=data.get("blockchain_tx_id"),
                blockchain_confirmed=data.get("blockchain_confirmed", False),
            )
            self._cache[document_id] = record
            return record

        return None

    async def verify_integrity(
        self,
        document_id: str,
        provided_hash: str,
    ) -> tuple[bool, str, str]:
        """
        Verify document integrity against stored hash.

        Args:
            document_id: Document ID to verify
            provided_hash: Hash to verify against

        Returns:
            Tuple of (is_valid, stored_hash, message)
        """
        stored_hash = await self.get_document_hash(document_id)

        if stored_hash is None:
            logger.warning("Document not found for verification", document_id=document_id)
            return False, "", "Document not found in integrity store"

        is_valid = stored_hash.lower() == provided_hash.lower()

        if is_valid:
            message = "Document integrity verified successfully"
            logger.info("Integrity verification passed", document_id=document_id)
        else:
            message = "Document integrity verification failed - hashes do not match"
            logger.warning(
                "Integrity verification failed",
                document_id=document_id,
                stored_hash=stored_hash[:16] + "...",
                provided_hash=provided_hash[:16] + "...",
            )

        return is_valid, stored_hash, message

    async def verify_file_integrity(
        self,
        document_id: str,
        file_bytes: bytes,
    ) -> tuple[bool, str, str]:
        """
        Verify file bytes against stored hash.

        Args:
            document_id: Document ID
            file_bytes: File content to verify

        Returns:
            Tuple of (is_valid, stored_hash, message)
        """
        computed_hash = compute_sha256(file_bytes)
        return await self.verify_integrity(document_id, computed_hash)

    async def delete_record(self, document_id: str) -> bool:
        """
        Delete a hash record.

        Args:
            document_id: Document ID to delete

        Returns:
            True if deleted, False if not found
        """
        # Remove from cache
        if document_id in self._cache:
            del self._cache[document_id]

        # Remove from disk
        store = await self._load_store()
        if document_id in store:
            del store[document_id]
            await self._save_store(store)
            logger.info("Hash record deleted", document_id=document_id)
            return True

        return False

    async def list_records(self) -> list[HashRecord]:
        """
        List all hash records.

        Returns:
            List of HashRecord objects
        """
        store = await self._load_store()
        records = []

        for data in store.values():
            records.append(
                HashRecord(
                    document_id=data["document_id"],
                    sha256_hash=data["sha256_hash"],
                    filename=data["filename"],
                    timestamp=data["timestamp"],
                    file_size_bytes=data["file_size_bytes"],
                    blockchain_tx_id=data.get("blockchain_tx_id"),
                    blockchain_confirmed=data.get("blockchain_confirmed", False),
                )
            )

        return records

    # ================================================================
    # Blockchain Integration Stubs
    # These methods are placeholders for future blockchain integration
    # ================================================================

    async def submit_to_blockchain(self, document_id: str) -> Optional[str]:
        """
        Submit hash to blockchain (stub for future implementation).

        Args:
            document_id: Document ID to submit

        Returns:
            Transaction ID or None if failed

        Note:
            This is a placeholder for blockchain integration.
            Implement actual blockchain submission logic here.
        """
        logger.info(
            "Blockchain submission stub called",
            document_id=document_id,
            note="Implement actual blockchain integration",
        )

        # TODO: Implement actual blockchain submission
        # Example flow:
        # 1. Get hash record
        # 2. Submit to smart contract
        # 3. Get transaction ID
        # 4. Update record with tx_id and confirmed status

        return None

    async def verify_on_blockchain(self, document_id: str) -> Optional[bool]:
        """
        Verify hash on blockchain (stub for future implementation).

        Args:
            document_id: Document ID to verify

        Returns:
            True if verified on blockchain, False if not, None if not submitted

        Note:
            This is a placeholder for blockchain integration.
            Implement actual blockchain verification logic here.
        """
        record = await self.get_hash_record(document_id)

        if not record or not record.blockchain_tx_id:
            return None

        # TODO: Implement actual blockchain verification
        # Example flow:
        # 1. Query blockchain using tx_id
        # 2. Compare hash stored on-chain with local hash
        # 3. Return verification result

        return record.blockchain_confirmed

    def get_blockchain_status(self) -> dict:
        """
        Get blockchain integration status.

        Returns:
            Status dictionary
        """
        return {
            "blockchain_enabled": False,
            "blockchain_type": None,
            "smart_contract_address": None,
            "message": "Blockchain integration not yet implemented. System is blockchain-ready.",
        }


# Singleton instance
integrity_service = IntegrityService()
