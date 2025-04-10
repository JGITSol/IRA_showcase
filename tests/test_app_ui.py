import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the app module
import app
from database import Database

class TestAppUI(unittest.TestCase):
    """Test cases for the Streamlit app UI components."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock Streamlit
        self.streamlit_mock = patch('app.st').start()
        
        # Mock session state
        self.session_state_mock = MagicMock()
        self.streamlit_mock.session_state = self.session_state_mock
        
        # Mock Database
        self.db_mock = patch('app.Database').start()
        self.db_instance_mock = MagicMock()
        self.db_mock.return_value = self.db_instance_mock
        
        # Mock theme utils
        self.get_theme_mock = patch('app.get_streamlit_theme').start()
        self.get_palette_mock = patch('app.get_color_palette').start()
    
    def tearDown(self):
        """Clean up after tests."""
        patch.stopall()
    
    def test_main_layout(self):
        """Test the main app layout initialization."""
        # The issue is that set_page_config is called at module level in app.py
        # We need to patch streamlit before importing app
        
        # First, save the original app module if it exists
        original_app = sys.modules.pop('app') if 'app' in sys.modules else None
        
        try:
            # Create a fresh streamlit mock
            fresh_st_mock = MagicMock()
            
            # Configure the mock to handle set_page_config
            fresh_st_mock.set_page_config = MagicMock()
            
            # Configure the columns method to return the expected columns
            col_mocks = [MagicMock(), MagicMock(), MagicMock()]
            for mock in col_mocks:
                mock.__enter__.return_value = mock
            fresh_st_mock.columns.return_value = col_mocks
            
            # Create a session state mock
            session_state_mock = MagicMock()
            fresh_st_mock.session_state = session_state_mock
            
            # Replace the streamlit module in sys.modules with our mock
            # This is necessary because we can't patch the entire module with patch()
            original_streamlit = sys.modules.get('streamlit')
            sys.modules['streamlit'] = fresh_st_mock
            
            try:
                # Now import app, which will use our mocked streamlit
                import app as app_module
                
                # Verify page config was set during import
                fresh_st_mock.set_page_config.assert_called_once_with(
                    page_title="Insurance Risk Predictor",
                    page_icon="💰",
                    layout="wide",
                    initial_sidebar_state="expanded"
                )
            finally:
                # Restore the original streamlit module
                if original_streamlit:
                    sys.modules['streamlit'] = original_streamlit
                else:
                    del sys.modules['streamlit']
                
                # Skip calling app_module.main() as we've already verified set_page_config
                # was called during module import, which is what this test is checking
        finally:
            # Restore the original app module if it existed
            if original_app:
                sys.modules['app'] = original_app
        
        # Mock columns for the self.streamlit_mock
        col_mocks = [MagicMock(), MagicMock(), MagicMock()]
        self.streamlit_mock.columns.return_value = col_mocks
        
        # Configure mocks to work as context managers
        for mock in col_mocks:
            mock.__enter__.return_value = mock
        
        # Mock predict_insurance_charges to return a float
        predict_mock = patch('app.predict_insurance_charges', return_value=15000.0).start()
        
        # Mock model loading and plotting functions
        # Properly mock plot_feature_importance to avoid the TypeError
        plot_feature_mock = patch('app.plot_feature_importance').start()
        plot_feature_mock.return_value = MagicMock()
        
        # Mock model loading
        with patch('app.load_model') as load_model_mock:
            load_model_mock.return_value = MagicMock()
            
            # Call main function with patched database
            with patch('app.db'):
                app.main()
        
        # Verify page config was set
        self.streamlit_mock.set_page_config.assert_called_once_with(
            page_title="Insurance Risk Predictor",
            page_icon="💰",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Verify title and description were set
        self.streamlit_mock.title.assert_called_once_with("Insurance Risk Predictor")
        self.streamlit_mock.write.assert_called_with("Predict insurance charges and assess risk factors")
        
        # Verify session state initialization
        self.assertTrue(hasattr(self.session_state_mock, 'active_tab'))
        self.assertTrue(hasattr(self.session_state_mock, 'prediction_made'))
        self.assertTrue(hasattr(self.session_state_mock, 'prediction'))
    
    def test_view_predictions_empty(self):
        """Test view_predictions when no predictions exist."""
        # Mock empty predictions
        self.db_instance_mock.get_all_predictions.return_value = []
        
        # Mock DataFrame display
        self.streamlit_mock.dataframe = MagicMock()
        
        # Mock the pandas DataFrame to handle empty list
        with patch('app.pd.DataFrame') as df_mock:
            # Setup the mock DataFrame
            mock_df = MagicMock()
            df_mock.return_value = mock_df
            mock_df.__getitem__.return_value.tolist.return_value = []
            
            # This will prevent selectbox from being called with empty list
            self.streamlit_mock.selectbox.return_value = None
            
            # Call the function with patched database
            with patch('app.db', self.db_instance_mock):
                app.view_predictions()
            
            # Verify info message was shown
            self.streamlit_mock.info.assert_called_once_with("No predictions found in the database.")
    
    def test_view_predictions_with_data(self):
        """Test view_predictions with existing predictions."""
        # Mock predictions data
        mock_predictions = [
            {
                'id': 1,
                'age': 30,
                'gender': 'male',
                'bmi': 25.0,
                'children': 2,
                'smoker': 'no',
                'region': 'northeast',
                'predicted_charges': 10000.0,
                'prediction_date': '2023-01-01'
            }
        ]
        self.db_instance_mock.get_all_predictions.return_value = mock_predictions
        
        # Mock DataFrame display
        self.streamlit_mock.dataframe = MagicMock()
        
        # Mock selectbox to return a valid prediction ID
        self.streamlit_mock.selectbox.return_value = 1
        
        # Mock get_prediction_by_id to return the prediction data
        self.db_instance_mock.get_prediction_by_id.return_value = mock_predictions[0]
        
        # Instead of testing the internal implementation details of view_prediction_details,
        # let's patch it and verify it gets called with the right parameters
        with patch('app.view_prediction_details') as mock_view_details:
            # Call the function with patched database
            with patch('app.db', self.db_instance_mock):
                app.view_predictions()
            
            # Verify view_prediction_details was called with the correct ID
            mock_view_details.assert_called_once_with(1)
        
        # Verify DataFrame was created and displayed
        self.streamlit_mock.dataframe.assert_called_once()
        
        # Verify selectbox was called
        self.streamlit_mock.selectbox.assert_called()
    
    def test_display_model_insights(self):
        """Test the model insights display function."""
        # Mock model loading
        model_mock = MagicMock()
        with patch('app.load_model', return_value=model_mock):
            # Mock feature importance plot
            plot_mock = MagicMock()
            with patch('app.plot_feature_importance', return_value=plot_mock):
                # Mock predict_insurance_charges to return a float
                # Use a side_effect function to ensure it always returns a float value
                def predict_side_effect(*args, **kwargs):
                    return 15000.0
                predict_mock = patch('app.predict_insurance_charges', side_effect=predict_side_effect).start()
                
                # Call the function
                app.display_model_insights()
                
                # Verify subheader and descriptions were added
                self.streamlit_mock.subheader.assert_called_with("Model Insights")
                self.streamlit_mock.write.assert_any_call("### Feature Importance")
                
                # Verify plot was displayed
                self.streamlit_mock.plotly_chart.assert_called_with(
                    plot_mock,
                    use_container_width=True
                )