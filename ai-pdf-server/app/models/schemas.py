"""Pydantic schemas for request/response models."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ============================================================
# Enums
# ============================================================


class IntentType(str, Enum):
    """Classification of user query intent."""

    DOCUMENT_QUERY = "document_query"
    GREETING = "greeting"
    OUT_OF_SCOPE = "out_of_scope"
    CLARIFICATION = "clarification"


class MessageType(str, Enum):
    """WebSocket message types."""

    QUESTION = "question"
    ANSWER_CHUNK = "answer_chunk"
    ANSWER_COMPLETE = "answer_complete"
    ERROR = "error"
    STATUS = "status"


# ============================================================
# Document & Chunk Models
# ============================================================


class TextChunk(BaseModel):
    """Represents a chunk of text from a document."""

    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    page_number: int = Field(..., description="Page number where chunk originates")
    text_content: str = Field(..., description="The actual text content")
    start_index: int = Field(default=0, description="Start character index in page")
    end_index: int = Field(default=0, description="End character index in page")


class DocumentMetadata(BaseModel):
    """Metadata for an uploaded document."""

    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    upload_timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When document was uploaded"
    )
    sha256_hash: str = Field(..., description="SHA-256 hash of document content")
    page_count: int = Field(..., description="Number of pages in document")
    chunk_count: int = Field(..., description="Number of chunks created")
    file_size_bytes: int = Field(default=0, description="Size of file in bytes")


# ============================================================
# RAG Response Models
# ============================================================


class SourceReference(BaseModel):
    """Reference to a source chunk in the document."""

    page: int = Field(..., description="Page number of the source")
    text: str = Field(..., description="Relevant text excerpt")
    chunk_id: str = Field(..., description="ID of the source chunk")
    relevance_score: float = Field(
        default=0.0, description="Similarity score for this source"
    )


class RAGResponse(BaseModel):
    """Complete response from RAG system."""

    answer: str = Field(..., description="The generated answer")
    sources: List[SourceReference] = Field(
        default_factory=list, description="Source references supporting the answer"
    )
    reasoning: str = Field(
        default="", description="Explanation of how the answer was derived"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence score for the answer"
    )
    intent: IntentType = Field(
        default=IntentType.DOCUMENT_QUERY, description="Classified intent of the query"
    )
    was_rejected: bool = Field(
        default=False, description="Whether the answer was rejected due to low confidence in strict mode"
    )


# ============================================================
# Request Models
# ============================================================


class ChatRequest(BaseModel):
    """Request for chat/question answering."""

    document_id: str = Field(..., description="ID of the document to query")
    question: str = Field(..., min_length=1, description="User's question")


class IntegrityVerifyRequest(BaseModel):
    """Request to verify document integrity."""

    document_id: str = Field(..., description="ID of the document to verify")
    provided_hash: str = Field(..., description="Hash to verify against")


# ============================================================
# Response Models
# ============================================================


class UploadResponse(BaseModel):
    """Response after successful PDF upload."""

    document_id: str = Field(..., description="Assigned document ID")
    filename: str = Field(..., description="Original filename")
    page_count: int = Field(..., description="Number of pages extracted")
    chunk_count: int = Field(..., description="Number of chunks created")
    sha256_hash: str = Field(..., description="SHA-256 hash of document")
    message: str = Field(default="Document uploaded successfully")


class DocumentHashResponse(BaseModel):
    """Response containing document hash."""

    document_id: str = Field(..., description="Document ID")
    sha256_hash: str = Field(..., description="SHA-256 hash of document")
    filename: str = Field(..., description="Original filename")
    blockchain_ready: bool = Field(
        default=True, description="Whether hash is ready for blockchain storage"
    )


class IntegrityVerifyResponse(BaseModel):
    """Response from integrity verification."""

    document_id: str = Field(..., description="Document ID verified")
    is_valid: bool = Field(..., description="Whether integrity check passed")
    stored_hash: str = Field(..., description="Hash stored in system")
    provided_hash: str = Field(..., description="Hash provided for verification")
    message: str = Field(..., description="Verification result message")


class DocumentListResponse(BaseModel):
    """Response containing list of documents."""

    documents: List[DocumentMetadata] = Field(
        default_factory=list, description="List of document metadata"
    )
    total_count: int = Field(default=0, description="Total number of documents")


class DeleteResponse(BaseModel):
    """Response after document deletion."""

    document_id: str = Field(..., description="ID of deleted document")
    message: str = Field(default="Document deleted successfully")


# ============================================================
# WebSocket Models
# ============================================================


class WebSocketMessage(BaseModel):
    """Message format for WebSocket communication."""

    type: MessageType = Field(..., description="Type of message")
    content: str = Field(default="", description="Message content")
    document_id: Optional[str] = Field(default=None, description="Associated document")
    metadata: Optional[dict] = Field(
        default=None, description="Additional metadata"
    )


class WebSocketQuestionMessage(BaseModel):
    """Incoming question message via WebSocket."""

    question: str = Field(..., min_length=1, description="User's question")


class WebSocketAnswerChunk(BaseModel):
    """Streaming answer chunk via WebSocket."""

    type: MessageType = Field(
        default=MessageType.ANSWER_CHUNK, description="Message type"
    )
    chunk: str = Field(..., description="Text chunk of the answer")
    is_final: bool = Field(default=False, description="Whether this is the final chunk")


class WebSocketCompleteResponse(BaseModel):
    """Complete response sent via WebSocket after streaming."""

    type: MessageType = Field(
        default=MessageType.ANSWER_COMPLETE, description="Message type"
    )
    response: RAGResponse = Field(..., description="Complete RAG response")


# ============================================================
# Error Models
# ============================================================


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Detailed error message")
    status_code: int = Field(..., description="HTTP status code")


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy", description="Service status")
    version: str = Field(default="1.0.0", description="API version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Current timestamp"
    )
