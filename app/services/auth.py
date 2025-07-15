"""Authentication and user management service."""

from datetime import timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    verify_password_reset_token,
)
from app.db import models
from app.db.session import get_db
from app.schemas.token import Token, TokenPayload
from app.schemas.user import User, UserCreate, UserInDB

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """Get a user by ID.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Optional[User]: The user if found, None otherwise
    """
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Get a user by email.
    
    Args:
        db: Database session
        email: User's email address
        
    Returns:
        Optional[User]: The user if found, None otherwise
    """
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: UserCreate) -> models.User:
    """Create a new user.
    
    Args:
        db: Database session
        user: User creation data
        
    Returns:
        User: The created user
        
    Raises:
        HTTPException: If a user with the email already exists
    """
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """Authenticate a user.
    
    Args:
        db: Database session
        email: User's email address
        password: Plain text password
        
    Returns:
        Optional[User]: The authenticated user if successful, None otherwise
    """
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_token(user: models.User) -> Token:
    """Create an access token for a user.
    
    Args:
        user: The user to create a token for
        
    Returns:
        Token: The access token and token type
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires,
    )
    return Token(token=access_token, token_type="bearer")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> models.User:
    """Get the current authenticated user from a token.
    
    Args:
        db: Database session
        token: JWT token
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If the token is invalid or the user doesn't exist
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenPayload(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    user = get_user(db, user_id=token_data.user_id)
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Get the current active user.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        User: The active user
        
    Raises:
        HTTPException: If the user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_active_superuser(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Get the current active superuser.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        User: The active superuser
        
    Raises:
        HTTPException: If the user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user


def request_password_reset(email: str, db: Session) -> None:
    """Request a password reset.
    
    Args:
        email: User's email address
        db: Database session
        
    Note:
        This function would typically send a password reset email.
        The implementation is a placeholder and should be completed.
    """
    user = get_user_by_email(db, email=email)
    if not user:
        return  # Don't reveal that the user doesn't exist
    
    # Generate password reset token
    reset_token = create_password_reset_token(email=email)
    
    # TODO: Send email with reset token
    print(f"Password reset token for {email}: {reset_token}")


def reset_password(
    token: str, new_password: str, db: Session
) -> Optional[models.User]:
    """Reset a user's password.
    
    Args:
        token: Password reset token
        new_password: New password
        db: Database session
        
    Returns:
        Optional[User]: The updated user if successful, None otherwise
    """
    email = verify_password_reset_token(token)
    if not email:
        return None
    
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    
    # Update password
    hashed_password = get_password_hash(new_password)
    user.hashed_password = hashed_password
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user
