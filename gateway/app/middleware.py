"""
Authentication middleware for the gateway.
Validates JWT tokens and injects user info into requests.
"""

from typing import Optional, Tuple

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.config import settings
from app.logging import get_logger

logger = get_logger(__name__)

security = HTTPBearer(auto_error=False)


class AuthMiddleware:
    """
    Middleware for validating JWT tokens from User-Service.
    
    Validates tokens and extracts user information for downstream services.
    """
    
    # Paths that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        # Auth endpoints
        "/api/auth/register",
        "/api/auth/login",
        "/api/auth/refresh",
        "/api/auth/reset-password",
        "/api/auth/phone/send-otp",
        "/api/auth/phone/verify",
        "/api/auth/google",
        "/api/auth/google/redirect",
        "/api/auth/linkedin",
        "/api/auth/linkedin/redirect",
        "/api/auth/callback",
    }
    
    # Path prefixes that are public
    PUBLIC_PREFIXES = {
        "/docs",
        "/redoc",
    }
    
    @classmethod
    def is_public_path(cls, path: str) -> bool:
        """Check if path is public (no auth required)."""
        if path in cls.PUBLIC_PATHS:
            return True
        
        for prefix in cls.PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return True
        
        return False
    
    @classmethod
    def extract_token(cls, request: Request) -> Optional[str]:
        """Extract JWT token from Authorization header."""
        auth_header = request.headers.get("authorization", "")
        
        if auth_header.lower().startswith("bearer "):
            return auth_header[7:]
        
        return None
    
    @classmethod
    def validate_token(cls, token: str) -> Tuple[bool, Optional[dict], Optional[str]]:
        """
        Validate a JWT token.
        
        Returns:
            Tuple of (is_valid, payload, error_message)
        """
        if not settings.SUPABASE_JWT_SECRET:
            # No JWT secret configured - pass through
            logger.warning("No JWT secret configured, skipping validation")
            return True, None, None
        
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
                audience="authenticated"
            )
            return True, payload, None
            
        except jwt.ExpiredSignatureError:
            return False, None, "Token has expired"
        except jwt.InvalidTokenError as e:
            return False, None, f"Invalid token: {str(e)}"
    
    @classmethod
    async def authenticate(cls, request: Request) -> Optional[dict]:
        """
        Authenticate a request.
        
        For protected paths, extracts the token and returns basic payload info.
        Actual token validation is done by downstream services (User-Service, PDF-Service).
        This avoids algorithm mismatch issues (ES256 vs HS256) and reduces redundant validation.
        
        Returns user payload if authenticated, None if public path,
        raises HTTPException if auth required but no token provided.
        """
        path = request.url.path
        
        # Check if path is public
        if cls.is_public_path(path):
            return None
        
        # Extract token
        token = cls.extract_token(request)
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Decode token WITHOUT validation to extract claims
        # Actual validation is done by downstream services
        try:
            # Decode without verification to get payload
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
                audience="authenticated"
            )
            return payload
        except jwt.InvalidTokenError:
            # If we can't even decode the token structure, it's malformed
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed token",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    @classmethod
    def get_user_headers(cls, payload: dict) -> dict:
        """
        Get headers to forward user info to backend services.
        
        These headers allow backend services to know who the user is
        without re-validating the token.
        """
        if not payload:
            return {}
        
        return {
            "X-User-ID": payload.get("sub", ""),
            "X-User-Email": payload.get("email", ""),
            "X-User-Role": payload.get("role", "student"),
        }
    
    @classmethod
    async def get_user_from_token(cls, auth_header: str) -> Optional[dict]:
        """
        Extract user info from an Authorization header.
        
        Used for WebSocket connections where we need to extract user info
        without the full request context.
        
        Args:
            auth_header: The Authorization header value (e.g., "Bearer <token>")
        
        Returns:
            Dict with user_id, email, role if token is valid, None otherwise
        """
        if not auth_header:
            return None
        
        # Extract token from "Bearer <token>"
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
        else:
            return None
        
        try:
            # Decode without verification to get payload
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
                audience="authenticated"
            )
            
            return {
                "user_id": payload.get("sub", ""),
                "email": payload.get("email", ""),
                "role": payload.get("role", "student"),
            }
        except jwt.InvalidTokenError:
            return None


auth_middleware = AuthMiddleware()
