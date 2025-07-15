"""Enhanced tests for the Streamlit app with better coverage."""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock, call
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import app
from database import Database


class TestStreamlitApp:
    """Enhanced tests for the Streamlit application."""
    
    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit components."""
        with patch('app.st') as mock_st:
            # Setup session state mock
            session_state = MagicMock()
            mock_st.session_state = session_state
            
            # Setup other common mocks
            mock_st.set_page_config = Mock()
            mock_st.title = Mock()
            mock_st.write = Mock()
            mock_st.success = Mock()
            mock_st.error = Mock()
            mock_st.warning = Mock()
            mock_st.info = Mock()
            mock_st.columns = Mock(return_value=[Mock(), Mock()])
            mock_st.form = Mock()
            mock_st.form_submit_button = Mock()
            mock_st.number_input = Mock()
            mock_st.selectbox = Mock()
            mock_st.button = Mock()
            mock_st.dataframe = Mock()
            mock_st.table = Mock()
            mock_st.plotly_chart = Mock()
            mock_st.metric = Mock()
            mock_st.markdown = Mock()
            mock_st.subheader = Mock()
            mock_st.rerun = Mock()
            
            yield mock_st
    
    @pytest.fixture
    def mock_database(self):
        """Mock database."""
        with patch('app.Database') as mock_db_class:
            mock_db = Mock(spec=Database)
            mock_db_class.return_value = mock_db
            yield mock_db
    
    @pytest.fixture
    def mock_utils(self):
        """Mock utility functions."""
        mocks = {}
        with patch('app.load_model') as mock_load, \
             patch('app.predict_insurance_charges') as mock_predict, \
             patch('app.generate_risk_score') as mock_risk, \
             patch('app.plot_risk_gauge') as mock_gauge, \
             patch('app.plot_feature_importance') as mock_importance, \
             patch('app.plot_prediction_comparison') as mock_comparison:
            
            mocks['load_model'] = mock_load
            mocks['predict'] = mock_predict
            mocks['risk_score'] = mock_risk
            mocks['gauge'] = mock_gauge
            mocks['importance'] = mock_importance
            mocks['comparison'] = mock_comparison
            
            yield mocks
    
    def test_make_prediction_complete_flow(self, mock_streamlit, mock_database, mock_utils):
        """Test complete prediction flow."""
        # Setup mocks
        mock_model = Mock()
        mock_utils['load_model'].return_value = mock_model
        mock_utils['predict'].return_value = 15000.0
        mock_utils['risk_score'].return_value = 6
        mock_database.add_prediction.return_value = 123
        
        # Setup session state
        mock_streamlit.session_state.age = 35
        mock_streamlit.session_state.gender = 'female'
        mock_streamlit.session_state.bmi = 28.5
        mock_streamlit.session_state.children = 1
        mock_streamlit.session_state.smoker = 'yes'
        mock_streamlit.session_state.region = 'southwest'
        
        # Call function
        with patch('app.db', mock_database):
            app.make_prediction()
        
        # Verify calls
        mock_utils['load_model'].assert_called_once()
        mock_utils['predict'].assert_called_once_with(
            mock_model, 35, 'female', 28.5, 1, 'yes', 'southwest'
        )
        mock_utils['risk_score'].assert_called_once_with(15000.0)
        mock_database.add_prediction.assert_called_once_with(
            35, 'female', 28.5, 1, 'yes', 'southwest', 15000.0
        )
        
        # Verify session state updates
        assert mock_streamlit.session_state.prediction == 15000.0
        assert mock_streamlit.session_state.risk_score == 6
        assert mock_streamlit.session_state.prediction_made == True
        
        # Verify success message
        mock_streamlit.success.assert_called_once_with("Prediction saved with ID: 123")
    
    def test_make_prediction_model_load_failure(self, mock_streamlit, mock_utils):
        """Test prediction when model loading fails."""
        mock_utils['load_model'].return_value = None
        
        app.make_prediction()
        
        mock_streamlit.error.assert_called_once_with(
            "Failed to load model. Please ensure the model has been trained."
        )
    
    def test_make_prediction_prediction_failure(self, mock_streamlit, mock_utils):
        """Test prediction when prediction fails."""
        mock_model = Mock()
        mock_utils['load_model'].return_value = mock_model
        mock_utils['predict'].return_value = None
        
        app.make_prediction()
        
        mock_streamlit.error.assert_called_once_with("Failed to make prediction.")
    
    def test_view_predictions_empty_database(self, mock_streamlit, mock_database):
        """Test viewing predictions with empty database."""
        mock_database.get_all_predictions.return_value = []
        
        with patch('app.db', mock_database):
            app.view_predictions()
        
        mock_streamlit.info.assert_called_once_with(
            "No predictions found in the database."
        )
    
    def test_view_predictions_with_data(self, mock_streamlit, mock_database):
        """Test viewing predictions with data."""
        mock_predictions = [
            {
                'id': 1, 'age': 30, 'gender': 'male', 'bmi': 25.0,
                'children': 2, 'smoker': 'no', 'region': 'northeast',
                'predicted_charges': 10000.0, 'prediction_date': '2023-01-01'
            },
            {
                'id': 2, 'age': 40, 'gender': 'female', 'bmi': 30.0,
                'children': 1, 'smoker': 'yes', 'region': 'southwest',
                'predicted_charges': 20000.0, 'prediction_date': '2023-01-02'
            }
        ]
        mock_database.get_all_predictions.return_value = mock_predictions
        mock_streamlit.selectbox.return_value = 1
        mock_database.get_prediction_by_id.return_value = mock_predictions[0]
        
        with patch('app.db', mock_database), \
             patch('app.pd.DataFrame') as mock_df:
            
            # Mock DataFrame behavior
            mock_df_instance = Mock()
            mock_df.return_value = mock_df_instance
            mock_df_instance.__getitem__.return_value.apply.return_value = Mock()
            mock_df_instance.__getitem__.return_value.tolist.return_value = [1, 2]
            
            app.view_predictions()
        
        # Verify dataframe was created and displayed
        mock_df.assert_called_once_with(mock_predictions)
        mock_streamlit.dataframe.assert_called_once()
        mock_streamlit.selectbox.assert_called_once()
    
    def test_view_prediction_details_load_for_editing(self, mock_streamlit, mock_database):
        """Test loading prediction details for editing."""
        prediction_data = {
            'id': 1, 'age': 30, 'gender': 'male', 'bmi': 25.0,
            'children': 2, 'smoker': 'no', 'region': 'northeast',
            'predicted_charges': 10000.0, 'prediction_date': '2023-01-01'
        }
        
        mock_streamlit.button.side_effect = [True, False]  # First button clicked
        
        with patch('app.db', mock_database):
            app.view_prediction_details(1)
        
        # Verify session state was updated for editing
        assert mock_streamlit.session_state.age == prediction_data['age']
        assert mock_streamlit.session_state.gender == prediction_data['gender']
        assert mock_streamlit.session_state.bmi == prediction_data['bmi']
        assert mock_streamlit.session_state.children == prediction_data['children']
        assert mock_streamlit.session_state.smoker == prediction_data['smoker']
        assert mock_streamlit.session_state.region == prediction_data['region']
        assert mock_streamlit.session_state.active_tab == "Predict"
        
        mock_streamlit.rerun.assert_called_once()
    
    def test_view_prediction_details_delete(self, mock_streamlit, mock_database):
        """Test deleting prediction from details view."""
        mock_streamlit.button.side_effect = [False, True]  # Second button clicked
        mock_database.delete_prediction.return_value = True
        
        with patch('app.db', mock_database), \
             patch('app.time.sleep') as mock_sleep:
            
            app.view_prediction_details(1)
        
        mock_database.delete_prediction.assert_called_once_with(1)
        mock_streamlit.success.assert_called_once_with("Prediction with ID 1 deleted.")
        mock_sleep.assert_called_once_with(1)
        mock_streamlit.rerun.assert_called_once()
    
    def test_view_prediction_details_delete_failure(self, mock_streamlit, mock_database):
        """Test failed prediction deletion."""
        mock_streamlit.button.side_effect = [False, True]  # Second button clicked
        mock_database.delete_prediction.return_value = False
        
        with patch('app.db', mock_database):
            app.view_prediction_details(1)
        
        mock_streamlit.error.assert_called_once_with(
            "Failed to delete prediction with ID 1."
        )
    
    def test_display_model_insights_success(self, mock_streamlit, mock_utils):
        """Test displaying model insights successfully."""
        mock_model = Mock()
        mock_utils['load_model'].return_value = mock_model
        mock_utils['importance'].return_value = Mock()
        mock_utils['predict'].side_effect = [10000.0, 25000.0, 18000.0, 12000.0]
        
        with patch('app.pd.DataFrame') as mock_df, \
             patch('app.pd.table') as mock_table:
            
            mock_df.return_value = Mock()
            
            app.display_model_insights()
        
        # Verify model loading and visualization
        mock_utils['load_model'].assert_called_once()
        mock_utils['importance'].assert_called_once_with(mock_model)
        mock_streamlit.plotly_chart.assert_called()
        
        # Verify example predictions were made
        assert mock_utils['predict'].call_count == 4
        mock_streamlit.table.assert_called_once()
    
    def test_display_model_insights_no_model(self, mock_streamlit, mock_utils):
        """Test displaying insights when model is not available."""
        mock_utils['load_model'].return_value = None
        
        app.display_model_insights()
        
        mock_streamlit.error.assert_called_once_with(
            "Failed to load model. Please ensure the model has been trained."
        )
    
    def test_display_model_insights_no_feature_importance(self, mock_streamlit, mock_utils):
        """Test displaying insights when feature importance is not available."""
        mock_model = Mock()
        mock_utils['load_model'].return_value = mock_model
        mock_utils['importance'].return_value = None
        mock_utils['predict'].side_effect = [10000.0, 25000.0, 18000.0, 12000.0]
        
        app.display_model_insights()
        
        mock_streamlit.warning.assert_called_once_with(
            "Feature importance visualization is not available for this model."
        )
    
    def test_main_function_initialization(self, mock_streamlit):
        """Test main function initialization."""
        with patch('app.Database') as mock_db_class:
            # Reset session state to test initialization
            mock_streamlit.session_state = {}
            
            app.main()
            
            # Verify page configuration
            mock_streamlit.set_page_config.assert_called_once()
            
            # Verify database initialization
            mock_db_class.assert_called_once()
            
            # Verify session state initialization
            assert 'active_tab' in mock_streamlit.session_state
            assert 'prediction_made' in mock_streamlit.session_state
            assert 'age' in mock_streamlit.session_state
            assert 'gender' in mock_streamlit.session_state
            assert 'bmi' in mock_streamlit.session_state
            assert 'children' in mock_streamlit.session_state
            assert 'smoker' in mock_streamlit.session_state
            assert 'region' in mock_streamlit.session_state
    
    def test_main_function_tab_navigation(self, mock_streamlit):
        """Test tab navigation in main function."""
        with patch('app.Database'), \
             patch('app.view_predictions') as mock_view, \
             patch('app.display_model_insights') as mock_insights:
            
            # Test History tab
            mock_streamlit.session_state.active_tab = "History"
            mock_streamlit.button.side_effect = [False, True, False]  # History button clicked
            
            app.main()
            
            mock_view.assert_called_once()
            
            # Reset mocks
            mock_view.reset_mock()
            mock_insights.reset_mock()
            
            # Test Insights tab
            mock_streamlit.session_state.active_tab = "Insights"
            mock_streamlit.button.side_effect = [False, False, True]  # Insights button clicked
            
            app.main()
            
            mock_insights.assert_called_once()
    
    def test_main_function_prediction_display(self, mock_streamlit, mock_utils):
        """Test prediction results display in main function."""
        with patch('app.Database'):
            # Setup prediction made state
            mock_streamlit.session_state.active_tab = "Predict"
            mock_streamlit.session_state.prediction_made = True
            mock_streamlit.session_state.prediction = 15000.0
            mock_streamlit.session_state.risk_score = 6
            mock_streamlit.session_state.smoker = 'yes'
            mock_streamlit.session_state.bmi = 32.0
            mock_streamlit.session_state.age = 55
            
            # Mock visualization functions
            mock_utils['gauge'].return_value = Mock()
            mock_utils['comparison'].return_value = Mock()
            
            app.main()
            
            # Verify metrics are displayed
            mock_streamlit.metric.assert_any_call("Predicted Insurance Charges", "$15000.00")
            mock_streamlit.metric.assert_any_call("Risk Score", "6/10")
            
            # Verify visualizations are displayed
            mock_streamlit.plotly_chart.assert_called()
            
            # Verify risk factor warnings
            mock_streamlit.warning.assert_any_call(
                "Being a smoker significantly increases your insurance risk."
            )
            mock_streamlit.warning.assert_any_call(
                "A BMI over 30 (considered obese) increases health risks and insurance costs."
            )
            mock_streamlit.info.assert_called_with(
                "Age is a factor in insurance pricing, with older individuals typically paying more."
            )
    
    def test_main_function_new_prediction_button(self, mock_streamlit):
        """Test new prediction button functionality."""
        with patch('app.Database'):
            # Setup prediction made state
            mock_streamlit.session_state.active_tab = "Predict"
            mock_streamlit.session_state.prediction_made = True
            mock_streamlit.button.return_value = True  # New prediction button clicked
            
            app.main()
            
            # Verify state is reset
            assert mock_streamlit.session_state.prediction_made == False
            mock_streamlit.rerun.assert_called_once()