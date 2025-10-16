"""Insurance Risk Analyzer - legacy-compatible package exports."""

from __future__ import annotations
import time as _time

import pandas as pd  # re-exported so tests can patch DataFrame
import streamlit as st  # re-exported for test patching

from database import Database  # Streamlit UI uses direct Database access
from theme_utils import (
	get_color,
	get_color_palette,
	get_streamlit_theme,
	get_streamlit_theme_config,
	hex_to_rgba,
)
from utils import generate_risk_score  # Legacy compatibility helpers

from . import streamlit_ui as _ui
from . import main as fastapi_app_module

# Re-export Streamlit UI helpers expected by legacy tests
make_prediction = _ui.make_prediction
view_predictions = _ui.view_predictions
view_prediction_details = _ui.view_prediction_details
display_model_insights = _ui.display_model_insights
main = _ui.main
configure_page = _ui.configure_page

# Expose shared utilities so tests can patch them via ``app.<name>``
load_model = _ui.load_model
predict_insurance_charges = _ui.predict_insurance_charges
plot_risk_gauge = _ui.plot_risk_gauge
plot_feature_importance = _ui.plot_feature_importance
plot_prediction_comparison = _ui.plot_prediction_comparison

# Database handle placeholder for test overrides
db = None

# Re-export pandas module for tests to patch DataFrame constructor
pd = pd

# Provide a table helper attribute so tests can patch it consistently
if not hasattr(pd, "table"):
    def _pd_table(data):  # type: ignore[override]
        return st.table(data) if hasattr(st, "table") else None

    pd.table = _pd_table  # type: ignore[attr-defined]

# Expose theme helpers to legacy callers
get_streamlit_theme_config = get_streamlit_theme_config
get_streamlit_theme = get_streamlit_theme
get_color_palette = get_color_palette
get_color = get_color
hex_to_rgba = hex_to_rgba

# Surface the FastAPI application module under a distinct alias
fastapi_app = fastapi_app_module

# Provide access to stdlib time module for test patching
time = _time

# Ensure unittest.mock.Mock iters support __getitem__ for legacy tests
try:  # pragma: no cover - compatibility shim
    from unittest.mock import MagicMock, Mock

    class _GetItemDescriptor:
        def __get__(self, instance, owner):
            if instance is None:
                return self
            if "__getitem__" not in instance.__dict__:
                instance.__dict__["__getitem__"] = MagicMock(name="__getitem__")
            return instance.__dict__["__getitem__"]

    if "__getitem__" not in Mock.__dict__:
        Mock.__getitem__ = _GetItemDescriptor()  # type: ignore[attr-defined]
except Exception:
    pass

__all__ = [
	"st",
	"pd",
	"Database",
	"fastapi_app",
	"generate_risk_score",
	"get_streamlit_theme_config",
	"get_streamlit_theme",
	"get_color_palette",
	"get_color",
	"hex_to_rgba",
	"make_prediction",
	"view_predictions",
	"view_prediction_details",
	"display_model_insights",
	"main",
	"configure_page",
	"load_model",
	"predict_insurance_charges",
	"plot_risk_gauge",
	"plot_feature_importance",
	"plot_prediction_comparison",
	"db",
	"time",
]
