"""API routes for blockchain verification and proofs."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.blockchain_service import blockchain_service, ProofType
from app.core.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/verify", tags=["verification"])


class VerificationResponse(BaseModel):
    """Response for verification request."""
    verified: bool
    proof_type: Optional[str] = None
    hash_value: Optional[str] = None
    timestamp: Optional[str] = None
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    chain_id: Optional[int] = None
    error: Optional[str] = None


class ProofListResponse(BaseModel):
    """Response for proof list request."""
    proofs: List[dict]
    count: int


class BlockchainStatusResponse(BaseModel):
    """Response for blockchain status."""
    enabled: bool
    chain_id: int
    rpc_url_configured: bool
    contract_configured: bool
    merkle_batching: bool


@router.get("/status", response_model=BlockchainStatusResponse)
async def get_blockchain_status():
    """
    Get blockchain integration status.
    """
    return BlockchainStatusResponse(
        enabled=settings.ENABLE_BLOCKCHAIN,
        chain_id=settings.BLOCKCHAIN_CHAIN_ID,
        rpc_url_configured=bool(settings.BLOCKCHAIN_RPC_URL),
        contract_configured=bool(settings.BLOCKCHAIN_CONTRACT_ADDRESS),
        merkle_batching=settings.ENABLE_MERKLE_BATCHING,
    )


@router.get("/document/{document_id}", response_model=VerificationResponse)
async def verify_document(document_id: str):
    """
    Verify document integrity against blockchain.
    
    Returns the blockchain proof and verification status for a document.
    """
    try:
        result = await blockchain_service.verify_document(document_id)
        
        return VerificationResponse(
            verified=result.get("verified", False),
            proof_type=result.get("proof_type"),
            hash_value=result.get("hash_value"),
            timestamp=result.get("timestamp"),
            tx_hash=result.get("tx_hash"),
            block_number=result.get("block_number"),
            chain_id=result.get("chain_id"),
            error=result.get("error"),
        )
        
    except Exception as e:
        logger.error(f"Document verification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}", response_model=VerificationResponse)
async def verify_session(session_id: str):
    """
    Verify voice session proof.
    
    Returns the blockchain proof for a voice call session.
    """
    try:
        result = await blockchain_service.verify_session(session_id)
        
        if "error" in result:
            return VerificationResponse(
                verified=False,
                error=result.get("error"),
            )
        
        return VerificationResponse(
            verified=result.get("verified", False),
            proof_type=result.get("proof_type"),
            hash_value=result.get("hash_value"),
            timestamp=result.get("timestamp"),
            tx_hash=result.get("tx_hash"),
            block_number=result.get("block_number"),
            chain_id=result.get("chain_id"),
        )
        
    except Exception as e:
        logger.error(f"Session verification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document/{document_id}/proofs", response_model=ProofListResponse)
async def get_document_proofs(document_id: str):
    """
    Get all proofs for a document.
    
    Returns all blockchain proofs associated with a document,
    including document hash, embedding fingerprint, extraction proofs, etc.
    """
    try:
        proofs = await blockchain_service.get_document_proofs(document_id)
        
        return ProofListResponse(
            proofs=proofs,
            count=len(proofs),
        )
        
    except Exception as e:
        logger.error(f"Failed to get document proofs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/proofs", response_model=ProofListResponse)
async def get_session_proofs(session_id: str):
    """
    Get all proofs for a voice session.
    
    Returns all blockchain proofs for a session including
    session anchor, transcript proof, retrieval proofs, etc.
    """
    try:
        proofs = await blockchain_service.get_session_proofs(session_id)
        
        return ProofListResponse(
            proofs=proofs,
            count=len(proofs),
        )
        
    except Exception as e:
        logger.error(f"Failed to get session proofs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/anchor/document/{document_id}")
async def anchor_document_manually(document_id: str):
    """
    Manually trigger document anchoring to blockchain.
    
    This is usually done automatically on upload, but can be
    triggered manually if needed.
    """
    if not settings.ENABLE_BLOCKCHAIN:
        raise HTTPException(
            status_code=400,
            detail="Blockchain integration is not enabled",
        )
    
    try:
        from app.services.pdf_service import pdf_service
        
        pdf_path = await pdf_service.get_pdf_path(document_id)
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="Document not found")
        
        with open(pdf_path, "rb") as f:
            document_bytes = f.read()
        
        proof = await blockchain_service.store_document_proof(
            document_id=document_id,
            document_bytes=document_bytes,
            user_id="manual",
            filename=f"{document_id}.pdf",
        )
        
        return {
            "success": True,
            "proof": proof.to_dict(),
            "message": "Document anchored to blockchain",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual anchoring failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
