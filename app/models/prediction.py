"""Prediction model and related schemas."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Region(str, Enum):
    """Enum for region values."""
    SOUTHWEST = "southwest"
    SOUTHEAST = "southeast"
    NORTHWEST = "northwest"
    NORTHEAST = "northeast"


class Sex(str, Enum):
    """Enum for sex values."""
    MALE = "male"
    FEMALE = "female"


class PredictionBase(BaseModel):
    """Base prediction schema with common fields."""
    
    age: int = Field(..., ge=18, le=100, description="Age of the policyholder (18-100)")
    sex: Sex = Field(..., description="Gender of the policyholder")
    bmi: float = Field(..., gt=0, le=60, description="Body mass index (0-60)")
    children: int = Field(..., ge=0, le=10, description="Number of children/dependents (0-10)")
    smoker: bool = Field(..., description="Whether the policyholder is a smoker")
    region: Region = Field(..., description="Region where the policyholder lives")
    charges: Optional[float] = Field(None, gt=0, description="Insurance charges (auto-calculated if not provided)")
    risk_score: Optional[float] = Field(None, ge=0, le=100, description="Risk score (0-100)")


class PredictionCreate(PredictionBase):
    """Schema for creating a new prediction."""
    pass


class PredictionUpdate(BaseModel):
    """Schema for updating an existing prediction."""
    
    age: Optional[int] = Field(None, ge=18, le=100, description="Age of the policyholder (18-100)")
    sex: Optional[Sex] = Field(None, description="Gender of the policyholder")
    bmi: Optional[float] = Field(None, gt=0, le=60, description="Body mass index (0-60)")
    children: Optional[int] = Field(None, ge=0, le=10, description="Number of children/dependents (0-10)")
    smoker: Optional[bool] = Field(None, description="Whether the policyholder is a smoker")
    region: Optional[Region] = Field(None, description="Region where the policyholder lives")
    charges: Optional[float] = Field(None, gt=0, description="Insurance charges")
    risk_score: Optional[float] = Field(None, ge=0, le=100, description="Risk score (0-100)")


class PredictionInDBBase(PredictionBase):
    """Base schema for prediction stored in database."""
    
    id: int = Field(..., description="Unique identifier for the prediction")
    user_id: int = Field(..., description="ID of the user who created the prediction")
    created_at: datetime = Field(..., description="When the prediction was created")
    updated_at: datetime = Field(..., description="When the prediction was last updated")
    
    class Config:
        from_attributes = True


class Prediction(PredictionInDBBase):
    """Prediction schema for API responses."""
    pass


class PredictionModel(Base):
    """SQLAlchemy model for predictions table."""
    
    __tablename__ = "predictions"
    
    # User relationship
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID of the user who created the prediction"
    )
    
    # Prediction fields
    age: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Age of the policyholder (18-100)"
    )
    sex: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Gender of the policyholder"
    )
    bmi: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Body mass index (0-60)"
    )
    children: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Number of children/dependents (0-10)"
    )
    smoker: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="Whether the policyholder is a smoker"
    )
    region: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Region where the policyholder lives"
    )
    charges: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Insurance charges"
    )
    risk_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Risk score (0-100)"
    )
    
    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="predictions")
    
    def to_schema(self) -> Prediction:
        """Convert to Pydantic model for API responses."""
        return Prediction.model_validate({
            "id": self.id,
            "user_id": self.user_id,
            "age": self.age,
            "sex": self.sex,
            "bmi": self.bmi,
            "children": self.children,
            "smoker": self.smoker,
            "region": self.region,
            "charges": self.charges,
            "risk_score": self.risk_score,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        })
