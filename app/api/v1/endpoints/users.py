# app/api/v1/endpoints/auth.py

"""
Authentication and user management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

# Import CRUD functions directly (no 'crud.' namespace)
from app.crud.user import (
    get_user_by_email,
    get_user_by_id,
    create_user,
    create_admin_with_otp,
    authenticate_user,
    set_verification_token,
    verify_email_token,
    verify_otp,
    generate_new_otp,
    create_password_reset_token,
    reset_password_with_token,
    update_user_profile,
    create_refresh_token_db,
    get_refresh_token,
    revoke_refresh_token,
    revoke_all_user_tokens,
    search_users
)

# Import schemas directly (no 'schemas.' namespace)
from app.schemas.user import (
    UserCreate,
    UserCreateByAdmin,
    UserLogin,
    OTPVerify,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserUpdate,
    TokenRefresh,
    Token,
    UserResponse,
    UserRole
)
from app.models.user import User
from app.db.session import get_db
from app.utils import email, auth

router = APIRouter()


# ==================== DEPENDENCIES ====================

async def get_current_user(
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from token"""
    payload = auth.verify_token(token, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    email_address = payload.get("sub")
    if not email_address:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user_obj = get_user_by_email(db, email_address)
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user_obj


async def get_verified_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure user is verified"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return current_user


async def get_admin_user(current_user: User = Depends(get_verified_user)) -> User:
    """Ensure user is admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_admin_or_teacher(current_user: User = Depends(get_verified_user)) -> User:
    """Ensure user is admin or teacher"""
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or teacher access required"
        )
    return current_user


# ==================== AUTHENTICATION ENDPOINTS ====================

@router.post(
    "/registration",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Register a student or admin. Teachers must be created by admins."
)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Register a new user:
    - **ADMIN**: Registers with email and receives OTP for verification
    - **STUDENT**: Registers with email/password and receives verification email
    - **TEACHER**: Cannot self-register (must be created by admin)
    """
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    if user_data.role == UserRole.ADMIN:
        if not user_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required for admin registration"
            )
        
        db_user, otp = create_admin_with_otp(
            db,
            user_data.email,
            user_data.first_name,
            user_data.last_name,
            user_data.password,
        )
        
        background_tasks.add_task(
            email.send_otp_email,
            user_data.email,
            otp
        )
        
        return db_user

    elif user_data.role == UserRole.STUDENT:
        if not user_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required for student registration"
            )
    
        if not user_data.user_class:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student class is required"
            )
        
        # Create and VERIFY immediately — no email needed
        db_user = create_user(
            db,
            email=user_data.email,
            role=user_data.role,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            password=user_data.password,
            user_class=user_data.user_class
        )
        
        # ✅ Mark as verified instantly
        db_user.is_verified = True
        db.commit()
        db.refresh(db_user)
        
        return db_user
        

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers cannot self-register. They must be created by an administrator."
        )


@router.post(
    "/login",
    response_model=Token,
    summary="User login",
    description="Authenticate user and receive access/refresh tokens"
)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.
    Returns access token and refresh token.
    """
    user_obj = authenticate_user(db, credentials.email, credentials.password)
    
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password, or account is locked",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user_obj.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in"
        )
    
    access_token = auth.create_access_token(data={"sub": user_obj.email, "role": user_obj.role.value})
    refresh_token = auth.create_refresh_token(data={"sub": user_obj.email})
    
    create_refresh_token_db(db, user_obj.id, refresh_token)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Logout and revoke all refresh tokens"
)
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user and revoke all active refresh tokens.
    """
    revoke_all_user_tokens(db, current_user.id)
    return {"message": "Successfully logged out"}


# ==================== EMAIL VERIFICATION ====================

@router.post(
    "/verification",
    status_code=status.HTTP_200_OK,
    summary="Verify email or OTP",
    description="Verify user email with token or admin OTP"
)
async def verify_user(
    otp_data: Optional[OTPVerify] = None,
    token: Optional[str] = Query(None, description="Email verification token"),
    db: Session = Depends(get_db)
):
    """
    Verify user account:
    - **Email verification**: Provide token parameter
    - **Admin OTP verification**: Provide otp_data in request body
    """
    if token:
        if verify_email_token(db, token):
            return {"message": "Email verified successfully"}
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    if otp_data:
        if verify_otp(db, otp_data.email, otp_data.otp):
            return {"message": "Admin account verified successfully"}
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Please provide either token or OTP for verification"
    )


@router.post(
    "/verification/resend",
    status_code=status.HTTP_200_OK,
    summary="Resend verification OTP",
    description="Resend OTP for admin verification"
)
async def resend_verification_otp(
    email_data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Resend OTP to admin email for verification.
    Only works for unverified admin accounts.
    """
    user_obj = get_user_by_email(db, email_data.email)
    
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user_obj.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP verification is only for admin accounts"
        )
    
    if user_obj.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already verified"
        )
    
    otp = generate_new_otp(db, user_obj)
    
    background_tasks.add_task(
        email.send_otp_email,
        email_data.email,
        otp
    )
    
    return {"message": "OTP has been resent to your email"}


# ==================== PASSWORD MANAGEMENT ====================

@router.post(
    "/password-reset",
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Initiate password reset process"
)
async def request_password_reset(
    email_data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Request password reset link.
    Available for students and teachers (not admins).
    """
    user_obj = get_user_by_email(db, email_data.email)
    
    if not user_obj or user_obj.role == UserRole.ADMIN:
        return {"message": "If the email exists, a password reset link has been sent"}
    
    token = create_password_reset_token(db, user_obj)
    
    background_tasks.add_task(
        email.send_password_reset_email,
        email_data.email,
        token
    )
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post(
    "/password-reset/confirm",
    status_code=status.HTTP_200_OK,
    summary="Confirm password reset",
    description="Complete password reset with token"
)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Complete password reset using the token received via email.
    """
    if reset_password_with_token(db, reset_data.token, reset_data.new_password):
        return {"message": "Password has been reset successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired reset token"
    )


# ==================== TOKEN MANAGEMENT ====================

@router.post(
    "/token/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Get new access token using refresh token"
)
async def refresh_access_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using a valid refresh token.
    Returns new access and refresh tokens.
    """
    refresh_token_record = get_refresh_token(db, token_data.refresh_token)
    
    if not refresh_token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    payload = auth.verify_token(token_data.refresh_token, "refresh")
    
    if not payload:
        revoke_refresh_token(db, token_data.refresh_token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    email_address = payload.get("sub")
    if not email_address:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user_obj = get_user_by_email(db, email_address)
    if not user_obj or not user_obj.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or not verified"
        )
    
    new_access_token = auth.create_access_token(data={"sub": email_address, "role": user_obj.role.value})
    new_refresh_token = auth.create_refresh_token(data={"sub": email_address})
    
    create_refresh_token_db(db, refresh_token_record.user_id, new_refresh_token)
    revoke_refresh_token(db, token_data.refresh_token)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


# ==================== USER PROFILE ====================

@router.get(
    "/profile",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Retrieve authenticated user's profile"
)
async def get_current_user_profile(
    current_user: User = Depends(get_verified_user)
):
    return current_user


@router.put(
    "/profile",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update authenticated user's profile information"
)
async def update_current_user_profile(
    updates: UserUpdate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    updated_user = update_user_profile(
        db,
        current_user,
        first_name=updates.first_name,
        last_name=updates.last_name,
        user_class=updates.user_class,
        subject=updates.subject
    )
    return updated_user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieve specific user's profile"
)
async def get_user_by_id_endpoint(
    user_id: str,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    """
    Renamed to avoid conflict with imported `get_user_by_id` function.
    """
    target_user = get_user_by_id(db, user_id)
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if current_user.role == UserRole.STUDENT and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )
    
    return target_user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user by ID",
    description="Update specific user's profile (Admin/Teacher only)"
)
async def update_user_by_id(
    user_id: str,
    updates: UserUpdate,
    current_user: User = Depends(get_admin_or_teacher),
    db: Session = Depends(get_db)
):
    target_user = get_user_by_id(db, user_id)
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if current_user.role == UserRole.TEACHER:
        if target_user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teachers cannot modify admin accounts"
            )
        if target_user.role == UserRole.TEACHER and target_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teachers cannot modify other teacher accounts"
            )
    
    updated_user = update_user_profile(
        db,
        target_user,
        first_name=updates.first_name,
        last_name=updates.last_name,
        user_class=updates.user_class,
        subject=updates.subject
    )
    
    return updated_user


# ==================== ADMIN OPERATIONS ====================

@router.post(
    "/teachers",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create teacher account (Admin only)",
    description="Admin creates a new teacher account"
)
async def create_teacher(
    teacher_data: UserCreateByAdmin,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    existing_user = get_user_by_email(db, teacher_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    if not teacher_data.subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject is required for teacher accounts"
        )
    
    db_user = create_user(
        db,
        email=teacher_data.email,
        role=UserRole.TEACHER,
        first_name=teacher_data.first_name,
        last_name=teacher_data.last_name,
        subject=teacher_data.subject
    )
    
    token = create_password_reset_token(db, db_user)
    
    background_tasks.add_task(
        email.send_password_set_email,
        teacher_data.email,
        token
    )
    
    return db_user


# ==================== SEARCH ====================

@router.get(
    "/search",
    response_model=List[UserResponse],
    summary="Search users",
    description="Search users by name, class, or subject"
)
async def search_users_endpoint(
    name: Optional[str] = Query(None, description="Search by name"),
    user_class: Optional[str] = Query(None, description="Filter by class"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    """
    Renamed to avoid conflict with imported `search_users` function.
    """
    users = search_users(
        db,
        name=name,
        user_class=user_class,
        subject=subject
    )
    return users