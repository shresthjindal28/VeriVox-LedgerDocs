"""RAG orchestration service for document question answering."""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional

from openai import AsyncOpenAI

from app.core.config import settings
from app.models.schemas import IntentType, RAGResponse, SourceReference, TextChunk
from app.services.embedding_service import embedding_service
from app.services.vector_service import SearchResult, vector_store
from app.utils.helpers import get_logger, truncate_text

logger = get_logger(__name__)


class ExtractionMode(str, Enum):
    """Modes for RAG extraction."""
    CONVERSATIONAL = "conversational"  # Default top-K RAG
    EXHAUSTIVE = "exhaustive"  # Full document extraction


@dataclass
class ExtractedItem:
    """A single extracted item from the document."""
    text: str
    page: int
    snippet: str
    category: str = ""
    char_start: int = 0
    char_end: int = 0
    confidence: float = 1.0


@dataclass
class ExtractionResult:
    """Result of exhaustive extraction."""
    items: List[ExtractedItem] = field(default_factory=list)
    categories: Dict[str, List[ExtractedItem]] = field(default_factory=dict)
    total_count: int = 0
    pages_scanned: int = 0
    query: str = ""
    document_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "items": [
                {
                    "text": item.text,
                    "page": item.page,
                    "snippet": item.snippet,
                    "category": item.category,
                    "char_start": item.char_start,
                    "char_end": item.char_end,
                    "confidence": item.confidence,
                }
                for item in self.items
            ],
            "categories": {
                cat: [
                    {"text": i.text, "page": i.page, "snippet": i.snippet}
                    for i in items
                ]
                for cat, items in self.categories.items()
            },
            "total_count": self.total_count,
            "pages_scanned": self.pages_scanned,
            "query": self.query,
            "document_id": self.document_id,
        }


# System prompts for different tasks
INTENT_CLASSIFICATION_PROMPT = """You are an intent classifier. Classify the user's message into one of these categories:

1. "document_query" - Questions about document content, requests for information from the document
2. "greeting" - Greetings, introductions, or casual conversation starters
3. "clarification" - Requests for clarification about previous answers
4. "out_of_scope" - Questions unrelated to document analysis

Respond with ONLY the category name, nothing else."""

RAG_SYSTEM_PROMPT = """You are a precise document analysis assistant. Your role is to answer questions STRICTLY based on the provided document context.

CRITICAL RULES:
1. ONLY use information from the provided context chunks
2. If the answer is not in the context, say "The information is not found in the document."
3. Always cite your sources by referencing page numbers
4. Provide reasoning for your answer
5. Be concise but complete
6. Never make up information not in the context

You must respond in the following JSON format:
{
    "answer": "Your answer based strictly on the document context",
    "sources": [
        {"page": <page_number>, "text": "relevant quote", "chunk_id": "<chunk_id>"}
    ],
    "reasoning": "Brief explanation of how you derived the answer from the sources",
    "confidence": <0.0 to 1.0 based on how well the context supports the answer>
}

If the information is not found, respond with:
{
    "answer": "The information is not found in the document.",
    "sources": [],
    "reasoning": "The provided context does not contain information relevant to this question.",
    "confidence": 0.0
}"""

GREETING_RESPONSES = {
    "hello": "Hello! I'm ready to help you with questions about your uploaded document. What would you like to know?",
    "hi": "Hi there! Feel free to ask me any questions about the document content.",
    "hey": "Hey! I'm your document assistant. What would you like to learn from the document?",
    "default": "Hello! I'm here to help you explore and understand your document. What questions do you have?",
}

# Exhaustive extraction prompts
EXHAUSTIVE_EXTRACTION_PROMPT = """You are a document extraction assistant performing EXHAUSTIVE extraction.

You MUST:
- Extract ALL instances related to the user request from the provided text
- Do NOT summarize - include every individual item
- Do NOT skip any items, even if they seem minor
- Return structured JSON with category, page, and snippet for each item
- Include the exact text and surrounding context as snippet
- Do NOT use knowledge outside the provided document text

You MUST respond in this JSON format:
{
    "items": [
        {
            "text": "exact text of the item",
            "category": "category name (e.g., skill, project, certification)",
            "page": <page_number>,
            "snippet": "surrounding context (10-20 words)",
            "char_start": <character start position if available>,
            "char_end": <character end position if available>
        }
    ],
    "summary": "Brief summary of what was extracted"
}

If no relevant items are found in this batch, return:
{
    "items": [],
    "summary": "No relevant items found in this section"
}"""

# Exhaustive intent detection patterns
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


class RAGService:
    """Service for RAG-based question answering."""

    def __init__(self):
        """Initialize RAG service."""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.model = settings.LLM_MODEL
        self.top_k = settings.TOP_K_RESULTS
        self.hard_reject_enabled = settings.RAG_HARD_REJECT_ENABLED
        self.min_confidence_for_voice = settings.RAG_MIN_CONFIDENCE_FOR_VOICE
        self.refusal_message = settings.RAG_REFUSAL_MESSAGE

    async def classify_intent(self, question: str) -> IntentType:
        """
        Classify the intent of a user's question.

        Args:
            question: User's question

        Returns:
            Classified IntentType
        """
        if not self.client:
            # Fallback to simple keyword matching
            return self._simple_intent_classification(question)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": INTENT_CLASSIFICATION_PROMPT},
                    {"role": "user", "content": question},
                ],
                temperature=0,
                max_tokens=20,
            )

            intent_str = response.choices[0].message.content.strip().lower()

            # Map response to IntentType
            intent_map = {
                "document_query": IntentType.DOCUMENT_QUERY,
                "greeting": IntentType.GREETING,
                "clarification": IntentType.CLARIFICATION,
                "out_of_scope": IntentType.OUT_OF_SCOPE,
            }

            return intent_map.get(intent_str, IntentType.DOCUMENT_QUERY)

        except Exception as e:
            logger.error("Intent classification failed", error=str(e))
            return self._simple_intent_classification(question)

    def _simple_intent_classification(self, question: str) -> IntentType:
        """
        Simple rule-based intent classification fallback.

        Args:
            question: User's question

        Returns:
            Classified IntentType
        """
        question_lower = question.lower().strip()

        # Greeting patterns
        greeting_patterns = [
            r"^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening))[\s!.,]*$",
            r"^how\s+are\s+you",
            r"^what'?s\s+up",
        ]
        for pattern in greeting_patterns:
            if re.match(pattern, question_lower):
                return IntentType.GREETING

        # Out of scope patterns
        out_of_scope_patterns = [
            r"weather",
            r"what\s+time\s+is\s+it",
            r"tell\s+me\s+a\s+joke",
            r"who\s+are\s+you",
        ]
        for pattern in out_of_scope_patterns:
            if re.search(pattern, question_lower):
                return IntentType.OUT_OF_SCOPE

        return IntentType.DOCUMENT_QUERY

    async def answer_question(
        self,
        document_id: str,
        question: str,
        strict_mode: bool = False,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> RAGResponse:
        """
        Answer a question using RAG pipeline.

        Args:
            document_id: ID of document to query
            question: User's question

        Returns:
            RAGResponse with answer, sources, reasoning, confidence
        """
        logger.info(
            "Processing question",
            document_id=document_id,
            question_length=len(question),
        )

        # Step 1: Classify intent
        intent = await self.classify_intent(question)
        logger.debug("Intent classified", intent=intent.value)

        # Handle non-document intents
        if intent == IntentType.GREETING:
            return self._handle_greeting(question)

        if intent == IntentType.OUT_OF_SCOPE:
            return self._handle_out_of_scope(question)

        # Step 2: Check document exists
        if not await vector_store.document_exists(document_id):
            return RAGResponse(
                answer="Document not found. Please upload a document first.",
                sources=[],
                reasoning="The specified document ID does not exist in the system.",
                confidence=0.0,
                intent=intent,
            )

        # Step 3: Generate question embedding
        question_embedding = await embedding_service.generate_embedding(question)

        # Step 4: Retrieve relevant chunks
        search_results = await vector_store.search(
            document_id=document_id,
            query_embedding=question_embedding,
            top_k=self.top_k,
        )

        if not search_results:
            return RAGResponse(
                answer="No relevant content found in the document for this question.",
                sources=[],
                reasoning="Vector search returned no results.",
                confidence=0.0,
                intent=intent,
            )

        # Step 5: Build context and generate answer
        context = self._build_context_with_history(search_results, conversation_history)
        response = await self._generate_answer(question, context, search_results)
        response.intent = intent

        # Apply strict mode rejection if enabled
        if strict_mode and self.hard_reject_enabled:
            if response.confidence < self.min_confidence_for_voice:
                logger.info(
                    "Strict mode rejection",
                    document_id=document_id,
                    confidence=response.confidence,
                    threshold=self.min_confidence_for_voice,
                )
                return RAGResponse(
                    answer=self.refusal_message,
                    sources=[],
                    reasoning="The retrieved context does not sufficiently address this question.",
                    confidence=0.0,
                    intent=intent,
                    was_rejected=True,
                )

        logger.info(
            "Question answered",
            document_id=document_id,
            sources_count=len(response.sources),
            confidence=response.confidence,
            strict_mode=strict_mode,
        )

        return response

    def _build_context(self, search_results: List[SearchResult]) -> str:
        """
        Build context string from search results.

        Args:
            search_results: List of SearchResult objects

        Returns:
            Formatted context string
        """
        context_parts = []

        for result in search_results:
            chunk = result.chunk
            context_parts.append(
                f"[Page {chunk.page_number}, Chunk {chunk.chunk_id}]\n{chunk.text_content}"
            )

        return "\n\n---\n\n".join(context_parts)

    def _build_context_with_history(
        self,
        search_results: List[SearchResult],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Build context string from search results with conversation history.

        Args:
            search_results: List of SearchResult objects
            conversation_history: Optional list of previous messages

        Returns:
            Formatted context string with history
        """
        context_parts = []
        
        # Add conversation history if provided
        if conversation_history:
            history_text = []
            # Limit to last 10 exchanges to avoid token overflow
            recent_history = conversation_history[-10:]
            for msg in recent_history:
                role = msg.get("role", "user").capitalize()
                content = msg.get("content", "")
                history_text.append(f"{role}: {content}")
            
            if history_text:
                context_parts.append("Previous conversation:\n" + "\n".join(history_text))
                context_parts.append("---")
        
        # Add document chunks
        context_parts.append("Relevant document content:")
        for result in search_results:
            chunk = result.chunk
            context_parts.append(
                f"[Page {chunk.page_number}, Chunk {chunk.chunk_id}]\n{chunk.text_content}"
            )

        return "\n\n".join(context_parts)

    async def _generate_answer(
        self,
        question: str,
        context: str,
        search_results: List[SearchResult],
    ) -> RAGResponse:
        """
        Generate answer using LLM with the provided context.

        Args:
            question: User's question
            context: Document context
            search_results: Search results for source mapping

        Returns:
            RAGResponse with generated answer
        """
        if not self.client:
            return self._fallback_answer(search_results)

        try:
            user_prompt = f"""Document Context:
{context}

Question: {question}

Please answer the question based ONLY on the document context provided above. Follow the JSON response format specified."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": RAG_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=1500,
            )

            content = response.choices[0].message.content

            # Parse JSON response
            return self._parse_llm_response(content, search_results)

        except Exception as e:
            logger.error("LLM generation failed", error=str(e))
            return self._fallback_answer(search_results)

    def _parse_llm_response(
        self,
        content: str,
        search_results: List[SearchResult],
    ) -> RAGResponse:
        """
        Parse LLM JSON response into RAGResponse.

        Args:
            content: Raw LLM response
            search_results: Original search results for fallback

        Returns:
            Parsed RAGResponse
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")

            data = json.loads(json_str)

            # Build sources
            sources = []
            for src in data.get("sources", []):
                sources.append(
                    SourceReference(
                        page=src.get("page", 0),
                        text=truncate_text(src.get("text", ""), 200),
                        chunk_id=src.get("chunk_id", ""),
                        relevance_score=0.0,
                    )
                )

            # If no sources provided, use search results
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
                answer=data.get("answer", "Unable to generate answer."),
                sources=sources,
                reasoning=data.get("reasoning", ""),
                confidence=float(data.get("confidence", 0.5)),
            )

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse LLM response as JSON", error=str(e))

            # Return content as plain answer with search results as sources
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
                reasoning="Response parsed from unstructured LLM output.",
                confidence=0.5,
            )

    def _fallback_answer(self, search_results: List[SearchResult]) -> RAGResponse:
        """
        Generate fallback answer when LLM is unavailable.

        Args:
            search_results: Search results to use

        Returns:
            Simple RAGResponse
        """
        if not search_results:
            return RAGResponse(
                answer="Unable to generate answer. No relevant content found.",
                sources=[],
                reasoning="LLM service unavailable and no context found.",
                confidence=0.0,
            )

        # Use top result as answer
        top_result = search_results[0]
        return RAGResponse(
            answer=f"Based on the document, here is relevant information from page {top_result.chunk.page_number}:\n\n{top_result.chunk.text_content}",
            sources=[
                SourceReference(
                    page=r.chunk.page_number,
                    text=truncate_text(r.chunk.text_content, 200),
                    chunk_id=r.chunk.chunk_id,
                    relevance_score=r.score,
                )
                for r in search_results[:3]
            ],
            reasoning="Fallback response using vector search results directly.",
            confidence=top_result.score,
        )

    def _handle_greeting(self, question: str) -> RAGResponse:
        """Handle greeting intent."""
        question_lower = question.lower().strip()

        for key, response in GREETING_RESPONSES.items():
            if key in question_lower:
                answer = response
                break
        else:
            answer = GREETING_RESPONSES["default"]

        return RAGResponse(
            answer=answer,
            sources=[],
            reasoning="User sent a greeting message.",
            confidence=1.0,
            intent=IntentType.GREETING,
        )

    def _handle_out_of_scope(self, question: str) -> RAGResponse:
        """Handle out of scope intent."""
        return RAGResponse(
            answer="I'm designed to help you with questions about your uploaded document. Please ask something related to the document content.",
            sources=[],
            reasoning="Question is outside the scope of document analysis.",
            confidence=1.0,
            intent=IntentType.OUT_OF_SCOPE,
        )

    async def stream_answer(
        self,
        document_id: str,
        question: str,
    ) -> AsyncGenerator[str, None]:
        """
        Stream answer generation for WebSocket support.

        Args:
            document_id: Document ID
            question: User's question

        Yields:
            Answer tokens as they are generated
        """
        logger.info("Starting streaming answer", document_id=document_id)

        # Classify intent
        intent = await self.classify_intent(question)

        # Handle non-document intents (non-streamed)
        if intent == IntentType.GREETING:
            response = self._handle_greeting(question)
            yield json.dumps({"type": "complete", "response": response.model_dump()})
            return

        if intent == IntentType.OUT_OF_SCOPE:
            response = self._handle_out_of_scope(question)
            yield json.dumps({"type": "complete", "response": response.model_dump()})
            return

        # Check document exists
        if not await vector_store.document_exists(document_id):
            yield json.dumps({
                "type": "error",
                "message": "Document not found"
            })
            return

        # Generate embedding and search
        question_embedding = await embedding_service.generate_embedding(question)
        search_results = await vector_store.search(
            document_id=document_id,
            query_embedding=question_embedding,
            top_k=self.top_k,
        )

        if not search_results:
            yield json.dumps({
                "type": "complete",
                "response": {
                    "answer": "No relevant content found in the document.",
                    "sources": [],
                    "reasoning": "Vector search returned no results.",
                    "confidence": 0.0,
                    "intent": intent.value,
                }
            })
            return

        # Build context
        context = self._build_context(search_results)

        # Stream from LLM
        if self.client:
            try:
                user_prompt = f"""Document Context:
{context}

Question: {question}

Please answer the question based ONLY on the document context provided above. Follow the JSON response format specified."""

                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": RAG_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.1,
                    max_tokens=1500,
                    stream=True,
                )

                full_response = ""
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        full_response += token
                        yield json.dumps({"type": "token", "content": token})

                # Parse and send complete response
                parsed = self._parse_llm_response(full_response, search_results)
                parsed.intent = intent
                yield json.dumps({"type": "complete", "response": parsed.model_dump()})

            except Exception as e:
                logger.error("Streaming error", error=str(e))
                yield json.dumps({"type": "error", "message": str(e)})
        else:
            # Fallback for no LLM
            response = self._fallback_answer(search_results)
            response.intent = intent
            yield json.dumps({"type": "complete", "response": response.model_dump()})

    async def answer_for_voice(
        self,
        document_id: str,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> tuple[str, bool, List[SourceReference]]:
        """
        Answer a question for voice call with strict PDF-only enforcement.
        
        This method is optimized for voice responses:
        - Returns plain text suitable for TTS
        - Enforces strict PDF-only mode
        - Returns whether the answer was rejected
        
        Args:
            document_id: Document ID to query
            question: User's question
            conversation_history: Previous conversation for context
        
        Returns:
            Tuple of (answer_text, was_rejected, sources)
        """
        response = await self.answer_question(
            document_id=document_id,
            question=question,
            strict_mode=True,
            conversation_history=conversation_history,
        )
        
        return response.answer, response.was_rejected, response.sources

    async def get_document_summary_for_voice(self, document_id: str) -> str:
        """
        Get a brief document summary suitable for voice greeting.
        
        Args:
            document_id: Document ID
        
        Returns:
            Brief summary text
        """
        try:
            metadata = await vector_store.get_document_metadata(document_id)
            if not metadata:
                return "I'm ready to help you with questions about this document."
            
            # Get a few chunks to understand the document
            question_embedding = await embedding_service.generate_embedding(
                "main topics summary overview"
            )
            search_results = await vector_store.search(
                document_id=document_id,
                query_embedding=question_embedding,
                top_k=3,
            )
            
            if not search_results:
                return f"I'm ready to help you with questions about {metadata.filename}."
            
            # Generate a brief summary
            if self.client:
                context = self._build_context(search_results)
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Generate a very brief (1-2 sentences) summary of what this document is about. Be concise and natural."
                        },
                        {
                            "role": "user",
                            "content": f"Document: {metadata.filename}\n\nContent sample:\n{context[:2000]}"
                        }
                    ],
                    temperature=0.3,
                    max_tokens=100,
                )
                
                summary = response.choices[0].message.content.strip()
                return f"This is {metadata.filename}. {summary} What would you like to know about it?"
            
            return f"I'm ready to help you with questions about {metadata.filename}, which has {metadata.page_count} pages."
            
        except Exception as e:
            logger.error(f"Error generating voice summary: {e}")
            return "I'm ready to help you with questions about this document."

    def detect_exhaustive_intent(self, query: str) -> bool:
        """
        Detect if the user's query requires exhaustive extraction.

        Args:
            query: User's query text

        Returns:
            True if exhaustive extraction should be used
        """
        query_lower = query.lower()
        for pattern in EXHAUSTIVE_INTENT_PATTERNS:
            if re.search(pattern, query_lower):
                logger.info(f"Exhaustive intent detected for query: {query[:50]}...")
                return True
        return False

    async def extract_all_from_document(
        self,
        query: str,
        document_id: str,
    ) -> ExtractionResult:
        """
        Perform exhaustive extraction from the entire document.
        
        This method retrieves ALL chunks for the document and extracts
        all instances matching the user's query.
        
        Args:
            query: What to extract (e.g., "all skills", "all projects")
            document_id: Document ID to extract from
            
        Returns:
            ExtractionResult with all extracted items
        """
        if not settings.ENABLE_EXHAUSTIVE_EXTRACTION:
            logger.warning("Exhaustive extraction disabled")
            return ExtractionResult(query=query, document_id=document_id)

        logger.info(
            "Starting exhaustive extraction",
            document_id=document_id,
            query=query[:100],
        )

        # Get all chunks for the document
        all_chunks = await vector_store.get_all_chunks(
            document_id=document_id,
            max_chunks=settings.EXTRACTION_MAX_CHUNKS,
        )

        if not all_chunks:
            logger.warning("No chunks found for exhaustive extraction")
            return ExtractionResult(query=query, document_id=document_id)

        # Sort by page number for ordered processing
        all_chunks.sort(key=lambda c: (c.page_number, c.start_index))

        # Process in batches to avoid token overflow
        all_items: List[ExtractedItem] = []
        pages_scanned = set()
        batch_size = settings.EXTRACTION_BATCH_SIZE

        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i + batch_size]
            batch_items = await self._extract_from_batch(query, batch)
            all_items.extend(batch_items)
            pages_scanned.update(c.page_number for c in batch)

        # Deduplicate items
        all_items = self._deduplicate_items(all_items)

        # Categorize items
        categories: Dict[str, List[ExtractedItem]] = {}
        for item in all_items:
            cat = item.category or "general"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)

        result = ExtractionResult(
            items=all_items,
            categories=categories,
            total_count=len(all_items),
            pages_scanned=len(pages_scanned),
            query=query,
            document_id=document_id,
        )

        logger.info(
            "Exhaustive extraction complete",
            document_id=document_id,
            total_items=result.total_count,
            pages_scanned=result.pages_scanned,
        )

        return result

    async def _extract_from_batch(
        self,
        query: str,
        chunks: List[TextChunk],
    ) -> List[ExtractedItem]:
        """
        Extract items from a batch of chunks.
        
        Args:
            query: What to extract
            chunks: Batch of chunks to process
            
        Returns:
            List of extracted items
        """
        if not self.client:
            return []

        # Build context from chunks
        context_parts = []
        for chunk in chunks:
            context_parts.append(
                f"[Page {chunk.page_number}, Pos {chunk.start_index}-{chunk.end_index}]\n{chunk.text_content}"
            )
        context = "\n\n---\n\n".join(context_parts)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": EXHAUSTIVE_EXTRACTION_PROMPT},
                    {
                        "role": "user",
                        "content": f"Extract from the following document text:\n\n{context}\n\nUser request: {query}"
                    },
                ],
                temperature=0,
                max_tokens=settings.MAX_EXTRACTION_TOKENS,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            data = json.loads(content)

            items = []
            for item_data in data.get("items", []):
                items.append(ExtractedItem(
                    text=item_data.get("text", ""),
                    page=item_data.get("page", 0),
                    snippet=item_data.get("snippet", ""),
                    category=item_data.get("category", ""),
                    char_start=item_data.get("char_start", 0),
                    char_end=item_data.get("char_end", 0),
                    confidence=item_data.get("confidence", 1.0),
                ))
            return items

        except Exception as e:
            logger.error(f"Batch extraction failed: {e}")
            return []

    def _deduplicate_items(self, items: List[ExtractedItem]) -> List[ExtractedItem]:
        """
        Remove duplicate items based on text similarity.
        
        Args:
            items: List of extracted items
            
        Returns:
            Deduplicated list
        """
        if not items:
            return []

        seen_texts = set()
        unique_items = []

        for item in items:
            # Normalize text for comparison
            normalized = item.text.lower().strip()
            if normalized not in seen_texts:
                seen_texts.add(normalized)
                unique_items.append(item)

        logger.debug(f"Deduplicated {len(items)} items to {len(unique_items)}")
        return unique_items

    async def answer_with_extraction(
        self,
        document_id: str,
        question: str,
        mode: ExtractionMode = ExtractionMode.CONVERSATIONAL,
        strict_mode: bool = False,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> tuple[RAGResponse, Optional[ExtractionResult]]:
        """
        Answer a question with optional exhaustive extraction.
        
        This method auto-detects exhaustive intent and switches modes
        accordingly, or uses the explicitly specified mode.
        
        Args:
            document_id: Document ID
            question: User's question
            mode: Extraction mode (can be auto-detected)
            strict_mode: Whether to enforce strict PDF-only answers
            conversation_history: Previous conversation context
            
        Returns:
            Tuple of (RAGResponse, optional ExtractionResult)
        """
        # Auto-detect exhaustive intent if in conversational mode
        if mode == ExtractionMode.CONVERSATIONAL and self.detect_exhaustive_intent(question):
            mode = ExtractionMode.EXHAUSTIVE

        extraction_result = None

        if mode == ExtractionMode.EXHAUSTIVE:
            # Perform exhaustive extraction
            extraction_result = await self.extract_all_from_document(question, document_id)
            
            # Generate a summary response
            if extraction_result.total_count > 0:
                answer = self._format_extraction_response(extraction_result)
                sources = [
                    SourceReference(
                        page=item.page,
                        text=item.snippet,
                        chunk_id="",
                        relevance_score=item.confidence,
                    )
                    for item in extraction_result.items[:10]  # Limit sources
                ]
                response = RAGResponse(
                    answer=answer,
                    sources=sources,
                    reasoning=f"Exhaustive extraction found {extraction_result.total_count} items across {extraction_result.pages_scanned} pages.",
                    confidence=1.0,
                    intent=IntentType.DOCUMENT_QUERY,
                )
            else:
                response = RAGResponse(
                    answer="No matching items found in the document for your extraction request.",
                    sources=[],
                    reasoning="Exhaustive extraction did not find any matching items.",
                    confidence=0.0,
                    intent=IntentType.DOCUMENT_QUERY,
                )
        else:
            # Standard conversational RAG
            response = await self.answer_question(
                document_id=document_id,
                question=question,
                strict_mode=strict_mode,
                conversation_history=conversation_history,
            )

        return response, extraction_result

    def _format_extraction_response(self, result: ExtractionResult) -> str:
        """
        Format extraction result for voice/text response.
        
        Args:
            result: ExtractionResult to format
            
        Returns:
            Formatted string response
        """
        if not result.items:
            return "No items found."

        # Group by category if available
        if result.categories and len(result.categories) > 1:
            parts = [f"I found {result.total_count} items in {len(result.categories)} categories:"]
            for category, items in result.categories.items():
                item_texts = [item.text for item in items[:5]]  # Limit per category
                more = f" (and {len(items) - 5} more)" if len(items) > 5 else ""
                parts.append(f"\n{category.title()}: {', '.join(item_texts)}{more}")
            return "\n".join(parts)
        else:
            item_texts = [item.text for item in result.items[:10]]
            more = f"\n\nAnd {result.total_count - 10} more items." if result.total_count > 10 else ""
            return f"I found {result.total_count} items: {', '.join(item_texts)}{more}"


# Singleton instance
rag_service = RAGService()
