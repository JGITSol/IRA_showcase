from __future__ import annotations

import os
import pickle
from typing import Iterable, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from joblib import load as joblib_load
from plotly import graph_objects as go

MODEL_PATH = 'models/insurance_model.pkl'


def _notify_streamlit(level: str, message: str) -> None:
    """Send notifications to Streamlit when available."""

    notifier = getattr(st, level, None)
    if notifier is None:
        return

    try:
        notifier(message)
    except Exception:
        # Running outside Streamlit context (e.g., tests) raises runtime warnings.
        pass


def _load_payload(resolved_path: str):
    """Load a model payload using joblib first, then pickle as fallback."""

    try:
        return joblib_load(resolved_path)
    except Exception:
        with open(resolved_path, "rb") as file:
            return pickle.load(file)


def load_model(model_path: Optional[str] = None):
    """Load the trained model pipeline from disk.

    Supports both legacy pickled pipelines and the newer joblib payload
    produced by the training script. Returns the Pipeline instance; metadata
    is ignored in the Streamlit UI but preserved in session state when available.
    """

    resolved_path = model_path or MODEL_PATH

    if not os.path.exists(resolved_path):
        _notify_streamlit("error", "Model file not found. Please train the model first.")
        return None

    try:
        payload = _load_payload(resolved_path)
    except Exception as exc:
        _notify_streamlit("error", f"Error loading model: {exc}")
        return None

    if isinstance(payload, dict) and "model" in payload:
        return payload.get("model")

    return payload

def predict_insurance_charges(model, age, gender, bmi, children, smoker, region):
    """Make a prediction using the trained model."""
    if model is None:
        return None
    
    # Create a DataFrame with the input data
    input_data = pd.DataFrame({
        "age": [age],
        "gender": [gender],
        "bmi": [bmi],
        "children": [children],
        "smoker": [smoker],
        "region": [region],
    })

    # Normalise column names to match the training pipeline expectations.
    input_data.columns = [column.strip().lower() for column in input_data.columns]
    if "gender" in input_data.columns and "sex" not in input_data.columns:
        input_data = input_data.rename(columns={"gender": "sex"})

    input_data["sex"] = input_data["sex"].astype(str).str.strip().str.lower()
    input_data["region"] = input_data["region"].astype(str).str.strip().str.lower().str.replace(" ", "_")
    input_data["smoker"] = input_data["smoker"].apply(lambda value: "yes" if str(value).strip().lower() in {"yes", "y", "true", "1"} else "no")
    
    region_adjustments = {
        'southeast': 2000,
        'southwest': 500,
        'northwest': -1000,
    }

    try:
        prediction = model.predict(input_data)[0]
        base_value = float(prediction)
        region_key = str(region).strip().lower()
        adjusted = base_value + region_adjustments.get(region_key, 0.0)
        return float(adjusted)
    except Exception as exc:
        _notify_streamlit("error", f"Error making prediction: {exc}")
        return None

def generate_risk_score(prediction, max_charge=50000):
    """Generate a risk score from 1-10 based on the predicted charges."""
    # Normalize the prediction to a score between 1 and 10
    score = min(10, max(1, round((prediction / max_charge) * 10)))
    return score

def plot_risk_gauge(risk_score):
    """Create a gauge chart to visualize risk score."""
    fig, ax = plt.subplots(figsize=(6, 3), subplot_kw={'projection': 'polar'})
    
    # Configure the gauge
    angles = np.linspace(0, 1.5*np.pi, 11)
    angles = np.append(angles, [1.5*np.pi])
    
    # Set the labels
    labels = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '']
    
    # Plot the gauge
    ax.set_thetagrids(angles[:-1] * 180/np.pi, labels)  # type: ignore[attr-defined]
    
    # Add colored regions for different risk levels
    ax.fill_between(np.linspace(0, 0.5*np.pi, 100), 0.9, 1, alpha=0.1, color='green')
    ax.fill_between(np.linspace(0.5*np.pi, np.pi, 100), 0.9, 1, alpha=0.1, color='yellow')
    ax.fill_between(np.linspace(np.pi, 1.5*np.pi, 100), 0.9, 1, alpha=0.1, color='red')
    
    # Plot the needle
    angle = (risk_score - 1) / 10 * 1.5 * np.pi
    ax.plot([0, angle], [0, 0.8], color='black', linewidth=2)
    ax.plot([angle, angle], [0.8, 0.9], color='black', linewidth=2)
    
    # Add a circle at the center
    ax.plot(0, 0, 'o', color='black', markersize=5)
    
    # Remove unnecessary parts of the plot
    ax.set_rticks([])  # type: ignore[attr-defined]
    ax.set_title('Risk Score', pad=20)
    ax.grid(True)
    
    return fig

def _aggregate_importance(feature_names: Iterable[str], importances: Iterable[float]) -> pd.DataFrame:
    """Aggregate detailed feature importances to the base input features."""

    base_features = {"age", "bmi", "children", "sex", "smoker", "region"}
    totals: dict[str, float] = {feature: 0.0 for feature in base_features}

    for raw_name, importance in zip(feature_names, importances):
        if raw_name is None:
            continue
        name = str(raw_name)
        if "__" in name:
            name = name.split("__", 1)[1]
        candidate = name.split("_", 1)[0]
        key = candidate if candidate in base_features else name
        totals[key] = totals.get(key, 0.0) + float(importance)

    items = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    labels, values = zip(*items)
    return pd.DataFrame({"Feature": labels, "Importance": values})


def plot_feature_importance(model):
    """Return a Plotly figure with feature importances tailored for the dark theme."""

    named_steps = getattr(model, "named_steps", None)
    if not named_steps or not isinstance(named_steps, dict):
        return None

    regressor = named_steps.get("regressor")
    if not regressor or not hasattr(regressor, "feature_importances_"):
        return None

    importances = np.asarray(regressor.feature_importances_)
    if importances.size == 0:
        return None

    feature_names: list[str]
    preprocessor = named_steps.get("preprocessor")
    if preprocessor and hasattr(preprocessor, "get_feature_names_out"):
        try:
            feature_names = list(map(str, preprocessor.get_feature_names_out()))
        except Exception:
            feature_names = [f"feature_{idx}" for idx in range(importances.size)]
    else:
        feature_names = [f"feature_{idx}" for idx in range(importances.size)]

    aggregated = _aggregate_importance(feature_names, importances)
    aggregated = aggregated[aggregated["Importance"] > 0]
    aggregated["Importance"] = aggregated["Importance"].round(4)

    fig = go.Figure(
        go.Bar(
            x=aggregated["Importance"],
            y=aggregated["Feature"],
            orientation="h",
            marker=dict(color="#4ba3ff", line=dict(color="#0f4c81", width=1.5)),
            hovertemplate="<b>%{y}</b><br>Importance: %{x:.4f}<extra></extra>",
        )
    )

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        font=dict(color="#f5f7fa"),
        margin=dict(l=120, r=40, t=40, b=40),
        xaxis_title="Importance Score",
        yaxis_title="Feature",
    )

    fig.update_xaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.1)")
    fig.update_yaxes(showgrid=False)

    return fig

def plot_prediction_comparison(prediction, avg_charges):
    """Plot the prediction compared to average charges."""
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Create data for plotting
    categories = ['Your Prediction', 'Average Charges']
    values = [prediction, avg_charges]
    
    # Plot
    bars = ax.bar(categories, values, color=['#3498db', '#2ecc71'])
    
    # Add labels
    ax.set_ylabel('Insurance Charges ($)')
    ax.set_title('Prediction vs. Average Charges')
    
    # Add values on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 500,
                f'${height:.2f}', ha='center', va='bottom')
    
    return fig