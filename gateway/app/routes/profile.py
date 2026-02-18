"""
Profile routes - proxied to User-Service.
"""

from fastapi import APIRouter, Request, Response, Depends

from app.proxy import proxy_service
from app.middleware import auth_middleware

router = APIRouter(prefix="/api/profile", tags=["Profile"])


async def get_auth_headers(request: Request) -> dict:
    """Dependency to get auth headers."""
    payload = await auth_middleware.authenticate(request)
    return auth_middleware.get_user_headers(payload) if payload else {}


@router.get("", summary="Get profile")
async def get_profile(request: Request, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Get current user's profile."""
    return await proxy_service.proxy_request(
        request, "user", "/api/profile",
        extra_headers=auth_headers
    )


@router.put("", summary="Update profile")
async def update_profile(request: Request, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Update current user's profile."""
    return await proxy_service.proxy_request(
        request, "user", "/api/profile",
        extra_headers=auth_headers
    )


@router.get("/full", summary="Get full profile")
async def get_full_profile(request: Request, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Get full profile including user info and preferences."""
    return await proxy_service.proxy_request(
        request, "user", "/api/profile/full",
        extra_headers=auth_headers
    )


@router.get("/preferences", summary="Get preferences")
async def get_preferences(request: Request, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Get study preferences."""
    return await proxy_service.proxy_request(
        request, "user", "/api/profile/preferences",
        extra_headers=auth_headers
    )


@router.put("/preferences", summary="Update preferences")
async def update_preferences(request: Request, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Update study preferences."""
    return await proxy_service.proxy_request(
        request, "user", "/api/profile/preferences",
        extra_headers=auth_headers
    )


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    include_in_schema=False
)
async def proxy_profile(request: Request, path: str, auth_headers: dict = Depends(get_auth_headers)) -> Response:
    """Proxy all other /api/profile/* requests."""
    return await proxy_service.proxy_request(
        request, "user", f"/api/profile/{path}",
        extra_headers=auth_headers
    )
