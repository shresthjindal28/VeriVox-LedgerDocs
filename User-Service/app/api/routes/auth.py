"""
Authentication routes for email/password and phone login.
"""

from fastapi import APIRouter, HTTPException, status, Depends

from app.models.schemas import (
    RegisterRequest, RegisterResponse,
    LoginRequest, TokenResponse,
    PhoneOTPRequest, PhoneVerifyRequest,
    RefreshTokenRequest, MessageResponse,
    PasswordResetRequest, PasswordUpdateRequest,
    ErrorResponse
)
from app.services.auth_service import auth_service
from app.utils.dependencies import get_current_user, AuthenticatedUser
from app.utils.helpers import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# EMAIL/PASSWORD AUTHENTICATION
# ============================================================================

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}}
)
async def register(request: RegisterRequest):
    """
    Register a new user with email and password.
    
    - **email**: Valid email address
    - **password**: Minimum 8 characters with uppercase, lowercase, and digit
    - **display_name**: Optional display name
    - **role**: User role (default: student)
    
    An email verification link will be sent to the provided email address.
    """
    try:
        return await auth_service.register(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}}
)
async def login(request: LoginRequest):
    """
    Login with email and password.
    
    Returns access token and refresh token for authenticated requests.
    """
    try:
        return await auth_service.login(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post(
    "/logout",
    response_model=MessageResponse
)
async def logout(user: AuthenticatedUser = Depends(get_current_user)):
    """
    Logout current user and invalidate session.
    
    Requires authentication.
    """
    return await auth_service.logout()


# ============================================================================
# PHONE OTP AUTHENTICATION
# ============================================================================

@router.post(
    "/phone/send-otp",
    response_model=MessageResponse,
    responses={400: {"model": ErrorResponse}}
)
async def send_phone_otp(request: PhoneOTPRequest):
    """
    Send OTP code to phone number.
    
    - **phone**: Phone number with country code (e.g., +1234567890)
    
    The OTP will be sent via SMS.
    """
    try:
        result = await auth_service.send_phone_otp(request)
        return MessageResponse(message=result["message"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/phone/verify",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}}
)
async def verify_phone_otp(request: PhoneVerifyRequest):
    """
    Verify phone OTP and login.
    
    - **phone**: Phone number that received the OTP
    - **token**: 6-digit OTP code
    
    Returns access token and refresh token on success.
    """
    try:
        return await auth_service.verify_phone_otp(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


# ============================================================================
# TOKEN MANAGEMENT
# ============================================================================

@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}}
)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    
    Use this endpoint when the access token expires to get a new one
    without requiring the user to login again.
    """
    try:
        return await auth_service.refresh_token(request.refresh_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


# ============================================================================
# PASSWORD RESET
# ============================================================================

@router.post(
    "/reset-password",
    response_model=MessageResponse
)
async def request_password_reset(request: PasswordResetRequest):
    """
    Request password reset email.
    
    - **email**: User's email address
    
    If the email exists, a password reset link will be sent.
    For security, always returns success even if email doesn't exist.
    """
    result = await auth_service.request_password_reset(request.email)
    return MessageResponse(message=result["message"])


@router.post(
    "/update-password",
    response_model=MessageResponse,
    responses={400: {"model": ErrorResponse}}
)
async def update_password(
    request: PasswordUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Update user password.
    
    Requires authentication. User must be logged in or have clicked
    the password reset link.
    """
    try:
        result = await auth_service.update_password(request.password)
        return MessageResponse(message=result["message"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# USER INFO
# ============================================================================

@router.get(
    "/me",
    response_model=dict
)
async def get_current_user_info(user: AuthenticatedUser = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Returns basic user info from the JWT token.
    """
    return {
        "id": user.id,
        "email": user.email,
        "phone": user.phone,
        "role": user.role.value,
        "email_confirmed": user.email_confirmed,
        "phone_confirmed": user.phone_confirmed
    }
