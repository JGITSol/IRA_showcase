import unittest
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import (
    load_model, predict_insurance_charges, generate_risk_score,
    plot_risk_gauge, plot_feature_importance, plot_prediction_comparison
)

class TestUtils(unittest.TestCase):
    """Test cases for the utils module."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock model for testing
        self.mock_model = MockModel()
    
    def test_generate_risk_score(self):
        """Test risk score generation."""
        # Test minimum score
        min_score = generate_risk_score(1000, max_charge=50000)
        self.assertEqual(min_score, 1)
        
        # Test maximum score
        max_score = generate_risk_score(60000, max_charge=50000)
        self.assertEqual(max_score, 10)
        
        # Test middle score
        mid_score = generate_risk_score(25000, max_charge=50000)
        self.assertEqual(mid_score, 5)
    
    def test_predict_insurance_charges(self):
        """Test insurance charge prediction."""
        # Test with mock model
        prediction = predict_insurance_charges(
            self.mock_model, 30, 'male', 25.0, 2, 'no', 'northeast'
        )
        
        # Check if prediction is a number
        self.assertIsInstance(prediction, (int, float))
        
        # Test with None model
        prediction = predict_insurance_charges(None, 30, 'male', 25.0, 2, 'no', 'northeast')
        self.assertIsNone(prediction)
    
    def test_plot_risk_gauge(self):
        """Test risk gauge plot generation."""
        # Test with various risk scores
        for score in [1, 5, 10]:
            fig = plot_risk_gauge(score)
            self.assertIsInstance(fig, plt.Figure)
            plt.close(fig)  # Close to avoid memory leaks
    
    def test_plot_prediction_comparison(self):
        """Test prediction comparison plot generation."""
        fig = plot_prediction_comparison(15000, 10000)
        self.assertIsInstance(fig, plt.Figure)
        plt.close(fig)  # Close to avoid memory leaks

# Mock model class for testing
class MockModel:
    """A mock model class for testing."""
    
    def predict(self, X):
        """Return a fixed prediction value for testing."""
        # Simple logic to return different values based on input
        if X['smoker'].iloc[0] == 'yes':
            return np.array([20000.0])
        else:
            return np.array([10000.0])
    
    @property
    def named_steps(self):
        return {
            'regressor': MockRegressor(),
            'preprocessor': MockPreprocessor()
        }

class MockRegressor:
    """A mock regressor for testing."""
    
    @property
    def feature_importances_(self):
        return np.array([0.3, 0.2, 0.1, 0.2, 0.1, 0.1])

class MockPreprocessor:
    """A mock preprocessor for testing."""
    
    @property
    def named_transformers_(self):
        return {
            'cat': MockEncoder()
        }

class MockEncoder:
    """A mock encoder for testing."""
    
    @property
    def categories_(self):
        return [
            np.array(['male', 'female']),
            np.array(['no', 'yes']),
            np.array(['northeast', 'northwest', 'southeast', 'southwest'])
        ]

if __name__ == '__main__':
    unittest.main()