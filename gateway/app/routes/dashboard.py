"""
Dashboard routes - proxied to PDF Service.
"""

from fastapi import APIRouter, Request, Response, Depends

from app.proxy import proxy_service
from app.middleware import auth_middleware

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


async def get_auth_headers(request: Request) -> dict:
    """Dependency to get auth headers."""
    payload = await auth_middleware.authenticate(request)
    return auth_middleware.get_user_headers(payload) if payload else {}


@router.get("/stats", summary="Get dashboard statistics")
async def get_dashboard_stats(request: Request, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Get aggregated statistics for the current user."""
    return await proxy_service.proxy_request(
        request, "pdf", "/api/dashboard/stats",
        extra_headers=auth_headers
    )


@router.get("/documents", summary="Get user documents (paginated)")
async def get_dashboard_documents(request: Request, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Get paginated documents for the current user."""
    return await proxy_service.proxy_request(
        request, "pdf", "/api/dashboard/documents",
        extra_headers=auth_headers
    )


@router.get("/sessions/recent", summary="Get recent voice sessions")
async def get_recent_sessions(request: Request, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Get recent voice sessions for the current user."""
    return await proxy_service.proxy_request(
        request, "pdf", "/api/dashboard/sessions/recent",
        extra_headers=auth_headers
    )


@router.get("/extractions/recent", summary="Get recent RAG extractions")
async def get_recent_extractions(request: Request, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Get recent RAG extraction runs for the current user."""
    return await proxy_service.proxy_request(
        request, "pdf", "/api/dashboard/extractions/recent",
        extra_headers=auth_headers
    )


@router.get("/blockchain/proofs", summary="Get blockchain proofs")
async def get_blockchain_proofs(request: Request, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Get blockchain proofs for the current user."""
    return await proxy_service.proxy_request(
        request, "pdf", "/api/dashboard/blockchain/proofs",
        extra_headers=auth_headers
    )
