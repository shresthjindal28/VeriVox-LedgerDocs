"""
Verification routes - proxied to PDF Service.
"""

from fastapi import APIRouter, Request, Response, Depends

from app.proxy import proxy_service
from app.middleware import auth_middleware

router = APIRouter(prefix="/api/verify", tags=["Verification"])


async def get_auth_headers(request: Request) -> dict:
    """Dependency to get auth headers."""
    payload = await auth_middleware.authenticate(request)
    return auth_middleware.get_user_headers(payload) if payload else {}


@router.get("/status", summary="Get blockchain status")
async def get_blockchain_status(request: Request, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Get blockchain integration status."""
    return await proxy_service.proxy_request(
        request, "pdf", "/api/verify/status",
        extra_headers=auth_headers
    )


@router.get("/document/{document_id}", summary="Verify document")
async def verify_document(request: Request, document_id: str, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Verify document integrity."""
    return await proxy_service.proxy_request(
        request, "pdf", f"/api/verify/document/{document_id}",
        extra_headers=auth_headers
    )


@router.get("/document/{document_id}/proofs", summary="Get document proofs")
async def get_document_proofs(request: Request, document_id: str, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Get all proofs for a document."""
    return await proxy_service.proxy_request(
        request, "pdf", f"/api/verify/document/{document_id}/proofs",
        extra_headers=auth_headers
    )


@router.get("/session/{session_id}", summary="Verify session")
async def verify_session(request: Request, session_id: str, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Verify session integrity."""
    return await proxy_service.proxy_request(
        request, "pdf", f"/api/verify/session/{session_id}",
        extra_headers=auth_headers
    )


@router.get("/session/{session_id}/proofs", summary="Get session proofs")
async def get_session_proofs(request: Request, session_id: str, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Get all proofs for a session."""
    return await proxy_service.proxy_request(
        request, "pdf", f"/api/verify/session/{session_id}/proofs",
        extra_headers=auth_headers
    )


@router.post("/anchor/document/{document_id}", summary="Anchor document manually")
async def anchor_document(request: Request, document_id: str, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Manually anchor a document to the blockchain."""
    return await proxy_service.proxy_request(
        request, "pdf", f"/api/verify/anchor/document/{document_id}",
        method="POST",
        extra_headers=auth_headers
    )


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    include_in_schema=False
)
async def proxy_verification(request: Request, path: str, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Proxy all other /api/verify/* requests."""
    return await proxy_service.proxy_request(
        request, "pdf", f"/api/verify/{path}",
        extra_headers=auth_headers
    )
