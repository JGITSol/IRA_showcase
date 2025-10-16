"""Authentication API endpoints."""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.api.deps import get_db
from app.db import models as db_models
from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_password_reset_token,
    get_password_hash,
    verify_password_reset_token,
)
from app.schemas.msg import Msg
from app.schemas.token import Token
from app.schemas.user import User
from app.utils.email import send_reset_password_email
from app.services import auth as auth_service

router = APIRouter()


@router.post("/login/access-token", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """OAuth2 compatible token login, get an access token for future requests.
    
    Args:
        db: Database session
        form_data: OAuth2 form data with username (email) and password
        
    Returns:
        dict: Access token and token type
    """
    user = auth_service.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/login/test-token", response_model=User)
def test_token(current_user: db_models.User = Depends(deps.get_current_user)) -> Any:
    """Test access token.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current user information
    """
    return current_user


@router.post("/password-recovery/{email}", response_model=Msg)
def recover_password(email: str, db: Session = Depends(get_db)) -> Any:
    """Password recovery.
    
    Args:
        email: Email address for password recovery
        db: Database session
        
    Returns:
        dict: Message indicating success
    """
    user = (
        db.query(db_models.User)
        .filter(db_models.User.email == email)
        .first()
    )
    
    if not user:
        # Don't reveal that the user doesn't exist
        return {"msg": "If this email is registered, you will receive a password reset link."}
    
    # Generate password reset token
    password_reset_token = generate_password_reset_token(email=email)
    
    # Send email with password reset link
    send_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    
    return {"msg": "Password recovery email sent"}


@router.post("/reset-password/", response_model=Token)
def reset_password(
    token: str = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(get_db),
) -> Any:
    """Reset password.
    
    Args:
        token: Password reset token
        new_password: New password
        db: Database session
        
    Returns:
        dict: Access token and token type
    """
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid token"
        )
    
    user = (
        db.query(db_models.User)
        .filter(db_models.User.email == email)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this email does not exist in the system.",
        )
    
    # Update password
    hashed_password = get_password_hash(new_password)
    user.hashed_password = hashed_password
    db.add(user)
    db.commit()
    
    # Return new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
