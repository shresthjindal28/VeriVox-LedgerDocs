"""Chat and RAG question answering routes."""

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import ChatRequest, IntentType, RAGResponse
from app.services.rag_service import rag_service
from app.services.vector_service import vector_store
from app.utils.helpers import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Chat"])


@router.post(
    "/chat",
    response_model=RAGResponse,
    summary="Ask a question about a document",
    description="Send a question about an uploaded document and receive an AI-generated answer with sources.",
)
async def chat(request: ChatRequest):
    """
    RAG-based question answering endpoint.

    This endpoint:
    1. Classifies the intent of the question
    2. Retrieves relevant document chunks via semantic search
    3. Generates an answer grounded in the document context
    4. Provides source citations with page numbers
    5. Returns confidence score and reasoning

    The response format includes:
    - answer: The generated response
    - sources: List of source chunks with page numbers
    - reasoning: Explanation of how the answer was derived
    - confidence: 0.0 to 1.0 confidence score
    - intent: Classified intent type

    If the answer cannot be found in the document, the system
    will explicitly state this rather than making up information.
    """
    # Validate document exists
    if not await vector_store.document_exists(request.document_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {request.document_id}. Please upload a document first.",
        )

    # Validate question
    if not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty",
        )

    if len(request.question) > 2000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question is too long. Maximum 2000 characters allowed.",
        )

    try:
        logger.info(
            "Processing chat request",
            document_id=request.document_id,
            question_length=len(request.question),
        )

        # Get RAG response
        response = await rag_service.answer_question(
            document_id=request.document_id,
            question=request.question,
        )

        logger.info(
            "Chat response generated",
            document_id=request.document_id,
            intent=response.intent.value,
            confidence=response.confidence,
            sources_count=len(response.sources),
        )

        return response

    except ValueError as e:
        logger.error("Chat value error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "Chat failed",
            error=str(e),
            document_id=request.document_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}",
        )


@router.post(
    "/chat/classify",
    summary="Classify question intent",
    description="Classify the intent of a question without generating a full response.",
)
async def classify_intent(request: ChatRequest):
    """
    Classify the intent of a question.

    Intent types:
    - document_query: Question about document content
    - greeting: Casual greeting or introduction
    - clarification: Request for clarification
    - out_of_scope: Question unrelated to document analysis

    This is useful for understanding user behavior
    and routing queries appropriately.
    """
    try:
        intent = await rag_service.classify_intent(request.question)

        return {
            "question": request.question,
            "intent": intent.value,
            "description": _get_intent_description(intent),
        }

    except Exception as e:
        logger.error("Intent classification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to classify intent: {str(e)}",
        )


@router.get(
    "/chat/health",
    summary="Check chat service health",
    description="Verify that the chat and embedding services are operational.",
)
async def chat_health():
    """
    Check health of chat-related services.

    Verifies:
    - Embedding service connectivity
    - RAG service readiness
    - Vector store status
    """
    from app.services.embedding_service import embedding_service

    try:
        # Check embedding service
        embedding_healthy = await embedding_service.health_check()

        # Get vector store stats
        vector_stats = vector_store.get_stats()

        return {
            "status": "healthy" if embedding_healthy else "degraded",
            "services": {
                "embedding_service": "healthy" if embedding_healthy else "unhealthy",
                "vector_store": "healthy",
                "rag_service": "healthy",
            },
            "vector_store_stats": vector_stats,
        }

    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
        }


def _get_intent_description(intent: IntentType) -> str:
    """Get human-readable description for intent type."""
    descriptions = {
        IntentType.DOCUMENT_QUERY: "Question about document content",
        IntentType.GREETING: "Greeting or casual conversation",
        IntentType.CLARIFICATION: "Request for clarification",
        IntentType.OUT_OF_SCOPE: "Question unrelated to document analysis",
    }
    return descriptions.get(intent, "Unknown intent")
