"""Dashboard routes for aggregating user statistics and data."""

from typing import Optional
from fastapi import APIRouter, Request, Query

from app.services.dashboard_service import dashboard_service
from app.utils.dependencies import require_user_id

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", summary="Get dashboard statistics")
async def get_dashboard_stats(request: Request):
    """
    Get aggregated statistics for the authenticated user.
    Returns: total_documents, active_sessions, total_extractions, total_proofs.
    """
    user_id = await require_user_id(request)
    return await dashboard_service.get_stats(user_id)


@router.get("/documents", summary="Get user documents (paginated)")
async def get_dashboard_documents(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
):
    """
    Get paginated list of documents for the authenticated user.
    Returns: documents (id, name, upload_date, pages, blockchain_status, blockchain_hash), pagination.
    """
    user_id = await require_user_id(request)
    return await dashboard_service.get_user_documents(user_id, page=page, limit=limit)


@router.get("/sessions/recent", summary="Get recent voice sessions")
async def get_recent_sessions(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get recent voice sessions for the authenticated user.
    
    Args:
        limit: Maximum number of sessions to return (1-100)
        offset: Offset for pagination
        
    Returns:
        Dictionary with:
        - sessions: List of session data
        - total: Total count
        - limit: Limit used
        - offset: Offset used
    """
    user_id = await require_user_id(request)
    result = await dashboard_service.get_recent_sessions(user_id, limit, offset)
    return result


@router.get("/blockchain/proofs", summary="Get blockchain proofs")
async def get_blockchain_proofs(
    request: Request,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    proof_type: Optional[str] = Query(None, description="Filter by proof type")
):
    """
    Get blockchain proofs for the authenticated user.
    
    Args:
        limit: Maximum number of proofs to return (1-100)
        offset: Offset for pagination
        proof_type: Optional filter by proof type (document, session, transcript, extraction)
        
    Returns:
        Dictionary with:
        - proofs: List of proof data
        - total: Total count
        - limit: Limit used
        - offset: Offset used
    """
    user_id = await require_user_id(request)
    result = await dashboard_service.get_blockchain_proofs(
        user_id, limit, offset, proof_type
    )
    return result
