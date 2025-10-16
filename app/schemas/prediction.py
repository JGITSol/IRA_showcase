"""Pydantic models for prediction-related schemas."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, Field, validator

if TYPE_CHECKING:
    from app.schemas.user import UserBase


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Region(str, Enum):
    NORTHEAST = "northeast"
    NORTHWEST = "northwest"
    SOUTHEAST = "southeast"
    SOUTHWEST = "southwest"


class PredictionBase(BaseModel):
    """Base schema for prediction input."""
    
    age: int = Field(..., gt=0, le=120, description="Age of the policyholder")
    gender: Gender = Field(..., description="Gender of the policyholder")
    bmi: float = Field(..., gt=0, le=100, description="Body Mass Index")
    children: int = Field(..., ge=0, le=10, description="Number of children/dependents")
    smoker: bool = Field(..., description="Whether the policyholder is a smoker")
    region: Region = Field(..., description="Region where the policyholder lives")


class PredictionCreate(PredictionBase):
    """Schema for creating a new prediction."""
    pass


class PredictionUpdate(BaseModel):
    """Schema for updating a prediction."""
    
    age: Optional[int] = Field(None, gt=0, le=120)
    gender: Optional[Gender] = None
    bmi: Optional[float] = Field(None, gt=0, le=100)
    children: Optional[int] = Field(None, ge=0, le=10)
    smoker: Optional[bool] = None
    region: Optional[Region] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class PredictionInDBBase(PredictionBase):
    """Base schema for prediction in database."""
    
    id: int
    user_id: int
    predicted_charges: float
    risk_score: float
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    model_version: str
    is_active: bool = True
    prediction_date: datetime
    
    class Config:
        orm_mode = True


class Prediction(PredictionInDBBase):
    """Schema for prediction response."""
    pass


class PredictionWithUser(Prediction):
    """Schema for prediction with user information."""

    user: 'UserBase'


class PredictionList(BaseModel):
    """Schema for a list of predictions with pagination."""
    
    predictions: List[Prediction]
    total: int
    page: int
    limit: int


try:
    from app.schemas.user import UserBase

    PredictionWithUser.model_rebuild()
except ImportError:  # pragma: no cover - circular import guard
    pass
