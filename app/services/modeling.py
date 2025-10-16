"""Core utilities for training and evaluating the insurance risk model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


class RoundedPredictionPipeline(Pipeline):
    """Pipeline that rounds predictions to stabilise equality checks."""

    def predict(self, X, *args, **kwargs):
        predictions = super().predict(X, *args, **kwargs)
        try:
            return np.round(predictions, 6)
        except Exception:
            return predictions

# Feature definitions used across the service and training scripts
DEFAULT_FEATURES: List[str] = ["age", "sex", "bmi", "children", "smoker", "region"]
NUMERIC_FEATURES: List[str] = ["age", "bmi", "children"]
CATEGORICAL_FEATURES: List[str] = ["sex", "smoker", "region"]


@dataclass
class ModelArtifact:
    """Container for a trained model pipeline and its metadata."""

    model: Pipeline
    metadata: Dict[str, Any]


# ---------------------------------------------------------------------------
# Data preparation helpers
# ---------------------------------------------------------------------------

def _coerce_bool(value: Any) -> bool:
    """Convert various truthy representations to boolean values."""
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"y", "yes", "true", "1"}:
            return True
        if lowered in {"n", "no", "false", "0"}:
            return False
    return bool(value)


def _standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise column names and expected feature aliases."""
    renamed = {
        "gender": "sex",
        "male": "sex",  # legacy naming
        "female": "sex",
        "children_count": "children",
        "dependents": "children",
    }
    df = df.rename(columns={k: v for k, v in renamed.items() if k in df.columns})
    df.columns = [col.strip().lower() for col in df.columns]
    return df


def prepare_training_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate a dataframe used for training the model."""
    df = _standardise_columns(df).copy()

    expected_columns = set(DEFAULT_FEATURES + ["charges"])
    missing = expected_columns.difference(df.columns)
    if missing:
        raise ValueError(f"Training data missing required columns: {sorted(missing)}")

    # Basic type coercion
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df["bmi"] = pd.to_numeric(df["bmi"], errors="coerce")
    df["children"] = pd.to_numeric(df["children"], errors="coerce")
    df["charges"] = pd.to_numeric(df["charges"], errors="coerce")

    df["sex"] = df["sex"].astype(str).str.strip().str.lower()
    df["region"] = df["region"].astype(str).str.strip().str.lower().str.replace(" ", "_")
    df["smoker"] = df["smoker"].apply(lambda value: "yes" if _coerce_bool(value) else "no")

    # Drop invalid rows and enforce sensible bounds
    df = df.dropna(subset=DEFAULT_FEATURES + ["charges"])
    df = df[(df["age"].between(18, 100)) & (df["bmi"].between(12, 70))]
    df["children"] = df["children"].clip(lower=0).astype(int)
    df["age"] = df["age"].astype(int)
    df["smoker"] = df["smoker"].astype(str)

    df = df.reset_index(drop=True)
    return df


def prepare_inference_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Clean incoming prediction data and enforce required schema."""
    df = _standardise_columns(df).copy()

    missing = set(DEFAULT_FEATURES).difference(df.columns)
    if missing:
        raise ValueError(f"Prediction data missing required fields: {sorted(missing)}")

    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df["bmi"] = pd.to_numeric(df["bmi"], errors="coerce")
    df["children"] = pd.to_numeric(df["children"], errors="coerce")

    df["sex"] = df["sex"].astype(str).str.strip().str.lower()
    df["region"] = df["region"].astype(str).str.strip().str.lower().str.replace(" ", "_")
    df["smoker"] = df["smoker"].apply(lambda value: "yes" if _coerce_bool(value) else "no")

    if df[DEFAULT_FEATURES].isnull().any().any():
        raise ValueError("Prediction data contains invalid or missing values")

    df["children"] = df["children"].clip(lower=0).astype(int)
    df["age"] = df["age"].astype(int)
    df["smoker"] = df["smoker"].astype(str)

    return df[DEFAULT_FEATURES].reset_index(drop=True)


def _generate_synthetic_data(n_samples: int = 8000, random_state: int = 42) -> pd.DataFrame:
    """Generate a synthetic dataset that mimics insurance risk dynamics."""
    rng = np.random.default_rng(random_state)

    age = rng.integers(18, 66, size=n_samples)
    sex = rng.choice(["male", "female"], size=n_samples, p=[0.52, 0.48])
    bmi = rng.normal(28, 5, size=n_samples).clip(16, 52)
    children = rng.poisson(1.4, size=n_samples).clip(0, 5)
    smoker = rng.choice([False, True], size=n_samples, p=[0.78, 0.22])
    region = rng.choice(["southwest", "southeast", "northwest", "northeast"], size=n_samples)

    # Risk drivers
    base_charge = 2500 + age * 115 + bmi ** 1.5 * 35
    smoker_penalty = smoker.astype(float) * 18500
    children_load = children * 950
    region_adjustment = np.select(
        [region == "northeast", region == "northwest", region == "southeast"],
        [1400, 900, 700],
        default=500,
    )
    bmi_penalty = np.where(bmi > 30, (bmi - 30) * 420, 0)
    noise = rng.normal(0, 1800, size=n_samples)

    charges = (
        base_charge
        + smoker_penalty
        + children_load
        + region_adjustment
        + bmi_penalty
        + noise
    ).clip(2000, 65000)

    df = pd.DataFrame(
        {
            "age": age,
            "sex": sex,
            "bmi": bmi,
            "children": children,
            "smoker": np.where(smoker, "yes", "no"),
            "region": region,
            "charges": charges,
        }
    )
    return df


def load_training_dataframe(dataset_path: Optional[Path] = None) -> pd.DataFrame:
    """Load training data from disk, or generate synthetic data if unavailable."""
    path = dataset_path or Path("data/insurance_data.csv")
    if path.exists():
        df = pd.read_csv(path)
    else:
        df = _generate_synthetic_data()
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)

    return prepare_training_frame(df)


# ---------------------------------------------------------------------------
# Feature importance helpers
# ---------------------------------------------------------------------------

def _canonical_feature_name(name: str) -> str:
    """Reduce transformed feature names back to their base feature."""
    if "__" in name:
        name = name.split("__", 1)[1]
    base = name.split("_", 1)[0]
    return base if base in DEFAULT_FEATURES else name


def _aggregate_feature_importance(feature_names: Sequence[str], importances: Sequence[float]) -> Dict[str, float]:
    totals: Dict[str, float] = {feature: 0.0 for feature in DEFAULT_FEATURES}
    for name, importance in zip(feature_names, importances):
        base = _canonical_feature_name(name)
        totals[base] = totals.get(base, 0.0) + float(importance)

    total_importance = sum(totals.values())
    if total_importance > 0:
        totals = {feature: float(value / total_importance) for feature, value in totals.items()}
    return totals


# ---------------------------------------------------------------------------
# Training pipeline
# ---------------------------------------------------------------------------

def _root_mean_squared_error(y_true, y_pred) -> float:
    """Compute RMSE with backwards compatibility for older sklearn versions."""

    try:
        return float(mean_squared_error(y_true, y_pred, squared=False))
    except TypeError:
        return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def train_model_from_dataframe(
    df: pd.DataFrame,
    *,
    random_state: int = 42,
    test_size: float = 0.2,
) -> ModelArtifact:
    """Train the insurance risk model and collect metadata."""
    df = prepare_training_frame(df)

    X = df[DEFAULT_FEATURES]
    y = df["charges"].astype(float)

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="infrequent_if_exist",
                    min_frequency=0.02,
                    sparse_output=False,
                ),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )

    regressor = RandomForestRegressor(
        n_estimators=150,
        max_depth=None,
        min_samples_leaf=3,
        random_state=random_state,
        n_jobs=-1,
    )

    pipeline = RoundedPredictionPipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", regressor),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
    )

    pipeline.fit(X_train, y_train)

    y_train_pred = pipeline.predict(X_train)
    y_test_pred = pipeline.predict(X_test)

    metrics = {
        "train": {
            "r2": float(r2_score(y_train, y_train_pred)),
            "mae": float(mean_absolute_error(y_train, y_train_pred)),
            "rmse": _root_mean_squared_error(y_train, y_train_pred),
        },
        "test": {
            "r2": float(r2_score(y_test, y_test_pred)),
            "mae": float(mean_absolute_error(y_test, y_test_pred)),
            "rmse": _root_mean_squared_error(y_test, y_test_pred),
        },
    }

    n_splits = 5 if len(df) >= 500 else min(5, len(df))
    if n_splits >= 2:
        cv = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
        cv_mae = cross_val_score(
            pipeline,
            X,
            y,
            cv=cv,
            scoring="neg_mean_absolute_error",
            n_jobs=-1,
        )
        metrics["cv"] = {
            "mae_mean": float(-cv_mae.mean()),
            "mae_std": float(cv_mae.std()),
        }
    else:
        nan_value = float("nan")
        metrics["cv"] = {"mae_mean": nan_value, "mae_std": nan_value}

    preprocessor_fitted: ColumnTransformer = pipeline.named_steps["preprocessor"]
    feature_names = list(map(str, preprocessor_fitted.get_feature_names_out()))
    regressor_fitted: RandomForestRegressor = pipeline.named_steps["regressor"]

    raw_importance = np.asarray(regressor_fitted.feature_importances_, dtype=float).tolist()
    aggregated_importance = _aggregate_feature_importance(feature_names, raw_importance)

    perm_result = permutation_importance(
        pipeline,
        X_test,
        y_test,
        n_repeats=3,
        random_state=random_state,
        n_jobs=-1,
    )
    perm_mean = np.asarray(perm_result["importances_mean"], dtype=float).tolist()
    perm_aggregated = _aggregate_feature_importance(feature_names, perm_mean)

    quantiles = np.quantile(y, np.linspace(0, 1, 101))
    target_summary = {
        "mean": float(np.mean(y)),
        "median": float(np.median(y)),
        "std": float(np.std(y)),
        "min": float(np.min(y)),
        "max": float(np.max(y)),
    }

    metadata: Dict[str, Any] = {
        "trained_at": datetime.utcnow().isoformat(timespec="seconds"),
        "metrics": metrics,
        "feature_names": list(map(str, feature_names)),
        "feature_importance": aggregated_importance,
        "permutation_importance": perm_aggregated,
        "target_quantiles": [float(q) for q in quantiles],
        "target_summary": target_summary,
        "categorical_levels": {
            "sex": sorted(df["sex"].unique()),
            "region": sorted(df["region"].unique()),
            "smoker": sorted(df["smoker"].unique()),
        },
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "n_samples": int(len(df)),
    }

    return ModelArtifact(model=pipeline, metadata=metadata)


__all__ = [
    "DEFAULT_FEATURES",
    "NUMERIC_FEATURES",
    "CATEGORICAL_FEATURES",
    "ModelArtifact",
    "load_training_dataframe",
    "prepare_training_frame",
    "prepare_inference_frame",
    "train_model_from_dataframe",
]
