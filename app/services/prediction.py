"""Prediction service backed by the shared modeling utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import structlog
from sklearn.pipeline import Pipeline
from sqlalchemy.orm import Session

from app.core.cache import cache, cache_key_for_prediction
from app.core.config import settings
from app.core.monitoring import MODEL_LOAD_TIME, track_prediction
from app.models.prediction import PredictionModel, PredictionCreate, PredictionUpdate
from app.services.modeling import (
    DEFAULT_FEATURES,
    ModelArtifact,
    load_training_dataframe,
    prepare_inference_frame,
    train_model_from_dataframe,
)

logger = structlog.get_logger(__name__)


class PredictionService:
    """Service for handling insurance risk predictions."""

    def __init__(self) -> None:
        self.model: Optional[Pipeline] = None
        self.metadata: Dict[str, Any] = {}
        self.model_version = "v1.0"
        self.feature_columns: List[str] = list(DEFAULT_FEATURES)

    async def load_model(self) -> bool:
        """Load model artefact from cache or disk, training if absent."""
        try:
            cache_key = f"model:{self.model_version}"
            cached_payload = cache.get(cache_key)
            if cached_payload:
                self._apply_model_payload(cached_payload)
                logger.info("Model loaded from cache", version=self.model_version)
                return True

            model_path = Path(settings.MODEL_PATH)
            if not model_path.exists():
                logger.warning("Model file not found, triggering training", path=str(model_path))
                await self._train_model()
                return True

            with MODEL_LOAD_TIME.time():
                model_data = joblib.load(model_path)

            self._apply_model_payload(model_data)
            cache.set(
                cache_key,
                {
                    "model": self.model,
                    "metadata": self.metadata,
                    "feature_columns": self.feature_columns,
                },
                ttl=settings.MODEL_CACHE_TTL,
            )
            logger.info("Model loaded from disk", path=str(model_path))
            return True

        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Failed to load model", error=str(exc))
            return False

    def _apply_model_payload(self, payload: Dict[str, Any]) -> None:
        """Apply a model payload to the service state."""
        model = payload.get("model")
        if model is None:
            raise ValueError("Model payload does not contain a model instance")

        self.model = model
        self.metadata = payload.get("metadata", {})
        feature_columns = payload.get("feature_columns")
        if feature_columns:
            self.feature_columns = list(feature_columns)

    async def _train_model(self) -> None:
        """Train a new model using the shared modeling pipeline."""
        logger.info("Training new model artefact", version=self.model_version)

        training_frame = load_training_dataframe()
        artifact: ModelArtifact = train_model_from_dataframe(training_frame)

        self.model = artifact.model
        self.metadata = artifact.metadata

        model_path = Path(settings.MODEL_PATH)
        model_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "model": self.model,
            "metadata": self.metadata,
            "version": self.model_version,
            "feature_columns": self.feature_columns,
        }
        joblib.dump(payload, model_path)

        cache.set(
            f"model:{self.model_version}",
            {
                "model": self.model,
                "metadata": self.metadata,
                "feature_columns": self.feature_columns,
            },
            ttl=settings.MODEL_CACHE_TTL,
        )

        logger.info("Model training completed", path=str(model_path))

    @track_prediction()
    async def predict(
        self,
        age: int,
        sex: str,
        bmi: float,
        children: int,
        smoker: bool,
        region: str,
    ) -> Dict[str, Any]:
        """Make a prediction for insurance charges."""

        cache_key = cache_key_for_prediction(age, sex, bmi, children, smoker, region)
        cached_result = cache.get(f"prediction:{cache_key}")
        if cached_result:
            logger.debug("Prediction cache hit", cache_key=cache_key)
            return cached_result

        if self.model is None:
            await self.load_model()

        if self.model is None:
            raise ValueError("Model not available")

        try:
            input_frame = prepare_inference_frame(
                pd.DataFrame(
                    {
                        "age": [age],
                        "sex": [sex],
                        "bmi": [bmi],
                        "children": [children],
                        "smoker": [smoker],
                        "region": [region],
                    }
                )
            )

            self._validate_categories(input_frame.iloc[0])

            prediction = float(self.model.predict(input_frame)[0])
            risk_score = self._compute_risk_score(prediction)
            confidence, confidence_interval = self._estimate_confidence(input_frame, prediction)

            result = {
                "predicted_charges": prediction,
                "risk_score": risk_score,
                "feature_importance": self.metadata.get("feature_importance", {}),
                "model_version": self.model_version,
                "confidence": confidence,
                "confidence_interval": confidence_interval,
            }

            cache.set(
                f"prediction:{cache_key}",
                result,
                ttl=settings.PREDICTION_CACHE_TTL,
            )

            logger.info(
                "Prediction completed",
                predicted_charges=prediction,
                risk_score=risk_score,
                cache_key=cache_key,
            )
            return result

        except Exception as exc:
            logger.error("Prediction failed", error=str(exc))
            raise ValueError(f"Prediction failed: {exc}")

    def _validate_categories(self, row: pd.Series) -> None:
        """Ensure categorical inputs are part of the trained domain."""
        categories = self.metadata.get("categorical_levels", {})
        for field in ("sex", "region"):
            allowed = categories.get(field)
            if allowed and row[field] not in allowed:
                raise ValueError(f"Unknown category for {field}: {row[field]}")
        if categories.get("smoker") is not None and bool(row["smoker"]) not in categories["smoker"]:
            raise ValueError(f"Unknown category for smoker: {row['smoker']}")

    def _compute_risk_score(self, prediction: float) -> float:
        """Map the raw prediction to a 0-100 risk score using quantiles."""
        quantiles = self.metadata.get("target_quantiles")
        if quantiles and len(quantiles) >= 2:
            risk_grid = np.linspace(0, 100, num=len(quantiles))
            score = float(np.clip(np.interp(prediction, quantiles, risk_grid), 0, 100))
            return score
        return float(np.clip((prediction - 1000) / 500, 0, 100))

    def _estimate_confidence(
        self,
        input_frame: pd.DataFrame,
        prediction: float,
    ) -> Tuple[float, Dict[str, float]]:
        """Estimate confidence level and interval using ensemble dispersion."""
        summary = self.metadata.get("target_summary", {})
        target_std = float(summary.get("std", 1.0))

        prediction_std = None
        model = self.model
        if model is not None and hasattr(model, "named_steps"):
            regressor = model.named_steps.get("regressor")
            preprocessor = model.named_steps.get("preprocessor")
        else:  # pragma: no cover - fallback path
            regressor = None
            preprocessor = None

        if regressor is not None and hasattr(regressor, "estimators_") and preprocessor is not None:
            transformed = preprocessor.transform(input_frame)
            tree_predictions = np.array([est.predict(transformed)[0] for est in regressor.estimators_])
            prediction_std = float(tree_predictions.std())

        if prediction_std is None:
            prediction_std = float(target_std * 0.15)

        interval_half = 1.96 * prediction_std
        confidence_interval = {
            "lower": float(max(0.0, prediction - interval_half)),
            "upper": float(max(prediction + interval_half, 0.0)),
        }
        confidence = float(np.clip(1 - (prediction_std / (target_std + 1e-6)), 0.2, 0.99))

        return confidence, confidence_interval

    def get_model_info(self) -> Dict[str, Any]:
        """Return metadata about the loaded model."""
        if self.model is None:
            return {"status": "not_loaded"}

        model_type = type(self.model.named_steps.get("regressor", self.model)).__name__ if hasattr(self.model, "named_steps") else type(self.model).__name__

        info: Dict[str, Any] = {
            "status": "loaded",
            "version": self.model_version,
            "feature_columns": self.feature_columns,
            "model_type": model_type,
            "n_features": len(self.feature_columns),
        }

        if self.metadata.get("trained_at"):
            info["trained_at"] = self.metadata["trained_at"]
        if self.metadata.get("metrics"):
            info["metrics"] = self.metadata["metrics"]
        if self.metadata.get("categorical_levels"):
            info["categorical_levels"] = self.metadata["categorical_levels"]

        return info


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