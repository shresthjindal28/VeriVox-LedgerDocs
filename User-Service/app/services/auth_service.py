"""
Authentication service using Supabase GoTrue.
Handles registration, login, OAuth, and session management.
"""

from typing import Optional, Tuple
from gotrue.errors import AuthApiError

from app.core.config import settings
from app.core.supabase import supabase
from app.models.schemas import (
    RegisterRequest, RegisterResponse,
    LoginRequest, TokenResponse, UserResponse,
    PhoneOTPRequest, PhoneVerifyRequest,
    AuthProvider, UserRole
)
from app.utils.helpers import get_logger, mask_email, mask_phone

logger = get_logger(__name__)


class AuthService:
    """
    Authentication service wrapping Supabase GoTrue.
    
    Features:
    - Email/password registration and login
    - Phone OTP authentication
    - OAuth (Google, LinkedIn)
    - Token refresh
    - Password reset
    - Session management
    """
    
    # ========================================================================
    # EMAIL/PASSWORD AUTH
    # ========================================================================
    
    async def register(self, request: RegisterRequest) -> RegisterResponse:
        """
        Register a new user with email and password.
        
        Args:
            request: Registration data
        
        Returns:
            RegisterResponse with user ID and confirmation status
        
        Raises:
            Exception: If registration fails
        """
        logger.info("Registering new user", email=mask_email(request.email))
        
        try:
            # Sign up with Supabase
            result = supabase.auth.sign_up({
                "email": request.email,
                "password": request.password,
                "options": {
                    "data": {
                        "display_name": request.display_name or request.email.split("@")[0],
                        "role": request.role.value
                    }
                }
            })
            
            if not result.user:
                raise Exception("Registration failed - no user returned")
            
            user_id = result.user.id
            
            # Create profile in profiles table
            await self._create_profile(
                user_id=user_id,
                display_name=request.display_name or request.email.split("@")[0],
                role=request.role
            )
            
            logger.info("User registered successfully", user_id=user_id)
            
            return RegisterResponse(
                user_id=user_id,
                email=request.email,
                message="Registration successful. Please check your email to verify your account.",
                email_confirmation_required=True
            )
            
        except AuthApiError as e:
            logger.error("Registration failed", error=str(e))
            raise Exception(f"Registration failed: {e.message}")
        except Exception as e:
            logger.error("Registration failed", error=str(e))
            raise
    
    async def login(self, request: LoginRequest) -> TokenResponse:
        """
        Login with email and password.
        
        Args:
            request: Login credentials
        
        Returns:
            TokenResponse with access and refresh tokens
        """
        logger.info("User login attempt", email=mask_email(request.email))
        
        try:
            result = supabase.auth.sign_in_with_password({
                "email": request.email,
                "password": request.password
            })
            
            if not result.user or not result.session:
                raise Exception("Login failed - invalid credentials")
            
            logger.info("User logged in successfully", user_id=result.user.id)
            
            # Get user role from profile
            role = await self._get_user_role(result.user.id)
            
            return TokenResponse(
                access_token=result.session.access_token,
                refresh_token=result.session.refresh_token,
                token_type="bearer",
                expires_in=result.session.expires_in or 3600,
                expires_at=result.session.expires_at,
                user=UserResponse(
                    id=result.user.id,
                    email=result.user.email,
                    phone=result.user.phone,
                    email_confirmed_at=result.user.email_confirmed_at,
                    phone_confirmed_at=result.user.phone_confirmed_at,
                    created_at=result.user.created_at,
                    last_sign_in_at=result.user.last_sign_in_at,
                    role=role
                )
            )
            
        except AuthApiError as e:
            logger.warning("Login failed", error=str(e))
            raise Exception(f"Login failed: {e.message}")
    
    # ========================================================================
    # PHONE OTP AUTH
    # ========================================================================
    
    async def send_phone_otp(self, request: PhoneOTPRequest) -> dict:
        """
        Send OTP code to phone number.
        
        Args:
            request: Phone number
        
        Returns:
            Status message
        """
        logger.info("Sending phone OTP", phone=mask_phone(request.phone))
        
        try:
            supabase.auth.sign_in_with_otp({
                "phone": request.phone
            })
            
            return {"message": "OTP sent successfully", "phone": request.phone}
            
        except AuthApiError as e:
            logger.error("Failed to send OTP", error=str(e))
            raise Exception(f"Failed to send OTP: {e.message}")
    
    async def verify_phone_otp(self, request: PhoneVerifyRequest) -> TokenResponse:
        """
        Verify phone OTP and login.
        
        Args:
            request: Phone and OTP token
        
        Returns:
            TokenResponse with tokens
        """
        logger.info("Verifying phone OTP", phone=mask_phone(request.phone))
        
        try:
            result = supabase.auth.verify_otp({
                "phone": request.phone,
                "token": request.token,
                "type": "sms"
            })
            
            if not result.user or not result.session:
                raise Exception("OTP verification failed")
            
            # Check if profile exists, create if not
            profile_exists = await self._profile_exists(result.user.id)
            if not profile_exists:
                await self._create_profile(
                    user_id=result.user.id,
                    display_name=f"User {request.phone[-4:]}",
                    role=UserRole.STUDENT
                )
            
            role = await self._get_user_role(result.user.id)
            
            return TokenResponse(
                access_token=result.session.access_token,
                refresh_token=result.session.refresh_token,
                token_type="bearer",
                expires_in=result.session.expires_in or 3600,
                expires_at=result.session.expires_at,
                user=UserResponse(
                    id=result.user.id,
                    email=result.user.email,
                    phone=result.user.phone,
                    phone_confirmed_at=result.user.phone_confirmed_at,
                    role=role
                )
            )
            
        except AuthApiError as e:
            logger.error("OTP verification failed", error=str(e))
            raise Exception(f"OTP verification failed: {e.message}")
    
    # ========================================================================
    # OAUTH
    # ========================================================================
    
    async def get_oauth_url(self, provider: AuthProvider) -> str:
        """
        Get OAuth redirect URL for a provider.
        
        Args:
            provider: OAuth provider (google, linkedin)
        
        Returns:
            Redirect URL
        """
        logger.info("Getting OAuth URL", provider=provider.value)
        
        try:
            redirect_url = settings.GOOGLE_REDIRECT_URL if provider == AuthProvider.GOOGLE else settings.LINKEDIN_REDIRECT_URL
            
            result = supabase.auth.sign_in_with_oauth({
                "provider": provider.value,
                "options": {
                    "redirect_to": redirect_url
                }
            })
            
            return result.url
            
        except AuthApiError as e:
            logger.error("Failed to get OAuth URL", error=str(e))
            raise Exception(f"OAuth setup failed: {e.message}")
    
    async def handle_oauth_callback(self, code: str) -> TokenResponse:
        """
        Handle OAuth callback and exchange code for tokens.
        
        Args:
            code: Authorization code from OAuth provider
        
        Returns:
            TokenResponse with tokens
        """
        logger.info("Handling OAuth callback")
        
        try:
            result = supabase.auth.exchange_code_for_session({"auth_code": code})
            
            if not result.user or not result.session:
                raise Exception("OAuth callback failed")
            
            # Create profile if doesn't exist
            profile_exists = await self._profile_exists(result.user.id)
            if not profile_exists:
                display_name = result.user.user_metadata.get("full_name") or \
                               result.user.user_metadata.get("name") or \
                               result.user.email.split("@")[0] if result.user.email else "User"
                await self._create_profile(
                    user_id=result.user.id,
                    display_name=display_name,
                    role=UserRole.STUDENT,
                    avatar_url=result.user.user_metadata.get("avatar_url")
                )
            
            role = await self._get_user_role(result.user.id)
            
            return TokenResponse(
                access_token=result.session.access_token,
                refresh_token=result.session.refresh_token,
                token_type="bearer",
                expires_in=result.session.expires_in or 3600,
                expires_at=result.session.expires_at,
                user=UserResponse(
                    id=result.user.id,
                    email=result.user.email,
                    role=role
                )
            )
            
        except AuthApiError as e:
            logger.error("OAuth callback failed", error=str(e))
            raise Exception(f"OAuth authentication failed: {e.message}")
    
    # ========================================================================
    # TOKEN MANAGEMENT
    # ========================================================================
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Current refresh token
        
        Returns:
            New TokenResponse
        """
        logger.info("Refreshing token")
        
        try:
            result = supabase.auth.refresh_session(refresh_token)
            
            if not result.user or not result.session:
                raise Exception("Token refresh failed")
            
            role = await self._get_user_role(result.user.id)
            
            return TokenResponse(
                access_token=result.session.access_token,
                refresh_token=result.session.refresh_token,
                token_type="bearer",
                expires_in=result.session.expires_in or 3600,
                expires_at=result.session.expires_at,
                user=UserResponse(
                    id=result.user.id,
                    email=result.user.email,
                    phone=result.user.phone,
                    role=role
                )
            )
            
        except AuthApiError as e:
            logger.error("Token refresh failed", error=str(e))
            raise Exception(f"Token refresh failed: {e.message}")
    
    async def logout(self) -> dict:
        """Sign out current user."""
        logger.info("User logout")
        
        try:
            supabase.auth.sign_out()
            return {"message": "Logged out successfully"}
        except AuthApiError as e:
            logger.warning("Logout error", error=str(e))
            return {"message": "Logged out"}
    
    # ========================================================================
    # PASSWORD RESET
    # ========================================================================
    
    async def request_password_reset(self, email: str) -> dict:
        """
        Send password reset email.
        
        Args:
            email: User email
        
        Returns:
            Status message
        """
        logger.info("Password reset requested", email=mask_email(email))
        
        try:
            supabase.auth.reset_password_email(
                email,
                options={"redirect_to": f"{settings.FRONTEND_URL}/reset-password"}
            )
            return {"message": "Password reset email sent"}
            
        except AuthApiError as e:
            logger.error("Password reset failed", error=str(e))
            # Don't reveal if email exists
            return {"message": "If the email exists, a reset link has been sent"}
    
    async def update_password(self, new_password: str) -> dict:
        """
        Update user password (requires authenticated session).
        
        Args:
            new_password: New password
        
        Returns:
            Status message
        """
        logger.info("Updating password")
        
        try:
            supabase.auth.update_user({"password": new_password})
            return {"message": "Password updated successfully"}
            
        except AuthApiError as e:
            logger.error("Password update failed", error=str(e))
            raise Exception(f"Password update failed: {e.message}")
    
    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================
    
    async def _create_profile(
        self,
        user_id: str,
        display_name: str,
        role: UserRole,
        avatar_url: Optional[str] = None
    ) -> None:
        """Create user profile in profiles table."""
        try:
            supabase.admin_table("profiles").insert({
                "id": user_id,
                "display_name": display_name,
                "role": role.value,
                "avatar_url": avatar_url
            }).execute()
            
            # Also create default preferences
            supabase.admin_table("study_preferences").insert({
                "user_id": user_id,
                "voice": "nova",
                "theme": "system",
                "language": "en",
                "notifications_enabled": True
            }).execute()
            
            logger.info("Profile created", user_id=user_id)
        except Exception as e:
            logger.error("Failed to create profile", error=str(e))
            # Don't fail registration if profile creation fails
    
    async def _profile_exists(self, user_id: str) -> bool:
        """Check if profile exists for user."""
        try:
            result = supabase.admin_table("profiles").select("id").eq("id", user_id).execute()
            return bool(result.data)
        except Exception:
            return False
    
    async def _get_user_role(self, user_id: str) -> UserRole:
        """Get user role from profile."""
        try:
            result = supabase.admin_table("profiles").select("role").eq("id", user_id).single().execute()
            if result.data:
                return UserRole(result.data.get("role", "student"))
        except Exception:
            pass
        return UserRole.STUDENT


# Singleton instance
auth_service = AuthService()
