from __future__ import annotations

import logging
import os
import sys
import time
from contextlib import contextmanager
from typing import Any, Iterable, Optional

import pandas as pd
import streamlit as st

from database import Database
from utils import generate_risk_score as _generate_risk_score_impl
from utils import load_model as _load_model_impl
from utils import predict_insurance_charges as _predict_insurance_impl
from utils_plotly import (
    plot_feature_importance as _plot_feature_importance_impl,
    plot_prediction_comparison as _plot_prediction_comparison_impl,
    plot_risk_gauge as _plot_risk_gauge_impl,
)

_PAGE_CONFIGURED_ATTR = "_ira_page_configured"


def setup_json_logging() -> None:
    """Configure root logger to output JSON logs to stdout."""
    try:
        from pythonjsonlogger import jsonlogger
    except Exception:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        return

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    root = logging.getLogger()
    root.handlers = []
    root.setLevel(log_level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    root.addHandler(handler)


def _configure_logging() -> logging.Logger:
    setup_json_logging()
    return logging.getLogger(__name__)


logger = _configure_logging()


db: Optional[Database] = None


def _resolve(name: str, fallback):
    module = sys.modules.get("app")
    override = getattr(module, name, None) if module else None
    current = globals().get(name)
    if override is None or override is current:
        return fallback
    return override


def _ensure_page_config(ui: Any) -> None:
    if getattr(ui, _PAGE_CONFIGURED_ATTR, False):
        return

    setter = getattr(ui, "set_page_config", None)
    if callable(setter):
        setter(
            page_title="Insurance Risk Predictor",
            page_icon="💰",
            layout="wide",
            initial_sidebar_state="expanded",
        )
    setattr(ui, _PAGE_CONFIGURED_ATTR, True)


def _get_streamlit():
    ui = _resolve("st", st)
    _ensure_page_config(ui)
    return ui


def _get_pandas():
    return _resolve("pd", pd)


def _get_session_state(ui: Any):
    state = getattr(ui, "session_state", None)
    if state is None:
        state = {}
        setattr(ui, "session_state", state)
    return state


def _session_state_storage(state: Any):
    return getattr(state, "__dict__", {})


def _session_state_has(state: Any, key: str) -> bool:
    if isinstance(state, dict):
        return key in state
    if hasattr(state, "__contains__"):
        try:
            return key in state  # type: ignore[operator]
        except Exception:
            pass
    return key in _session_state_storage(state)


def _session_state_get(state: Any, key: str, default: Any = None) -> Any:
    if isinstance(state, dict):
        return state.get(key, default)
    if hasattr(state, "get"):
        try:
            return state.get(key, default)  # type: ignore[call-arg]
        except Exception:
            pass
    if _session_state_has(state, key):
        try:
            return state[key]  # type: ignore[index]
        except Exception:
            return getattr(state, key)
    return default


def _session_state_set(state: Any, key: str, value: Any) -> None:
    if isinstance(state, dict):
        state[key] = value
    elif hasattr(state, "__setitem__"):
        try:
            state[key] = value  # type: ignore[index]
            return
        except Exception:
            setattr(state, key, value)
    else:
        setattr(state, key, value)


def _session_state_setdefault(state: Any, key: str, value: Any) -> Any:
    if not _session_state_has(state, key):
        _session_state_set(state, key, value)
    return _session_state_get(state, key)


def _ensure_columns(ui_component: Any, count: int) -> list[Any]:
    try:
        columns = ui_component.columns(count)
    except Exception:
        return [ui_component] * count

    if columns is None:
        return [ui_component] * count

    try:
        columns_list = list(columns)
    except TypeError:
        columns_list = [columns]

    if len(columns_list) < count:
        columns_list.extend([ui_component] * (count - len(columns_list)))

    return columns_list[:count]


def _call_widget(target: Any, method: str, *args, fallback_parent: Any = None, **kwargs):
    candidate = getattr(target, method, None)
    if callable(candidate):
        try:
            return candidate(*args, **kwargs)
        except Exception as exc:  # pragma: no cover - defensive logging only
            logger.debug("Widget call failed", exc_info=exc)

    parent = fallback_parent or _get_streamlit()
    fallback = getattr(parent, method, None)
    if callable(fallback):
        return fallback(*args, **kwargs)
    return None


def _safe_format(value: Any, pattern: str = "{:.2f}") -> str:
    try:
        return pattern.format(float(value))
    except Exception:
        return str(value)


@contextmanager
def _form_context(ui: Any, key: str):
    form_factory = getattr(ui, "form", None)
    if not callable(form_factory):
        yield ui
        return

    form_obj = form_factory(key)
    enter = getattr(form_obj, "__enter__", None)
    exit_ = getattr(form_obj, "__exit__", None)
    if callable(enter) and callable(exit_):
        with form_obj:
            yield form_obj
        return

    yield form_obj or ui


def configure_page() -> None:
    """Apply Streamlit page configuration once the runtime is ready."""

    ui = _resolve("st", st)
    _ensure_page_config(ui)


def _run_on_import() -> None:
    try:  # pragma: no cover - execute during import for legacy tests
        configure_page()
    except Exception:  # pragma: no cover - defensive guard only
        pass


_run_on_import()


def load_model():
    loader = _resolve("load_model", _load_model_impl)
    return loader()


def predict_insurance_charges(model, age, gender, bmi, children, smoker, region):
    predictor = _resolve("predict_insurance_charges", _predict_insurance_impl)
    return predictor(model, age, gender, bmi, children, smoker, region)


def generate_risk_score(prediction):
    scorer = _resolve("generate_risk_score", _generate_risk_score_impl)
    return scorer(prediction)


def plot_feature_importance(model):
    plotter = _resolve("plot_feature_importance", _plot_feature_importance_impl)
    return plotter(model)


def plot_prediction_comparison(prediction, average):
    plotter = _resolve("plot_prediction_comparison", _plot_prediction_comparison_impl)
    return plotter(prediction, average)


def plot_risk_gauge(score):
    plotter = _resolve("plot_risk_gauge", _plot_risk_gauge_impl)
    return plotter(score)


def _get_database() -> Database:
    """Return a database instance, creating it lazily."""

    global db
    module_db = getattr(sys.modules.get("app"), "db", None)
    if module_db is not None and module_db is not db and hasattr(module_db, "get_all_predictions"):
        db = module_db

    if db is None:
        db = Database()
    return db


def make_prediction() -> bool:
    """Make a prediction based on user inputs and save to database."""

    ui = _get_streamlit()
    state = _get_session_state(ui)
    loader = _resolve("load_model", _load_model_impl)
    predictor = _resolve("predict_insurance_charges", _predict_insurance_impl)
    scorer = _resolve("generate_risk_score", _generate_risk_score_impl)

    model = loader()
    if model is None:
        ui.error("Failed to load model. Please ensure the model has been trained.")
        return False

    age = _session_state_get(state, "age")
    gender = _session_state_get(state, "gender")
    bmi = _session_state_get(state, "bmi")
    children = _session_state_get(state, "children")
    smoker = _session_state_get(state, "smoker")
    region = _session_state_get(state, "region")

    prediction = predictor(model, age, gender, bmi, children, smoker, region)
    if prediction is None:
        ui.error("Failed to make prediction.")
        return False

    risk_score = scorer(prediction)

    _session_state_set(state, "prediction", prediction)
    _session_state_set(state, "risk_score", risk_score)

    prediction_id = _get_database().add_prediction(
        age,
        gender,
        bmi,
        children,
        smoker,
        region,
        float(prediction),
    )

    _session_state_set(state, "prediction_made", True)
    ui.success(f"Prediction saved with ID: {prediction_id}")
    return True


def _format_predictions_dataframe(data: Iterable[dict[str, Any]]) -> Optional[pd.DataFrame]:
    pandas_module = _get_pandas()
    try:
        df = pandas_module.DataFrame(list(data))
    except Exception:
        return None

    if "predicted_charges" in getattr(df, "columns", []):
        try:
            df["predicted_charges"] = df["predicted_charges"].apply(lambda x: f"${_safe_format(x)}")
        except Exception:
            pass
    return df


def view_predictions() -> None:
    """View all saved predictions."""

    ui = _get_streamlit()
    details_viewer = _resolve("view_prediction_details", view_prediction_details)
    predictions = _get_database().get_all_predictions()
    if not predictions:
        ui.info("No predictions found in the database.")
        return

    df = _format_predictions_dataframe(predictions)
    if df is None:
        ui.error("Unable to display predictions table.")
        return

    ui.dataframe(df)

    try:
        prediction_ids = df["id"].tolist()
    except Exception:
        prediction_ids = []

    selected_id = ui.selectbox("Select a prediction to view details:", prediction_ids)

    if selected_id:
        details_viewer(selected_id)


def view_prediction_details(prediction_id: int) -> None:
    """View details of a specific prediction."""

    ui = _get_streamlit()
    prediction = _get_database().get_prediction_by_id(prediction_id)
    if not prediction:
        ui.error(f"Prediction with ID {prediction_id} not found.")
        return

    col1, col2 = _ensure_columns(ui, 2)

    _call_widget(col1, "subheader", "Input Parameters", fallback_parent=ui)
    _call_widget(col1, "write", f"**Age:** {prediction['age']}", fallback_parent=ui)
    _call_widget(col1, "write", f"**Gender:** {prediction['gender']}", fallback_parent=ui)
    _call_widget(col1, "write", f"**BMI:** {_safe_format(prediction['bmi'])}", fallback_parent=ui)
    _call_widget(col1, "write", f"**Children:** {prediction['children']}", fallback_parent=ui)
    _call_widget(col1, "write", f"**Smoker:** {prediction['smoker']}", fallback_parent=ui)
    _call_widget(col1, "write", f"**Region:** {prediction['region']}", fallback_parent=ui)

    _call_widget(col2, "subheader", "Prediction Result", fallback_parent=ui)
    _call_widget(
        col2,
        "write",
        f"**Predicted Charges:** ${_safe_format(prediction['predicted_charges'])}",
        fallback_parent=ui,
    )
    _call_widget(
        col2,
        "write",
        f"**Prediction Date:** {prediction['prediction_date']}",
        fallback_parent=ui,
    )

    ui.subheader("Actions")
    action_cols = _ensure_columns(ui, 2)
    state = _get_session_state(ui)

    if _call_widget(action_cols[0], "button", "Load this prediction for editing", fallback_parent=ui):
        _session_state_set(state, "age", prediction['age'])
        _session_state_set(state, "gender", prediction['gender'])
        _session_state_set(state, "bmi", prediction['bmi'])
        _session_state_set(state, "children", prediction['children'])
        _session_state_set(state, "smoker", prediction['smoker'])
        _session_state_set(state, "region", prediction['region'])
        _session_state_set(state, "active_tab", "Predict")
        ui.rerun()
        return

    if _call_widget(action_cols[1], "button", "Delete this prediction", fallback_parent=ui):
        if _get_database().delete_prediction(prediction_id):
            ui.success(f"Prediction with ID {prediction_id} deleted.")
            time.sleep(1)
            ui.rerun()
            return
        ui.error(f"Failed to delete prediction with ID {prediction_id}.")


def display_model_insights() -> None:
    """Display insights and visualizations about the model."""

    ui = _get_streamlit()
    loader = _resolve("load_model", _load_model_impl)
    feature_plotter = _resolve("plot_feature_importance", _plot_feature_importance_impl)

    model = loader()
    if model is None:
        ui.error("Failed to load model. Please ensure the model has been trained.")
        return

    ui.subheader("Model Insights")
    ui.write("### Feature Importance")
    ui.write("This chart shows which factors have the most influence on insurance charges:")

    feature_imp_fig = feature_plotter(model)
    if feature_imp_fig:
        ui.plotly_chart(feature_imp_fig, use_container_width=True)
    else:
        ui.warning("Feature importance visualization is not available for this model.")

    ui.write("### Example Predictions")
    ui.write("See how different profiles affect insurance charges:")

    profiles = [
        {"name": "Young Non-Smoker", "age": 25, "gender": "male", "bmi": 22, "children": 0, "smoker": "no", "region": "northeast"},
        {"name": "Young Smoker", "age": 25, "gender": "male", "bmi": 22, "children": 0, "smoker": "yes", "region": "northeast"},
        {"name": "Middle-Aged Family", "age": 45, "gender": "female", "bmi": 28, "children": 2, "smoker": "no", "region": "southeast"},
        {"name": "Senior Citizen", "age": 65, "gender": "male", "bmi": 30, "children": 0, "smoker": "no", "region": "southwest"},
    ]

    predictor = _resolve("predict_insurance_charges", _predict_insurance_impl)
    results = []
    for profile in profiles:
        pred = predictor(
            model,
            profile["age"],
            profile["gender"],
            profile["bmi"],
            profile["children"],
            profile["smoker"],
            profile["region"],
        )
        results.append({"Profile": profile["name"], "Predicted Charges": f"${_safe_format(pred)}"})

    pandas_module = _get_pandas()
    ui.table(pandas_module.DataFrame(results))


def _render_predict_form(ui: Any, state: Any) -> bool:
    ui.subheader("Enter Your Information")
    left_col, right_col = _ensure_columns(ui, 2)

    _call_widget(
        left_col,
        "number_input",
        "Age",
        min_value=18,
        max_value=100,
        value=_session_state_get(state, "age", 30),
        key="age",
        fallback_parent=ui,
    )
    _call_widget(
        left_col,
        "selectbox",
        "Gender",
        options=["male", "female"],
        index=0 if _session_state_get(state, "gender") == "male" else 1,
        key="gender",
        fallback_parent=ui,
    )
    _call_widget(
        left_col,
        "number_input",
        "BMI",
        min_value=10.0,
        max_value=50.0,
        value=_session_state_get(state, "bmi", 25.0),
        step=0.1,
        key="bmi",
        fallback_parent=ui,
    )

    _call_widget(
        right_col,
        "number_input",
        "Number of Children",
        min_value=0,
        max_value=10,
        value=_session_state_get(state, "children", 0),
        key="children",
        fallback_parent=ui,
    )
    _call_widget(
        right_col,
        "selectbox",
        "Smoker",
        options=["yes", "no"],
        index=0 if _session_state_get(state, "smoker") == "yes" else 1,
        key="smoker",
        fallback_parent=ui,
    )
    _call_widget(
        right_col,
        "selectbox",
        "Region",
        options=["northeast", "northwest", "southeast", "southwest"],
        index=["northeast", "northwest", "southeast", "southwest"].index(_session_state_get(state, "region", "northeast")),
        key="region",
        fallback_parent=ui,
    )

    submit_target = getattr(ui, "form_submit_button", None)
    if callable(submit_target):
        return bool(submit_target("Calculate Risk"))
    return bool(ui.button("Calculate Risk"))


def main() -> None:
    ui = _get_streamlit()
    state = _get_session_state(ui)
    comparison_plotter = _resolve("plot_prediction_comparison", _plot_prediction_comparison_impl)
    risk_plotter = _resolve("plot_risk_gauge", _plot_risk_gauge_impl)
    history_viewer = _resolve("view_predictions", view_predictions)
    insights_viewer = _resolve("display_model_insights", display_model_insights)

    configure_page()

    ui.title("Insurance Risk Predictor")
    ui.write("Predict insurance charges and assess risk factors")

    default_values = {
        "active_tab": "Predict",
        "prediction_made": False,
        "prediction": None,
        "risk_score": None,
        "age": 30,
        "gender": "male",
        "bmi": 25.0,
        "children": 0,
        "smoker": "no",
        "region": "northeast",
    }

    for key, value in default_values.items():
        _session_state_setdefault(state, key, value)

    col1, col2, col3 = _ensure_columns(ui, 3)

    if _call_widget(col1, "button", "Predict", use_container_width=True, fallback_parent=ui):
        _session_state_set(state, "active_tab", "Predict")

    if _call_widget(col2, "button", "History", use_container_width=True, fallback_parent=ui):
        _session_state_set(state, "active_tab", "History")

    if _call_widget(col3, "button", "Insights", use_container_width=True, fallback_parent=ui):
        _session_state_set(state, "active_tab", "Insights")

    ui.markdown(f"**Current Tab:** {_session_state_get(state, 'active_tab')}")
    ui.markdown("---")

    active_tab = _session_state_get(state, "active_tab")

    if active_tab == "Predict":
        with _form_context(ui, "prediction_form"):
            submitted = _render_predict_form(ui, state)
            if submitted:
                make_prediction()

        if _session_state_get(state, "prediction_made"):
            ui.markdown("---")
            ui.subheader("Prediction Results")

            results_cols = _ensure_columns(ui, 2)
            _call_widget(
                results_cols[0],
                "metric",
                "Predicted Insurance Charges",
                f"${_safe_format(_session_state_get(state, 'prediction'))}",
                fallback_parent=ui,
            )
            _call_widget(
                results_cols[0],
                "metric",
                "Risk Score",
                f"{_safe_format(_session_state_get(state, 'risk_score', 0), '{:.0f}')}/10",
                fallback_parent=ui,
            )

            risk_score_value = _session_state_get(state, "risk_score")
            if risk_score_value is not None:
                risk_gauge = risk_plotter(float(risk_score_value))
                ui.plotly_chart(risk_gauge, use_container_width=True)

            ui.markdown("---")
            ui.subheader("Comparison with Average")

            avg_charges = 13270.42
            comparison_fig = comparison_plotter(_session_state_get(state, "prediction"), avg_charges)
            ui.plotly_chart(comparison_fig, use_container_width=True)

            ui.markdown("---")
            ui.subheader("Risk Factors")

            if _session_state_get(state, "smoker") == "yes":
                ui.warning("Being a smoker significantly increases your insurance risk.")

            if _session_state_get(state, "bmi", 0) > 30:
                ui.warning("A BMI over 30 (considered obese) increases health risks and insurance costs.")

            if _session_state_get(state, "age", 0) > 50:
                ui.info("Age is a factor in insurance pricing, with older individuals typically paying more.")

            if ui.button("Make a New Prediction"):
                _session_state_set(state, "prediction_made", False)
                ui.rerun()

    elif active_tab == "History":
        history_viewer()

    elif active_tab == "Insights":
        insights_viewer()


__all__ = [
    "st",
    "Database",
    "db",
    "configure_page",
    "display_model_insights",
    "make_prediction",
    "main",
    "plot_feature_importance",
    "plot_prediction_comparison",
    "plot_risk_gauge",
    "view_prediction_details",
    "view_predictions",
]


if __name__ == "__main__":  # pragma: no cover
    main()
