"""
Avatar upload route for user profile images.
Uses Supabase Storage for file storage.
"""

import uuid
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File

from app.services.user_service import user_service
from app.models.schemas import ProfileResponse, ProfileUpdate, ErrorResponse
from app.utils.dependencies import get_current_user, AuthenticatedUser
from app.utils.helpers import get_logger
from app.core.supabase import supabase

logger = get_logger(__name__)

router = APIRouter(prefix="/profile", tags=["Avatar"])

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def _get_extension(filename: str) -> str:
    """Extract file extension from filename."""
    if "." in filename:
        return filename.rsplit(".", 1)[1].lower()
    return ""


@router.post(
    "/avatar",
    response_model=ProfileResponse,
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}},
)
async def upload_avatar(
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Upload a profile avatar image.

    - Accepts PNG, JPG, JPEG, GIF, WEBP
    - Max file size: 5 MB
    - Stores in Supabase Storage bucket 'avatars'
    - Updates user profile with the new avatar URL
    """
    # Validate file extension
    ext = _get_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )

    # Generate unique filename
    unique_name = f"{user.id}/{uuid.uuid4().hex}.{ext}"

    try:
        # Upload to Supabase Storage (bucket: avatars)
        storage = supabase.admin.storage
        bucket_name = "avatars"

        # Try to create bucket if it doesn't exist
        try:
            storage.create_bucket(
                bucket_name,
                options={
                    "public": True,
                    "file_size_limit": MAX_FILE_SIZE,
                    "allowed_mime_types": [
                        "image/png",
                        "image/jpeg",
                        "image/gif",
                        "image/webp",
                    ],
                },
            )
        except Exception:
            # Bucket likely already exists
            pass

        # Delete old avatar if exists
        try:
            existing_files = storage.from_(bucket_name).list(user.id)
            if existing_files:
                paths_to_delete = [f"{user.id}/{f['name']}" for f in existing_files]
                if paths_to_delete:
                    storage.from_(bucket_name).remove(paths_to_delete)
        except Exception:
            pass

        # Upload new avatar
        content_type = file.content_type or f"image/{ext}"
        storage.from_(bucket_name).upload(
            unique_name,
            content,
            file_options={"content-type": content_type, "upsert": "true"},
        )

        # Get public URL
        public_url = storage.from_(bucket_name).get_public_url(unique_name)

        logger.info("Avatar uploaded", user_id=user.id, url=public_url)

        # Update profile with new avatar URL
        profile = await user_service.update_profile(
            user.id, ProfileUpdate(avatar_url=public_url)
        )

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile with avatar URL",
            )

        return profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Avatar upload failed", user_id=user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Avatar upload failed: {str(e)}",
        )


@router.delete(
    "/avatar",
    response_model=ProfileResponse,
    responses={400: {"model": ErrorResponse}},
)
async def delete_avatar(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Delete the current user's avatar.
    Removes the file from storage and clears the avatar_url in profile.
    """
    try:
        # Remove files from storage
        storage = supabase.admin.storage
        bucket_name = "avatars"

        try:
            existing_files = storage.from_(bucket_name).list(user.id)
            if existing_files:
                paths_to_delete = [f"{user.id}/{f['name']}" for f in existing_files]
                if paths_to_delete:
                    storage.from_(bucket_name).remove(paths_to_delete)
        except Exception:
            pass

        # Clear avatar_url in profile
        profile = await user_service.update_profile(
            user.id, ProfileUpdate(avatar_url="")
        )

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        logger.info("Avatar deleted", user_id=user.id)
        return profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Avatar delete failed", user_id=user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
