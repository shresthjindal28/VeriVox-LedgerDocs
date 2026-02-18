"""Voice chat routes for AI teacher interactions."""

import base64
import json
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.responses import Response, StreamingResponse

from app.models.schemas import RAGResponse
from app.services.teacher_service import teacher_service
from app.services.vector_service import vector_store
from app.services.voice_service import voice_service
from app.utils.helpers import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Voice"])


# ============================================================
# Voice Schemas (inline for this route file)
# ============================================================


from pydantic import BaseModel, Field


class VoiceChatRequest(BaseModel):
    """Request for text-to-voice chat."""
    
    document_id: str = Field(..., description="Document ID to query")
    question: str = Field(..., description="Student's question")
    student_name: Optional[str] = Field(None, description="Student's name for personalization")
    voice: Optional[str] = Field(None, description="TTS voice (nova, alloy, echo, fable, onyx, shimmer)")
    return_audio: bool = Field(True, description="Whether to return audio response")


class VoiceChatResponse(BaseModel):
    """Response from voice chat."""
    
    answer: str = Field(..., description="Teacher's response text")
    audio_base64: Optional[str] = Field(None, description="Base64 encoded audio")
    audio_format: str = Field(default="mp3", description="Audio format")
    sources: list = Field(default_factory=list, description="Source references")
    confidence: float = Field(default=0.0, description="Response confidence")


class TranscriptionRequest(BaseModel):
    """Request for audio transcription."""
    
    audio_base64: str = Field(..., description="Base64 encoded audio")
    language: Optional[str] = Field(None, description="Language code (e.g., 'en')")


class TextToSpeechRequest(BaseModel):
    """Request for text-to-speech."""
    
    text: str = Field(..., description="Text to convert to speech")
    voice: Optional[str] = Field(None, description="Voice to use")
    speed: float = Field(default=1.0, ge=0.25, le=4.0, description="Speech speed")
    hd: bool = Field(default=False, description="Use HD quality")


# ============================================================
# REST Endpoints
# ============================================================


@router.post(
    "/voice/chat",
    response_model=VoiceChatResponse,
    summary="Voice chat with AI teacher",
    description="Send a text question and receive both text and audio response from the AI teacher.",
)
async def voice_chat(request: VoiceChatRequest):
    """
    Voice chat endpoint for AI teacher interaction.
    
    Send a text question and receive:
    - Text response from the AI teacher
    - Audio response (base64 encoded MP3)
    - Source references from the document
    """
    # Validate document exists
    if not await vector_store.document_exists(request.document_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {request.document_id}",
        )

    try:
        # Get teaching response
        response = await teacher_service.answer_student_question(
            document_id=request.document_id,
            question=request.question,
            student_name=request.student_name,
        )

        audio_base64 = None
        audio_format = "mp3"

        # Generate audio if requested
        if request.return_audio:
            speech = await voice_service.synthesize_speech(
                text=response.answer,
                voice=request.voice or voice_service.DEFAULT_TEACHER_VOICE,
                speed=0.95,
            )
            audio_base64 = voice_service.audio_to_base64(speech.audio_data)
            audio_format = speech.format

        return VoiceChatResponse(
            answer=response.answer,
            audio_base64=audio_base64,
            audio_format=audio_format,
            sources=[s.model_dump() for s in response.sources],
            confidence=response.confidence,
        )

    except Exception as e:
        logger.error("Voice chat failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice chat failed: {str(e)}",
        )


@router.post(
    "/voice/chat/audio",
    summary="Voice-to-voice chat with AI teacher",
    description="Upload audio question and receive audio response.",
)
async def voice_to_voice_chat(
    audio: UploadFile = File(..., description="Audio file (webm, mp3, wav)"),
    document_id: str = Form(..., description="Document ID"),
    student_name: Optional[str] = Form(None, description="Student name"),
    voice: Optional[str] = Form(None, description="TTS voice"),
):
    """
    Complete voice-to-voice interaction.
    
    Upload an audio file with your question and receive:
    - Audio response from the AI teacher
    - Downloadable MP3 file
    """
    # Validate document
    if not await vector_store.document_exists(document_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    try:
        # Read audio data
        audio_data = await audio.read()

        if len(audio_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty audio file",
            )

        # Process voice-to-voice
        response, speech = await teacher_service.voice_to_voice_chat(
            document_id=document_id,
            audio_data=audio_data,
            student_name=student_name,
            voice=voice,
        )

        # Return audio response
        return Response(
            content=speech.audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=teacher_response.mp3",
                "X-Answer-Text": base64.b64encode(response.answer.encode()).decode(),
                "X-Confidence": str(response.confidence),
            },
        )

    except Exception as e:
        logger.error("Voice-to-voice chat failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice-to-voice chat failed: {str(e)}",
        )


@router.post(
    "/voice/transcribe",
    summary="Transcribe audio to text",
    description="Convert audio to text using OpenAI Whisper.",
)
async def transcribe_audio(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    language: Optional[str] = Form(None, description="Language code"),
):
    """
    Transcribe audio file to text.
    
    Supported formats: mp3, wav, webm, m4a, ogg
    """
    try:
        audio_data = await audio.read()

        if len(audio_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty audio file",
            )

        result = await voice_service.transcribe_audio(
            audio_data=audio_data,
            language=language,
        )

        return {
            "text": result.text,
            "language": result.language,
        }

    except Exception as e:
        logger.error("Transcription failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}",
        )


@router.post(
    "/voice/synthesize",
    summary="Text to speech",
    description="Convert text to speech audio.",
)
async def synthesize_speech(request: TextToSpeechRequest):
    """
    Convert text to speech.
    
    Returns MP3 audio file.
    """
    if not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty",
        )

    try:
        if request.hd:
            result = await voice_service.synthesize_speech_hd(
                text=request.text,
                voice=request.voice,
                speed=request.speed,
            )
        else:
            result = await voice_service.synthesize_speech(
                text=request.text,
                voice=request.voice,
                speed=request.speed,
            )

        return Response(
            content=result.audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3",
            },
        )

    except Exception as e:
        logger.error("Speech synthesis failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis failed: {str(e)}",
        )


@router.get(
    "/voice/stream/{document_id}",
    summary="Stream voice response",
    description="Stream audio response for a question.",
)
async def stream_voice_response(
    document_id: str,
    question: str,
    student_name: Optional[str] = None,
    voice: Optional[str] = None,
):
    """
    Stream audio response for real-time playback.
    
    Returns chunked audio stream.
    """
    if not await vector_store.document_exists(document_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    async def generate():
        async for chunk in teacher_service.stream_voice_response(
            document_id=document_id,
            question=question,
            student_name=student_name,
            voice=voice,
        ):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="audio/mpeg",
    )


@router.get(
    "/voice/voices",
    summary="Get available voices",
    description="Get list of available TTS voices.",
)
async def get_voices():
    """Get available TTS voices with descriptions."""
    return {
        "voices": voice_service.get_available_voices(),
        "default": voice_service.DEFAULT_TEACHER_VOICE,
    }


@router.get(
    "/voice/health",
    summary="Voice service health check",
)
async def voice_health():
    """Check voice service health."""
    healthy = await voice_service.health_check()
    return {
        "status": "healthy" if healthy else "unhealthy",
        "service": "voice",
        "stt_available": healthy,
        "tts_available": healthy,
    }


# ============================================================
# WebSocket for Real-time Voice Chat
# ============================================================


@router.websocket("/ws/voice/{document_id}")
async def websocket_voice_chat(websocket: WebSocket, document_id: str):
    """
    WebSocket endpoint for real-time voice chat.
    
    Protocol:
    1. Client sends: {"type": "audio", "data": "<base64_audio>"}
       Or: {"type": "text", "question": "your question"}
    2. Server sends: {"type": "transcription", "text": "..."}
    3. Server sends: {"type": "answer", "text": "...", "audio": "<base64>"}
    
    For streaming:
    1. Server sends: {"type": "audio_chunk", "data": "<base64_chunk>"}
    2. Server sends: {"type": "complete", "answer": {...}}
    """
    # Verify document exists
    if not await vector_store.document_exists(document_id):
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=f"Document not found: {document_id}",
        )
        return

    await websocket.accept()
    
    # Send welcome message
    await websocket.send_json({
        "type": "connected",
        "message": "Hello! I'm your AI teacher. You can send me audio or text questions!",
        "document_id": document_id,
    })

    student_name = None
    voice = voice_service.DEFAULT_TEACHER_VOICE

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format",
                })
                continue

            msg_type = message.get("type", "")

            # Handle configuration
            if msg_type == "config":
                student_name = message.get("student_name")
                voice = message.get("voice", voice)
                await websocket.send_json({
                    "type": "config_updated",
                    "student_name": student_name,
                    "voice": voice,
                })
                continue

            # Handle audio input
            if msg_type == "audio":
                audio_base64 = message.get("data", "")
                if not audio_base64:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Audio data required",
                    })
                    continue

                try:
                    # Decode audio
                    audio_data = base64.b64decode(audio_base64)

                    # Send processing status
                    await websocket.send_json({
                        "type": "status",
                        "message": "Processing your voice...",
                    })

                    # Transcribe
                    transcription = await voice_service.transcribe_audio(audio_data)
                    
                    await websocket.send_json({
                        "type": "transcription",
                        "text": transcription.text,
                    })

                    # Get teacher response
                    response = await teacher_service.answer_student_question(
                        document_id=document_id,
                        question=transcription.text,
                        student_name=student_name,
                    )

                    # Generate speech
                    speech = await voice_service.synthesize_speech(
                        text=response.answer,
                        voice=voice,
                        speed=0.95,
                    )

                    # Send complete response
                    await websocket.send_json({
                        "type": "answer",
                        "text": response.answer,
                        "audio": voice_service.audio_to_base64(speech.audio_data),
                        "audio_format": speech.format,
                        "sources": [s.model_dump() for s in response.sources],
                        "confidence": response.confidence,
                    })

                except Exception as e:
                    logger.error("Voice processing error", error=str(e))
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Voice processing failed: {str(e)}",
                    })

            # Handle text input
            elif msg_type == "text":
                question = message.get("question", "").strip()
                if not question:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Question required",
                    })
                    continue

                try:
                    await websocket.send_json({
                        "type": "status",
                        "message": "Thinking...",
                    })

                    # Get teacher response
                    response = await teacher_service.answer_student_question(
                        document_id=document_id,
                        question=question,
                        student_name=student_name,
                    )

                    # Generate speech
                    speech = await voice_service.synthesize_speech(
                        text=response.answer,
                        voice=voice,
                        speed=0.95,
                    )

                    # Send response
                    await websocket.send_json({
                        "type": "answer",
                        "text": response.answer,
                        "audio": voice_service.audio_to_base64(speech.audio_data),
                        "audio_format": speech.format,
                        "sources": [s.model_dump() for s in response.sources],
                        "confidence": response.confidence,
                    })

                except Exception as e:
                    logger.error("Text processing error", error=str(e))
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Processing failed: {str(e)}",
                    })

    except WebSocketDisconnect:
        logger.info("Voice WebSocket disconnected", document_id=document_id)
    except Exception as e:
        logger.error("Voice WebSocket error", error=str(e))
