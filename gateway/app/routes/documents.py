"""
Document routes - proxied to PDF Service.
"""

from fastapi import APIRouter, Request, Response, Depends, UploadFile, File

from app.proxy import proxy_service
from app.middleware import auth_middleware

router = APIRouter(prefix="/api/documents", tags=["Documents"])


async def get_auth_headers(request: Request) -> dict:
    """Dependency to get auth headers."""
    payload = await auth_middleware.authenticate(request)
    return auth_middleware.get_user_headers(payload) if payload else {}


@router.get("", summary="List documents")
async def list_documents(request: Request, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """List all documents for the current user."""
    return await proxy_service.proxy_request(
        request, "pdf", "/api/documents",
        extra_headers=auth_headers
    )


@router.get("/", summary="List documents", include_in_schema=False)
async def list_documents_slash(request: Request, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """List all documents for the current user (with trailing slash)."""
    return await proxy_service.proxy_request(
        request, "pdf", "/api/documents",
        extra_headers=auth_headers
    )


@router.post("/upload", summary="Upload PDF")
async def upload_document(request: Request, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Upload a PDF document for processing."""
    return await proxy_service.proxy_request(
        request, "pdf", "/api/upload",
        extra_headers=auth_headers
    )


@router.get("/{document_id}", summary="Get document info")
async def get_document(request: Request, document_id: str, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Get document information."""
    return await proxy_service.proxy_request(
        request, "pdf", f"/api/documents/{document_id}",
        extra_headers=auth_headers
    )


@router.delete("/{document_id}", summary="Delete document")
async def delete_document(request: Request, document_id: str, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Delete a document."""
    return await proxy_service.proxy_request(
        request, "pdf", f"/api/documents/{document_id}",
        extra_headers=auth_headers
    )


@router.get("/{document_id}/file", summary="Download PDF file")
async def get_document_file(request: Request, document_id: str, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Download the original PDF file."""
    return await proxy_service.proxy_request(
        request, "pdf", f"/api/documents/{document_id}/file",
        extra_headers=auth_headers
    )


@router.get("/{document_id}/verify", summary="Verify document integrity")
async def verify_document(request: Request, document_id: str, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Verify document integrity."""
    return await proxy_service.proxy_request(
        request, "pdf", f"/api/documents/{document_id}/verify",
        extra_headers=auth_headers
    )


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    include_in_schema=False
)
async def proxy_documents(request: Request, path: str, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Proxy all other /api/documents/* requests."""
    return await proxy_service.proxy_request(
        request, "pdf", f"/api/documents/{path}",
        extra_headers=auth_headers
    )
