"""Prediction model and related schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.db import models as db_models


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


PredictionModel = db_models.Prediction
