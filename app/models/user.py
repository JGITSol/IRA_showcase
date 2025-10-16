"""User model and related schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.db import models as db_models


class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    email: EmailStr = Field(..., description="User's email address (must be unique)")
    full_name: Optional[str] = Field(None, description="User's full name")
    is_active: bool = Field(True, description="Whether the user is active")
    is_superuser: bool = Field(False, description="Whether the user has superuser privileges")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    
    password: str = Field(..., min_length=8, description="User's password (min 8 characters)")
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""
    
    email: Optional[EmailStr] = Field(None, description="User's email address (must be unique)")
    full_name: Optional[str] = Field(None, description="User's full name")
    password: Optional[str] = Field(None, min_length=8, description="User's new password (min 8 characters)")
    is_active: Optional[bool] = Field(None, description="Whether the user is active")
    is_superuser: Optional[bool] = Field(None, description="Whether the user has superuser privileges")


class UserInDBBase(UserBase):
    """Base schema for user stored in database."""
    
    id: int = Field(..., description="Unique identifier for the user")
    created_at: datetime = Field(..., description="When the user was created")
    updated_at: datetime = Field(..., description="When the user was last updated")
    
    class Config:
        from_attributes = True


class User(UserInDBBase):
    """User schema for API responses."""
    pass


class UserInDB(UserInDBBase):
    """User schema with hashed password for database storage."""
    
    hashed_password: str = Field(..., description="Hashed password")


UserModel = db_models.User
