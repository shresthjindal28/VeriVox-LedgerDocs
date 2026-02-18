"""
OAuth routes for social login (Google, LinkedIn).
"""

from fastapi import APIRouter, HTTPException, status, Query, Response
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.models.schemas import (
    OAuthURLResponse, AuthProvider, TokenResponse, ErrorResponse
)
from app.services.auth_service import auth_service
from app.utils.helpers import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["OAuth"])


# ============================================================================
# OAUTH INITIATION
# ============================================================================

@router.get(
    "/google",
    response_model=OAuthURLResponse
)
async def google_login():
    """
    Get Google OAuth login URL.
    
    Redirect the user to the returned URL to initiate Google login.
    After successful authentication, Google will redirect back to
    the callback URL with an authorization code.
    """
    try:
        url = await auth_service.get_oauth_url(AuthProvider.GOOGLE)
        return OAuthURLResponse(url=url, provider=AuthProvider.GOOGLE)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/google/redirect"
)
async def google_redirect():
    """
    Redirect to Google OAuth login.
    
    This endpoint immediately redirects to Google for authentication.
    Use this for direct browser navigation.
    """
    try:
        url = await auth_service.get_oauth_url(AuthProvider.GOOGLE)
        return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/linkedin",
    response_model=OAuthURLResponse
)
async def linkedin_login():
    """
    Get LinkedIn OAuth login URL.
    
    Redirect the user to the returned URL to initiate LinkedIn login.
    """
    try:
        url = await auth_service.get_oauth_url(AuthProvider.LINKEDIN)
        return OAuthURLResponse(url=url, provider=AuthProvider.LINKEDIN)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/linkedin/redirect"
)
async def linkedin_redirect():
    """
    Redirect to LinkedIn OAuth login.
    """
    try:
        url = await auth_service.get_oauth_url(AuthProvider.LINKEDIN)
        return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# OAUTH CALLBACK
# ============================================================================

@router.get(
    "/callback",
    responses={
        200: {"model": TokenResponse},
        400: {"model": ErrorResponse}
    }
)
async def oauth_callback(
    code: str = Query(None, description="Authorization code from OAuth provider"),
    state: str = Query(None, description="State parameter"),
    error: str = Query(None, description="Error from OAuth provider"),
    error_description: str = Query(None, description="Error description")
):
    """
    OAuth callback handler.
    
    This endpoint receives the callback from OAuth providers (Google, LinkedIn)
    after user authentication. It exchanges the authorization code for tokens.
    
    Parameters:
    - **code**: Authorization code from the provider
    - **state**: State parameter for CSRF protection
    - **error**: Error code if authentication failed
    - **error_description**: Human-readable error description
    
    Returns tokens on success, or redirects to frontend with error.
    """
    # Handle OAuth error
    if error:
        logger.warning("OAuth error", error=error, description=error_description)
        # Redirect to frontend with error
        error_url = f"{settings.FRONTEND_URL}/auth/error?error={error}&description={error_description or ''}"
        return RedirectResponse(url=error_url, status_code=status.HTTP_302_FOUND)
    
    # Require authorization code
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code is required"
        )
    
    try:
        token_response = await auth_service.handle_oauth_callback(code)
        
        # Option 1: Return tokens as JSON (for SPA with JS handling)
        # return token_response
        
        # Option 2: Redirect to frontend with tokens (more common for OAuth flows)
        # The frontend should handle these tokens and store them appropriately
        redirect_url = (
            f"{settings.FRONTEND_URL}/auth/callback"
            f"?access_token={token_response.access_token}"
            f"&refresh_token={token_response.refresh_token}"
            f"&expires_in={token_response.expires_in}"
        )
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
        
    except Exception as e:
        logger.error("OAuth callback failed", error=str(e))
        error_url = f"{settings.FRONTEND_URL}/auth/error?error=auth_failed&description={str(e)}"
        return RedirectResponse(url=error_url, status_code=status.HTTP_302_FOUND)


@router.post(
    "/callback/exchange",
    response_model=TokenResponse,
    responses={400: {"model": ErrorResponse}}
)
async def exchange_oauth_code(code: str = Query(..., description="Authorization code")):
    """
    Exchange OAuth authorization code for tokens.
    
    This is an alternative to the GET callback that returns tokens as JSON
    instead of redirecting. Use this for custom OAuth flow handling.
    """
    try:
        return await auth_service.handle_oauth_callback(code)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
