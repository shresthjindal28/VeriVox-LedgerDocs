"""
Chat and RAG routes - proxied to PDF Service.
"""

from fastapi import APIRouter, Request, Response, Depends

from app.proxy import proxy_service
from app.middleware import auth_middleware

router = APIRouter(prefix="/api/chat", tags=["Chat"])


async def get_auth_headers(request: Request) -> dict:
    """Dependency to get auth headers."""
    payload = await auth_middleware.authenticate(request)
    return auth_middleware.get_user_headers(payload) if payload else {}


@router.post("/{document_id}", summary="Ask question")
async def ask_question(request: Request, document_id: str, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Ask a question about a document."""
    # PDF service expects /api/chat with document_id in body
    return await proxy_service.proxy_request(
        request, "pdf", "/api/chat",
        extra_headers=auth_headers
    )


@router.get("/{document_id}/stream", summary="Stream answer")
async def stream_answer(request: Request, document_id: str, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Stream a response for a question (SSE)."""
    return await proxy_service.proxy_streaming(
        request, "pdf", f"/api/chat/{document_id}/stream",
        extra_headers=auth_headers
    )


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST"],
    include_in_schema=False
)
async def proxy_chat(request: Request, path: str, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Proxy all other /api/chat/* requests."""
    return await proxy_service.proxy_request(
        request, "pdf", f"/api/chat/{path}",
        extra_headers=auth_headers
    )
