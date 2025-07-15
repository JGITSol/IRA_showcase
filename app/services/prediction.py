"""Prediction service with enhanced features."""

import asyncio
import pickle
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import structlog
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sqlalchemy.orm import Session

from app.core.cache import cache, cached, cache_key_for_prediction
from app.core.config import settings
from app.core.monitoring import track_prediction, PREDICTION_COUNT, MODEL_LOAD_TIME
from app.models.prediction import PredictionModel, PredictionCreate, PredictionUpdate
from app.schemas.prediction import Prediction

logger = structlog.get_logger(__name__)


class PredictionService:
    """Service for handling insurance risk predictions."""
    
    def __init__(self):
        self.model: Optional[RandomForestRegressor] = None
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.model_version = "v1.0"
        self.feature_columns = ['age', 'sex', 'bmi', 'children', 'smoker', 'region']
        
    async def load_model(self) -> bool:
        """Load the trained model and encoders."""
        try:
            model_path = Path(settings.MODEL_PATH)
            
            if not model_path.exists():
                logger.warning("Model file not found, training new model", path=str(model_path))
                await self._train_model()
                return True
            
            # Load model from cache first
            cached_model = cache.get(f"model:{self.model_version}")
            if cached_model:
                self.model = cached_model["model"]
                self.label_encoders = cached_model["encoders"]
                logger.info("Model loaded from cache")
                return True
            
            # Load from file
            with MODEL_LOAD_TIME.time():
                model_data = joblib.load(model_path)
                self.model = model_data["model"]
                self.label_encoders = model_data["encoders"]
                
                # Cache the model
                cache.set(
                    f"model:{self.model_version}",
                    {"model": self.model, "encoders": self.label_encoders},
                    ttl=settings.MODEL_CACHE_TTL
                )
            
            logger.info("Model loaded successfully", path=str(model_path))
            return True
            
        except Exception as e:
            logger.error("Failed to load model", error=str(e))
            return False
    
    async def _train_model(self) -> None:
        """Train a new model with synthetic data."""
        logger.info("Training new model with synthetic data")
        
        # Generate synthetic data
        np.random.seed(42)
        n_samples = 10000
        
        data = {
            'age': np.random.randint(18, 65, n_samples),
            'sex': np.random.choice(['male', 'female'], n_samples),
            'bmi': np.random.normal(25, 5, n_samples).clip(15, 50),
            'children': np.random.poisson(1, n_samples).clip(0, 5),
            'smoker': np.random.choice([True, False], n_samples, p=[0.2, 0.8]),
            'region': np.random.choice(['southwest', 'southeast', 'northwest', 'northeast'], n_samples)
        }
        
        df = pd.DataFrame(data)
        
        # Create synthetic charges based on realistic factors
        base_charge = 5000
        age_factor = (df['age'] - 18) * 50
        bmi_factor = np.where(df['bmi'] > 30, (df['bmi'] - 30) * 200, 0)
        smoker_factor = np.where(df['smoker'], 15000, 0)
        children_factor = df['children'] * 500
        
        df['charges'] = (
            base_charge + age_factor + bmi_factor + 
            smoker_factor + children_factor + 
            np.random.normal(0, 1000, n_samples)
        ).clip(1000, 50000)
        
        # Prepare features
        X = df[self.feature_columns].copy()
        y = df['charges']
        
        # Encode categorical variables
        self.label_encoders = {}
        for col in ['sex', 'region']:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col])
            self.label_encoders[col] = le
        
        # Convert boolean to int
        X['smoker'] = X['smoker'].astype(int)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model = RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(X_train, y_train)
        
        # Save model
        model_path = Path(settings.MODEL_PATH)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            "model": self.model,
            "encoders": self.label_encoders,
            "version": self.model_version,
            "feature_columns": self.feature_columns
        }
        
        joblib.dump(model_data, model_path)
        
        # Cache the model
        cache.set(
            f"model:{self.model_version}",
            {"model": self.model, "encoders": self.label_encoders},
            ttl=settings.MODEL_CACHE_TTL
        )
        
        logger.info("Model training completed and saved")
    
    @track_prediction()
    async def predict(
        self,
        age: int,
        sex: str,
        bmi: float,
        children: int,
        smoker: bool,
        region: str
    ) -> Dict[str, Any]:
        """Make a prediction for insurance charges."""
        
        # Check cache first
        cache_key = cache_key_for_prediction(age, sex, bmi, children, smoker, region)
        cached_result = cache.get(f"prediction:{cache_key}")
        if cached_result:
            logger.debug("Prediction cache hit", cache_key=cache_key)
            return cached_result
        
        # Ensure model is loaded
        if self.model is None:
            await self.load_model()
        
        if self.model is None:
            raise ValueError("Model not available")
        
        try:
            # Prepare input data
            input_data = pd.DataFrame({
                'age': [age],
                'sex': [sex],
                'bmi': [bmi],
                'children': [children],
                'smoker': [smoker],
                'region': [region]
            })
            
            # Encode categorical variables
            for col in ['sex', 'region']:
                if col in self.label_encoders:
                    input_data[col] = self.label_encoders[col].transform(input_data[col])
                else:
                    raise ValueError(f"Unknown category for {col}: {input_data[col].iloc[0]}")
            
            # Convert boolean to int
            input_data['smoker'] = input_data['smoker'].astype(int)
            
            # Make prediction
            prediction = self.model.predict(input_data)[0]
            
            # Calculate risk score (0-100)
            risk_score = min(100, max(0, (prediction - 1000) / 500))
            
            # Get feature importance for explanation
            feature_importance = dict(zip(
                self.feature_columns,
                self.model.feature_importances_
            ))
            
            result = {
                "predicted_charges": float(prediction),
                "risk_score": float(risk_score),
                "feature_importance": feature_importance,
                "model_version": self.model_version,
                "confidence": 0.85  # Placeholder confidence score
            }
            
            # Cache the result
            cache.set(
                f"prediction:{cache_key}",
                result,
                ttl=settings.PREDICTION_CACHE_TTL
            )
            
            logger.info(
                "Prediction completed",
                predicted_charges=prediction,
                risk_score=risk_score,
                cache_key=cache_key
            )
            
            return result
            
        except Exception as e:
            logger.error("Prediction failed", error=str(e))
            raise ValueError(f"Prediction failed: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        if self.model is None:
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "version": self.model_version,
            "feature_columns": self.feature_columns,
            "model_type": type(self.model).__name__,
            "n_features": len(self.feature_columns)
        }


# Database operations
def create_prediction(
    db: Session,
    prediction_in: PredictionCreate,
    user_id: int
) -> PredictionModel:
    """Create a new prediction in the database."""
    db_prediction = PredictionModel(
        user_id=user_id,
        age=prediction_in.age,
        sex=prediction_in.sex.value,
        bmi=prediction_in.bmi,
        children=prediction_in.children,
        smoker=prediction_in.smoker,
        region=prediction_in.region.value,
        charges=prediction_in.charges,
        risk_score=prediction_in.risk_score
    )
    
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    
    logger.info("Prediction created", prediction_id=db_prediction.id, user_id=user_id)
    return db_prediction


def get_predictions(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100
) -> Tuple[List[PredictionModel], int]:
    """Get predictions for a user with pagination."""
    query = db.query(PredictionModel).filter(PredictionModel.user_id == user_id)
    
    total = query.count()
    predictions = query.offset(skip).limit(limit).all()
    
    return predictions, total


def get_prediction(
    db: Session,
    prediction_id: int,
    user_id: int
) -> Optional[PredictionModel]:
    """Get a specific prediction by ID for a user."""
    return db.query(PredictionModel).filter(
        PredictionModel.id == prediction_id,
        PredictionModel.user_id == user_id
    ).first()


def update_prediction(
    db: Session,
    db_prediction: PredictionModel,
    prediction_in: PredictionUpdate
) -> PredictionModel:
    """Update an existing prediction."""
    update_data = prediction_in.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(db_prediction, field):
            if field in ['sex', 'region'] and hasattr(value, 'value'):
                setattr(db_prediction, field, value.value)
            else:
                setattr(db_prediction, field, value)
    
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    
    logger.info("Prediction updated", prediction_id=db_prediction.id)
    return db_prediction


def delete_prediction(
    db: Session,
    db_prediction: PredictionModel
) -> PredictionModel:
    """Delete a prediction."""
    db.delete(db_prediction)
    db.commit()
    
    logger.info("Prediction deleted", prediction_id=db_prediction.id)
    return db_prediction


# Global service instance
prediction_service = PredictionService()