"""
Dependency injection for FastAPI routes.

Provides database sessions and current user extraction from JWT tokens.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend_database import SessionLocal
from backend_models import User, UserType
from backend.app.services.auth_service import verify_token
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


def get_db() -> Session:
    """
    FastAPI dependency to get database session.

    Yields:
        SQLAlchemy Session

    Example:
        @app.get("/")
        def get_data(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to extract and verify JWT token from Authorization header.

    Extracts Bearer token from Authorization header, verifies JWT, and returns user.

    Args:
        credentials: HTTP Bearer credentials from Authorization header
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If token is invalid or user not found (401 Unauthorized)

    Example:
        @app.get("/me")
        def get_me(current_user: User = Depends(get_current_user)):
            return current_user
    """
    try:
        token = credentials.credentials

        # Verify token and get user_id
        user_id = verify_token(token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Fetch user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_officer(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to verify current user is an officer.

    Checks that authenticated user has 'officer' user_type and is active.

    Args:
        current_user: User object from get_current_user dependency
        db: Database session

    Returns:
        User object (officer)

    Raises:
        HTTPException 403: If user is not an officer

    Example:
        @app.patch("/api/complaints/{id}")
        def update_complaint(
            current_officer: User = Depends(get_current_officer),
            db: Session = Depends(get_db)
        ):
            return {"message": "Officer only endpoint"}
    """
    if current_user.user_type != UserType.officer:
        logger.warning(f"Non-officer user {current_user.id} attempted officer action")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only officers can perform this action"
        )

    return current_user

