"""
Voice routes - proxied to PDF Service.
"""

from fastapi import APIRouter, Request, Response, Depends

from app.proxy import proxy_service
from app.middleware import auth_middleware

router = APIRouter(prefix="/api/voice", tags=["Voice"])


async def get_auth_headers(request: Request) -> dict:
    """Dependency to get auth headers."""
    payload = await auth_middleware.authenticate(request)
    return auth_middleware.get_user_headers(payload) if payload else {}


@router.post("/chat", summary="Voice chat")
async def voice_chat(request: Request, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Voice-to-voice chat with AI teacher."""
    return await proxy_service.proxy_request(
        request, "pdf", "/api/voice/chat",
        extra_headers=auth_headers
    )


@router.post("/chat/audio", summary="Voice chat (audio response)")
async def voice_chat_audio(request: Request, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Voice chat with audio response."""
    return await proxy_service.proxy_request(
        request, "pdf", "/api/voice/chat/audio",
        extra_headers=auth_headers
    )


@router.post("/transcribe", summary="Transcribe audio")
async def transcribe(request: Request, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Transcribe audio to text."""
    return await proxy_service.proxy_request(
        request, "pdf", "/api/voice/transcribe",
        extra_headers=auth_headers
    )


@router.post("/synthesize", summary="Synthesize speech")
async def synthesize(request: Request, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Convert text to speech."""
    return await proxy_service.proxy_request(
        request, "pdf", "/api/voice/synthesize",
        extra_headers=auth_headers
    )


@router.get("/voices", summary="List voices")
async def list_voices(request: Request) -> Response:
    """Get available TTS voices."""
    return await proxy_service.proxy_request(
        request, "pdf", "/api/voice/voices"
    )


@router.get("/health", summary="Voice service health")
async def voice_health(request: Request) -> Response:
    """Check voice service health."""
    return await proxy_service.proxy_request(
        request, "pdf", "/api/voice/health"
    )


@router.get("/stream/{document_id}", summary="Stream voice response")
async def stream_voice(request: Request, document_id: str, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Stream voice response."""
    return await proxy_service.proxy_streaming(
        request, "pdf", f"/api/voice/stream/{document_id}",
        extra_headers=auth_headers
    )


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST"],
    include_in_schema=False
)
async def proxy_voice(request: Request, path: str, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Proxy all other /api/voice/* requests."""
    return await proxy_service.proxy_request(
        request, "pdf", f"/api/voice/{path}",
        extra_headers=auth_headers
    )
