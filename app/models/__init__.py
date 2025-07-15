"""Models package for the Insurance Risk Analyzer application."""

from app.models.user import User, UserCreate, UserInDB, UserUpdate, UserModel
from app.models.prediction import (
    Prediction,
    PredictionCreate,
    PredictionUpdate,
    PredictionModel,
    Region,
    Sex,
)

__all__ = [
    "User",
    "UserCreate",
    "UserInDB",
    "UserUpdate",
    "UserModel",
    "Prediction",
    "PredictionCreate",
    "PredictionUpdate",
    "PredictionModel",
    "Region",
    "Sex",
]
