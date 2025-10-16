"""User API endpoints."""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_superuser, get_current_user, get_db
from app.db import models as db_models
from app.core.security import get_password_hash
from app.schemas.user import User, UserCreate, UserUpdate

router = APIRouter()


@router.get("/", response_model=List[User])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: db_models.User = Depends(get_current_active_superuser),
) -> Any:
    """Retrieve users (admin only).
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user (must be superuser)
        
    Returns:
        List[User]: List of users
    """
    users = db.query(db_models.User).offset(skip).limit(limit).all()
    return users


@router.post("/", response_model=User)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: db_models.User = Depends(get_current_active_superuser),
) -> Any:
    """Create new user (admin only).
    
    Args:
        db: Database session
        user_in: User creation data
        current_user: Current authenticated user (must be superuser)
        
    Returns:
        User: Created user
        
    Raises:
        HTTPException: If user with email already exists
    """
    user = (
        db.query(db_models.User)
        .filter(db_models.User.email == user_in.email)
        .first()
    )
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    
    hashed_password = get_password_hash(user_in.password)
    db_user = db_models.User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        is_superuser=user_in.is_superuser,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/me", response_model=User)
def read_user_me(
    current_user: db_models.User = Depends(get_current_user),
) -> Any:
    """Get current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current user information
    """
    return current_user


@router.put("/me", response_model=User)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: db_models.User = Depends(get_current_user),
) -> Any:
    """Update own user.
    
    Args:
        db: Database session
        user_in: User update data
        current_user: Current authenticated user
        
    Returns:
        User: Updated user information
    """
    user_data = user_in.dict(exclude_unset=True)
    
    if "password" in user_data:
        hashed_password = get_password_hash(user_data["password"])
        current_user.hashed_password = hashed_password
    
    for field, value in user_data.items():
        if field != "password" and hasattr(current_user, field):
            setattr(current_user, field, value)
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/{user_id}", response_model=User)
def read_user_by_id(
    user_id: int,
    current_user: db_models.User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
) -> Any:
    """Get a specific user by id (admin only).
    
    Args:
        user_id: ID of the user to retrieve
        current_user: Current authenticated user (must be superuser)
        db: Database session
        
    Returns:
        User: Requested user information
        
    Raises:
        HTTPException: If user is not found
    """
    user = db.query(db_models.User).filter(db_models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user does not exist in the system",
        )
    return user


@router.put("/{user_id}", response_model=User)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: db_models.User = Depends(get_current_active_superuser),
) -> Any:
    """Update a user (admin only).
    
    Args:
        db: Database session
        user_id: ID of the user to update
        user_in: User update data
        current_user: Current authenticated user (must be superuser)
        
    Returns:
        User: Updated user information
        
    Raises:
        HTTPException: If user is not found
    """
    user = db.query(db_models.User).filter(db_models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user does not exist in the system",
        )
    
    user_data = user_in.dict(exclude_unset=True)
    
    if "password" in user_data:
        hashed_password = get_password_hash(user_data["password"])
        user.hashed_password = hashed_password
    
    for field, value in user_data.items():
        if field != "password" and hasattr(user, field):
            setattr(user, field, value)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", response_model=User)
def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: db_models.User = Depends(get_current_active_superuser),
) -> Any:
    """Delete a user (admin only).
    
    Args:
        db: Database session
        user_id: ID of the user to delete
        current_user: Current authenticated user (must be superuser)
        
    Returns:
        User: Deleted user information
        
    Raises:
        HTTPException: If user is not found
    """
    user = db.query(db_models.User).filter(db_models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user does not exist in the system",
        )
    
    db.delete(user)
    db.commit()
    return user
