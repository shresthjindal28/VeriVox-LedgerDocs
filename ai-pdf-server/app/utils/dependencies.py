"""
Dependency injection utilities for FastAPI routes.
"""

from typing import Optional
from fastapi import Request, HTTPException, status

from app.utils.helpers import get_logger

logger = get_logger(__name__)


async def get_user_id_from_header(request: Request) -> Optional[str]:
    """
    Extract user_id from X-User-ID header.
    
    The gateway middleware validates the JWT token and forwards
    the user_id in the X-User-ID header to backend services.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User ID string if present, None otherwise
    """
    user_id = request.headers.get("x-user-id")
    if not user_id:
        return None
    return user_id.strip()


async def require_user_id(request: Request) -> str:
    """
    Require user_id from X-User-ID header.
    
    Raises 401 if user_id is not present.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User ID string
        
    Raises:
        HTTPException: 401 if user_id not present
    """
    user_id = await get_user_id_from_header(request)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user_id
