from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Union

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import utils
from app.services.modeling import DEFAULT_FEATURES, prepare_inference_frame
from theme_utils import get_color, get_color_palette, get_streamlit_theme

ARTIFACT_PATH = Path("models/insurance_model.pkl")


def _notify_streamlit(level: str, message: str) -> None:
    """Safely send notifications to Streamlit without breaking tests."""

    notifier = getattr(st, level, None)
    if notifier is None:
        return

    try:
        notifier(message)
    except Exception:
        # Tests run outside Streamlit context; ignore UI errors.
        pass


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"yes", "y", "true", "1"}:
            return True
        if lowered in {"no", "n", "false", "0"}:
            return False
    return bool(value)


def load_model(path: Optional[Union[str, Path]] = None) -> Optional[Dict[str, Any]]:
    """Load model artefact, falling back to legacy pickle pipelines if needed."""

    artifact_path = Path(path) if path is not None else ARTIFACT_PATH

    if not os.path.exists(str(artifact_path)):
        _notify_streamlit("error", "Model file not found. Please train the model first.")
        return None

    try:
        with open(artifact_path, "rb") as file:
            try:
                payload = pickle.load(file)
            except Exception:
                file.seek(0)
                payload = joblib.load(file)
    except Exception as exc:  # pragma: no cover - defensive handling
        _notify_streamlit("error", f"Error loading model: {exc}")
        return None

    if isinstance(payload, dict) and "model" in payload:
        model = payload.get("model")
        metadata = payload.get("metadata") or {}
        feature_columns = payload.get("feature_columns") or list(DEFAULT_FEATURES)
    else:
        model = payload
        metadata = {}
        feature_columns = list(DEFAULT_FEATURES)

    if model is None:
        _notify_streamlit("error", "Model artefact is missing the trained estimator.")
        return None

    return {
        "model": model,
        "metadata": metadata,
        "feature_columns": feature_columns,
    }


def _validate_categories(row: pd.Series, metadata: Dict[str, Any]) -> None:
    categories = metadata.get("categorical_levels", {})
    for field in ("sex", "region"):
        allowed = categories.get(field)
        if allowed and row[field] not in allowed:
            raise ValueError(f"Unknown category for {field}: {row[field]}")
    smoker_levels = categories.get("smoker")
    if smoker_levels:
        normalized = "yes" if _coerce_bool(row["smoker"]) else "no"
        if normalized not in smoker_levels:
            raise ValueError(f"Unknown category for smoker: {row['smoker']}")


def _compute_risk_score(prediction: float, metadata: Dict[str, Any]) -> float:
    quantiles = metadata.get("target_quantiles")
    if quantiles and len(quantiles) >= 2:
        risk_grid = np.linspace(0, 100, num=len(quantiles))
        return float(np.clip(np.interp(prediction, quantiles, risk_grid), 0, 100))
    return float(np.clip((prediction - 1000) / 500, 0, 100))


def _estimate_confidence(bundle: Dict[str, Any], transformed: np.ndarray, prediction: float) -> Dict[str, float]:
    model: Any = bundle["model"]
    metadata = bundle["metadata"]
    summary = metadata.get("target_summary", {})
    target_std = float(summary.get("std", 1.0))

    prediction_std: Optional[float] = None
    if hasattr(model, "named_steps"):
        regressor = model.named_steps.get("regressor")  # type: ignore[attr-defined]
        if regressor is not None and hasattr(regressor, "estimators_"):
            tree_predictions = np.array([est.predict(transformed)[0] for est in regressor.estimators_])
            prediction_std = float(tree_predictions.std())

    if prediction_std is None:
        prediction_std = float(target_std * 0.15)

    interval_half = 1.96 * prediction_std
    lower = float(max(0.0, prediction - interval_half))
    upper = float(max(prediction + interval_half, 0.0))
    confidence = float(np.clip(1 - (prediction_std / (target_std + 1e-6)), 0.2, 0.99))
    return {"confidence": confidence, "lower": lower, "upper": upper}


def _predict_with_bundle(
    bundle: Optional[Dict[str, Any]],
    age: float,
    gender: str,
    bmi: float,
    children: int,
    smoker: object,
    region: str,
) -> Optional[Dict[str, Any]]:
    """Make a prediction using the trained model bundle."""
    if not bundle:
        return None

    model: Any = bundle.get("model")
    metadata: Dict[str, Any] = bundle.get("metadata", {})

    if model is None:
        st.error("Model artefact is missing the trained estimator.")
        return None
    if not hasattr(model, "predict"):
        st.error("Loaded artefact is not a predictive pipeline.")
        return None

    try:
        raw_input = pd.DataFrame(
            {
                "age": [age],
                "sex": [str(gender).strip().lower()],
                "bmi": [bmi],
                "children": [children],
                "smoker": [_coerce_bool(smoker)],
                "region": [str(region).strip().lower().replace(" ", "_")],
            }
        )

        prepared = prepare_inference_frame(raw_input)
        _validate_categories(prepared.iloc[0], metadata)

        prediction = float(model.predict(prepared)[0])

        if hasattr(model, "named_steps") and "preprocessor" in model.named_steps:  # type: ignore[attr-defined]
            transformed = model.named_steps["preprocessor"].transform(prepared)  # type: ignore[index]
        else:
            transformed = prepared.to_numpy()
        confidence_payload = _estimate_confidence(bundle, transformed, prediction)
        risk_score = _compute_risk_score(prediction, metadata)

        return {
            "predicted_charges": prediction,
            "risk_score": risk_score,
            "confidence": confidence_payload["confidence"],
            "confidence_interval": {
                "lower": confidence_payload["lower"],
                "upper": confidence_payload["upper"],
            },
            "metadata": metadata,
        }
    except Exception as exc:
        _notify_streamlit("error", f"Error making prediction: {exc}")
        return None


def predict_insurance_charges(
    model_or_bundle: Any,
    age: float,
    gender: str,
    bmi: float,
    children: int,
    smoker: object,
    region: str,
) -> Optional[Any]:
    """Make a prediction, supporting both bundle dictionaries and plain estimators."""

    if isinstance(model_or_bundle, dict) and "model" in model_or_bundle:
        return _predict_with_bundle(model_or_bundle, age, gender, bmi, children, smoker, region)

    if model_or_bundle is None:
        return None

    try:
        return utils.predict_insurance_charges(model_or_bundle, age, gender, bmi, children, smoker, region)
    except Exception as exc:  # pragma: no cover - defensive handling
        _notify_streamlit("error", f"Error making prediction: {exc}")
        return None


def generate_risk_score(prediction: float, max_charge: float = 50000) -> int:
    """Legacy-compatible risk score helper mirroring utils.generate_risk_score."""

    try:
        return utils.generate_risk_score(prediction, int(max_charge))
    except Exception as exc:  # pragma: no cover - defensive handling
        _notify_streamlit("warning", f"Unable to compute risk score: {exc}")
        return 1


def plot_risk_gauge(risk_score: float) -> go.Figure:
    """Render a gauge chart highlighting the predicted risk percentile."""

    theme = get_streamlit_theme()
    palette = get_color_palette(theme)
    text_color = palette.get("text", "#222222")
    background_color = palette.get("background", palette.get("surface", "#FFFFFF"))
    grid_color = palette.get("grid", "#CCCCCC")
    paper_bgcolor = background_color

    raw_score = float(risk_score)
    if raw_score <= 10:
        scale_max = 10.0
        low_threshold = 3.5
        high_threshold = 7.0
    else:
        scale_max = 100.0
        low_threshold = 35.0
        high_threshold = 70.0

    value = float(np.clip(raw_score, 0.0, scale_max))

    if value <= low_threshold:
        color_key = "success"
    elif value <= high_threshold:
        color_key = "warning"
    else:
        color_key = "danger"

    color = get_color(color_key)

    include_delta = isinstance(theme, str)

    indicator_kwargs: Dict[str, Any] = {
        "mode": "gauge+number+delta" if include_delta else "gauge+number",
        "value": value,
        "domain": {"x": [0, 1], "y": [0, 1]},
        "title": {"text": "Risk Score", "font": {"size": 24, "color": text_color}},
        "number": {"font": {"size": 40, "color": color}},
        "gauge": {
            "axis": {
                "range": [0, scale_max],
                "tickwidth": 2,
                "tickcolor": text_color,
                "tickfont": {"size": 14},
            },
            "bar": {"color": color, "thickness": 0.8},
            "bgcolor": background_color,
            "borderwidth": 2,
            "bordercolor": grid_color,
            "steps": [
                {"range": [0, low_threshold], "color": "rgba(40, 167, 69, 0.3)"},
                {"range": [low_threshold, high_threshold], "color": "rgba(255, 193, 7, 0.3)"},
                {"range": [high_threshold, scale_max], "color": "rgba(220, 53, 69, 0.3)"},
            ],
            "threshold": {
                "line": {"color": text_color, "width": 4},
                "thickness": 0.8,
                "value": value,
            },
        },
    }

    if include_delta:
        indicator_kwargs["delta"] = {
            "reference": scale_max / 2.0,
            "increasing": {"color": get_color("danger")},
            "decreasing": {"color": get_color("success")},
        }

    fig = go.Figure(go.Indicator(**indicator_kwargs))

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor=paper_bgcolor,
        font={"color": text_color, "family": "Arial"},
        plot_bgcolor=background_color,
    )

    return fig

def _normalise_feature_name(name: str) -> str:
    """Map transformed feature names back to the base input column."""

    base_mappings = {
        "gender": "sex",
    }

    candidate = str(name)
    if "__" in candidate:
        candidate = candidate.split("__", 1)[1]
    prefix = candidate.split("_", 1)[0]
    mapped = base_mappings.get(prefix, prefix)
    if mapped in {"age", "bmi", "children", "sex", "smoker", "region"}:
        return mapped
    return candidate


def _aggr_feature_importance(feature_names: Iterable[str], importances: Iterable[float]) -> Dict[str, float]:
    totals: Dict[str, float] = {feature: 0.0 for feature in ["age", "bmi", "children", "sex", "smoker", "region"]}
    for name, importance in zip(feature_names, importances):
        key = _normalise_feature_name(name)
        totals[key] = totals.get(key, 0.0) + float(importance)

    total_importance = sum(totals.values())
    if total_importance > 0:
        totals = {feature: value / total_importance for feature, value in totals.items()}
    return totals


def _build_importance_dataframe(estimator: Any, metadata: Dict[str, Any]) -> Optional[pd.DataFrame]:
    if metadata:
        feature_importance = metadata.get("feature_importance")
        if isinstance(feature_importance, dict) and feature_importance:
            df = pd.DataFrame(
                {
                    "Feature": list(feature_importance.keys()),
                    "Importance": [float(value) for value in feature_importance.values()],
                }
            )
            permutation_importance = metadata.get("permutation_importance")
            if isinstance(permutation_importance, dict):
                df["Permutation"] = df["Feature"].map(permutation_importance).fillna(0.0)
            return df.sort_values("Importance", ascending=False)

    if estimator is None or not hasattr(estimator, "named_steps"):
        return None

    regressor = estimator.named_steps.get("regressor")  # type: ignore[attr-defined]
    if regressor is None or not hasattr(regressor, "feature_importances_"):
        return None

    importances = np.asarray(regressor.feature_importances_, dtype=float)
    if importances.size == 0:
        return None

    feature_names: list[str] = []
    preprocessor = estimator.named_steps.get("preprocessor")  # type: ignore[attr-defined]
    if metadata and isinstance(metadata.get("feature_names"), list):
        feature_names = [str(name) for name in metadata["feature_names"]]

    if not feature_names and preprocessor is not None:
        try:
            feature_names = list(map(str, preprocessor.get_feature_names_out()))  # type: ignore[attr-defined]
        except Exception:
            feature_names = []

    if not feature_names and hasattr(preprocessor, "transformers_"):
        feature_names = []
        for _, transformer, columns in getattr(preprocessor, "transformers_", []):
            if transformer is None:
                continue
            if hasattr(transformer, "get_feature_names_out"):
                try:
                    derived = transformer.get_feature_names_out(columns)
                    feature_names.extend(map(str, derived))
                    continue
                except Exception:
                    pass
            if isinstance(columns, (list, tuple)):
                feature_names.extend(map(str, columns))

    if not feature_names:
        feature_names = [f"feature_{idx}" for idx in range(importances.size)]

    aggregated = _aggr_feature_importance(feature_names, importances)
    frame = pd.DataFrame(
        {
            "Feature": list(aggregated.keys()),
            "Importance": [float(value) for value in aggregated.values()],
        }
    )
    frame = frame[frame["Importance"] > 0].copy()
    return frame.sort_values("Importance", ascending=False)


def plot_feature_importance(model_or_bundle: Any) -> Optional[go.Figure]:
    """Plot feature importance for the model using Plotly with dark-theme support."""

    try:
        theme = get_streamlit_theme()
        palette = get_color_palette(theme)
        if not model_or_bundle:
            return None

        if isinstance(model_or_bundle, dict) and "model" in model_or_bundle:
            estimator = model_or_bundle.get("model")
            metadata_candidate = model_or_bundle.get("metadata", {})
        else:
            estimator = model_or_bundle
            metadata_candidate = getattr(model_or_bundle, "metadata", {}) or {}

        metadata = metadata_candidate if isinstance(metadata_candidate, dict) else {}

        importance_df = _build_importance_dataframe(estimator, metadata)
        if importance_df is None or importance_df.empty:
            return None

        importance_df["Importance"] = importance_df["Importance"].round(4)

        color_scale = palette.get("importance_scale", "Blues")

        fig = px.bar(
            importance_df,
            x="Importance",
            y="Feature",
            orientation="h",
            color="Importance",
            color_continuous_scale=color_scale,
        )

        text_color = palette.get("text", "#222222")
        background = palette.get("background", "rgba(0,0,0,0)")
        grid_color = palette.get("grid", "#444444")

        fig.update_layout(
            height=480,
            xaxis_title="Importance Score",
            yaxis_title="Feature",
            font=dict(family="Arial", size=14, color=text_color),
            margin=dict(l=80, r=20, t=40, b=40),
            paper_bgcolor=background,
            plot_bgcolor=background,
            coloraxis_colorbar=dict(
                title=dict(text="Importance", font=dict(color=text_color)),
                tickcolor=text_color,
                tickfont=dict(color=text_color),
                outlinecolor=grid_color,
            ),
        )

        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor=grid_color,
            title_font={"color": text_color},
            tickfont={"color": text_color},
        )
        fig.update_yaxes(
            showgrid=False,
            title_font={"color": text_color},
            tickfont={"color": text_color},
            autorange="reversed",
        )

        return fig

    except Exception as exc:  # pragma: no cover - visualization fallback
        _notify_streamlit("error", f"Error creating feature importance plot: {exc}")
        return None

def plot_prediction_comparison(prediction, avg_charges):
    """Plot the prediction compared to average charges using Plotly."""
    try:
        theme = get_streamlit_theme()
        palette = get_color_palette(theme)
        text_color = palette.get('text', '#222222')
        info_color = palette.get('info', '#17A2B8')
        background_color = palette.get('background', '#FFFFFF')
        grid_color = palette.get('grid', '#CCCCCC')

        categories = ['Your Prediction', 'Average Charges']
        values = [prediction, avg_charges]

        colors = [
            palette.get('primary', '#4CAF50'),
            info_color,
        ]
        if prediction > avg_charges:
            colors[0] = palette.get('danger', '#DC3545')
        else:
            colors[0] = palette.get('success', '#198754')

        fig = go.Figure(
            data=[
                go.Bar(
                    x=categories,
                    y=values,
                    text=[f'${v:,.2f}' for v in values],
                    textposition='auto',
                    marker_color=colors,
                    hovertemplate='%{y:$,.2f}<extra></extra>',
                )
            ]
        )

        fig.add_shape(
            type="line",
            x0=-0.5,
            y0=avg_charges,
            x1=1.5,
            y1=avg_charges,
            line=dict(color=info_color, width=3, dash="dash"),
        )

        fig.update_layout(
            title={
                'text': 'Prediction vs. Average Charges',
                'y': 0.9,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 20, 'color': text_color},
            },
            yaxis_title="Insurance Charges ($)",
            font=dict(family="Arial", size=14, color=text_color),
            margin=dict(l=20, r=20, t=80, b=20),
            paper_bgcolor=background_color,
            plot_bgcolor=background_color,
            height=400,
        )

        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor=grid_color,
            title_font={'color': text_color},
            tickfont={'color': text_color},
            tickprefix='$',
            tickformat=',',
        )

        fig.add_annotation(
            x=1.5,
            y=avg_charges,
            text="Industry Average",
            showarrow=False,
            font=dict(size=14, color=info_color, family="Arial"),
            xshift=10,
            yshift=10,
            bgcolor="rgba(255,255,255,0.7)" if get_streamlit_theme() == 'light' else "rgba(0,0,0,0.7)",
            bordercolor=info_color,
            borderwidth=1,
            borderpad=4,
            opacity=0.9,
        )

        return fig
    except Exception as e:  # pragma: no cover - visualization fallback
        st.error(f"Error creating comparison plot: {e}")
        return None