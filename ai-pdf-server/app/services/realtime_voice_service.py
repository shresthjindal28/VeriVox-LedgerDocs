"""
Real-time Voice Service with WebSocket streaming and interruption support.
Handles voice-to-voice conversations with the AI teacher, including:
- Real-time audio streaming
- Interruption detection and handling
- Session state management
- Audio buffering
"""

import asyncio
import base64
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, AsyncGenerator, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    """States for the voice conversation session."""
    IDLE = "idle"                    # No activity
    USER_SPEAKING = "user_speaking"  # User is speaking, buffering audio
    PROCESSING = "processing"        # Processing user speech, generating response
    AI_SPEAKING = "ai_speaking"      # AI is streaming audio response
    INTERRUPTED = "interrupted"      # User interrupted AI speech


@dataclass
class VoiceSession:
    """Manages state for a single voice conversation session."""
    session_id: str
    document_id: str
    state: ConversationState = ConversationState.IDLE
    audio_buffer: list = field(default_factory=list)
    current_task: Optional[asyncio.Task] = None
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    last_activity: datetime = field(default_factory=datetime.now)
    conversation_history: list = field(default_factory=list)
    
    def reset_buffer(self):
        """Clear the audio buffer."""
        self.audio_buffer = []
    
    def add_audio_chunk(self, chunk: bytes):
        """Add audio chunk to buffer."""
        self.audio_buffer.append(chunk)
        self.last_activity = datetime.now()
    
    def get_full_audio(self) -> bytes:
        """Get all buffered audio as single bytes object."""
        return b"".join(self.audio_buffer)
    
    def request_cancellation(self):
        """Signal cancellation of current task."""
        self.cancel_event.set()
    
    def reset_cancellation(self):
        """Reset cancellation event for new task."""
        self.cancel_event.clear()
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        # Keep last 20 messages for context
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]


class RealtimeVoiceService:
    """
    Service for handling real-time voice conversations with interruption support.
    
    Features:
    - WebSocket-based audio streaming
    - User interruption detection (pauses AI speech)
    - Session state management
    - Audio buffering and processing
    """
    
    def __init__(self):
        self.sessions: dict[str, VoiceSession] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = 300  # 5 minutes
        self._session_timeout = 1800  # 30 minutes
    
    async def start(self):
        """Start the service and cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_inactive_sessions())
        logger.info("RealtimeVoiceService started")
    
    async def stop(self):
        """Stop the service and cleanup."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all active sessions
        for session in self.sessions.values():
            if session.current_task:
                session.current_task.cancel()
        
        self.sessions.clear()
        logger.info("RealtimeVoiceService stopped")
    
    async def _cleanup_inactive_sessions(self):
        """Periodically cleanup inactive sessions."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                now = datetime.now()
                expired = [
                    sid for sid, session in self.sessions.items()
                    if (now - session.last_activity).total_seconds() > self._session_timeout
                ]
                for sid in expired:
                    await self.end_session(sid)
                    logger.info(f"Cleaned up inactive session: {sid}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
    
    def create_session(self, session_id: str, document_id: str) -> VoiceSession:
        """Create a new voice session."""
        session = VoiceSession(session_id=session_id, document_id=document_id)
        self.sessions[session_id] = session
        logger.info(f"Created voice session: {session_id} for document: {document_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[VoiceSession]:
        """Get an existing session."""
        return self.sessions.get(session_id)
    
    async def end_session(self, session_id: str):
        """End and cleanup a session."""
        session = self.sessions.pop(session_id, None)
        if session:
            if session.current_task:
                session.current_task.cancel()
                try:
                    await session.current_task
                except asyncio.CancelledError:
                    pass
            logger.info(f"Ended voice session: {session_id}")
    
    async def handle_audio_chunk(
        self,
        session: VoiceSession,
        audio_data: bytes,
        on_state_change: Callable[[ConversationState], None]
    ):
        """
        Handle incoming audio chunk from user.
        
        If AI is speaking, this triggers an interruption.
        Otherwise, buffer the audio for processing.
        """
        # Check if user is interrupting AI speech
        if session.state == ConversationState.AI_SPEAKING:
            await self._handle_interruption(session, on_state_change)
        
        # Update state to user speaking if not already
        if session.state in [ConversationState.IDLE, ConversationState.INTERRUPTED]:
            session.state = ConversationState.USER_SPEAKING
            on_state_change(session.state)
        
        # Buffer the audio
        session.add_audio_chunk(audio_data)
    
    async def _handle_interruption(
        self,
        session: VoiceSession,
        on_state_change: Callable[[ConversationState], None]
    ):
        """Handle user interruption of AI speech."""
        logger.info(f"Handling interruption for session: {session.session_id}")
        
        # Signal cancellation to stop audio streaming
        session.request_cancellation()
        
        # Update state
        session.state = ConversationState.INTERRUPTED
        on_state_change(session.state)
        
        # Wait for current task to acknowledge cancellation
        if session.current_task:
            try:
                # Give it a short time to stop gracefully
                await asyncio.wait_for(
                    asyncio.shield(session.current_task),
                    timeout=0.5
                )
            except (asyncio.TimeoutError, asyncio.CancelledError):
                session.current_task.cancel()
        
        # Reset for new input
        session.reset_buffer()
        session.reset_cancellation()
        logger.info(f"Interruption handled for session: {session.session_id}")
    
    async def process_user_speech(
        self,
        session: VoiceSession,
        on_state_change: Callable[[ConversationState], None],
        on_transcription: Callable[[str], None],
    ) -> Optional[str]:
        """
        Process buffered user audio and return transcription.
        
        Returns:
            Transcribed text or None if buffer is empty
        """
        from app.services.voice_service import voice_service
        
        # Get buffered audio
        audio_data = session.get_full_audio()
        if not audio_data:
            return None
        
        # Update state
        session.state = ConversationState.PROCESSING
        on_state_change(session.state)
        
        try:
            # Transcribe audio
            transcription = await voice_service.transcribe_audio(audio_data)
            
            if transcription:
                # Add to conversation history
                session.add_to_history("user", transcription)
                on_transcription(transcription)
            
            # Clear buffer
            session.reset_buffer()
            
            return transcription
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            session.state = ConversationState.IDLE
            on_state_change(session.state)
            return None
    
    async def stream_ai_response(
        self,
        session: VoiceSession,
        user_text: str,
        on_state_change: Callable[[ConversationState], None],
        on_text_chunk: Callable[[str], None],
    ) -> AsyncGenerator[bytes, None]:
        """
        Generate and stream AI audio response.
        
        Yields audio chunks that can be streamed to the client.
        Checks for interruption and stops if cancelled.
        """
        from app.services.teacher_service import teacher_service
        from app.services.voice_service import voice_service
        
        # Update state
        session.state = ConversationState.AI_SPEAKING
        on_state_change(session.state)
        
        try:
            # Build context from conversation history
            context_messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in session.conversation_history[-10:]  # Last 10 messages
            ]
            
            # Get AI text response using teacher service
            response_text = await teacher_service.answer_student_question(
                question=user_text,
                document_id=session.document_id,
                voice="nova"  # Default teacher voice
            )
            
            # Add to history
            session.add_to_history("assistant", response_text)
            
            # Notify about text response
            on_text_chunk(response_text)
            
            # Stream TTS audio
            async for audio_chunk in voice_service.stream_speech(
                text=response_text,
                voice="nova"
            ):
                # Check for interruption
                if session.cancel_event.is_set():
                    logger.info(f"AI response interrupted for session: {session.session_id}")
                    return
                
                yield audio_chunk
            
            # Completed successfully
            if not session.cancel_event.is_set():
                session.state = ConversationState.IDLE
                on_state_change(session.state)
                
        except asyncio.CancelledError:
            logger.info(f"AI response cancelled for session: {session.session_id}")
            raise
        except Exception as e:
            logger.error(f"Error streaming AI response: {e}")
            session.state = ConversationState.IDLE
            on_state_change(session.state)
    
    async def handle_end_speech(
        self,
        session: VoiceSession,
        on_state_change: Callable[[ConversationState], None],
        on_transcription: Callable[[str], None],
        on_text_response: Callable[[str], None],
    ) -> AsyncGenerator[bytes, None]:
        """
        Handle end of user speech - process and generate response.
        
        This is called when the user stops speaking.
        Processes the buffered audio and streams the AI response.
        """
        # Process user speech
        transcription = await self.process_user_speech(
            session=session,
            on_state_change=on_state_change,
            on_transcription=on_transcription
        )
        
        if not transcription:
            session.state = ConversationState.IDLE
            on_state_change(session.state)
            return
        
        # Stream AI response
        async for audio_chunk in self.stream_ai_response(
            session=session,
            user_text=transcription,
            on_state_change=on_state_change,
            on_text_chunk=on_text_response
        ):
            yield audio_chunk


# Singleton instance
realtime_voice_service = RealtimeVoiceService()
