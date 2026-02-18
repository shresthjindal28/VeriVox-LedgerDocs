"""WebSocket streaming routes for real-time chat."""

import json
import base64
import uuid
from typing import Dict, Set, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Header

from app.models.schemas import MessageType, WebSocketMessage
from app.services.rag_service import rag_service
from app.services.vector_service import vector_store
from app.services.call_session_service import (
    call_session_manager,
    CallSessionState,
    VoiceMode,
)
from app.services.openai_realtime_service import (
    openai_realtime_service,
    CallState,
)
from app.utils.helpers import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """
    Manages WebSocket connections.

    Handles connection tracking, broadcasting, and cleanup.
    """

    def __init__(self):
        """Initialize connection manager."""
        # Active connections by document_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # All connections
        self.all_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, document_id: str) -> bool:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: WebSocket instance
            document_id: Document ID for scoping

        Returns:
            True if connected successfully
        """
        await websocket.accept()

        # Track connection
        self.all_connections.add(websocket)

        if document_id not in self.active_connections:
            self.active_connections[document_id] = set()
        self.active_connections[document_id].add(websocket)

        logger.info(
            "WebSocket connected",
            document_id=document_id,
            total_connections=len(self.all_connections),
        )

        return True

    def disconnect(self, websocket: WebSocket, document_id: str) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket instance
            document_id: Document ID
        """
        self.all_connections.discard(websocket)

        if document_id in self.active_connections:
            self.active_connections[document_id].discard(websocket)
            if not self.active_connections[document_id]:
                del self.active_connections[document_id]

        logger.info(
            "WebSocket disconnected",
            document_id=document_id,
            total_connections=len(self.all_connections),
        )

    async def send_message(
        self,
        websocket: WebSocket,
        message: dict,
    ) -> None:
        """
        Send a message to a websocket.

        Args:
            websocket: Target WebSocket
            message: Message dict to send
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error("Failed to send message", error=str(e))

    async def broadcast_to_document(
        self,
        document_id: str,
        message: dict,
    ) -> None:
        """
        Broadcast message to all connections for a document.

        Args:
            document_id: Document ID
            message: Message to broadcast
        """
        if document_id not in self.active_connections:
            return

        disconnected = set()
        for websocket in self.active_connections[document_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)

        # Clean up disconnected
        for ws in disconnected:
            self.disconnect(ws, document_id)

    def get_stats(self) -> dict:
        """Get connection statistics."""
        return {
            "total_connections": len(self.all_connections),
            "documents_with_connections": len(self.active_connections),
            "connections_per_document": {
                doc_id: len(conns)
                for doc_id, conns in self.active_connections.items()
            },
        }


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/chat/{document_id}")
async def websocket_chat(websocket: WebSocket, document_id: str):
    """
    WebSocket endpoint for streaming chat.

    Protocol:
    1. Client sends: {"question": "your question here"}
    2. Server streams: {"type": "token", "content": "..."}
    3. Server sends final: {"type": "complete", "response": {...}}

    Error format: {"type": "error", "message": "..."}
    Status format: {"type": "status", "content": "..."}
    """
    # Verify document exists before accepting connection
    if not await vector_store.document_exists(document_id):
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=f"Document not found: {document_id}",
        )
        return

    # Accept connection
    await manager.connect(websocket, document_id)

    # Send connection confirmation
    await manager.send_message(
        websocket,
        {
            "type": MessageType.STATUS.value,
            "content": "Connected successfully. Send your questions.",
            "document_id": document_id,
        },
    )

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await manager.send_message(
                    websocket,
                    {
                        "type": MessageType.ERROR.value,
                        "message": "Invalid JSON format",
                    },
                )
                continue

            # Extract question
            question = message.get("question", "").strip()

            if not question:
                await manager.send_message(
                    websocket,
                    {
                        "type": MessageType.ERROR.value,
                        "message": "Question is required",
                    },
                )
                continue

            if len(question) > 2000:
                await manager.send_message(
                    websocket,
                    {
                        "type": MessageType.ERROR.value,
                        "message": "Question too long. Maximum 2000 characters.",
                    },
                )
                continue

            logger.info(
                "WebSocket question received",
                document_id=document_id,
                question_length=len(question),
            )

            # Send processing status
            await manager.send_message(
                websocket,
                {
                    "type": MessageType.STATUS.value,
                    "content": "Processing your question...",
                },
            )

            # Stream the answer
            try:
                async for chunk in rag_service.stream_answer(document_id, question):
                    chunk_data = json.loads(chunk)
                    await manager.send_message(websocket, chunk_data)

            except Exception as e:
                logger.error(
                    "Streaming error",
                    document_id=document_id,
                    error=str(e),
                )
                await manager.send_message(
                    websocket,
                    {
                        "type": MessageType.ERROR.value,
                        "message": f"Failed to generate response: {str(e)}",
                    },
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, document_id)
    except Exception as e:
        logger.error(
            "WebSocket error",
            document_id=document_id,
            error=str(e),
        )
        manager.disconnect(websocket, document_id)


@router.websocket("/ws/voice/realtime/{document_id}")
async def websocket_voice_realtime(websocket: WebSocket, document_id: str):
    """
    Real-time voice WebSocket endpoint with interruption support.

    Protocol:
    Client → Server:
    - {"type": "audio_chunk", "data": "<base64_audio>"}  # Audio data during speech
    - {"type": "end_speech"}                              # User finished speaking
    - {"type": "interrupt"}                               # Explicitly interrupt AI
    - {"type": "ping"}                                    # Keep-alive ping

    Server → Client:
    - {"type": "state_change", "state": "<state>"}       # Session state changed
    - {"type": "transcription", "text": "..."}           # User speech transcribed
    - {"type": "text_response", "text": "..."}           # AI text response
    - {"type": "audio_chunk", "data": "<base64_audio>"}  # AI audio response chunk
    - {"type": "audio_end"}                              # AI audio finished
    - {"type": "error", "message": "..."}                # Error occurred
    - {"type": "pong"}                                   # Keep-alive response

    States: idle, user_speaking, processing, ai_speaking, interrupted
    """
    import base64
    import uuid
    from app.services.realtime_voice_service import realtime_voice_service, ConversationState

    # Verify document exists
    if not await vector_store.document_exists(document_id):
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=f"Document not found: {document_id}",
        )
        return

    await websocket.accept()

    # Create session
    session_id = str(uuid.uuid4())
    session = realtime_voice_service.create_session(session_id, document_id)

    logger.info(
        "Real-time voice WebSocket connected",
        session_id=session_id,
        document_id=document_id,
    )

    # Callback helpers
    async def send_state_change(state: ConversationState):
        try:
            await websocket.send_json({
                "type": "state_change",
                "state": state.value
            })
        except Exception as e:
            logger.error(f"Failed to send state change: {e}")

    async def send_transcription(text: str):
        try:
            await websocket.send_json({
                "type": "transcription",
                "text": text
            })
        except Exception as e:
            logger.error(f"Failed to send transcription: {e}")

    async def send_text_response(text: str):
        try:
            await websocket.send_json({
                "type": "text_response",
                "text": text
            })
        except Exception as e:
            logger.error(f"Failed to send text response: {e}")

    # Convert async callbacks to sync for the service
    def on_state_change(state: ConversationState):
        import asyncio
        try:
            asyncio.create_task(send_state_change(state))
        except Exception:
            pass

    def on_transcription(text: str):
        import asyncio
        try:
            asyncio.create_task(send_transcription(text))
        except Exception:
            pass

    def on_text_response(text: str):
        import asyncio
        try:
            asyncio.create_task(send_text_response(text))
        except Exception:
            pass

    # Send initial state
    await websocket.send_json({
        "type": "state_change",
        "state": ConversationState.IDLE.value,
        "session_id": session_id,
        "message": "Connected. Start speaking."
    })

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
                continue

            msg_type = message.get("type", "")

            if msg_type == "ping":
                # Keep-alive
                await websocket.send_json({"type": "pong"})

            elif msg_type == "audio_chunk":
                # Decode and handle audio
                audio_b64 = message.get("data", "")
                if audio_b64:
                    try:
                        audio_bytes = base64.b64decode(audio_b64)
                        await realtime_voice_service.handle_audio_chunk(
                            session=session,
                            audio_data=audio_bytes,
                            on_state_change=on_state_change
                        )
                    except Exception as e:
                        logger.error(f"Error handling audio chunk: {e}")

            elif msg_type == "end_speech":
                # User finished speaking - process and respond
                try:
                    async for audio_chunk in realtime_voice_service.handle_end_speech(
                        session=session,
                        on_state_change=on_state_change,
                        on_transcription=on_transcription,
                        on_text_response=on_text_response
                    ):
                        # Stream audio to client
                        audio_b64 = base64.b64encode(audio_chunk).decode('utf-8')
                        await websocket.send_json({
                            "type": "audio_chunk",
                            "data": audio_b64
                        })

                    # Signal audio streaming complete
                    await websocket.send_json({"type": "audio_end"})

                except Exception as e:
                    logger.error(f"Error processing speech: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Failed to process speech: {str(e)}"
                    })
                    session.state = ConversationState.IDLE
                    on_state_change(session.state)

            elif msg_type == "interrupt":
                # Explicit interrupt
                if session.state == ConversationState.AI_SPEAKING:
                    session.request_cancellation()
                    session.state = ConversationState.INTERRUPTED
                    on_state_change(session.state)
                    logger.info(f"User interrupted AI for session: {session_id}")

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                })

    except WebSocketDisconnect:
        logger.info(f"Real-time voice WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Real-time voice WebSocket error: {e}")
    finally:
        await realtime_voice_service.end_session(session_id)


@router.websocket("/ws/voice/call/{document_id}")
async def websocket_voice_call(
    websocket: WebSocket,
    document_id: str,
):
    """
    Voice call WebSocket endpoint using OpenAI Realtime API.
    
    This provides a true phone-call-like experience with:
    - Full duplex audio streaming
    - Server-side Voice Activity Detection (VAD)
    - Natural interruption support
    - PDF-only intelligence enforcement
    
    Protocol:
    Client → Server:
    - {"type": "start_call"}                              # Initialize the call
    - {"type": "audio_chunk", "data": "<base64_pcm16>"}   # Audio data (PCM16, 24kHz, mono)
    - {"type": "interrupt"}                               # Interrupt AI response
    - {"type": "mute"}                                    # Mute microphone
    - {"type": "unmute"}                                  # Unmute microphone
    - {"type": "end_call"}                                # End the call
    - {"type": "ping"}                                    # Keep-alive
    
    Server → Client:
    - {"type": "call_started", "session_id": "...", "greeting": "..."}
    - {"type": "state_change", "state": "<state>"}
    - {"type": "transcription", "role": "user|assistant", "text": "..."}
    - {"type": "audio_chunk", "data": "<base64_pcm16>"}
    - {"type": "audio_end"}
    - {"type": "call_ended", "duration_seconds": ..., "questions_asked": ...}
    - {"type": "fallback_activated", "reason": "..."}
    - {"type": "error", "message": "...", "code": "..."}
    - {"type": "pong"}
    
    Call States: connecting, connected, user_speaking, ai_speaking, processing, ended
    
    Authentication:
    - Requires X-User-ID header (forwarded by gateway)
    - User must own the document
    """
    # Get user ID from header (forwarded by gateway after auth)
    user_id = websocket.headers.get("x-user-id")
    
    if not user_id:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Authentication required. Missing user ID.",
        )
        return
    
    # Verify document exists
    if not await vector_store.document_exists(document_id):
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=f"Document not found: {document_id}",
        )
        return
    
    await websocket.accept()
    
    call_session = None
    openai_session = None
    session_id = str(uuid.uuid4())
    
    logger.info(
        "Voice call WebSocket connected",
        session_id=session_id,
        user_id=user_id,
        document_id=document_id,
    )
    
    # Callback functions for OpenAI events
    async def on_state_change(state: CallState):
        try:
            await websocket.send_json({
                "type": "state_change",
                "state": state.value
            })
        except Exception as e:
            logger.error(f"Failed to send state change: {e}")
    
    async def on_audio(audio_bytes: bytes):
        try:
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            await websocket.send_json({
                "type": "audio_chunk",
                "data": audio_b64
            })
        except Exception as e:
            logger.error(f"Failed to send audio chunk: {e}")
    
    async def on_transcript(role: str, text: str):
        try:
            # Track conversation history
            if call_session and role in ["user", "assistant"]:
                call_session.add_message(role, text)
            
            await websocket.send_json({
                "type": "transcription",
                "role": role,
                "text": text
            })
        except Exception as e:
            logger.error(f"Failed to send transcription: {e}")
    
    async def on_error(error_msg: str):
        try:
            await websocket.send_json({
                "type": "error",
                "message": error_msg,
                "code": "openai_error"
            })
        except Exception as e:
            logger.error(f"Failed to send error: {e}")
    
    async def on_highlights(highlights: list):
        """Send highlights to frontend for PDF visualization."""
        try:
            await websocket.send_json({
                "type": "highlights",
                "highlights": highlights
            })
        except Exception as e:
            logger.error(f"Failed to send highlights: {e}")
    
    # Sync wrappers for callbacks
    def sync_on_state_change(state):
        import asyncio
        asyncio.create_task(on_state_change(state))
    
    def sync_on_audio(audio_bytes):
        import asyncio
        asyncio.create_task(on_audio(audio_bytes))
    
    def sync_on_transcript(role, text):
        import asyncio
        asyncio.create_task(on_transcript(role, text))
    
    def sync_on_error(error_msg):
        import asyncio
        asyncio.create_task(on_error(error_msg))
    
    def sync_on_highlights(highlights):
        import asyncio
        asyncio.create_task(on_highlights(highlights))
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {data[:100]}", session_id=session_id)
            
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data[:100]}", session_id=session_id)
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "code": "invalid_json"
                })
                continue
            
            msg_type = message.get("type", "")
            logger.info(f"Processing message type: {msg_type}", session_id=session_id, msg_type=msg_type)
            
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            elif msg_type == "start_call":
                logger.info("Processing start_call request", session_id=session_id, user_id=user_id, document_id=document_id)
                # Initialize the call
                try:
                    # Create call session with ownership validation
                    call_session = await call_session_manager.create_session(
                        user_id=user_id,
                        document_id=document_id,
                        voice_mode=VoiceMode.OPENAI_REALTIME,
                    )
                    
                    # Start OpenAI Realtime session
                    openai_session = await openai_realtime_service.start_call(
                        session_id=session_id,
                        document_id=document_id,
                        on_state_change=sync_on_state_change,
                        on_audio=sync_on_audio,
                        on_transcript=sync_on_transcript,
                        on_error=sync_on_error,
                        on_highlights=sync_on_highlights,
                        user_id=user_id,
                    )
                    
                    # Activate session
                    await call_session_manager.activate_session(call_session.session_id)
                    
                    # Get document summary for greeting
                    greeting = await rag_service.get_document_summary_for_voice(document_id)
                    
                    await websocket.send_json({
                        "type": "call_started",
                        "session_id": session_id,
                        "greeting": greeting,
                        "voice_mode": call_session.voice_mode.value,
                    })
                    
                    logger.info(f"Voice call started: {session_id}")
                    
                except ValueError as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                        "code": "validation_error"
                    })
                except PermissionError as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                        "code": "permission_denied"
                    })
                except Exception as e:
                    import traceback
                    error_trace = traceback.format_exc()
                    logger.error(
                        f"Failed to start call: {e}",
                        session_id=session_id,
                        user_id=user_id,
                        document_id=document_id,
                        error_type=type(e).__name__,
                        traceback=error_trace
                    )
                    
                    # Try fallback to Whisper+TTS
                    if call_session:
                        await call_session_manager.switch_to_fallback(call_session.session_id)
                        await websocket.send_json({
                            "type": "fallback_activated",
                            "reason": "OpenAI Realtime API unavailable, using Whisper+TTS",
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Failed to start call: {str(e)}",
                            "code": "call_start_failed"
                        })
            
            elif msg_type == "audio_chunk":
                if not openai_session:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Call not started. Send 'start_call' first.",
                        "code": "call_not_started"
                    })
                    continue
                
                audio_b64 = message.get("data", "")
                if audio_b64:
                    try:
                        audio_bytes = base64.b64decode(audio_b64)
                        
                        # Rate limit check
                        if call_session and not call_session_manager.check_rate_limit(
                            call_session, len(audio_bytes)
                        ):
                            logger.warning("Audio rate limit exceeded")
                            continue
                        
                        # Track bytes
                        if call_session:
                            call_session.total_audio_bytes_received += len(audio_bytes)
                        
                        # Send to OpenAI
                        await openai_realtime_service.send_audio(
                            session_id, 
                            audio_bytes
                        )
                    except Exception as e:
                        logger.error(f"Error processing audio chunk: {e}")
            
            elif msg_type == "interrupt":
                if openai_session:
                    await openai_realtime_service.interrupt(session_id)
                    if call_session:
                        call_session.interruption_count += 1
                    logger.info(f"User interrupted AI for session: {session_id}")
            
            elif msg_type == "mute":
                if call_session:
                    call_session.is_muted = True
                    await websocket.send_json({
                        "type": "state_change",
                        "state": "muted"
                    })
            
            elif msg_type == "unmute":
                if call_session:
                    call_session.is_muted = False
                    await websocket.send_json({
                        "type": "state_change",
                        "state": "unmuted"
                    })
            
            elif msg_type == "end_call":
                # End the call gracefully
                break
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                    "code": "unknown_message_type"
                })
    
    except WebSocketDisconnect:
        logger.info(f"Voice call WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Voice call WebSocket error: {e}")
    finally:
        # Cleanup
        duration_seconds = 0
        questions_asked = 0
        
        if openai_session:
            await openai_realtime_service.end_call(session_id)
        
        if call_session:
            duration_seconds = call_session.get_session_duration_seconds()
            questions_asked = call_session.question_count
            await call_session_manager.end_session(call_session.session_id)
        
        try:
            await websocket.send_json({
                "type": "call_ended",
                "duration_seconds": duration_seconds,
                "questions_asked": questions_asked,
            })
        except Exception:
            pass
        
        logger.info(
            f"Voice call ended: {session_id}, "
            f"duration: {duration_seconds:.1f}s, "
            f"questions: {questions_asked}"
        )


@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    return manager.get_stats()


@router.get("/ws/health")
async def websocket_health():
    """Check WebSocket service health."""
    return {
        "status": "healthy",
        "service": "websocket",
        "connections": len(manager.all_connections),
    }
