"""
WebSocket routes - proxied to backend services.
"""

from fastapi import APIRouter, WebSocket, Query
from typing import Optional

from app.websocket_proxy import websocket_proxy
from app.middleware import auth_middleware

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/chat/{document_id}")
async def websocket_chat(websocket: WebSocket, document_id: str):
    """
    WebSocket for streaming chat with document.
    
    Protocol:
    1. Client sends: {"question": "your question here"}
    2. Server streams: {"type": "token", "content": "..."}
    3. Server sends final: {"type": "complete", "response": {...}}
    """
    await websocket_proxy.proxy_websocket(
        client_ws=websocket,
        service="pdf",
        path=f"/ws/chat/{document_id}"
    )


@router.websocket("/ws/voice/{document_id}")
async def websocket_voice(websocket: WebSocket, document_id: str):
    """
    WebSocket for voice-to-voice chat.
    
    Protocol:
    - Client sends audio chunks as base64
    - Server responds with transcription and AI audio
    """
    await websocket_proxy.proxy_websocket(
        client_ws=websocket,
        service="pdf",
        path=f"/ws/voice/{document_id}"
    )


@router.websocket("/ws/voice/realtime/{document_id}")
async def websocket_voice_realtime(websocket: WebSocket, document_id: str):
    """
    Real-time voice WebSocket with interruption support.
    
    Protocol:
    Client → Server:
    - {"type": "audio_chunk", "data": "<base64>"}
    - {"type": "end_speech"}
    - {"type": "interrupt"}
    
    Server → Client:
    - {"type": "state_change", "state": "..."}
    - {"type": "transcription", "text": "..."}
    - {"type": "audio_chunk", "data": "<base64>"}
    - {"type": "audio_end"}
    """
    await websocket_proxy.proxy_websocket(
        client_ws=websocket,
        service="pdf",
        path=f"/ws/voice/realtime/{document_id}"
    )


@router.websocket("/ws/voice/call/{document_id}")
async def websocket_voice_call(websocket: WebSocket, document_id: str):
    """
    Voice call WebSocket using OpenAI Realtime API.
    
    This provides a true phone-call-like experience with:
    - Full duplex audio streaming (PCM16, 24kHz)
    - Server-side Voice Activity Detection
    - Natural interruption support
    - PDF-only intelligence enforcement
    
    Authentication:
    - Requires valid auth token
    - User must own the document
    
    Protocol:
    Client → Server:
    - {"type": "start_call"}
    - {"type": "audio_chunk", "data": "<base64_pcm16>"}
    - {"type": "interrupt"}
    - {"type": "mute"} / {"type": "unmute"}
    - {"type": "end_call"}
    
    Server → Client:
    - {"type": "call_started", "session_id": "...", "greeting": "..."}
    - {"type": "state_change", "state": "..."}
    - {"type": "transcription", "role": "...", "text": "..."}
    - {"type": "audio_chunk", "data": "<base64_pcm16>"}
    - {"type": "call_ended", "duration_seconds": ..., "questions_asked": ...}
    - {"type": "error", "message": "...", "code": "..."}
    """
    # Extract user info and forward to backend (required for voice call auth)
    extra_headers = {}
    
    # 1. Prefer Authorization header (if client could send it)
    auth_header = websocket.headers.get("authorization")
    
    # 2. Fallback: token from query string (browsers cannot set headers on WebSocket)
    if not auth_header:
        query_string = (websocket.scope.get("query_string") or b"").decode()
        if query_string:
            from urllib.parse import parse_qs
            params = parse_qs(query_string)
            token_list = params.get("token") or params.get("access_token")
            if token_list:
                auth_header = f"Bearer {token_list[0]}"
    
    if auth_header:
        user_info = await auth_middleware.get_user_from_token(auth_header)
        if user_info:
            user_id = user_info.get("user_id", "").strip()
            if user_id:
                extra_headers["X-User-ID"] = user_id
                extra_headers["X-User-Email"] = user_info.get("email", "") or ""
    
    await websocket_proxy.proxy_websocket(
        client_ws=websocket,
        service="pdf",
        path=f"/ws/voice/call/{document_id}",
        extra_headers=extra_headers
    )
