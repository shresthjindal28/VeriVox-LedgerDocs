"""
Pydantic schemas for authentication and user management.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


# ============================================================================
# ENUMS
# ============================================================================

class UserRole(str, Enum):
    """User roles for access control."""
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class AuthProvider(str, Enum):
    """Authentication providers."""
    EMAIL = "email"
    PHONE = "phone"
    GOOGLE = "google"
    LINKEDIN = "linkedin"


class ThemePreference(str, Enum):
    """UI theme preferences."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class VoicePreference(str, Enum):
    """AI voice preferences."""
    NOVA = "nova"
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    SHIMMER = "shimmer"


# ============================================================================
# AUTH SCHEMAS - Registration
# ============================================================================

class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 chars)")
    display_name: Optional[str] = Field(None, max_length=100, description="Display name")
    role: UserRole = Field(default=UserRole.STUDENT, description="User role")
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class RegisterResponse(BaseModel):
    """Registration response."""
    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    message: str = Field(..., description="Status message")
    email_confirmation_required: bool = Field(default=True)


# ============================================================================
# AUTH SCHEMAS - Login
# ============================================================================

class LoginRequest(BaseModel):
    """Email/password login request."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class PhoneOTPRequest(BaseModel):
    """Phone OTP send request."""
    phone: str = Field(..., description="Phone number with country code (e.g., +1234567890)")
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number format."""
        # Basic validation - should start with + and contain only digits
        if not v.startswith("+"):
            raise ValueError("Phone number must start with country code (e.g., +1)")
        if not re.match(r"^\+\d{10,15}$", v):
            raise ValueError("Invalid phone number format")
        return v


class PhoneVerifyRequest(BaseModel):
    """Phone OTP verification request."""
    phone: str = Field(..., description="Phone number")
    token: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")


class TokenResponse(BaseModel):
    """Authentication token response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="bearer")
    expires_in: int = Field(..., description="Token expiry in seconds")
    expires_at: Optional[int] = Field(None, description="Token expiry timestamp")
    user: "UserResponse" = Field(..., description="User information")


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str = Field(..., description="Refresh token")


# ============================================================================
# AUTH SCHEMAS - Password Reset
# ============================================================================

class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr = Field(..., description="User email")


class PasswordUpdateRequest(BaseModel):
    """Password update request."""
    password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


# ============================================================================
# AUTH SCHEMAS - OAuth
# ============================================================================

class OAuthURLResponse(BaseModel):
    """OAuth redirect URL response."""
    url: str = Field(..., description="OAuth provider redirect URL")
    provider: AuthProvider = Field(..., description="OAuth provider")


class OAuthCallbackRequest(BaseModel):
    """OAuth callback parameters."""
    code: Optional[str] = Field(None, description="Authorization code")
    state: Optional[str] = Field(None, description="State parameter")
    error: Optional[str] = Field(None, description="Error from provider")
    error_description: Optional[str] = Field(None, description="Error description")


# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserResponse(BaseModel):
    """User information response."""
    id: str = Field(..., description="User ID")
    email: Optional[str] = Field(None, description="User email")
    phone: Optional[str] = Field(None, description="User phone")
    email_confirmed_at: Optional[datetime] = Field(None)
    phone_confirmed_at: Optional[datetime] = Field(None)
    created_at: Optional[datetime] = Field(None)
    updated_at: Optional[datetime] = Field(None)
    last_sign_in_at: Optional[datetime] = Field(None)
    role: Optional[UserRole] = Field(None)
    
    class Config:
        from_attributes = True


# ============================================================================
# PROFILE SCHEMAS
# ============================================================================

class ProfileBase(BaseModel):
    """Base profile fields."""
    display_name: Optional[str] = Field(None, max_length=100, description="Display name")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar URL")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")


class ProfileCreate(ProfileBase):
    """Profile creation schema (internal use)."""
    user_id: str = Field(..., description="User ID from auth.users")
    role: UserRole = Field(default=UserRole.STUDENT)


class ProfileUpdate(ProfileBase):
    """Profile update request."""
    pass


class ProfileResponse(ProfileBase):
    """Profile response."""
    id: str = Field(..., description="Profile ID (same as user ID)")
    role: UserRole = Field(..., description="User role")
    created_at: Optional[datetime] = Field(None, description="Profile creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Profile last update timestamp")
    
    class Config:
        from_attributes = True


# ============================================================================
# STUDY PREFERENCES SCHEMAS
# ============================================================================

class StudyPreferencesBase(BaseModel):
    """Base study preferences fields."""
    voice: VoicePreference = Field(default=VoicePreference.NOVA, description="AI voice preference")
    theme: ThemePreference = Field(default=ThemePreference.SYSTEM, description="UI theme")
    language: str = Field(default="en", max_length=10, description="Preferred language")
    notifications_enabled: bool = Field(default=True, description="Enable notifications")
    auto_play_audio: bool = Field(default=False, description="Auto-play AI responses")
    playback_speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Audio playback speed")


class StudyPreferencesUpdate(StudyPreferencesBase):
    """Study preferences update request."""
    voice: Optional[VoicePreference] = None
    theme: Optional[ThemePreference] = None
    language: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    auto_play_audio: Optional[bool] = None
    playback_speed: Optional[float] = None


class StudyPreferencesResponse(StudyPreferencesBase):
    """Study preferences response."""
    user_id: str = Field(..., description="User ID")
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# COMBINED SCHEMAS
# ============================================================================

class FullProfileResponse(BaseModel):
    """Full user profile including preferences."""
    user: UserResponse
    profile: ProfileResponse
    preferences: StudyPreferencesResponse


# ============================================================================
# COMMON SCHEMAS
# ============================================================================

class MessageResponse(BaseModel):
    """Generic message response."""
    message: str = Field(..., description="Response message")
    success: bool = Field(default=True)


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Current timestamp")
    supabase_status: Optional[str] = Field(None, description="Supabase connection status")


# Update forward references
TokenResponse.model_rebuild()
