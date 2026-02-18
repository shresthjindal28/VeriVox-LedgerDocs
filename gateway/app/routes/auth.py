"""
Auth routes - proxied to User-Service.
"""

from fastapi import APIRouter, Request, Response

from app.proxy import proxy_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    include_in_schema=False
)
async def proxy_auth(request: Request, path: str) -> Response:
    """
    Proxy all /api/auth/* requests to User-Service.
    
    Handles:
    - POST /api/auth/register
    - POST /api/auth/login
    - POST /api/auth/logout
    - POST /api/auth/refresh
    - POST /api/auth/reset-password
    - POST /api/auth/update-password
    - POST /api/auth/phone/send-otp
    - POST /api/auth/phone/verify
    - GET /api/auth/me
    - GET /api/auth/google
    - GET /api/auth/linkedin
    - GET /api/auth/callback
    """
    return await proxy_service.proxy_request(
        request=request,
        service="user",
        path=f"/api/auth/{path}"
    )


# Explicit routes for OpenAPI documentation
@router.post("/register", summary="Register new user", include_in_schema=True)
async def register(request: Request) -> Response:
    """Register a new user with email and password."""
    return await proxy_service.proxy_request(request, "user", "/api/auth/register")


@router.post("/login", summary="Login", include_in_schema=True)
async def login(request: Request) -> Response:
    """Login with email and password."""
    return await proxy_service.proxy_request(request, "user", "/api/auth/login")


@router.post("/logout", summary="Logout", include_in_schema=True)
async def logout(request: Request) -> Response:
    """Logout current user."""
    return await proxy_service.proxy_request(request, "user", "/api/auth/logout")


@router.post("/refresh", summary="Refresh token", include_in_schema=True)
async def refresh(request: Request) -> Response:
    """Refresh access token."""
    return await proxy_service.proxy_request(request, "user", "/api/auth/refresh")


@router.get("/me", summary="Get current user", include_in_schema=True)
async def me(request: Request) -> Response:
    """Get current authenticated user info."""
    return await proxy_service.proxy_request(request, "user", "/api/auth/me")
