"""Basic functionality tests."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestBasicFunctionality:
    """Test basic application functionality."""
    
    def test_imports(self):
        """Test that basic imports work."""
        # Test basic libraries
        import pandas as pd
        import numpy as np
        import plotly.graph_objects as go
        
        # Test custom modules
        from database import Database
        from utils_plotly import load_model, predict_insurance_charges
        from theme_utils import get_streamlit_theme, get_color_palette
        
        assert pd is not None
        assert np is not None
        assert go is not None
    
    def test_database_creation(self, temp_db_path):
        """Test database creation and basic operations."""
        from database import Database
        
        db_name = Path(temp_db_path).name
        db = Database(db_name=db_name)
        
        # Test adding a prediction
        pred_id = db.add_prediction(
            age=30, gender='male', bmi=25.0, children=2,
            smoker='no', region='northeast', predicted_charges=10000.0
        )
        
        assert pred_id is not None
        assert pred_id > 0
        
        # Test retrieving the prediction
        prediction = db.get_prediction_by_id(pred_id)
        assert prediction is not None
        assert prediction['age'] == 30
        assert prediction['gender'] == 'male'
        
        db.close()
    
    def test_model_loading(self):
        """Test model loading functionality."""
        from utils_plotly import load_model
        
        # Test with existing model
        model = load_model()
        assert model is not None
    
    def test_prediction_functionality(self, mock_model):
        """Test prediction functionality."""
        from utils_plotly import predict_insurance_charges, generate_risk_score
        
        # Test prediction
        prediction = predict_insurance_charges(
            mock_model, age=30, gender='male', bmi=25.0,
            children=2, smoker='no', region='northeast'
        )
        
        assert prediction is not None
        assert isinstance(prediction, (int, float))
        assert prediction > 0
        
        # Test risk score generation
        risk_score = generate_risk_score(prediction)
        assert isinstance(risk_score, int)
        assert 1 <= risk_score <= 10
    
    def test_visualization_creation(self):
        """Test visualization creation."""
        from utils_plotly import plot_risk_gauge, plot_prediction_comparison
        
        # Test risk gauge
        fig = plot_risk_gauge(5)
        assert fig is not None
        
        # Test prediction comparison
        fig = plot_prediction_comparison(15000, 12000)
        assert fig is not None
    
    def test_theme_utilities(self):
        """Test theme utilities."""
        from theme_utils import get_streamlit_theme, get_color_palette
        
        # Test theme detection
        theme = get_streamlit_theme()
        assert theme in ['light', 'dark']
        
        # Test color palette
        palette = get_color_palette()
        assert isinstance(palette, dict)
        assert 'primary' in palette
        assert 'background' in palette
        assert 'text' in palette
    
    def test_utils_error_handling(self):
        """Test error handling in utilities."""
        from utils_plotly import predict_insurance_charges
        
        # Test with None model
        result = predict_insurance_charges(
            None, age=30, gender='male', bmi=25.0,
            children=2, smoker='no', region='northeast'
        )
        assert result is None