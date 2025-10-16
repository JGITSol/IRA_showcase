"""Dependencies for FastAPI endpoints."""

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db import models as db_models
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.schemas.token import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token"
)


def get_db() -> Generator:
    """Get database session.
    
    Yields:
        Session: Database session
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> db_models.User:
    """Get current user from token.
    
    Args:
        db: Database session
        token: OAuth2 token
        
    Returns:
        models.User: Current authenticated user
        
    Raises:
        HTTPException: If credentials are invalid or user is not found
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    user = db.query(db_models.User).filter(db_models.User.id == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_current_active_user(
    current_user: db_models.User = Depends(get_current_user),
) -> db_models.User:
    """Get current active user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        models.User: Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_active_superuser(
    current_user: db_models.User = Depends(get_current_user),
) -> db_models.User:
    """Get current active superuser.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        models.User: Current active superuser
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user
