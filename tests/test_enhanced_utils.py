"""Enhanced tests for utils modules with better coverage."""

import pytest
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
import pickle
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import utils
import utils_plotly
from theme_utils import get_streamlit_theme, get_color_palette


class TestUtilsEnhanced:
    """Enhanced tests for the utils module."""
    
    @pytest.fixture
    def mock_model(self):
        """Create a comprehensive mock model."""
        model = Mock()
        
        # Mock prediction method
        def mock_predict(X):
            # Simulate realistic prediction based on input features
            if hasattr(X, 'iloc'):
                row = X.iloc[0]
                base_charge = 5000
                age_factor = row.get('age', 30) * 100
                smoker_factor = 15000 if row.get('smoker') == 'yes' else 0
                bmi_factor = max(0, (row.get('bmi', 25) - 25) * 200)
                return np.array([base_charge + age_factor + smoker_factor + bmi_factor])
            return np.array([10000.0])
        
        model.predict = mock_predict
        
        # Mock pipeline structure for feature importance
        regressor_mock = Mock()
        regressor_mock.feature_importances_ = np.array([0.3, 0.25, 0.2, 0.1, 0.1, 0.05])
        
        preprocessor_mock = Mock()
        cat_transformer_mock = Mock()
        cat_transformer_mock.categories_ = [
            np.array(['male', 'female']),
            np.array(['no', 'yes']),
            np.array(['northeast', 'northwest', 'southeast', 'southwest'])
        ]
        preprocessor_mock.named_transformers_ = {'cat': cat_transformer_mock}
        
        model.named_steps = {
            'regressor': regressor_mock,
            'preprocessor': preprocessor_mock
        }
        
        return model
    
    def test_load_model_success(self, mock_model):
        """Test successful model loading."""
        with patch('utils.os.path.exists', return_value=True), \
             patch('utils.pickle.load', return_value=mock_model):
            
            with patch('builtins.open', mock_open_read()):
                model = utils.load_model()
                
                assert model is not None
                assert hasattr(model, 'predict')
    
    def test_load_model_file_not_found(self):
        """Test model loading when file doesn't exist."""
        with patch('utils.os.path.exists', return_value=False):
            model = utils.load_model()
            assert model is None
    
    def test_load_model_custom_path(self, mock_model):
        """Test model loading with custom path."""
        custom_path = 'custom/path/model.pkl'
        
        with patch('utils.os.path.exists', return_value=True), \
             patch('utils.pickle.load', return_value=mock_model):
            
            with patch('builtins.open', mock_open_read()) as mock_open:
                model = utils.load_model(custom_path)
                
                assert model is not None
                mock_open.assert_called_once_with(custom_path, 'rb')
    
    def test_load_model_exception_handling(self):
        """Test model loading with file corruption."""
        with patch('utils.os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=IOError("File corrupted")):
            
            model = utils.load_model()
            assert model is None
    
    def test_predict_insurance_charges_comprehensive(self, mock_model):
        """Test comprehensive prediction scenarios."""
        test_cases = [
            # (age, gender, bmi, children, smoker, region, expected_min, expected_max)
            (25, 'male', 22.0, 0, 'no', 'northeast', 7000, 9000),
            (45, 'female', 30.0, 2, 'yes', 'southwest', 22000, 26000),
            (60, 'male', 35.0, 0, 'no', 'southeast', 15000, 18000),
            (30, 'female', 25.0, 1, 'yes', 'northwest', 18000, 22000),
        ]
        
        for age, gender, bmi, children, smoker, region, exp_min, exp_max in test_cases:
            prediction = utils.predict_insurance_charges(
                mock_model, age, gender, bmi, children, smoker, region
            )
            
            assert prediction is not None
            assert isinstance(prediction, (int, float))
            assert exp_min <= prediction <= exp_max
    
    def test_predict_insurance_charges_edge_cases(self, mock_model):
        """Test prediction with edge case values."""
        # Minimum values
        prediction_min = utils.predict_insurance_charges(
            mock_model, 18, 'male', 15.0, 0, 'no', 'northeast'
        )
        assert prediction_min is not None
        
        # Maximum values
        prediction_max = utils.predict_insurance_charges(
            mock_model, 100, 'female', 50.0, 10, 'yes', 'southwest'
        )
        assert prediction_max is not None
        assert prediction_max > prediction_min
    
    def test_predict_insurance_charges_none_model(self):
        """Test prediction with None model."""
        prediction = utils.predict_insurance_charges(
            None, 30, 'male', 25.0, 2, 'no', 'northeast'
        )
        assert prediction is None
    
    def test_predict_insurance_charges_model_exception(self):
        """Test prediction when model raises exception."""
        mock_model = Mock()
        mock_model.predict.side_effect = Exception("Model error")
        
        prediction = utils.predict_insurance_charges(
            mock_model, 30, 'male', 25.0, 2, 'no', 'northeast'
        )
        assert prediction is None
    
    def test_generate_risk_score_range(self):
        """Test risk score generation across full range."""
        test_cases = [
            (1000, 50000, 1),    # Minimum
            (50000, 50000, 10),  # Maximum
            (25500, 50000, 5),   # Middle
            (13000, 50000, 3),   # Lower-middle
            (38000, 50000, 8),   # Upper-middle
        ]
        
        for charges, max_charge, expected_score in test_cases:
            score = utils.generate_risk_score(charges, max_charge)
            assert score == expected_score
    
    def test_generate_risk_score_custom_max(self):
        """Test risk score with custom maximum charge."""
        score = utils.generate_risk_score(15000, max_charge=30000)
        assert 1 <= score <= 10
        
        # Should be roughly in the middle
        assert 4 <= score <= 6
    
    def test_generate_risk_score_extreme_values(self):
        """Test risk score with extreme values."""
        # Very high charges
        score_high = utils.generate_risk_score(100000, max_charge=50000)
        assert score_high == 10
        
        # Negative charges (edge case)
        score_negative = utils.generate_risk_score(-1000, max_charge=50000)
        assert score_negative == 1
        
        # Zero charges
        score_zero = utils.generate_risk_score(0, max_charge=50000)
        assert score_zero == 1
    
    def test_plot_risk_gauge_all_scores(self):
        """Test risk gauge plotting for all possible scores."""
        for score in range(1, 11):
            fig = utils.plot_risk_gauge(score)
            
            assert isinstance(fig, plt.Figure)
            assert len(fig.axes) > 0
            
            # Close figure to prevent memory leaks
            plt.close(fig)
    
    def test_plot_risk_gauge_invalid_scores(self):
        """Test risk gauge with invalid scores."""
        # Score too low
        fig_low = utils.plot_risk_gauge(0)
        assert isinstance(fig_low, plt.Figure)
        plt.close(fig_low)
        
        # Score too high
        fig_high = utils.plot_risk_gauge(15)
        assert isinstance(fig_high, plt.Figure)
        plt.close(fig_high)
        
        # Negative score
        fig_neg = utils.plot_risk_gauge(-5)
        assert isinstance(fig_neg, plt.Figure)
        plt.close(fig_neg)
    
    def test_plot_feature_importance_success(self, mock_model):
        """Test feature importance plotting."""
        fig = utils.plot_feature_importance(mock_model)
        
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) > 0
        
        # Check that the plot has the expected elements
        ax = fig.axes[0]
        assert len(ax.patches) > 0  # Should have bars
        
        plt.close(fig)
    
    def test_plot_feature_importance_no_pipeline(self):
        """Test feature importance with non-pipeline model."""
        simple_model = Mock()
        simple_model.feature_importances_ = np.array([0.4, 0.3, 0.2, 0.1])
        
        # Should return None for non-pipeline models
        fig = utils.plot_feature_importance(simple_model)
        assert fig is None
    
    def test_plot_feature_importance_no_named_steps(self):
        """Test feature importance with model without named_steps."""
        model_without_steps = Mock()
        del model_without_steps.named_steps  # Remove the attribute
        
        fig = utils.plot_feature_importance(model_without_steps)
        assert fig is None
    
    def test_plot_prediction_comparison_various_values(self):
        """Test prediction comparison with various value combinations."""
        test_cases = [
            (10000, 12000),  # Prediction lower than average
            (15000, 12000),  # Prediction higher than average
            (12000, 12000),  # Prediction equal to average
            (5000, 20000),   # Large difference
            (25000, 8000),   # Prediction much higher
        ]
        
        for prediction, avg_charges in test_cases:
            fig = utils.plot_prediction_comparison(prediction, avg_charges)
            
            assert isinstance(fig, plt.Figure)
            assert len(fig.axes) > 0
            
            # Verify bars are present
            ax = fig.axes[0]
            assert len(ax.patches) == 2  # Should have 2 bars
            
            plt.close(fig)
    
    def test_plot_prediction_comparison_zero_values(self):
        """Test prediction comparison with zero values."""
        fig = utils.plot_prediction_comparison(0, 10000)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
        
        fig = utils.plot_prediction_comparison(10000, 0)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
    
    def test_plot_prediction_comparison_negative_values(self):
        """Test prediction comparison with negative values."""
        # Should handle negative values gracefully
        fig = utils.plot_prediction_comparison(-5000, 10000)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestUtilsPlotlyEnhanced:
    """Enhanced tests for the utils_plotly module."""
    
    @pytest.fixture
    def mock_model(self):
        """Create a mock model for plotly tests."""
        model = Mock()
        model.predict.return_value = np.array([15000.0])
        
        # Mock for feature importance
        regressor_mock = Mock()
        regressor_mock.feature_importances_ = np.array([0.35, 0.25, 0.2, 0.1, 0.05, 0.05])
        
        preprocessor_mock = Mock()
        cat_transformer_mock = Mock()
        cat_transformer_mock.categories_ = [
            np.array(['male', 'female']),
            np.array(['no', 'yes']),
            np.array(['northeast', 'northwest', 'southeast', 'southwest'])
        ]
        preprocessor_mock.named_transformers_ = {'cat': cat_transformer_mock}
        
        model.named_steps = {
            'regressor': regressor_mock,
            'preprocessor': preprocessor_mock
        }
        
        return model
    
    def test_plot_risk_gauge_plotly_all_scores(self):
        """Test Plotly risk gauge for all scores."""
        for score in range(1, 11):
            fig = utils_plotly.plot_risk_gauge(score)
            
            assert isinstance(fig, go.Figure)
            assert len(fig.data) > 0
            
            # Check gauge properties
            gauge_data = fig.data[0]
            assert gauge_data.type == 'indicator'
            assert gauge_data.mode == 'gauge+number+delta'
    
    def test_plot_risk_gauge_plotly_theme_awareness(self):
        """Test risk gauge with different themes."""
        with patch('utils_plotly.get_streamlit_theme') as mock_theme:
            # Test dark theme
            mock_theme.return_value = 'dark'
            fig_dark = utils_plotly.plot_risk_gauge(5)
            assert isinstance(fig_dark, go.Figure)
            
            # Test light theme
            mock_theme.return_value = 'light'
            fig_light = utils_plotly.plot_risk_gauge(5)
            assert isinstance(fig_light, go.Figure)
            
            # Figures should be different (different styling)
            assert fig_dark.layout.paper_bgcolor != fig_light.layout.paper_bgcolor
    
    def test_plot_feature_importance_plotly_success(self, mock_model):
        """Test Plotly feature importance plotting."""
        fig = utils_plotly.plot_feature_importance(mock_model)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
        
        # Check bar chart properties
        bar_data = fig.data[0]
        assert bar_data.type == 'bar'
        assert len(bar_data.x) > 0
        assert len(bar_data.y) > 0
    
    def test_plot_feature_importance_plotly_theme_awareness(self, mock_model):
        """Test feature importance with theme awareness."""
        with patch('utils_plotly.get_streamlit_theme') as mock_theme:
            # Test with different themes
            for theme in ['light', 'dark']:
                mock_theme.return_value = theme
                fig = utils_plotly.plot_feature_importance(mock_model)
                
                assert isinstance(fig, go.Figure)
                # Verify theme-appropriate styling is applied
                assert fig.layout.paper_bgcolor is not None
    
    def test_plot_prediction_comparison_plotly_various_cases(self):
        """Test Plotly prediction comparison with various cases."""
        test_cases = [
            (8000, 12000, "Below Average"),
            (16000, 12000, "Above Average"),
            (12000, 12000, "Equal to Average"),
            (25000, 10000, "Much Higher"),
            (3000, 15000, "Much Lower"),
        ]
        
        for prediction, avg_charges, description in test_cases:
            fig = utils_plotly.plot_prediction_comparison(prediction, avg_charges)
            
            assert isinstance(fig, go.Figure)
            assert len(fig.data) > 0
            
            # Check bar chart properties
            bar_data = fig.data[0]
            assert bar_data.type == 'bar'
            assert len(bar_data.x) == 2  # Two bars
            assert len(bar_data.y) == 2
    
    def test_predict_insurance_charges_plotly_consistency(self, mock_model):
        """Test that plotly utils prediction is consistent with regular utils."""
        test_params = (35, 'female', 28.5, 2, 'yes', 'southwest')
        
        # Both should return the same result
        prediction_regular = utils.predict_insurance_charges(mock_model, *test_params)
        prediction_plotly = utils_plotly.predict_insurance_charges(mock_model, *test_params)
        
        assert prediction_regular == prediction_plotly
    
    def test_generate_risk_score_plotly_consistency(self):
        """Test that plotly utils risk score is consistent with regular utils."""
        test_charges = [5000, 15000, 25000, 35000, 45000]
        
        for charges in test_charges:
            score_regular = utils.generate_risk_score(charges)
            score_plotly = utils_plotly.generate_risk_score(charges)
            
            assert score_regular == score_plotly
    
    def test_load_model_plotly_consistency(self):
        """Test that plotly utils model loading is consistent."""
        with patch('utils_plotly.os.path.exists', return_value=False):
            model_plotly = utils_plotly.load_model()
            assert model_plotly is None
        
        mock_model = Mock()
        with patch('utils_plotly.os.path.exists', return_value=True), \
             patch('utils_plotly.pickle.load', return_value=mock_model):
            
            with patch('builtins.open', mock_open_read()):
                model_plotly = utils_plotly.load_model()
                assert model_plotly is not None


class TestThemeUtils:
    """Test theme utilities."""
    
    def test_get_streamlit_theme_default(self):
        """Test getting default Streamlit theme."""
        with patch('theme_utils.st.config.get_option', side_effect=Exception()):
            theme = get_streamlit_theme()
            assert theme == "light"  # Default fallback
    
    def test_get_streamlit_theme_dark(self):
        """Test getting dark theme."""
        with patch('theme_utils.st.config.get_option', return_value="dark"):
            theme = get_streamlit_theme()
            assert theme == "dark"
    
    def test_get_streamlit_theme_light(self):
        """Test getting light theme."""
        with patch('theme_utils.st.config.get_option', return_value="light"):
            theme = get_streamlit_theme()
            assert theme == "light"
    
    def test_get_color_palette_light(self):
        """Test getting color palette for light theme."""
        palette = get_color_palette("light")
        
        assert isinstance(palette, dict)
        assert "background" in palette
        assert "text" in palette
        assert "primary" in palette
        assert "secondary" in palette
    
    def test_get_color_palette_dark(self):
        """Test getting color palette for dark theme."""
        palette = get_color_palette("dark")
        
        assert isinstance(palette, dict)
        assert "background" in palette
        assert "text" in palette
        assert "primary" in palette
        assert "secondary" in palette
        
        # Dark theme should have different colors than light
        light_palette = get_color_palette("light")
        assert palette["background"] != light_palette["background"]
        assert palette["text"] != light_palette["text"]
    
    def test_get_color_palette_invalid_theme(self):
        """Test getting color palette for invalid theme."""
        palette = get_color_palette("invalid_theme")
        
        # Should fallback to light theme
        light_palette = get_color_palette("light")
        assert palette == light_palette


def mock_open_read():
    """Helper function to mock file opening for reading."""
    return MagicMock()


# Additional helper functions for testing
def create_test_model_file(path, model_data):
    """Create a test model file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(model_data, f)