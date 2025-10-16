"""Convenience wrapper for training the insurance risk model locally."""

from pathlib import Path
from typing import Dict

import joblib

from app.services.modeling import DEFAULT_FEATURES, load_training_dataframe, train_model_from_dataframe

MODEL_ARTIFACT_PATH = Path("models/insurance_model.pkl")


def _print_metrics(metrics: Dict[str, Dict[str, float]]) -> None:
    """Pretty-print core model metrics for quick inspection."""
    if not metrics:
        return
    train = metrics.get("train", {})
    test = metrics.get("test", {})
    print("Training Metrics:")
    print(f"  R²:  {train.get('r2', float('nan')):.4f}")
    print(f"  MAE: {train.get('mae', float('nan')):.2f}")
    print(f"  RMSE:{train.get('rmse', float('nan')):.2f}")
    print("Validation Metrics:")
    print(f"  R²:  {test.get('r2', float('nan')):.4f}")
    print(f"  MAE: {test.get('mae', float('nan')):.2f}")
    print(f"  RMSE:{test.get('rmse', float('nan')):.2f}")


def train_model():
    """Train the shared model pipeline and persist it for local use."""
    training_frame = load_training_dataframe()
    artifact = train_model_from_dataframe(training_frame)

    MODEL_ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": artifact.model,
            "metadata": artifact.metadata,
            "feature_columns": DEFAULT_FEATURES,
            "version": artifact.metadata.get("trained_at"),
        },
        MODEL_ARTIFACT_PATH,
    )

    print(f"Model saved to {MODEL_ARTIFACT_PATH}")
    _print_metrics(artifact.metadata.get("metrics", {}))

    return artifact.model


if __name__ == "__main__":
    train_model()