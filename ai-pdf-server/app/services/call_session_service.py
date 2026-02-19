"""
Call Session Service for managing real-time voice call sessions.

This service handles:
- Session lifecycle management (create, get, end, cleanup)
- User-document ownership validation
- Conversation memory within sessions
- Rate limiting and session limits
- Fallback handling when OpenAI Realtime API is unavailable
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
import httpx

from app.core.config import settings
from app.core.supabase import supabase
from app.services.vector_service import vector_store
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class CallSessionState(str, Enum):
    """States for a call session."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    ERROR = "error"


class VoiceMode(str, Enum):
    """Voice processing mode."""
    OPENAI_REALTIME = "openai_realtime"  # True duplex via OpenAI Realtime API
    WHISPER_TTS = "whisper_tts"  # Fallback: Whisper STT + TTS


@dataclass
class ConversationMessage:
    """A single message in the conversation history."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    audio_duration_ms: Optional[int] = None
    sources: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CallSession:
    """
    Represents an active voice call session.
    
    Binds together:
    - User identity
    - Document/PDF context
    - Conversation memory
    - Session state and timing
    """
    session_id: str
    user_id: str
    document_id: str
    state: CallSessionState = CallSessionState.INITIALIZING
    voice_mode: VoiceMode = VoiceMode.OPENAI_REALTIME
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    # Conversation memory (cleared after session ends)
    conversation_history: List[ConversationMessage] = field(default_factory=list)
    
    # Session metadata
    total_audio_bytes_received: int = 0
    total_audio_bytes_sent: int = 0
    interruption_count: int = 0
    question_count: int = 0
    
    # Connection state
    is_muted: bool = False
    openai_session_id: Optional[str] = None
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
    
    def add_message(
        self,
        role: str,
        content: str,
        audio_duration_ms: Optional[int] = None,
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Add a message to conversation history."""
        self.conversation_history.append(ConversationMessage(
            role=role,
            content=content,
            audio_duration_ms=audio_duration_ms,
            sources=sources or []
        ))
        self.update_activity()
        
        # Limit history to last 20 messages to prevent memory bloat
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def get_recent_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history for context."""
        recent = self.conversation_history[-limit:]
        return [
            {"role": msg.role, "content": msg.content}
            for msg in recent
        ]
    
    def get_session_duration_seconds(self) -> float:
        """Get total session duration in seconds."""
        return (datetime.now() - self.created_at).total_seconds()
    
    def is_expired(self, timeout_minutes: int, max_duration_minutes: int) -> bool:
        """Check if session has expired due to inactivity or max duration."""
        now = datetime.now()
        
        # Check inactivity timeout
        inactivity = (now - self.last_activity).total_seconds() / 60
        if inactivity > timeout_minutes:
            return True
        
        # Check max duration
        total_duration = (now - self.created_at).total_seconds() / 60
        if total_duration > max_duration_minutes:
            return True
        
        return False


class CallSessionManager:
    """
    Manages all active call sessions.
    
    Responsibilities:
    - Create and validate sessions
    - Enforce user-document ownership
    - Track concurrent calls per user
    - Cleanup expired sessions
    - Handle fallback to Whisper+TTS
    """
    
    def __init__(self):
        self.sessions: Dict[str, CallSession] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start_cleanup_task(self) -> None:
        """Start background task for session cleanup."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Started session cleanup background task")
    
    async def stop_cleanup_task(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped session cleanup background task")
    
    async def _cleanup_loop(self) -> None:
        """Background loop to cleanup expired sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def create_session(
        self,
        user_id: str,
        document_id: str,
        voice_mode: VoiceMode = VoiceMode.OPENAI_REALTIME
    ) -> CallSession:
        """
        Create a new call session.
        
        Args:
            user_id: Authenticated user ID
            document_id: Document to discuss
            voice_mode: Voice processing mode
        
        Returns:
            New CallSession
        
        Raises:
            ValueError: If validation fails
            PermissionError: If user doesn't own document
        """
        # Check concurrent call limit
        user_session_count = len(self.user_sessions.get(user_id, []))
        if user_session_count >= settings.VOICE_MAX_CONCURRENT_CALLS_PER_USER:
            raise ValueError(
                f"Maximum concurrent calls ({settings.VOICE_MAX_CONCURRENT_CALLS_PER_USER}) reached. "
                "Please end your current call first."
            )
        
        # Verify document exists
        if not await vector_store.document_exists(document_id):
            raise ValueError(f"Document not found: {document_id}")
        
        # Verify user owns the document
        if not await self.verify_document_ownership(user_id, document_id):
            raise PermissionError(
                "You don't have permission to access this document. "
                "Only the document owner can start a voice call."
            )
        
        # Create session
        session_id = str(uuid.uuid4())
        session = CallSession(
            session_id=session_id,
            user_id=user_id,
            document_id=document_id,
            voice_mode=voice_mode,
            state=CallSessionState.INITIALIZING,
        )
        
        # Track session
        self.sessions[session_id] = session
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session_id)
        
        # Persist to database
        await self._persist_session_create(session)
        
        logger.info(
            "Created call session",
            session_id=session_id,
            user_id=user_id,
            document_id=document_id,
            voice_mode=voice_mode.value
        )
        
        return session
    
    async def verify_document_ownership(
        self,
        user_id: str,
        document_id: str
    ) -> bool:
        """
        Verify that a user owns a document.
        
        Queries the User-Service to check document ownership.
        
        Args:
            user_id: User ID to check
            document_id: Document ID to check
        
        Returns:
            True if user owns the document
        """
        try:
            # Query User-Service for document ownership
            # The User-Service should have an internal endpoint for this
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://localhost:8001/internal/documents/{document_id}/owner",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("owner_id") == user_id
                elif response.status_code == 404:
                    # Document not found in user service - allow if exists in vector store
                    # This handles documents uploaded before ownership tracking
                    logger.warning(
                        f"Document {document_id} not found in User-Service, allowing access"
                    )
                    return True
                else:
                    logger.error(f"Ownership check failed: {response.status_code}")
                    return False
                    
        except httpx.RequestError as e:
            # If User-Service is unavailable, allow access but log warning
            logger.warning(
                f"Could not verify document ownership (User-Service unavailable): {e}. "
                "Allowing access."
            )
            return True
        except Exception as e:
            logger.error(f"Error verifying document ownership: {e}")
            return True  # Fail open for now, can be changed to fail closed
    
    def get_session(self, session_id: str) -> Optional[CallSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)
    
    def get_user_sessions(self, user_id: str) -> List[CallSession]:
        """Get all active sessions for a user."""
        session_ids = self.user_sessions.get(user_id, [])
        return [
            self.sessions[sid]
            for sid in session_ids
            if sid in self.sessions
        ]
    
    async def activate_session(self, session_id: str) -> None:
        """Mark a session as active after successful initialization."""
        session = self.sessions.get(session_id)
        if session:
            session.state = CallSessionState.ACTIVE
            session.update_activity()
            await self._persist_session_update(session)
            logger.info(f"Session {session_id} is now active")
    
    async def end_session(self, session_id: str) -> Optional[CallSession]:
        """
        End a call session and clean up resources.
        
        Args:
            session_id: Session to end
        
        Returns:
            The ended session, or None if not found
        """
        session = self.sessions.pop(session_id, None)
        if not session:
            return None
        
        session.state = CallSessionState.ENDED
        
        # Calculate duration
        duration_seconds = int(session.get_session_duration_seconds())
        ended_at = datetime.now()
        
        # Persist session end to database
        await self._persist_session_end(session, ended_at, duration_seconds)
        
        # Remove from user tracking
        if session.user_id in self.user_sessions:
            self.user_sessions[session.user_id] = [
                sid for sid in self.user_sessions[session.user_id]
                if sid != session_id
            ]
            if not self.user_sessions[session.user_id]:
                del self.user_sessions[session.user_id]
        
        logger.info(
            "Ended call session",
            session_id=session_id,
            user_id=session.user_id,
            duration_seconds=duration_seconds,
            questions_asked=session.question_count
        )
        
        return session
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up all expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        expired_sessions = []
        
        for session_id, session in list(self.sessions.items()):
            if session.is_expired(
                timeout_minutes=settings.VOICE_SESSION_TIMEOUT_MINUTES,
                max_duration_minutes=settings.VOICE_SESSION_MAX_DURATION_MINUTES
            ):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.end_session(session_id)
            logger.info(f"Cleaned up expired session: {session_id}")
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def should_use_fallback(self, session: CallSession) -> bool:
        """
        Check if session should use fallback (Whisper+TTS) mode.
        
        Args:
            session: The call session
        
        Returns:
            True if fallback should be used
        """
        return session.voice_mode == VoiceMode.WHISPER_TTS
    
    async def switch_to_fallback(self, session_id: str) -> bool:
        """
        Switch a session to fallback mode.
        
        Called when OpenAI Realtime API connection fails.
        
        Args:
            session_id: Session to switch
        
        Returns:
            True if successfully switched
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        previous_mode = session.voice_mode
        session.voice_mode = VoiceMode.WHISPER_TTS
        
        logger.info(
            f"Switched session {session_id} from {previous_mode.value} to {session.voice_mode.value}"
        )
        
        return True
    
    def check_rate_limit(self, session: CallSession, audio_bytes: int) -> bool:
        """
        Check if an audio chunk is within rate limits.
        
        Args:
            session: The call session
            audio_bytes: Size of incoming audio chunk
        
        Returns:
            True if within limits
        """
        # Simple rate limiting: track bytes per second
        # 24kHz * 2 bytes (16-bit) * 1 channel = 48000 bytes/sec
        max_bytes = settings.VOICE_MAX_AUDIO_BYTES_PER_SECOND
        
        # For now, just check chunk size isn't too large
        # A more sophisticated implementation would track over time
        if audio_bytes > max_bytes:
            logger.warning(
                f"Audio chunk too large: {audio_bytes} bytes (max: {max_bytes})"
            )
            return False
        
        return True
    
    async def _persist_session_create(self, session: CallSession) -> None:
        """Persist session creation to database."""
        if not supabase.is_available():
            return
        
        try:
            supabase.client.table("voice_sessions").insert({
                "session_id": session.session_id,
                "user_id": session.user_id,
                "document_id": session.document_id,
                "state": session.state.value,
                "created_at": session.created_at.isoformat(),
                "question_count": session.question_count,
                "transcript_status": "pending",
                "verification_status": "pending",
                "metadata": {}
            }).execute()
        except Exception as e:
            logger.warning(f"Failed to persist session creation: {e}")
    
    async def _persist_session_update(self, session: CallSession) -> None:
        """Persist session state update to database."""
        if not supabase.is_available():
            return
        
        try:
            supabase.client.table("voice_sessions").update({
                "state": session.state.value,
                "question_count": session.question_count,
            }).eq("session_id", session.session_id).execute()
        except Exception as e:
            logger.warning(f"Failed to persist session update: {e}")
    
    async def _persist_session_end(
        self,
        session: CallSession,
        ended_at: datetime,
        duration_seconds: int
    ) -> None:
        """Persist session end to database."""
        if not supabase.is_available():
            return
        
        try:
            supabase.client.table("voice_sessions").update({
                "state": session.state.value,
                "ended_at": ended_at.isoformat(),
                "duration_seconds": duration_seconds,
                "question_count": session.question_count,
            }).eq("session_id", session.session_id).execute()
        except Exception as e:
            logger.warning(f"Failed to persist session end: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session manager statistics."""
        active_sessions = [
            s for s in self.sessions.values()
            if s.state == CallSessionState.ACTIVE
        ]
        
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len(active_sessions),
            "users_with_sessions": len(self.user_sessions),
            "sessions_by_mode": {
                VoiceMode.OPENAI_REALTIME.value: sum(
                    1 for s in self.sessions.values()
                    if s.voice_mode == VoiceMode.OPENAI_REALTIME
                ),
                VoiceMode.WHISPER_TTS.value: sum(
                    1 for s in self.sessions.values()
                    if s.voice_mode == VoiceMode.WHISPER_TTS
                ),
            }
        }


# Singleton instance
call_session_manager = CallSessionManager()
