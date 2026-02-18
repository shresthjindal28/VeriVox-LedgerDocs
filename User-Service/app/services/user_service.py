"""
User and Profile service for managing user data.
Handles profiles, preferences, and user management.
"""

from typing import Optional
from datetime import datetime

from app.core.supabase import supabase
from app.models.schemas import (
    ProfileResponse, ProfileUpdate, ProfileCreate,
    StudyPreferencesResponse, StudyPreferencesUpdate,
    UserRole, FullProfileResponse, UserResponse
)
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class UserService:
    """
    Service for user profile and preferences management.
    
    Uses Supabase PostgreSQL for data storage.
    """
    
    # ========================================================================
    # PROFILE MANAGEMENT
    # ========================================================================
    
    async def get_profile(self, user_id: str) -> Optional[ProfileResponse]:
        """
        Get user profile. Auto-creates profile if it doesn't exist.
        
        Args:
            user_id: User ID
        
        Returns:
            Profile data or None
        """
        try:
            result = supabase.admin_table("profiles").select("*").eq("id", user_id).single().execute()
            
            if not result.data:
                # Auto-create profile if it doesn't exist
                return await self._auto_create_profile(user_id)
            
            return ProfileResponse(
                id=result.data["id"],
                display_name=result.data.get("display_name"),
                avatar_url=result.data.get("avatar_url"),
                bio=result.data.get("bio"),
                role=UserRole(result.data.get("role", "student")),
                created_at=result.data.get("created_at"),
                updated_at=result.data.get("updated_at")
            )
            
        except Exception as e:
            error_str = str(e)
            # Check if error is "no rows returned" - profile doesn't exist
            if "PGRST116" in error_str or "0 rows" in error_str.lower() or "no rows" in error_str.lower():
                return await self._auto_create_profile(user_id)
            # Check if profiles table doesn't exist
            if "PGRST205" in error_str or "profiles" in error_str.lower():
                logger.warning("Profiles table may not exist. Please run Supabase migrations.", error=error_str)
                # Return a default profile response without database
                return ProfileResponse(
                    id=user_id,
                    display_name=None,
                    avatar_url=None,
                    bio=None,
                    role=UserRole.STUDENT,
                    created_at=None,
                    updated_at=None
                )
            logger.error("Failed to get profile", user_id=user_id, error=error_str)
            return None
    
    async def _auto_create_profile(self, user_id: str) -> Optional[ProfileResponse]:
        """
        Auto-create a profile for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Created profile
        """
        try:
            now = datetime.utcnow().isoformat()
            
            # Try to get user info from Supabase auth
            display_name = None
            try:
                user = supabase.auth_admin.get_user_by_id(user_id)
                if user and user.user:
                    metadata = user.user.user_metadata or {}
                    display_name = metadata.get("display_name") or metadata.get("full_name")
            except Exception:
                pass
            
            data = {
                "id": user_id,
                "display_name": display_name,
                "role": "student",
                "created_at": now,
                "updated_at": now
            }
            
            result = supabase.admin_table("profiles").insert(data).execute()
            
            if result.data:
                logger.info("Auto-created profile", user_id=user_id)
                return ProfileResponse(
                    id=user_id,
                    display_name=display_name,
                    avatar_url=None,
                    bio=None,
                    role=UserRole.STUDENT,
                    created_at=now,
                    updated_at=now
                )
            return None
            
        except Exception as e:
            error_str = str(e)
            # If table doesn't exist, return default profile
            if "PGRST205" in error_str:
                logger.warning("Profiles table does not exist. Please run Supabase migrations.")
                return ProfileResponse(
                    id=user_id,
                    display_name=None,
                    avatar_url=None,
                    bio=None,
                    role=UserRole.STUDENT,
                    created_at=None,
                    updated_at=None
                )
            logger.error("Failed to auto-create profile", user_id=user_id, error=error_str)
            return None
    
    async def update_profile(self, user_id: str, update: ProfileUpdate) -> Optional[ProfileResponse]:
        """
        Update user profile.
        
        Args:
            user_id: User ID
            update: Profile update data
        
        Returns:
            Updated profile
        """
        try:
            # Build update dict, excluding None values
            update_data = {k: v for k, v in update.model_dump().items() if v is not None}
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            result = supabase.admin_table("profiles").update(update_data).eq("id", user_id).execute()
            
            if not result.data:
                return None
            
            logger.info("Profile updated", user_id=user_id)
            return await self.get_profile(user_id)
            
        except Exception as e:
            logger.error("Failed to update profile", user_id=user_id, error=str(e))
            raise Exception(f"Failed to update profile: {e}")
    
    async def create_profile(self, profile: ProfileCreate) -> ProfileResponse:
        """
        Create a new profile (internal use).
        
        Args:
            profile: Profile creation data
        
        Returns:
            Created profile
        """
        try:
            now = datetime.utcnow().isoformat()
            
            data = {
                "id": profile.user_id,
                "display_name": profile.display_name,
                "avatar_url": profile.avatar_url,
                "bio": profile.bio,
                "role": profile.role.value,
                "created_at": now,
                "updated_at": now
            }
            
            result = supabase.admin_table("profiles").insert(data).execute()
            
            logger.info("Profile created", user_id=profile.user_id)
            return await self.get_profile(profile.user_id)
            
        except Exception as e:
            logger.error("Failed to create profile", error=str(e))
            raise Exception(f"Failed to create profile: {e}")
    
    # ========================================================================
    # PREFERENCES MANAGEMENT
    # ========================================================================
    
    async def get_preferences(self, user_id: str) -> Optional[StudyPreferencesResponse]:
        """
        Get user study preferences.
        
        Args:
            user_id: User ID
        
        Returns:
            Preferences or None
        """
        try:
            # Use maybe_single() or check without single() to avoid 406 error when no rows exist
            result = supabase.admin_table("study_preferences").select("*").eq("user_id", user_id).execute()
            
            if not result.data or len(result.data) == 0:
                # Return defaults if not found
                return StudyPreferencesResponse(
                    user_id=user_id,
                    voice="nova",
                    theme="system",
                    language="en",
                    notifications_enabled=True,
                    auto_play_audio=False,
                    playback_speed=1.0,
                    updated_at=datetime.utcnow()
                )
            
            # Get the first (and should be only) row
            pref_data = result.data[0]
            
            return StudyPreferencesResponse(
                user_id=pref_data["user_id"],
                voice=pref_data.get("voice", "nova"),
                theme=pref_data.get("theme", "system"),
                language=pref_data.get("language", "en"),
                notifications_enabled=pref_data.get("notifications_enabled", True),
                auto_play_audio=pref_data.get("auto_play_audio", False),
                playback_speed=pref_data.get("playback_speed", 1.0),
                updated_at=pref_data.get("updated_at")
            )
            
        except Exception as e:
            logger.error("Failed to get preferences", user_id=user_id, error=str(e))
            # Return defaults on error
            return StudyPreferencesResponse(
                user_id=user_id,
                voice="nova",
                theme="system",
                language="en",
                notifications_enabled=True,
                auto_play_audio=False,
                playback_speed=1.0,
                updated_at=datetime.utcnow()
            )
    
    async def update_preferences(
        self,
        user_id: str,
        update: StudyPreferencesUpdate
    ) -> StudyPreferencesResponse:
        """
        Update user study preferences.
        
        Args:
            user_id: User ID
            update: Preferences update data
        
        Returns:
            Updated preferences
        """
        try:
            # Build update dict, excluding None values
            update_data = {k: v.value if hasattr(v, 'value') else v 
                          for k, v in update.model_dump().items() if v is not None}
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Check if preferences exist
            existing = supabase.admin_table("study_preferences").select("user_id").eq("user_id", user_id).execute()
            
            if existing.data:
                # Update existing
                supabase.admin_table("study_preferences").update(update_data).eq("user_id", user_id).execute()
            else:
                # Insert new with defaults
                insert_data = {
                    "user_id": user_id,
                    "voice": "nova",
                    "theme": "system",
                    "language": "en",
                    "notifications_enabled": True,
                    "auto_play_audio": False,
                    "playback_speed": 1.0,
                    **update_data
                }
                supabase.admin_table("study_preferences").insert(insert_data).execute()
            
            logger.info("Preferences updated", user_id=user_id)
            return await self.get_preferences(user_id)
            
        except Exception as e:
            logger.error("Failed to update preferences", user_id=user_id, error=str(e))
            raise Exception(f"Failed to update preferences: {e}")
    
    # ========================================================================
    # COMBINED OPERATIONS
    # ========================================================================
    
    async def get_full_profile(self, user_id: str) -> Optional[FullProfileResponse]:
        """
        Get full profile including user info and preferences.
        
        Args:
            user_id: User ID
        
        Returns:
            Full profile data
        """
        profile = await self.get_profile(user_id)
        if not profile:
            return None
        
        preferences = await self.get_preferences(user_id)
        
        # Get user info from Supabase auth
        try:
            user_data = supabase.auth_admin.get_user_by_id(user_id)
            user = UserResponse(
                id=user_id,
                email=user_data.user.email if user_data.user else None,
                phone=user_data.user.phone if user_data.user else None,
                email_confirmed_at=user_data.user.email_confirmed_at if user_data.user else None,
                phone_confirmed_at=user_data.user.phone_confirmed_at if user_data.user else None,
                created_at=user_data.user.created_at if user_data.user else None,
                last_sign_in_at=user_data.user.last_sign_in_at if user_data.user else None,
                role=profile.role
            )
        except Exception as e:
            logger.warning("Failed to get user info", error=str(e))
            user = UserResponse(id=user_id, role=profile.role)
        
        return FullProfileResponse(
            user=user,
            profile=profile,
            preferences=preferences
        )
    
    # ========================================================================
    # ROLE MANAGEMENT
    # ========================================================================
    
    async def update_role(self, user_id: str, role: UserRole) -> Optional[ProfileResponse]:
        """
        Update user role (admin only).
        
        Args:
            user_id: Target user ID
            role: New role
        
        Returns:
            Updated profile
        """
        try:
            supabase.admin_table("profiles").update({
                "role": role.value,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", user_id).execute()
            
            logger.info("User role updated", user_id=user_id, new_role=role.value)
            return await self.get_profile(user_id)
            
        except Exception as e:
            logger.error("Failed to update role", user_id=user_id, error=str(e))
            raise Exception(f"Failed to update role: {e}")
    
    # ========================================================================
    # USER MANAGEMENT (ADMIN)
    # ========================================================================
    
    async def list_users(self, page: int = 1, per_page: int = 20) -> dict:
        """
        List all users (admin only).
        
        Args:
            page: Page number (1-indexed)
            per_page: Items per page
        
        Returns:
            Paginated user list
        """
        try:
            offset = (page - 1) * per_page
            
            result = supabase.admin_table("profiles").select(
                "*", count="exact"
            ).range(offset, offset + per_page - 1).order("created_at", desc=True).execute()
            
            return {
                "users": result.data,
                "total": result.count or len(result.data),
                "page": page,
                "per_page": per_page
            }
            
        except Exception as e:
            logger.error("Failed to list users", error=str(e))
            raise Exception(f"Failed to list users: {e}")
    
    async def delete_user(self, user_id: str) -> dict:
        """
        Delete a user (admin only).
        
        Args:
            user_id: User ID to delete
        
        Returns:
            Status message
        """
        try:
            # Delete from Supabase auth (will cascade due to FK)
            supabase.auth_admin.delete_user(user_id)
            
            logger.info("User deleted", user_id=user_id)
            return {"message": "User deleted successfully"}
            
        except Exception as e:
            logger.error("Failed to delete user", user_id=user_id, error=str(e))
            raise Exception(f"Failed to delete user: {e}")


# Singleton instance
user_service = UserService()
