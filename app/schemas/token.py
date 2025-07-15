"""Pydantic models for authentication tokens."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TokenBase(BaseModel):
    """Base token schema."""
    
    token: str = Field(..., description="The access token")
    token_type: str = Field(..., description="The token type (e.g., 'bearer')")


class Token(TokenBase):
    """Schema for token response."""
    pass


class TokenPayload(BaseModel):
    """Schema for token payload (decoded token)."""
    
    sub: Optional[int] = Field(None, description="Subject (user ID)")
    exp: Optional[datetime] = Field(None, description="Expiration time")
    iat: Optional[datetime] = Field(None, description="Issued at time")
    is_superuser: bool = Field(False, description="Whether the user is a superuser")
