"""AI Teacher service for educational voice interactions."""

import json
from typing import AsyncGenerator, Optional

from openai import AsyncOpenAI

from app.core.config import settings
from app.models.schemas import RAGResponse, SourceReference
from app.services.embedding_service import embedding_service
from app.services.vector_service import SearchResult, vector_store
from app.services.voice_service import voice_service, SpeechResult
from app.utils.helpers import get_logger, truncate_text

logger = get_logger(__name__)


# Teacher persona system prompt
TEACHER_SYSTEM_PROMPT = """You are an expert AI teacher helping students learn from educational documents. Your role is to:

1. EXPLAIN concepts clearly and patiently, as a caring teacher would
2. ENCOURAGE students and make learning engaging
3. BREAK DOWN complex topics into simple, understandable parts
4. USE EXAMPLES and analogies to illustrate points
5. ASK follow-up questions to check understanding
6. PRAISE effort and guide students when they struggle

TEACHING STYLE:
- Be warm, friendly, and encouraging
- Use phrases like "Great question!", "Let me explain that...", "Think of it this way..."
- Keep explanations concise but thorough
- Relate concepts to real-world examples when possible
- End responses with encouragement or a thought-provoking question

CRITICAL RULES:
- ONLY use information from the provided document context
- If information is not in the document, say "I don't see that in your document, but..."
- Always cite page numbers when referencing the document
- Make learning feel like a conversation, not a lecture

You must respond in the following JSON format:
{
    "answer": "Your teaching response here - warm, clear, educational",
    "sources": [
        {"page": <page_number>, "text": "relevant quote", "chunk_id": "<chunk_id>"}
    ],
    "reasoning": "Brief explanation of teaching approach used",
    "confidence": <0.0 to 1.0>,
    "follow_up_question": "Optional engaging question for the student"
}"""

GREETING_RESPONSES = {
    "hello": "Hello there, eager learner! I'm your AI teacher, ready to help you explore and understand your document. What would you like to learn about today?",
    "hi": "Hi! Great to see you ready to learn! I'm here to help you understand your study material. What topic shall we dive into?",
    "hey": "Hey there, student! Ready for an exciting learning session? Ask me anything about your document!",
    "help": "Of course I'll help! That's what I'm here for. Just ask me any question about your document, and I'll explain it in a way that makes sense.",
    "default": "Hello, wonderful student! I'm your AI teacher, and I'm excited to help you learn. What would you like to explore in your document today?",
}


class TeacherService:
    """
    AI Teacher service for educational voice-to-voice interactions.
    
    Combines RAG with a teaching persona and voice capabilities.
    """

    def __init__(self):
        """Initialize teacher service."""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.model = settings.LLM_MODEL
        self.top_k = settings.TOP_K_RESULTS

    async def answer_student_question(
        self,
        document_id: str,
        question: str,
        student_name: Optional[str] = None,
    ) -> RAGResponse:
        """
        Answer a student's question with a teaching approach.

        Args:
            document_id: Document being studied
            question: Student's question
            student_name: Optional student name for personalization

        Returns:
            RAGResponse with educational answer
        """
        logger.info(
            "Processing student question",
            document_id=document_id,
            question_length=len(question),
        )

        # Handle greetings
        if self._is_greeting(question):
            return self._handle_greeting(question, student_name)

        # Check document exists
        if not await vector_store.document_exists(document_id):
            return RAGResponse(
                answer="I don't see any document to study from yet! Please upload your study material first, and then we can dive into learning together.",
                sources=[],
                reasoning="No document uploaded",
                confidence=0.0,
            )

        # Get relevant context
        question_embedding = await embedding_service.generate_embedding(question)
        search_results = await vector_store.search(
            document_id=document_id,
            query_embedding=question_embedding,
            top_k=self.top_k,
        )

        if not search_results:
            return RAGResponse(
                answer="Hmm, I couldn't find information about that in your document. Could you rephrase your question, or perhaps it's a topic we should explore from a different angle?",
                sources=[],
                reasoning="No relevant content found",
                confidence=0.0,
            )

        # Build context and generate teaching response
        context = self._build_context(search_results)
        response = await self._generate_teaching_response(
            question, context, search_results, student_name
        )

        return response

    async def voice_to_voice_chat(
        self,
        document_id: str,
        audio_data: bytes,
        student_name: Optional[str] = None,
        voice: Optional[str] = None,
    ) -> tuple[RAGResponse, SpeechResult]:
        """
        Complete voice-to-voice teaching interaction.

        Args:
            document_id: Document being studied
            audio_data: Student's voice input
            student_name: Optional student name
            voice: TTS voice to use

        Returns:
            Tuple of (RAGResponse, SpeechResult)
        """
        logger.info("Processing voice-to-voice interaction", document_id=document_id)

        # Step 1: Transcribe student's question
        transcription = await voice_service.transcribe_audio(
            audio_data,
            prompt="Student asking a question about their study material.",
        )

        logger.info("Student said", text=transcription.text)

        # Step 2: Generate teaching response
        response = await self.answer_student_question(
            document_id=document_id,
            question=transcription.text,
            student_name=student_name,
        )

        # Step 3: Convert response to speech
        speech = await voice_service.synthesize_speech(
            text=response.answer,
            voice=voice or voice_service.DEFAULT_TEACHER_VOICE,
            speed=0.95,  # Slightly slower for clarity
        )

        return response, speech

    async def stream_voice_response(
        self,
        document_id: str,
        question: str,
        student_name: Optional[str] = None,
        voice: Optional[str] = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream voice response for real-time playback.

        Args:
            document_id: Document ID
            question: Student's question (text)
            student_name: Optional name
            voice: TTS voice

        Yields:
            Audio chunks
        """
        # Generate answer
        response = await self.answer_student_question(
            document_id=document_id,
            question=question,
            student_name=student_name,
        )

        # Stream the speech
        async for chunk in voice_service.stream_speech(
            text=response.answer,
            voice=voice or voice_service.DEFAULT_TEACHER_VOICE,
            speed=0.95,
        ):
            yield chunk

    def _is_greeting(self, text: str) -> bool:
        """Check if text is a greeting."""
        greetings = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "help me"]
        text_lower = text.lower().strip()
        return any(text_lower.startswith(g) or text_lower == g for g in greetings)

    def _handle_greeting(
        self,
        text: str,
        student_name: Optional[str] = None,
    ) -> RAGResponse:
        """Handle greeting with a warm teacher response."""
        text_lower = text.lower().strip()

        for key, response in GREETING_RESPONSES.items():
            if key in text_lower:
                answer = response
                break
        else:
            answer = GREETING_RESPONSES["default"]

        # Personalize if name provided
        if student_name:
            answer = answer.replace("Hello there", f"Hello {student_name}")
            answer = answer.replace("Hi!", f"Hi {student_name}!")

        return RAGResponse(
            answer=answer,
            sources=[],
            reasoning="Greeting response with teacher persona",
            confidence=1.0,
        )

    def _build_context(self, search_results: list[SearchResult]) -> str:
        """Build context string from search results."""
        context_parts = []
        for result in search_results:
            chunk = result.chunk
            context_parts.append(
                f"[Page {chunk.page_number}]\n{chunk.text_content}"
            )
        return "\n\n---\n\n".join(context_parts)

    async def _generate_teaching_response(
        self,
        question: str,
        context: str,
        search_results: list[SearchResult],
        student_name: Optional[str] = None,
    ) -> RAGResponse:
        """Generate a teaching-style response."""
        if not self.client:
            return self._fallback_response(search_results)

        try:
            personalization = f"The student's name is {student_name}. " if student_name else ""
            
            user_prompt = f"""{personalization}Document Context (from the student's study material):
{context}

Student's Question: {question}

Please provide a warm, educational response that helps the student understand this topic. Use the teaching style described in your instructions."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": TEACHER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,  # Slightly more creative for engaging teaching
                max_tokens=1500,
            )

            content = response.choices[0].message.content
            return self._parse_response(content, search_results)

        except Exception as e:
            logger.error("Teaching response generation failed", error=str(e))
            return self._fallback_response(search_results)

    def _parse_response(
        self,
        content: str,
        search_results: list[SearchResult],
    ) -> RAGResponse:
        """Parse LLM response into RAGResponse."""
        import re

        try:
            # Extract JSON
            json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found")

            data = json.loads(json_str)

            sources = []
            for src in data.get("sources", []):
                sources.append(
                    SourceReference(
                        page=src.get("page", 0),
                        text=truncate_text(src.get("text", ""), 200),
                        chunk_id=src.get("chunk_id", ""),
                    )
                )

            if not sources and search_results:
                sources = [
                    SourceReference(
                        page=r.chunk.page_number,
                        text=truncate_text(r.chunk.text_content, 200),
                        chunk_id=r.chunk.chunk_id,
                        relevance_score=r.score,
                    )
                    for r in search_results[:3]
                ]

            return RAGResponse(
                answer=data.get("answer", content),
                sources=sources,
                reasoning=data.get("reasoning", ""),
                confidence=float(data.get("confidence", 0.8)),
            )

        except (json.JSONDecodeError, ValueError):
            # Return content as plain answer
            return RAGResponse(
                answer=content,
                sources=[
                    SourceReference(
                        page=r.chunk.page_number,
                        text=truncate_text(r.chunk.text_content, 200),
                        chunk_id=r.chunk.chunk_id,
                        relevance_score=r.score,
                    )
                    for r in search_results[:3]
                ],
                reasoning="Parsed from unstructured response",
                confidence=0.7,
            )

    def _fallback_response(self, search_results: list[SearchResult]) -> RAGResponse:
        """Fallback when LLM unavailable."""
        if not search_results:
            return RAGResponse(
                answer="I'd love to help you learn, but I'm having trouble accessing my teaching capabilities right now. Please try again in a moment!",
                sources=[],
                reasoning="LLM unavailable",
                confidence=0.0,
            )

        top = search_results[0]
        return RAGResponse(
            answer=f"Great question! Based on your study material, here's what I found on page {top.chunk.page_number}:\n\n{top.chunk.text_content}\n\nWould you like me to explain this further?",
            sources=[
                SourceReference(
                    page=r.chunk.page_number,
                    text=truncate_text(r.chunk.text_content, 200),
                    chunk_id=r.chunk.chunk_id,
                    relevance_score=r.score,
                )
                for r in search_results[:3]
            ],
            reasoning="Fallback using vector search",
            confidence=top.score,
        )


# Singleton instance
teacher_service = TeacherService()
