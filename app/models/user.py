"""User model and related schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.core.security import get_password_hash, verify_password


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


class UserModel(Base):
    """SQLAlchemy model for users table."""
    
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="User's email address (must be unique)"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Hashed password"
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="User's full name"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean(),
        default=True,
        nullable=False,
        comment="Whether the user is active"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean(),
        default=False,
        nullable=False,
        comment="Whether the user has superuser privileges"
    )
    
    # Relationships
    predictions: Mapped[List["PredictionModel"]] = relationship(
        "PredictionModel",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def set_password(self, password: str) -> None:
        """Set the user's password."""
        self.hashed_password = get_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the stored hash."""
        return verify_password(password, self.hashed_password)
    
    def to_schema(self) -> User:
        """Convert to Pydantic model for API responses."""
        return User.model_validate({
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        })
