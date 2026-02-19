"""
API Gateway for Study With Me platform.
Routes requests to appropriate backend microservices.
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.logging import setup_logging, get_logger
from app.proxy import proxy_service

# Setup logging
setup_logging("DEBUG" if settings.DEBUG else "INFO")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    logger.info(
        "Starting API Gateway",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        pdf_service=settings.PDF_SERVICE_URL,
        user_service=settings.USER_SERVICE_URL
    )
    
    # Start proxy service
    await proxy_service.start()
    
    yield
    
    # Shutdown
    await proxy_service.stop()
    logger.info("API Gateway stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI gateway application."""
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="""
API Gateway for Study With Me platform.

This gateway routes requests to the appropriate backend services:
- **User-Service** (port 8001): Authentication, profiles, preferences
- **PDF-Service** (port 8000): Document processing, RAG, voice

All endpoints are available through this single gateway (port 8080).
        """,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routes
    register_routes(app)
    
    # Register exception handlers
    register_exception_handlers(app)
    
    return app


def register_routes(app: FastAPI) -> None:
    """Register all route handlers."""
    from app.routes import auth, profile, documents, chat, voice, websocket, verification, dashboard
    
    # API routes
    app.include_router(auth.router)
    app.include_router(profile.router)
    app.include_router(documents.router)
    app.include_router(chat.router)
    app.include_router(voice.router)
    app.include_router(verification.router)
    app.include_router(dashboard.router)
    
    # WebSocket routes
    app.include_router(websocket.router)
    
    # Health check
    @app.get("/health", tags=["Health"])
    async def health():
        """Gateway health check."""
        return {
            "status": "healthy",
            "service": "gateway",
            "version": settings.APP_VERSION,
            "timestamp": datetime.utcnow().isoformat(),
            "backends": {
                "pdf_service": settings.PDF_SERVICE_URL,
                "user_service": settings.USER_SERVICE_URL
            }
        }
    
    # Root
    @app.get("/", tags=["Health"])
    async def root():
        """Gateway root endpoint."""
        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/health"
        }
    
    # Backend health aggregation
    @app.get("/health/backends", tags=["Health"])
    async def backends_health():
        """Check health of all backend services."""
        import httpx
        
        results = {}
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check PDF Service
            try:
                resp = await client.get(f"{settings.PDF_SERVICE_URL}/health")
                results["pdf_service"] = {
                    "status": "healthy" if resp.status_code == 200 else "unhealthy",
                    "response_code": resp.status_code
                }
            except Exception as e:
                results["pdf_service"] = {"status": "unreachable", "error": str(e)}
            
            # Check User Service
            try:
                resp = await client.get(f"{settings.USER_SERVICE_URL}/health")
                results["user_service"] = {
                    "status": "healthy" if resp.status_code == 200 else "unhealthy",
                    "response_code": resp.status_code
                }
            except Exception as e:
                results["user_service"] = {"status": "unreachable", "error": str(e)}
        
        all_healthy = all(r.get("status") == "healthy" for r in results.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "backends": results
        }


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": str(exc) if settings.DEBUG else "An unexpected error occurred"
            }
        )


# Create application instance
app = create_app()
