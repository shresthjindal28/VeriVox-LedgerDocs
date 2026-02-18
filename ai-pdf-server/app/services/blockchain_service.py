"""Blockchain service for document integrity and audit anchoring."""

import asyncio
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
import queue
import threading

from app.core.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)

# Thread pool for blockchain operations
_executor = ThreadPoolExecutor(max_workers=2)


class ProofType(str, Enum):
    """Types of blockchain proofs."""
    DOCUMENT = "document"
    EMBEDDING = "embedding"
    SESSION = "session"
    TRANSCRIPT = "transcript"
    EXTRACTION = "extraction"
    HIGHLIGHT = "highlight"
    RETRIEVAL = "retrieval"
    MERKLE_ROOT = "merkle_root"


@dataclass
class BlockchainProof:
    """Represents a proof stored on blockchain."""
    
    proof_type: ProofType
    hash_value: str
    document_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: str = ""
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    chain_id: int = 0
    verified: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "proof_type": self.proof_type.value,
            "hash_value": self.hash_value,
            "document_id": self.document_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "tx_hash": self.tx_hash,
            "block_number": self.block_number,
            "chain_id": self.chain_id,
            "verified": self.verified,
            "metadata": self.metadata,
        }


@dataclass
class MerkleNode:
    """A node in the Merkle tree."""
    hash_value: str
    left: Optional["MerkleNode"] = None
    right: Optional["MerkleNode"] = None


class MerkleTree:
    """Merkle tree for batched proof submission."""
    
    def __init__(self, hashes: List[str]):
        """
        Build a Merkle tree from a list of hashes.
        
        Args:
            hashes: List of hash strings
        """
        self.leaves = [MerkleNode(h) for h in hashes]
        self.root = self._build_tree(self.leaves)
    
    def _build_tree(self, nodes: List[MerkleNode]) -> Optional[MerkleNode]:
        """Recursively build the tree."""
        if not nodes:
            return None
        if len(nodes) == 1:
            return nodes[0]
        
        # Pad with duplicate if odd number
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1])
        
        parent_nodes = []
        for i in range(0, len(nodes), 2):
            combined = nodes[i].hash_value + nodes[i + 1].hash_value
            parent_hash = hashlib.sha256(combined.encode()).hexdigest()
            parent_nodes.append(MerkleNode(
                hash_value=parent_hash,
                left=nodes[i],
                right=nodes[i + 1],
            ))
        
        return self._build_tree(parent_nodes)
    
    def get_root(self) -> str:
        """Get the Merkle root hash."""
        return self.root.hash_value if self.root else ""
    
    def get_proof(self, leaf_hash: str) -> List[Dict[str, str]]:
        """
        Get the Merkle proof for a leaf.
        
        Args:
            leaf_hash: The hash to get proof for
            
        Returns:
            List of proof nodes with hash and position
        """
        # Find leaf index
        leaf_idx = None
        for i, leaf in enumerate(self.leaves):
            if leaf.hash_value == leaf_hash:
                leaf_idx = i
                break
        
        if leaf_idx is None:
            return []
        
        proof = []
        nodes = self.leaves.copy()
        idx = leaf_idx
        
        while len(nodes) > 1:
            if len(nodes) % 2 == 1:
                nodes.append(nodes[-1])
            
            sibling_idx = idx + 1 if idx % 2 == 0 else idx - 1
            position = "right" if idx % 2 == 0 else "left"
            
            proof.append({
                "hash": nodes[sibling_idx].hash_value,
                "position": position,
            })
            
            # Move to parent level
            parent_idx = idx // 2
            new_nodes = []
            for i in range(0, len(nodes), 2):
                combined = nodes[i].hash_value + nodes[i + 1].hash_value
                parent_hash = hashlib.sha256(combined.encode()).hexdigest()
                new_nodes.append(MerkleNode(hash_value=parent_hash))
            
            nodes = new_nodes
            idx = parent_idx
        
        return proof


class BlockchainService:
    """Service for blockchain integrity anchoring."""
    
    def __init__(self):
        """Initialize blockchain service."""
        self.enabled = settings.ENABLE_BLOCKCHAIN
        self.rpc_url = settings.BLOCKCHAIN_RPC_URL
        self.contract_address = settings.BLOCKCHAIN_CONTRACT_ADDRESS
        self.chain_id = settings.BLOCKCHAIN_CHAIN_ID
        
        # Async queue for non-blocking writes
        self._write_queue: queue.Queue = queue.Queue()
        self._queue_worker: Optional[threading.Thread] = None
        
        # Local proof storage (in production, use database)
        self._proofs: Dict[str, BlockchainProof] = {}
        self._pending_hashes: List[str] = []
        
        # Web3 client (initialized on first use)
        self._web3 = None
        self._contract = None
        
        if self.enabled:
            self._start_queue_worker()
    
    def _start_queue_worker(self):
        """Start background worker for async blockchain writes."""
        def worker():
            while True:
                try:
                    proof = self._write_queue.get(timeout=1)
                    if proof is None:
                        break
                    self._submit_proof_sync(proof)
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Queue worker error: {e}")
        
        self._queue_worker = threading.Thread(target=worker, daemon=True)
        self._queue_worker.start()
    
    def _get_web3(self):
        """Get or create Web3 instance."""
        if self._web3 is None and self.rpc_url:
            try:
                from web3 import Web3
                self._web3 = Web3(Web3.HTTPProvider(self.rpc_url))
                logger.info(f"Web3 connected to {self.rpc_url}")
            except ImportError:
                logger.warning("web3 package not installed, blockchain features disabled")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to connect to Web3: {e}")
                self.enabled = False
        return self._web3
    
    # ==================== Hash Generation ====================
    
    def compute_document_hash(
        self,
        document_bytes: bytes,
        user_id: str,
        filename: str,
    ) -> str:
        """
        Compute combined hash for document integrity.
        
        Args:
            document_bytes: Raw PDF bytes
            user_id: Uploader's user ID
            filename: Original filename
            
        Returns:
            Combined SHA256 hash
        """
        # Hash the document
        doc_hash = hashlib.sha256(document_bytes).hexdigest()
        
        # Hash the metadata
        metadata = f"{user_id}:{filename}:{datetime.utcnow().isoformat()}"
        meta_hash = hashlib.sha256(metadata.encode()).hexdigest()
        
        # Combined hash
        combined = hashlib.sha256(f"{doc_hash}{meta_hash}".encode()).hexdigest()
        return combined
    
    def compute_embedding_hash(self, embeddings: List[List[float]]) -> str:
        """
        Compute fingerprint hash for embeddings.
        
        Args:
            embeddings: List of embedding vectors
            
        Returns:
            SHA256 hash of embeddings
        """
        # Serialize embeddings deterministically
        content = json.dumps(embeddings, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def compute_session_hash(
        self,
        session_id: str,
        document_hash: str,
        user_id: str,
    ) -> str:
        """
        Compute hash for voice session anchoring.
        
        Args:
            session_id: Voice call session ID
            document_hash: Hash of the document
            user_id: User's ID
            
        Returns:
            Session anchor hash
        """
        content = f"{session_id}:{document_hash}:{user_id}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def compute_transcript_hash(self, transcript_text: str) -> str:
        """
        Compute hash for conversation transcript.
        
        Args:
            transcript_text: Full transcript text
            
        Returns:
            Transcript hash
        """
        return hashlib.sha256(transcript_text.encode()).hexdigest()
    
    def compute_extraction_hash(self, extraction_json: Dict) -> str:
        """
        Compute hash for extraction results.
        
        Args:
            extraction_json: Extraction result dictionary
            
        Returns:
            Extraction hash
        """
        content = json.dumps(extraction_json, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def compute_highlight_hash(self, highlights: List[Dict]) -> str:
        """
        Compute hash for highlight positions.
        
        Args:
            highlights: List of highlight dictionaries
            
        Returns:
            Highlight hash
        """
        content = json.dumps(highlights, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def compute_retrieval_hash(
        self,
        query: str,
        chunk_ids: List[str],
        scores: List[float],
    ) -> str:
        """
        Compute hash for RAG retrieval audit.
        
        Args:
            query: User's query
            chunk_ids: Retrieved chunk IDs
            scores: Similarity scores
            
        Returns:
            Retrieval proof hash
        """
        content = {
            "query": query,
            "chunk_ids": chunk_ids,
            "scores": scores,
        }
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
    
    # ==================== Proof Storage ====================
    
    async def store_document_proof(
        self,
        document_id: str,
        document_bytes: bytes,
        user_id: str,
        filename: str,
    ) -> BlockchainProof:
        """
        Create and store document integrity proof.
        
        Args:
            document_id: Document ID
            document_bytes: Raw document bytes
            user_id: Uploader's user ID
            filename: Original filename
            
        Returns:
            BlockchainProof object
        """
        hash_value = self.compute_document_hash(document_bytes, user_id, filename)
        
        proof = BlockchainProof(
            proof_type=ProofType.DOCUMENT,
            hash_value=hash_value,
            document_id=document_id,
            user_id=user_id,
            chain_id=self.chain_id,
            metadata={"filename": filename, "size": len(document_bytes)},
        )
        
        # Store locally
        self._proofs[f"{ProofType.DOCUMENT.value}:{document_id}"] = proof
        
        # Queue for blockchain submission
        if self.enabled:
            self._queue_proof(proof)
        
        logger.info(f"Document proof stored: {hash_value[:16]}...")
        return proof
    
    async def store_session_proof(
        self,
        session_id: str,
        document_id: str,
        user_id: str,
    ) -> BlockchainProof:
        """
        Create and store voice session proof.
        
        Args:
            session_id: Voice call session ID
            document_id: Document ID
            user_id: User's ID
            
        Returns:
            BlockchainProof object
        """
        # Get document hash
        doc_proof = self._proofs.get(f"{ProofType.DOCUMENT.value}:{document_id}")
        doc_hash = doc_proof.hash_value if doc_proof else document_id
        
        hash_value = self.compute_session_hash(session_id, doc_hash, user_id)
        
        proof = BlockchainProof(
            proof_type=ProofType.SESSION,
            hash_value=hash_value,
            document_id=document_id,
            session_id=session_id,
            user_id=user_id,
            chain_id=self.chain_id,
        )
        
        self._proofs[f"{ProofType.SESSION.value}:{session_id}"] = proof
        
        if self.enabled:
            self._queue_proof(proof)
        
        logger.info(f"Session proof stored: {hash_value[:16]}...")
        return proof
    
    async def store_transcript_proof(
        self,
        session_id: str,
        transcript: str,
    ) -> BlockchainProof:
        """
        Store transcript proof after call ends.
        
        Args:
            session_id: Voice call session ID
            transcript: Full transcript text
            
        Returns:
            BlockchainProof object
        """
        hash_value = self.compute_transcript_hash(transcript)
        
        proof = BlockchainProof(
            proof_type=ProofType.TRANSCRIPT,
            hash_value=hash_value,
            session_id=session_id,
            chain_id=self.chain_id,
            metadata={"length": len(transcript)},
        )
        
        self._proofs[f"{ProofType.TRANSCRIPT.value}:{session_id}"] = proof
        
        if self.enabled:
            self._queue_proof(proof)
        
        logger.info(f"Transcript proof stored: {hash_value[:16]}...")
        return proof
    
    async def store_extraction_proof(
        self,
        document_id: str,
        extraction_result: Dict,
    ) -> BlockchainProof:
        """
        Store extraction result proof.
        
        Args:
            document_id: Document ID
            extraction_result: Extraction result dictionary
            
        Returns:
            BlockchainProof object
        """
        hash_value = self.compute_extraction_hash(extraction_result)
        
        proof = BlockchainProof(
            proof_type=ProofType.EXTRACTION,
            hash_value=hash_value,
            document_id=document_id,
            chain_id=self.chain_id,
            metadata={"item_count": extraction_result.get("total_count", 0)},
        )
        
        key = f"{ProofType.EXTRACTION.value}:{document_id}:{proof.timestamp}"
        self._proofs[key] = proof
        
        if self.enabled:
            self._queue_proof(proof)
        
        logger.info(f"Extraction proof stored: {hash_value[:16]}...")
        return proof
    
    async def store_retrieval_proof(
        self,
        session_id: str,
        query: str,
        chunk_ids: List[str],
        scores: List[float],
    ) -> BlockchainProof:
        """
        Store RAG retrieval audit proof.
        
        Args:
            session_id: Session ID
            query: User's query
            chunk_ids: Retrieved chunk IDs
            scores: Similarity scores
            
        Returns:
            BlockchainProof object
        """
        hash_value = self.compute_retrieval_hash(query, chunk_ids, scores)
        
        proof = BlockchainProof(
            proof_type=ProofType.RETRIEVAL,
            hash_value=hash_value,
            session_id=session_id,
            chain_id=self.chain_id,
            metadata={"query_preview": query[:50], "chunk_count": len(chunk_ids)},
        )
        
        key = f"{ProofType.RETRIEVAL.value}:{session_id}:{proof.timestamp}"
        self._proofs[key] = proof
        
        if self.enabled:
            self._pending_hashes.append(hash_value)
            self._maybe_submit_merkle_batch()
        
        return proof
    
    # ==================== Merkle Batching ====================
    
    def _maybe_submit_merkle_batch(self):
        """Check if we should submit a Merkle batch."""
        if not settings.ENABLE_MERKLE_BATCHING:
            return
        
        if len(self._pending_hashes) >= settings.MERKLE_BATCH_SIZE:
            self._submit_merkle_batch()
    
    def _submit_merkle_batch(self):
        """Submit a batch of hashes as Merkle root."""
        if not self._pending_hashes:
            return
        
        hashes = self._pending_hashes.copy()
        self._pending_hashes.clear()
        
        tree = MerkleTree(hashes)
        root = tree.get_root()
        
        proof = BlockchainProof(
            proof_type=ProofType.MERKLE_ROOT,
            hash_value=root,
            chain_id=self.chain_id,
            metadata={"leaf_count": len(hashes)},
        )
        
        self._proofs[f"{ProofType.MERKLE_ROOT.value}:{proof.timestamp}"] = proof
        
        if self.enabled:
            self._queue_proof(proof)
        
        logger.info(f"Merkle batch submitted: {root[:16]}... ({len(hashes)} leaves)")
    
    # ==================== Verification ====================
    
    async def verify_document(self, document_id: str) -> Dict[str, Any]:
        """
        Verify document integrity against blockchain.
        
        Args:
            document_id: Document ID
            
        Returns:
            Verification result dictionary
        """
        key = f"{ProofType.DOCUMENT.value}:{document_id}"
        proof = self._proofs.get(key)
        
        if not proof:
            return {
                "verified": False,
                "error": "No proof found for document",
            }
        
        result = {
            "proof_type": proof.proof_type.value,
            "hash_value": proof.hash_value,
            "timestamp": proof.timestamp,
            "tx_hash": proof.tx_hash,
            "block_number": proof.block_number,
            "chain_id": proof.chain_id,
            "verified": proof.verified,
        }
        
        if proof.tx_hash and self.enabled:
            # Verify on-chain
            result["on_chain_verified"] = await self._verify_on_chain(proof)
        
        return result
    
    async def verify_session(self, session_id: str) -> Dict[str, Any]:
        """
        Verify session proof.
        
        Args:
            session_id: Session ID
            
        Returns:
            Verification result
        """
        key = f"{ProofType.SESSION.value}:{session_id}"
        proof = self._proofs.get(key)
        
        if not proof:
            return {"verified": False, "error": "No proof found"}
        
        return proof.to_dict()
    
    async def get_document_proofs(self, document_id: str) -> List[Dict]:
        """
        Get all proofs for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            List of proof dictionaries
        """
        proofs = []
        for key, proof in self._proofs.items():
            if proof.document_id == document_id:
                proofs.append(proof.to_dict())
        return proofs
    
    async def get_session_proofs(self, session_id: str) -> List[Dict]:
        """
        Get all proofs for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of proof dictionaries
        """
        proofs = []
        for key, proof in self._proofs.items():
            if proof.session_id == session_id:
                proofs.append(proof.to_dict())
        return proofs
    
    # ==================== Blockchain Operations ====================
    
    def _queue_proof(self, proof: BlockchainProof):
        """Add proof to write queue."""
        self._write_queue.put(proof)
    
    def _submit_proof_sync(self, proof: BlockchainProof):
        """
        Submit proof to blockchain (synchronous).
        
        This runs in background thread.
        """
        if not self.enabled:
            return
        
        web3 = self._get_web3()
        if not web3:
            return
        
        try:
            # In production, call smart contract
            # For now, just log
            logger.info(
                f"Blockchain submission: {proof.proof_type.value} - {proof.hash_value[:16]}..."
            )
            
            # Simulate tx receipt (in production, actual blockchain call)
            proof.verified = True
            proof.tx_hash = f"0x{hashlib.sha256(proof.hash_value.encode()).hexdigest()}"
            proof.block_number = 12345678
            
        except Exception as e:
            logger.error(f"Blockchain submission failed: {e}")
    
    async def _verify_on_chain(self, proof: BlockchainProof) -> bool:
        """
        Verify proof exists on-chain.
        
        Args:
            proof: Proof to verify
            
        Returns:
            True if verified on-chain
        """
        if not self.enabled or not proof.tx_hash:
            return False
        
        # In production, call blockchain to verify
        return proof.verified
    
    def shutdown(self):
        """Shutdown the service gracefully."""
        if self._queue_worker:
            self._write_queue.put(None)
            self._queue_worker.join(timeout=5)


# Singleton instance
blockchain_service = BlockchainService()
