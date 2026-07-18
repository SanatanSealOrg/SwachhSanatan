"""
Authentication API routes for CleanLoop.

Provides endpoints for user registration, login, and current user retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend_schemas import UserRegisterRequest, UserLoginRequest, TokenResponse
from backend_models import User
from backend.app.services import auth_service
from backend.app.dependencies import get_db, get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    Validates password strength (min 8 chars), checks for duplicate email/phone,
    hashes password, and stores user in database.
    
    Args:
        request: UserRegisterRequest with email, phone, password, user_type, ward_id
        db: Database session
        
    Returns:
        TokenResponse with access_token, token_type, and user_id
        
    Raises:
        HTTPException 400: If validation fails (duplicate email/phone, weak password)
        HTTPException 500: If database error occurs
        
    Example (cURL):
        POST /api/auth/register
        {
            "email": "citizen@example.com",
            "phone": "9876543210",
            "password": "SecurePass123",
            "user_type": "citizen",
            "ward_id": "123e4567-e89b-12d3-a456-426614174000"
        }
        
        Response 201:
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "token_type": "bearer",
            "user_id": "123e4567-e89b-12d3-a456-426614174001"
        }
    """
    try:
        # Validate password strength
        if len(request.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        
        # Create user (will raise ValueError if email/phone exists)
        user = auth_service.create_user(
            db=db,
            email=request.email,
            phone=request.phone,
            password=request.password,
            user_type=request.user_type,
            ward_id=str(request.ward_id) if request.ward_id else None
        )
        
        # Generate access token
        access_token = auth_service.create_access_token(str(user.id))
        
        logger.info(f"User registered: {request.email}")
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login a user with email and password.
    
    Authenticates user by email/password, generates JWT token on success.
    
    Args:
        request: UserLoginRequest with email and password
        db: Database session
        
    Returns:
        TokenResponse with access_token, token_type, and user_id
        
    Raises:
        HTTPException 401: If email not found or password incorrect
        HTTPException 500: If database error occurs
        
    Example (cURL):
        POST /api/auth/login
        {
            "email": "citizen@example.com",
            "password": "SecurePass123"
        }
        
        Response 200:
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "token_type": "bearer",
            "user_id": "123e4567-e89b-12d3-a456-426614174001"
        }
    """
    try:
        # Authenticate user
        user = auth_service.authenticate_user(db, request.email, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate access token
        access_token = auth_service.create_access_token(str(user.id))
        
        logger.info(f"User logged in: {request.email}")
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.get("/auth/me", response_model=dict)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user details.
    
    Requires valid JWT token in Authorization header (Bearer token).
    Returns user details without password hash.
    
    Args:
        current_user: User object extracted from JWT token by get_current_user dependency
        
    Returns:
        User details: id, email, phone, user_type, ward_id, is_active, created_at
        
    Raises:
        HTTPException 401: If token missing, invalid, or user not found
        
    Example (cURL):
        GET /api/auth/me
        Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
        
        Response 200:
        {
            "id": "123e4567-e89b-12d3-a456-426614174001",
            "email": "citizen@example.com",
            "phone": "9876543210",
            "user_type": "citizen",
            "ward_id": "123e4567-e89b-12d3-a456-426614174000",
            "is_active": true,
            "created_at": "2024-01-15T10:30:00"
        }
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "phone": current_user.phone,
        "user_type": current_user.user_type,
        "ward_id": str(current_user.ward_id) if current_user.ward_id else None,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }
