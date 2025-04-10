import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the module to test
import utils_plotly
from theme_utils import get_streamlit_theme, get_color_palette

class TestUtilsPlotly(unittest.TestCase):
    """Test cases for the utils_plotly module."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock theme utils
        self.theme_mock = patch('utils_plotly.get_streamlit_theme').start()
        self.palette_mock = patch('utils_plotly.get_color_palette').start()
        self.color_mock = patch('utils_plotly.get_color').start()
        
        # Set up mock palette
        self.mock_palette = {
            'text': '#000000',
            'text_secondary': '#666666',
            'surface': '#FFFFFF',
            'gauge_low': '#00FF00',
            'gauge_medium': '#FFFF00',
            'gauge_high': '#FF0000',
            'plot_bg': '#F0F0F0',
            'grid': '#CCCCCC',
            'importance_scale': 'Viridis',
            'comparison_default': '#4CAF50',
            'comparison_good': '#2196F3',
            'comparison_bad': '#F44336'
        }
        self.palette_mock.return_value = self.mock_palette
    
    def tearDown(self):
        """Clean up after tests."""
        patch.stopall()
    
    def test_plot_risk_gauge_low_risk(self):
        """Test risk gauge creation with low risk score."""
        # Mock color function
        self.color_mock.return_value = '#00FF00'
        
        # Create gauge plot
        fig = utils_plotly.plot_risk_gauge(2)
        
        # Verify figure was created
        self.assertIsInstance(fig, go.Figure)
        
        # Verify gauge properties
        gauge_data = fig.data[0]
        self.assertEqual(gauge_data.mode, 'gauge+number')
        self.assertEqual(gauge_data.value, 2)
        self.assertEqual(gauge_data.gauge.bar.color, '#00FF00')
    
    def test_plot_risk_gauge_high_risk(self):
        """Test risk gauge creation with high risk score."""
        # Mock color function
        self.color_mock.return_value = '#FF0000'
        
        # Create gauge plot
        fig = utils_plotly.plot_risk_gauge(9)
        
        # Verify figure was created
        self.assertIsInstance(fig, go.Figure)
        
        # Verify gauge properties
        gauge_data = fig.data[0]
        self.assertEqual(gauge_data.mode, 'gauge+number')
        self.assertEqual(gauge_data.value, 9)
        self.assertEqual(gauge_data.gauge.bar.color, '#FF0000')
    
    def test_plot_feature_importance(self):
        """Test feature importance plot creation."""
        # Create mock model
        model = MagicMock()
        model.named_steps = {
            'preprocessor': MagicMock(),
            'regressor': MagicMock()
        }
        
        # Mock preprocessor
        preprocessor = model.named_steps['preprocessor']
        preprocessor.named_transformers_ = {
            'cat': MagicMock()
        }
        cat_encoder = preprocessor.named_transformers_['cat']
        cat_encoder.categories_ = [
            ['male', 'female'],
            ['no', 'yes'],
            ['northeast', 'northwest', 'southeast', 'southwest']
        ]
        
        # Mock regressor
        regressor = model.named_steps['regressor']
        regressor.feature_importances_ = np.array([0.3, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1])
        
        # Mock plotly express
        with patch('utils_plotly.px') as px_mock:
            # Create a mock figure
            mock_fig = go.Figure()
            mock_fig.update_layout(
                title={'text': 'Feature Importance', 'x': 0.5, 'xanchor': 'center'},
                xaxis_title='Importance Score',
                yaxis_title='Feature'
            )
            px_mock.bar.return_value = mock_fig
            # Mock sequential colors to be subscriptable
            sequential_mock = MagicMock()
            sequential_mock.__getitem__ = lambda _, key: ['#440154', '#208F8C', '#FDE725']
            px_mock.colors.sequential = sequential_mock
            
            # Create feature importance plot
            fig = utils_plotly.plot_feature_importance(model)
            
            # Verify figure was created
            self.assertIsInstance(fig, go.Figure)
            
            # Verify plot properties
            self.assertEqual(fig.layout.title.text, 'Feature Importance')
            self.assertEqual(fig.layout.xaxis.title.text, 'Importance Score')
            self.assertEqual(fig.layout.yaxis.title.text, 'Feature')
    
    def test_plot_prediction_comparison(self):
        """Test prediction comparison plot creation."""
        # Create comparison plot
        fig = utils_plotly.plot_prediction_comparison(15000, 10000)
        
        # Verify figure was created
        self.assertIsInstance(fig, go.Figure)
        
        # Verify plot data
        bar_data = fig.data[0]
        self.assertEqual(list(bar_data.x), ['Your Prediction', 'Average Charges'])
        self.assertEqual(list(bar_data.y), [15000, 10000])
        
        # Verify plot properties
        self.assertEqual(fig.layout.title.text, 'Prediction vs. Average Charges')
        self.assertEqual(fig.layout.yaxis.title.text, 'Insurance Charges ($)')