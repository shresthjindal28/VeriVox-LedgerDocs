"""
Profile and preferences routes for user management.
"""

from fastapi import APIRouter, HTTPException, status, Depends

from app.models.schemas import (
    ProfileResponse, ProfileUpdate,
    StudyPreferencesResponse, StudyPreferencesUpdate,
    FullProfileResponse, MessageResponse, ErrorResponse,
    UserRole
)
from app.services.user_service import user_service
from app.utils.dependencies import (
    get_current_user, AuthenticatedUser,
    require_role, require_admin
)
from app.utils.helpers import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/profile", tags=["Profile"])


# ============================================================================
# PROFILE ENDPOINTS
# ============================================================================

@router.get(
    "",
    response_model=ProfileResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_profile(user: AuthenticatedUser = Depends(get_current_user)):
    """
    Get current user's profile.
    
    Returns the profile data for the authenticated user.
    If profile doesn't exist, returns a default profile.
    """
    profile = await user_service.get_profile(user.id)
    
    if not profile:
        # Return a default profile instead of 404 for better UX
        return ProfileResponse(
            id=user.id,
            display_name=None,
            avatar_url=None,
            bio=None,
            role=UserRole.STUDENT,
            created_at=None,
            updated_at=None
        )
    
    return profile


@router.put(
    "",
    response_model=ProfileResponse,
    responses={400: {"model": ErrorResponse}}
)
async def update_profile(
    update: ProfileUpdate,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Update current user's profile.
    
    - **display_name**: User's display name
    - **avatar_url**: URL to user's avatar image
    - **bio**: Short user biography
    """
    try:
        profile = await user_service.update_profile(user.id, update)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        return profile
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/full",
    response_model=FullProfileResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_full_profile(user: AuthenticatedUser = Depends(get_current_user)):
    """
    Get complete user profile including user info and preferences.
    
    Returns:
    - User authentication info
    - Profile data
    - Study preferences
    """
    full_profile = await user_service.get_full_profile(user.id)
    
    if not full_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return full_profile


# ============================================================================
# PREFERENCES ENDPOINTS
# ============================================================================

@router.get(
    "/preferences",
    response_model=StudyPreferencesResponse
)
async def get_preferences(user: AuthenticatedUser = Depends(get_current_user)):
    """
    Get current user's study preferences.
    
    Returns preferences for AI voice, theme, language, and more.
    """
    return await user_service.get_preferences(user.id)


@router.put(
    "/preferences",
    response_model=StudyPreferencesResponse,
    responses={400: {"model": ErrorResponse}}
)
async def update_preferences(
    update: StudyPreferencesUpdate,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Update current user's study preferences.
    
    - **voice**: AI voice (nova, alloy, echo, fable, onyx, shimmer)
    - **theme**: UI theme (light, dark, system)
    - **language**: Preferred language code
    - **notifications_enabled**: Enable/disable notifications
    - **auto_play_audio**: Auto-play AI responses
    - **playback_speed**: Audio playback speed (0.5 - 2.0)
    """
    try:
        return await user_service.update_preferences(user.id, update)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@router.get(
    "/users",
    response_model=dict,
    responses={403: {"model": ErrorResponse}}
)
async def list_users(
    page: int = 1,
    per_page: int = 20,
    user: AuthenticatedUser = Depends(require_admin)
):
    """
    List all users (admin only).
    
    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 20)
    """
    try:
        return await user_service.list_users(page, per_page)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/users/{user_id}",
    response_model=FullProfileResponse,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
async def get_user_by_id(
    user_id: str,
    admin: AuthenticatedUser = Depends(require_admin)
):
    """
    Get any user's full profile (admin only).
    """
    full_profile = await user_service.get_full_profile(user_id)
    
    if not full_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return full_profile


@router.put(
    "/users/{user_id}/role",
    response_model=ProfileResponse,
    responses={403: {"model": ErrorResponse}}
)
async def update_user_role(
    user_id: str,
    role: UserRole,
    admin: AuthenticatedUser = Depends(require_admin)
):
    """
    Update a user's role (admin only).
    
    - **role**: New role (student, teacher, admin)
    """
    try:
        profile = await user_service.update_role(user_id, role)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return profile
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/users/{user_id}",
    response_model=MessageResponse,
    responses={403: {"model": ErrorResponse}}
)
async def delete_user(
    user_id: str,
    admin: AuthenticatedUser = Depends(require_admin)
):
    """
    Delete a user (admin only).
    
    This will permanently delete the user and all associated data.
    """
    try:
        result = await user_service.delete_user(user_id)
        return MessageResponse(message=result["message"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
