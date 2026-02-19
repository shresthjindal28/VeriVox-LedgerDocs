"""FastAPI application factory and configuration."""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import chat, upload, voice, websocket, extraction, verification, dashboard
from app.core.config import settings
from app.models.schemas import ErrorResponse, HealthCheckResponse
from app.services.vector_service import vector_store
from app.utils.helpers import get_logger, setup_logging

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "Starting AI PDF Server",
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG,
    )

    # Preload existing indices
    try:
        count = await vector_store.preload_all_indices()
        logger.info("Preloaded document indices", count=count)
    except Exception as e:
        logger.warning("Failed to preload indices", error=str(e))

    # Check OpenAI configuration
    if not settings.OPENAI_API_KEY:
        logger.warning(
            "OpenAI API key not configured. "
            "Set OPENAI_API_KEY environment variable for full functionality."
        )
    else:
        logger.info("OpenAI API configured", model=settings.LLM_MODEL)

    yield

    # Shutdown
    logger.info("Shutting down AI PDF Server")


# Create FastAPI application
app = FastAPI(
    title="AI PDF Document Intelligence API",
    description="""
    Cloud-native AI backend for PDF document analysis using RAG.

    ## Features
    - **PDF Upload**: Upload and process PDF documents
    - **Semantic Search**: Find relevant content using embeddings
    - **RAG Q&A**: Ask questions and get grounded answers
    - **Voice Chat**: Voice-to-voice AI teacher interactions
    - **Source Citations**: Every answer includes page references
    - **Integrity Verification**: SHA-256 hashing for authenticity
    - **Real-time Streaming**: WebSocket support for live responses

    ## AI Teacher
    The voice chat feature provides an AI teacher persona that:
    - Explains concepts clearly and patiently
    - Uses examples and analogies
    - Encourages students and checks understanding
    - Supports both text and voice input/output

    ## Architecture
    - FAISS vector store (scalable to pgvector/Pinecone)
    - OpenAI embeddings, LLM, Whisper STT, and TTS
    - Blockchain-ready integrity layer
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Exception Handlers
# ============================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            detail=exc.detail,
            status_code=exc.status_code,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            detail="An unexpected error occurred. Please try again.",
            status_code=500,
        ).model_dump(),
    )


# ============================================================
# Include Routers
# ============================================================


app.include_router(upload.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(voice.router, prefix="/api")
app.include_router(extraction.router, prefix="/api")
app.include_router(verification.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(websocket.router)


# ============================================================
# Core Endpoints
# ============================================================


@app.get(
    "/",
    summary="Root endpoint",
    description="Welcome message and API information.",
)
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI PDF Document Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health check",
    description="Check if the API is healthy and operational.",
)
async def health_check():
    """
    Health check endpoint.

    Returns service status for load balancers and monitoring.
    """
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow(),
    )


@app.get(
    "/ready",
    summary="Readiness check",
    description="Check if the API is ready to accept requests.",
)
async def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration.

    Verifies all dependencies are available.
    """
    checks = {
        "vector_store": True,
        "openai_configured": bool(settings.OPENAI_API_KEY),
    }

    # Get vector store stats
    vector_stats = vector_store.get_stats()

    all_ready = all(checks.values())

    return {
        "ready": all_ready,
        "checks": checks,
        "vector_store": vector_stats,
    }


@app.get(
    "/config",
    summary="Configuration info",
    description="Get non-sensitive configuration information.",
)
async def config_info():
    """Return non-sensitive configuration details."""
    return {
        "embedding_model": settings.EMBEDDING_MODEL,
        "llm_model": settings.LLM_MODEL,
        "chunk_size": settings.CHUNK_SIZE,
        "chunk_overlap": settings.CHUNK_OVERLAP,
        "top_k_results": settings.TOP_K_RESULTS,
        "embedding_dimensions": settings.EMBEDDING_DIMENSIONS,
        "openai_configured": bool(settings.OPENAI_API_KEY),
    }
