"""
FastAPI application factory for User Service.
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.supabase import supabase
from app.utils.helpers import setup_logging, get_logger

# Setup logging
setup_logging("DEBUG" if settings.DEBUG else "INFO")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Runs startup and shutdown logic.
    """
    # Startup
    logger.info(
        "Starting User Service",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT
    )
    
    # Verify Supabase connection
    try:
        health = await supabase.health_check()
        logger.info("Supabase connection", status=health.get("status"))
    except Exception as e:
        logger.warning("Supabase health check failed", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down User Service")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI instance
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description="Authentication and user management service for Study With Me platform",
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Register routes
    register_routes(app)
    
    return app


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors."""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "message": "Invalid request data",
                "details": errors
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected errors."""
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred" if settings.is_production else str(exc)
            }
        )


def register_routes(app: FastAPI) -> None:
    """Register API routes."""
    from app.api.routes import auth, oauth, profile, internal, avatar
    
    # Include routers with /api prefix
    app.include_router(auth.router, prefix="/api")
    app.include_router(oauth.router, prefix="/api")
    app.include_router(profile.router, prefix="/api")
    app.include_router(avatar.router, prefix="/api")
    
    # Internal routes (no /api prefix, for service-to-service)
    app.include_router(internal.router)
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Service health check."""
        supabase_health = await supabase.health_check()
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "timestamp": datetime.utcnow().isoformat(),
            "supabase_status": supabase_health.get("status", "unknown")
        }
    
    @app.get("/", tags=["Health"])
    async def root():
        """Root endpoint."""
        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs"
        }


# Create application instance
app = create_app()
