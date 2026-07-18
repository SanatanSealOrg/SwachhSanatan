"""
Authentication service for CleanLoop API

Handles password hashing, JWT token generation/verification, and user authentication.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from backend_models import User, UserType
from backend_schemas import TokenResponse
from backend.app.config import config
import logging

logger = logging.getLogger(__name__)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
        
    Example:
        >>> hashed = hash_password("myPassword123")
        >>> len(hashed) > 20
        True
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
        
    Example:
        >>> hashed = hash_password("test123")
        >>> verify_password("test123", hashed)
        True
        >>> verify_password("wrong", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token for a user.
    
    Args:
        user_id: User ID to encode in token
        expires_delta: Optional token expiration time delta
        
    Returns:
        JWT token string
        
    Example:
        >>> token = create_access_token("123e4567-e89b-12d3-a456-426614174000")
        >>> isinstance(token, str)
        True
        >>> len(token) > 20
        True
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"sub": user_id, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """
    Verify a JWT token and extract the user ID.
    
    Args:
        token: JWT token string
        
    Returns:
        User ID if token is valid, None otherwise
        
    Example:
        >>> token = create_access_token("123e4567-e89b-12d3-a456-426614174000")
        >>> user_id = verify_token(token)
        >>> user_id == "123e4567-e89b-12d3-a456-426614174000"
        True
    """
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError as e:
        logger.warning(f"Token verification failed: {str(e)}")
        return None


def create_user(
    db: Session,
    email: str,
    phone: Optional[str],
    password: str,
    user_type: str,
    ward_id: Optional[str] = None
) -> User:
    """
    Create a new user in the database.
    
    Args:
        db: Database session
        email: User email (must be unique)
        phone: User phone number (optional, must be unique if provided)
        password: Plain text password (will be hashed)
        user_type: User type ('citizen', 'officer', 'admin')
        ward_id: Ward ID (optional)
        
    Returns:
        Created User object
        
    Raises:
        ValueError: If email/phone already exists or invalid user_type
        
    Example:
        >>> user = create_user(db, "test@example.com", "9876543210", "password123", "citizen")
        >>> user.email == "test@example.com"
        True
        >>> user.is_active
        True
    """
    try:
        # Check if email already exists
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            raise ValueError(f"Email {email} already registered")
        
        # Check if phone already exists (if provided)
        if phone:
            existing_phone = db.query(User).filter(User.phone == phone).first()
            if existing_phone:
                raise ValueError(f"Phone {phone} already registered")
        
        # Validate user_type
        valid_types = [ut.value for ut in UserType]
        if user_type not in valid_types:
            raise ValueError(f"Invalid user_type. Must be one of: {', '.join(valid_types)}")
        
        # Create new user
        user = User(
            email=email,
            phone=phone,
            password_hash=hash_password(password),
            user_type=user_type,
            ward_id=ward_id,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"User created: {email} ({user_type})")
        return user
        
    except ValueError as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {str(e)}")
        raise ValueError(f"Failed to create user: {str(e)}")


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.
    
    Args:
        db: Database session
        email: User email
        password: Plain text password
        
    Returns:
        User object if authentication successful, None otherwise
        
    Example:
        >>> user = authenticate_user(db, "test@example.com", "password123")
        >>> user is not None
        True
    """
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.warning(f"Login attempt with non-existent email: {email}")
            return None
        
        if not user.is_active:
            logger.warning(f"Login attempt with inactive user: {email}")
            return None
        
        if not verify_password(password, user.password_hash):
            logger.warning(f"Failed login attempt for: {email}")
            return None
        
        logger.info(f"User authenticated: {email}")
        return user
        
    except Exception as e:
        logger.error(f"Error authenticating user: {str(e)}")
        return None
