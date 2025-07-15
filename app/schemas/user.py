"""Pydantic models for user-related schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, validator

from app.schemas.prediction import Prediction


class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    email: EmailStr = Field(..., description="User's email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    is_active: bool = Field(True, description="Whether the user is active")
    is_superuser: bool = Field(False, description="Whether the user is a superuser")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    
    password: str = Field(..., min_length=8, description="User's password (min 8 characters)")
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserInDBBase(UserBase):
    """Base schema for user in database."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class User(UserInDBBase):
    """Schema for user response (without sensitive data)."""
    pass


class UserInDB(UserInDBBase):
    """Schema for user in database (with hashed password)."""
    
    hashed_password: str


class UserWithPredictions(User):
    """Schema for user with their predictions."""
    
    predictions: List[Prediction] = []


class UserList(BaseModel):
    """Schema for a list of users with pagination."""
    
    users: List[User]
    total: int
    page: int
    limit: int


# Update ForwardRefs
UserWithPredictions.update_forward_refs()
