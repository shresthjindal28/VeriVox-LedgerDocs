"""
OpenAI Realtime API Service for real-time voice conversations.
Provides true duplex voice streaming like a phone call.
Enforces strict PDF-only intelligence for document queries.
Supports exhaustive extraction with visual highlights.
"""

import asyncio
import base64
import json
import os
import re
from typing import Optional, Callable, AsyncGenerator, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import websockets
from websockets.client import WebSocketClientProtocol

from app.core.config import settings
from app.services.vector_service import vector_store
from app.services.embedding_service import embedding_service
from app.utils.helpers import get_logger

logger = get_logger(__name__)

# Exhaustive intent patterns (same as rag_service)
EXHAUSTIVE_INTENT_PATTERNS = [
    r"list\s+all",
    r"extract\s+(all|every)",
    r"show\s+(me\s+)?(all|every)",
    r"give\s+(me\s+)?(all|every)",
    r"all\s+(the\s+)?(skills?|projects?|certifications?|experiences?|jobs?|roles?|education|qualifications?)",
    r"every\s+(single\s+)?",
    r"complete\s+list",
    r"full\s+list",
    r"enumerate",
    r"everything\s+(about|related)",
]


class CallState(str, Enum):
    """States for the voice call."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    USER_SPEAKING = "user_speaking"
    AI_SPEAKING = "ai_speaking"
    PROCESSING = "processing"
    ENDED = "ended"
    ERROR = "error"


@dataclass
class VoiceCallSession:
    """Manages a real-time voice call session."""
    session_id: str
    document_id: str
    state: CallState = CallState.CONNECTING
    openai_ws: Optional[WebSocketClientProtocol] = None
    document_context: str = ""
    conversation_id: Optional[str] = None
    last_activity: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    user_id: Optional[str] = None
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    _response_create_task: Optional[asyncio.Task] = field(default=None, repr=False)
    _current_response_id: Optional[str] = field(default=None, repr=False)
    _emitted_ai_speaking: bool = field(default=False, repr=False)

    def update_activity(self):
        self.last_activity = datetime.now()
    
    def add_to_history(self, role: str, content: str):
        """Add a message to conversation history."""
        self.conversation_history.append({"role": role, "content": content})
        # Keep only last 20 messages
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]


# PDF-Only System Prompt with balanced enforcement
PDF_ONLY_SYSTEM_PROMPT = """You are a helpful AI assistant having a voice conversation with a user about their uploaded document.

YOUR PRIMARY ROLE:
- Answer questions using information from the document context provided below
- Be helpful, friendly, and conversational
- When information is in the document, provide clear and accurate answers
- If information is NOT in the document, you can still help by:
  * Explaining what you found in the document
  * Suggesting what related information might be available
  * Being honest that specific details aren't in the document

Document Context:
{document_context}

IMPORTANT GUIDELINES:
1. Use the document context as your primary source of information
2. When answering from the document, be specific and cite relevant sections when helpful
3. If asked about something not in the document, acknowledge it but try to be helpful with what IS available
4. Speak naturally and conversationally - this is a voice call, not a formal document
5. Keep responses concise (2-4 sentences) unless asked for more detail
6. Be warm, professional, and engaging

CRITICAL - TOOL USE (search_document, extract_all):
- NEVER say "Let me gather...", "One moment", "Let me look that up", "I'm fetching...", or any filler before using a tool.
- When you need to use search_document or extract_all: call the tool first with NO spoken output. After you receive the tool result, give the complete answer in ONE spoken response.
- The user must hear ONLY the final answer - never placeholder acknowledgments. If you use a tool, stay silent until you have the result, then speak the full answer.

Remember: The user uploaded this document to discuss it with you. Help them understand and explore the content!
"""


class OpenAIRealtimeService:
    """
    Service for real-time voice conversations using OpenAI's Realtime API.
    
    This provides a true phone-call-like experience:
    - Real-time audio streaming in both directions
    - Voice Activity Detection (VAD) for natural turn-taking
    - Interruption support
    - Document context for RAG
    """
    
    OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime"
    MODEL = "gpt-4o-realtime-preview-2024-12-17"
    
    def __init__(self):
        self.sessions: dict[str, VoiceCallSession] = {}
        self.api_key = settings.OPENAI_API_KEY
    
    async def start_call(
        self,
        session_id: str,
        document_id: str,
        on_state_change: Callable[[CallState], None],
        on_audio: Callable[[bytes], None],
        on_transcript: Callable[[str, str], None],  # (role, text)
        on_error: Callable[[str], None],
        on_highlights: Optional[Callable[[List[Dict]], None]] = None,  # For visual highlighting
        user_id: Optional[str] = None,
    ) -> VoiceCallSession:
        """
        Start a new real-time voice call.
        
        Args:
            session_id: Unique session identifier
            document_id: Document to use for context
            on_state_change: Callback for state changes
            on_audio: Callback for AI audio chunks
            on_transcript: Callback for transcriptions (role, text)
            on_error: Callback for errors
            user_id: Optional user ID for session tracking
        
        Returns:
            VoiceCallSession object
        """
        # Get document context for RAG
        context = await self._get_document_context(document_id)
        
        session = VoiceCallSession(
            session_id=session_id,
            document_id=document_id,
            document_context=context,
            user_id=user_id,
        )
        self.sessions[session_id] = session
        
        try:
            # Connect to OpenAI Realtime API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "OpenAI-Beta": "realtime=v1",
            }
            
            ws_url = f"{self.OPENAI_REALTIME_URL}?model={self.MODEL}"
            
            logger.info(f"Connecting to OpenAI Realtime API for session {session_id}")
            
            # Use additional_headers for websockets 16+ (extra_headers is deprecated)
            # Fallback to extra_headers for older versions
            connect_kwargs = {
                "ping_interval": 30,
                "ping_timeout": 10
            }
            
            try:
                connect_kwargs["additional_headers"] = headers
                session.openai_ws = await websockets.connect(ws_url, **connect_kwargs)
            except TypeError as e:
                # Fallback for older websockets versions
                if "additional_headers" in str(e) or "unexpected keyword" in str(e):
                    logger.warning("Websockets library doesn't support additional_headers, trying extra_headers")
                    connect_kwargs.pop("additional_headers", None)
                    connect_kwargs["extra_headers"] = headers
                    session.openai_ws = await websockets.connect(ws_url, **connect_kwargs)
                else:
                    raise
            
            # Configure the session
            await self._configure_session(session, on_state_change, on_highlights)
            
            session.state = CallState.CONNECTED
            on_state_change(session.state)
            
            # Start listening for responses
            asyncio.create_task(
                self._listen_to_openai(
                    session,
                    on_state_change,
                    on_audio,
                    on_transcript,
                    on_error,
                )
            )
            
            logger.info(f"Voice call started for session {session_id}")
            return session
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(
                f"Failed to start OpenAI Realtime call: {e}",
                session_id=session_id,
                document_id=document_id,
                error_type=type(e).__name__,
                traceback=error_trace
            )
            session.state = CallState.ERROR
            on_error(f"Failed to connect: {str(e)}")
            raise
    
    async def _get_document_context(self, document_id: str) -> str:
        """Get relevant document context for the conversation."""
        try:
            # Get document metadata
            metadata = await vector_store.get_document_metadata(document_id)
            if not metadata:
                return ""
            
            # Get some key chunks from the document
            chunks = await vector_store.search(
                query="summary overview main points",
                document_id=document_id,
                top_k=5,
            )
            
            context_parts = [
                f"Document: {metadata.filename}",
                f"Pages: {metadata.page_count}",
                "",
                "Key content from the document:",
            ]
            
            for chunk in chunks:
                context_parts.append(f"- {chunk.text[:500]}...")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error getting document context: {e}")
            return ""
    
    async def _configure_session(
        self,
        session: VoiceCallSession,
        on_state_change: Callable[[CallState], None],
        on_highlights: Optional[Callable[[List[Dict]], None]] = None,
    ):
        """Configure the OpenAI Realtime session with PDF-only enforcement."""
        
        # Store highlights callback on session
        session._on_highlights = on_highlights
        
        # Use the PDF-only system prompt with strict enforcement
        system_prompt = PDF_ONLY_SYSTEM_PROMPT.format(
            document_context=session.document_context
        )

        # Define the RAG function tool for dynamic context retrieval
        rag_tool = {
            "type": "function",
            "name": "search_document",
            "description": "Search the uploaded document for specific information. Use this when you need to find something in the document that may not be in your initial context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant information in the document"
                    }
                },
                "required": ["query"]
            }
        }

        # Define the exhaustive extraction tool
        extract_tool = {
            "type": "function",
            "name": "extract_all",
            "description": "Extract ALL instances of a specific type of information from the entire document. Use this when the user asks to 'list all', 'show every', 'give me all', etc. This performs exhaustive extraction, not just similarity search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "extraction_type": {
                        "type": "string",
                        "description": "What to extract (e.g., 'skills', 'projects', 'certifications', 'experience')"
                    },
                    "full_query": {
                        "type": "string",
                        "description": "The user's full original query for context"
                    }
                },
                "required": ["extraction_type", "full_query"]
            }
        }

        # Map user preference to supported OpenAI Realtime voices
        # Supported: alloy, ash, ballad, coral, echo, sage, shimmer, verse, marin, cedar
        # Map "nova" (not supported) to "alloy" (similar friendly tone)
        voice_mapping = {
            "nova": "alloy",  # Friendly, conversational -> Neutral, balanced
            "alloy": "alloy",
            "echo": "echo",
            "shimmer": "shimmer",
        }
        # Default to "alloy" if preference not mapped
        selected_voice = voice_mapping.get("nova", "alloy")
        
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": system_prompt,
                "voice": selected_voice,  # Use mapped voice (alloy, echo, shimmer, etc.)
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500,
                    "interrupt_response": True,  # Stop AI when user speaks (barge-in)
                },
                "tools": [rag_tool, extract_tool],
                "tool_choice": "auto",
                "temperature": 0.7,
                "max_response_output_tokens": 1024,
            }
        }
        
        await session.openai_ws.send(json.dumps(config))
        logger.info(f"Session configured for {session.session_id} with PDF-only enforcement")
    
    async def _listen_to_openai(
        self,
        session: VoiceCallSession,
        on_state_change: Callable[[CallState], None],
        on_audio: Callable[[bytes], None],
        on_transcript: Callable[[str, str], None],
        on_error: Callable[[str], None],
    ):
        """Listen for messages from OpenAI Realtime API."""
        try:
            async for message in session.openai_ws:
                if not session.is_active:
                    break
                
                session.update_activity()
                
                try:
                    data = json.loads(message)
                    event_type = data.get("type", "")
                    
                    await self._handle_openai_event(
                        session,
                        event_type,
                        data,
                        on_state_change,
                        on_audio,
                        on_transcript,
                        on_error,
                    )
                    
                except json.JSONDecodeError:
                    logger.warning("Received non-JSON message from OpenAI")
                    
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"OpenAI connection closed: {e}")
            session.state = CallState.ENDED
            on_state_change(session.state)
        except Exception as e:
            logger.error(f"Error listening to OpenAI: {e}")
            on_error(str(e))
    
    async def _handle_openai_event(
        self,
        session: VoiceCallSession,
        event_type: str,
        data: dict,
        on_state_change: Callable[[CallState], None],
        on_audio: Callable[[bytes], None],
        on_transcript: Callable[[str, str], None],
        on_error: Callable[[str], None],
    ):
        """Handle events from OpenAI Realtime API."""
        
        if event_type == "session.created":
            logger.info(f"Session created: {data.get('session', {}).get('id')}")
            
        elif event_type == "session.updated":
            logger.info("Session updated")
            
        elif event_type == "input_audio_buffer.speech_started":
            # User started speaking - immediately cancel AI response for natural barge-in
            if session.state == CallState.AI_SPEAKING:
                try:
                    await session.openai_ws.send(json.dumps({"type": "response.cancel"}))
                    logger.debug(f"Interrupted AI for barge-in: {session.session_id}")
                except Exception as e:
                    logger.warning(f"Failed to cancel response on barge-in: {e}")
            # Invalidate current response to reject any stale audio deltas still in flight
            session._current_response_id = None
            session._emitted_ai_speaking = False
            session.state = CallState.USER_SPEAKING
            on_state_change(session.state)
            
        elif event_type == "input_audio_buffer.speech_stopped":
            session.state = CallState.PROCESSING
            on_state_change(session.state)
            
        elif event_type == "conversation.item.input_audio_transcription.completed":
            # User's speech was transcribed
            transcript = data.get("transcript", "")
            if transcript:
                on_transcript("user", transcript)
                
        elif event_type == "response.created":
            # Track current response ID to filter stale audio from cancelled responses
            session._current_response_id = data.get("response", {}).get("id")
            session._emitted_ai_speaking = False
            logger.debug(f"Response created: {session._current_response_id}")

        elif event_type == "response.audio.delta":
            # Ignore stale audio from cancelled/old responses
            response_id = data.get("response_id", "")
            if response_id and session._current_response_id and response_id != session._current_response_id:
                return

            # Only emit AI_SPEAKING state change once per response to avoid flooding
            if not session._emitted_ai_speaking:
                session.state = CallState.AI_SPEAKING
                on_state_change(session.state)
                session._emitted_ai_speaking = True

            audio_b64 = data.get("delta", "")
            if audio_b64:
                audio_bytes = base64.b64decode(audio_b64)
                on_audio(audio_bytes)
                
        elif event_type == "response.audio_transcript.delta":
            # AI text transcript delta - ignore if from stale response
            response_id = data.get("response_id", "")
            if response_id and session._current_response_id and response_id != session._current_response_id:
                return
            transcript = data.get("delta", "")
            if transcript:
                on_transcript("assistant_delta", transcript)

        elif event_type == "response.audio_transcript.done":
            # Complete AI transcript - ignore if from stale response
            response_id = data.get("response_id", "")
            if response_id and session._current_response_id and response_id != session._current_response_id:
                return
            transcript = data.get("transcript", "")
            if transcript:
                on_transcript("assistant", transcript)
                
        elif event_type == "response.done":
            # Ignore done events for cancelled or stale responses
            response = data.get("response", {})
            response_id = response.get("id", "")
            response_status = response.get("status", "")
            if response_status == "cancelled":
                logger.debug(f"Response cancelled: {response_id}")
                return
            if response_id and session._current_response_id and response_id != session._current_response_id:
                return
            session.state = CallState.CONNECTED
            on_state_change(session.state)
        
        elif event_type == "response.function_call_arguments.done":
            # Handle function call for document search
            await self._handle_function_call(session, data)
            
        elif event_type == "error":
            error_msg = data.get("error", {}).get("message", "Unknown error")
            logger.error(f"OpenAI error: {error_msg}")
            on_error(error_msg)
            
        elif event_type == "rate_limits.updated":
            # Rate limit info - just log
            pass
    
    def _schedule_response_create(self, session: VoiceCallSession):
        """
        Debounce response.create to avoid duplicate responses when the model
        makes multiple function calls (e.g. search_document + extract_all).
        Only one response.create is sent per batch of function calls.
        """
        async def _send_response_create():
            await asyncio.sleep(0.08)  # 80ms debounce
            session._response_create_task = None
            if session.openai_ws and session.is_active:
                try:
                    await session.openai_ws.send(json.dumps({"type": "response.create"}))
                    logger.debug(f"Scheduled response.create for {session.session_id}")
                except Exception as e:
                    logger.warning(f"Failed to send response.create: {e}")

        # Cancel any pending task
        if session._response_create_task and not session._response_create_task.done():
            session._response_create_task.cancel()

        session._response_create_task = asyncio.create_task(_send_response_create())

    async def _handle_function_call(self, session: VoiceCallSession, data: dict):
        """Handle a function call from OpenAI (e.g., document search, extraction)."""
        try:
            call_id = data.get("call_id", "")
            name = data.get("name", "")
            arguments = data.get("arguments", "{}")
            
            if name == "search_document":
                args = json.loads(arguments)
                query = args.get("query", "")
                
                if query:
                    # Search the document using RAG
                    result = await self._search_document_for_context(
                        session.document_id, 
                        query
                    )
                    
                    # Send the function result back to OpenAI
                    response = {
                        "type": "conversation.item.create",
                        "item": {
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": result
                        }
                    }
                    await session.openai_ws.send(json.dumps(response))
                    
                    # Debounced: triggers response once per batch of function calls
                    self._schedule_response_create(session)
                    
                    logger.info(f"Function call handled: search_document with query '{query}'")
            
            elif name == "extract_all":
                args = json.loads(arguments)
                extraction_type = args.get("extraction_type", "")
                full_query = args.get("full_query", extraction_type)
                
                if extraction_type:
                    # Perform exhaustive extraction (user_id for dashboard recording)
                    result, highlights = await self._extract_all_from_document(
                        session.document_id,
                        full_query,
                        user_id=session.user_id,
                    )
                    
                    # Send highlights to frontend if callback exists
                    if highlights and hasattr(session, '_on_highlights') and session._on_highlights:
                        try:
                            session._on_highlights(highlights)
                        except Exception as e:
                            logger.warning(f"Failed to send highlights: {e}")
                    
                    # Send the function result back to OpenAI
                    response = {
                        "type": "conversation.item.create",
                        "item": {
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": result
                        }
                    }
                    await session.openai_ws.send(json.dumps(response))
                    
                    # Debounced: triggers response once per batch of function calls
                    self._schedule_response_create(session)
                    
                    logger.info(f"Function call handled: extract_all for '{extraction_type}'")
                    
        except Exception as e:
            logger.error(f"Error handling function call: {e}")
    
    async def _search_document_for_context(
        self, 
        document_id: str, 
        query: str
    ) -> str:
        """Search document and return context as string."""
        try:
            # Generate embedding for the query
            query_embedding = await embedding_service.generate_embedding(query)
            
            # Search the vector store
            search_results = await vector_store.search(
                document_id=document_id,
                query_embedding=query_embedding,
                top_k=5,
            )
            
            if not search_results:
                return "No relevant information found in the document for this query."
            
            # Format results
            context_parts = []
            for result in search_results:
                chunk = result.chunk
                context_parts.append(
                    f"[Page {chunk.page_number}]: {chunk.text_content}"
                )
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error searching document: {e}")
            return "Unable to search the document at this time."
    
    async def _extract_all_from_document(
        self, 
        document_id: str, 
        query: str,
        user_id: Optional[str] = None,
    ) -> tuple[str, List[Dict]]:
        """
        Perform exhaustive extraction from document.
        
        Returns:
            Tuple of (formatted result string, list of highlight dicts)
        """
        try:
            # Import here to avoid circular dependency
            from app.services.rag_service import rag_service
            from app.services.highlight_service import highlight_service
            from app.services.dashboard_service import dashboard_service
            
            # Perform exhaustive extraction
            extraction_result = await rag_service.extract_all_from_document(
                query=query,
                document_id=document_id,
            )
            
            if user_id:
                await dashboard_service.record_extraction(
                    user_id=user_id,
                    document_id=document_id,
                    query=query,
                    item_count=extraction_result.total_count,
                    pages_scanned=extraction_result.pages_scanned,
                )
            
            if extraction_result.total_count == 0:
                return "No matching items found in the document.", []
            
            # Generate highlights for the extracted items
            highlights = []
            if settings.ENABLE_HIGHLIGHT_SYNC:
                highlight_set = await highlight_service.get_highlights_for_extraction(
                    document_id=document_id,
                    extraction_result=extraction_result,
                )
                highlights = [h.to_dict() for h in highlight_set.highlights]
            
            # Format the result for the AI to speak
            formatted = rag_service._format_extraction_response(extraction_result)
            
            # Add details about items found
            details_parts = [formatted, "\n\nDetails:"]
            for i, item in enumerate(extraction_result.items[:20], 1):  # Limit to first 20
                page_info = f" (page {item.page})" if item.page > 0 else ""
                details_parts.append(f"{i}. {item.text}{page_info}")
            
            if extraction_result.total_count > 20:
                details_parts.append(f"\n... and {extraction_result.total_count - 20} more items.")
            
            return "\n".join(details_parts), highlights
            
        except Exception as e:
            logger.error(f"Error extracting from document: {e}")
            return "Unable to perform extraction at this time.", []
    
    async def send_audio(self, session_id: str, audio_data: bytes):
        """
        Send audio data to OpenAI.
        
        Audio should be PCM16 format at 24kHz, mono.
        """
        session = self.sessions.get(session_id)
        if not session or not session.openai_ws or not session.is_active:
            return
        
        try:
            audio_b64 = base64.b64encode(audio_data).decode()
            
            message = {
                "type": "input_audio_buffer.append",
                "audio": audio_b64,
            }
            
            await session.openai_ws.send(json.dumps(message))
            session.update_activity()
            
        except Exception as e:
            logger.error(f"Error sending audio: {e}")
    
    async def interrupt(self, session_id: str):
        """Interrupt the current AI response."""
        session = self.sessions.get(session_id)
        if not session or not session.openai_ws:
            return
        
        try:
            # Cancel the current response
            message = {"type": "response.cancel"}
            await session.openai_ws.send(json.dumps(message))
            
            # Clear input buffer
            clear_message = {"type": "input_audio_buffer.clear"}
            await session.openai_ws.send(json.dumps(clear_message))
            
            logger.info(f"Interrupted AI response for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error interrupting: {e}")
    
    async def end_call(self, session_id: str):
        """End a voice call session."""
        session = self.sessions.pop(session_id, None)
        if not session:
            return
        
        session.is_active = False

        # Cancel any pending response.create debounce
        if session._response_create_task and not session._response_create_task.done():
            session._response_create_task.cancel()
            try:
                await session._response_create_task
            except asyncio.CancelledError:
                pass
            session._response_create_task = None
        
        if session.openai_ws:
            try:
                await session.openai_ws.close()
            except Exception:
                pass
        
        logger.info(f"Voice call ended for session {session_id}")
    
    def get_session(self, session_id: str) -> Optional[VoiceCallSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)


# Singleton instance
openai_realtime_service = OpenAIRealtimeService()
