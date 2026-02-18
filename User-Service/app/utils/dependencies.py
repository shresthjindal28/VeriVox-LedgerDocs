"""
Authentication dependencies for FastAPI route protection.
Provides get_current_user, require_role, and optional auth.
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.core.config import settings
from app.core.supabase import supabase
from app.models.schemas import UserRole, UserResponse
from app.utils.helpers import get_logger

logger = get_logger(__name__)

# Bearer token security scheme
security = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    """
    Represents an authenticated user with profile data.
    """
    
    def __init__(
        self,
        id: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        role: UserRole = UserRole.STUDENT,
        email_confirmed: bool = False,
        phone_confirmed: bool = False,
        metadata: dict = None
    ):
        self.id = id
        self.email = email
        self.phone = phone
        self.role = role
        self.email_confirmed = email_confirmed
        self.phone_confirmed = phone_confirmed
        self.metadata = metadata or {}
    
    def has_role(self, role: UserRole) -> bool:
        """Check if user has a specific role."""
        # Admin has all roles
        if self.role == UserRole.ADMIN:
            return True
        # Teacher has teacher and student roles
        if self.role == UserRole.TEACHER and role in [UserRole.TEACHER, UserRole.STUDENT]:
            return True
        return self.role == role
    
    def to_response(self) -> UserResponse:
        """Convert to UserResponse schema."""
        return UserResponse(
            id=self.id,
            email=self.email,
            phone=self.phone,
            role=self.role
        )


async def decode_jwt_token(token: str) -> dict:
    """
    Decode and validate a Supabase JWT token.
    
    Uses Supabase's auth.get_user() for proper token verification,
    which handles both HS256 and ES256 algorithms automatically.
    
    Args:
        token: JWT access token
    
    Returns:
        Decoded token payload with user data
    
    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Use Supabase's built-in token verification
        # This properly handles ES256 tokens from Supabase Auth v2
        user_response = supabase.client.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        user = user_response.user
        
        # Build payload similar to JWT decode
        return {
            "sub": user.id,
            "email": user.email,
            "phone": user.phone,
            "email_confirmed": user.email_confirmed_at is not None,
            "phone_confirmed": user.phone_confirmed_at is not None,
            "user_metadata": user.user_metadata or {},
            "app_metadata": user.app_metadata or {},
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "expired" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AuthenticatedUser:
    """
    Dependency to get the current authenticated user.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: AuthenticatedUser = Depends(get_current_user)):
            return {"user_id": user.id}
    
    Raises:
        HTTPException: 401 if not authenticated or token invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    payload = await decode_jwt_token(token)
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user role from profile table
    role = UserRole.STUDENT
    try:
        result = supabase.admin_table("profiles").select("role").eq("id", user_id).single().execute()
        if result.data:
            role = UserRole(result.data.get("role", "student"))
    except Exception as e:
        logger.warning(f"Failed to fetch user role: {e}")
    
    return AuthenticatedUser(
        id=user_id,
        email=payload.get("email"),
        phone=payload.get("phone"),
        role=role,
        email_confirmed=payload.get("email_confirmed", False),
        phone_confirmed=payload.get("phone_confirmed", False),
        metadata=payload.get("user_metadata", {})
    )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[AuthenticatedUser]:
    """
    Dependency to optionally get the current user.
    Returns None if not authenticated (instead of raising).
    
    Usage:
        @app.get("/public")
        async def public_route(user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)):
            if user:
                return {"user_id": user.id}
            return {"message": "Anonymous access"}
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_role(allowed_roles: List[UserRole]):
    """
    Dependency factory to require specific roles.
    
    Usage:
        @app.get("/admin-only")
        async def admin_route(user: AuthenticatedUser = Depends(require_role([UserRole.ADMIN]))):
            return {"admin": user.id}
        
        @app.get("/teachers")
        async def teacher_route(user: AuthenticatedUser = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN]))):
            return {"teacher": user.id}
    """
    async def role_checker(
        user: AuthenticatedUser = Depends(get_current_user)
    ) -> AuthenticatedUser:
        if not any(user.has_role(role) for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
            )
        return user
    
    return role_checker


def require_verified_email(
    user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    """
    Dependency to require a verified email address.
    """
    if not user.email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return user


# Convenience dependencies
require_admin = require_role([UserRole.ADMIN])
require_teacher = require_role([UserRole.TEACHER, UserRole.ADMIN])
require_student = require_role([UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN])
