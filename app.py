import streamlit as st
import pandas as pd
import numpy as np
import time
import os

# Import custom modules
from database import Database
from utils import (
    load_model, predict_insurance_charges, generate_risk_score,
    plot_risk_gauge, plot_feature_importance, plot_prediction_comparison
)

# Set page configuration
st.set_page_config(
    page_title="Insurance Risk Predictor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize the database
db = Database()

# Define functions
def make_prediction():
    """Make a prediction based on user inputs and save to database."""
    # Load model
    model = load_model()
    
    if model is None:
        st.error("Failed to load model. Please ensure the model has been trained.")
        return
    
    # Get user inputs
    age = st.session_state.age
    gender = st.session_state.gender
    bmi = st.session_state.bmi
    children = st.session_state.children
    smoker = st.session_state.smoker
    region = st.session_state.region
    
    # Make prediction
    prediction = predict_insurance_charges(model, age, gender, bmi, children, smoker, region)
    
    if prediction is not None:
        # Calculate risk score
        risk_score = generate_risk_score(prediction)
        
        # Update session state
        st.session_state.prediction = prediction
        st.session_state.risk_score = risk_score
        
        # Save prediction to database
        prediction_id = db.add_prediction(age, gender, bmi, children, smoker, region, prediction)
        
        st.session_state.prediction_made = True
        
        # Show success message
        st.success(f"Prediction saved with ID: {prediction_id}")
    else:
        st.error("Failed to make prediction.")

def view_predictions():
    """View all saved predictions."""
    predictions = db.get_all_predictions()
    
    if not predictions:
        st.info("No predictions found in the database.")
        return
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(predictions)
    
    # Format currency values
    df['predicted_charges'] = df['predicted_charges'].apply(lambda x: f"${x:.2f}")
    
    # Display as table
    st.dataframe(df)
    
    # Allow user to select a prediction to view details
    prediction_ids = df['id'].tolist()
    selected_id = st.selectbox("Select a prediction to view details:", prediction_ids)
    
    if selected_id:
        view_prediction_details(selected_id)

def view_prediction_details(prediction_id):
    """View details of a specific prediction."""
    prediction = db.get_prediction_by_id(prediction_id)
    
    if not prediction:
        st.error(f"Prediction with ID {prediction_id} not found.")
        return
    
    # Display prediction details
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Input Parameters")
        st.write(f"**Age:** {prediction['age']}")
        st.write(f"**Gender:** {prediction['gender']}")
        st.write(f"**BMI:** {prediction['bmi']:.2f}")
        st.write(f"**Children:** {prediction['children']}")
        st.write(f"**Smoker:** {prediction['smoker']}")
        st.write(f"**Region:** {prediction['region']}")
    
    with col2:
        st.subheader("Prediction Result")
        st.write(f"**Predicted Charges:** ${prediction['predicted_charges']:.2f}")
        st.write(f"**Prediction Date:** {prediction['prediction_date']}")
    
    # Show actions for this prediction
    st.subheader("Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Load this prediction for editing"):
            # Set session state variables to this prediction's values
            st.session_state.age = prediction['age']
            st.session_state.gender = prediction['gender']
            st.session_state.bmi = prediction['bmi']
            st.session_state.children = prediction['children']
            st.session_state.smoker = prediction['smoker']
            st.session_state.region = prediction['region']
            
            # Switch to the prediction tab
            st.session_state.active_tab = "Predict"
            st.experimental_rerun()
    
    with col2:
        if st.button("Delete this prediction"):
            if db.delete_prediction(prediction_id):
                st.success(f"Prediction with ID {prediction_id} deleted.")
                time.sleep(1)
                st.experimental_rerun()
            else:
                st.error(f"Failed to delete prediction with ID {prediction_id}.")

def display_model_insights():
    """Display insights and visualizations about the model."""
    model = load_model()
    
    if model is None:
        st.error("Failed to load model. Please ensure the model has been trained.")
        return
    
    st.subheader("Model Insights")
    
    # Feature importance
    st.write("### Feature Importance")
    st.write("This chart shows which factors have the most influence on insurance charges:")
    
    feature_imp_fig = plot_feature_importance(model)
    
    if feature_imp_fig:
        st.pyplot(feature_imp_fig)
    else:
        st.warning("Feature importance visualization is not available for this model.")
    
    # Example predictions
    st.write("### Example Predictions")
    st.write("See how different profiles affect insurance charges:")
    
    # Create example profiles
    profiles = [
        {"name": "Young Non-Smoker", "age": 25, "gender": "male", "bmi": 22, "children": 0, "smoker": "no", "region": "northeast"},
        {"name": "Young Smoker", "age": 25, "gender": "male", "bmi": 22, "children": 0, "smoker": "yes", "region": "northeast"},
        {"name": "Middle-Aged Family", "age": 45, "gender": "female", "bmi": 28, "children": 2, "smoker": "no", "region": "southeast"},
        {"name": "Senior Citizen", "age": 65, "gender": "male", "bmi": 30, "children": 0, "smoker": "no", "region": "southwest"}
    ]
    
    # Make predictions for each profile
    results = []
    for profile in profiles:
        pred = predict_insurance_charges(
            model, profile["age"], profile["gender"], profile["bmi"], 
            profile["children"], profile["smoker"], profile["region"]
        )
        results.append({"Profile": profile["name"], "Predicted Charges": f"${pred:.2f}"})
    
    # Display as table
    st.table(pd.DataFrame(results))

# Main app layout
def main():
    # Add logo or header
    st.title("Insurance Risk Predictor")
    st.write("Predict insurance charges and assess risk factors")
    
    # Initialize session state variables if they don't exist
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Predict"
    
    if 'prediction_made' not in st.session_state:
        st.session_state.prediction_made = False
    
    if 'prediction' not in st.session_state:
        st.session_state.prediction = None
    
    if 'risk_score' not in st.session_state:
        st.session_state.risk_score = None
    
    # Input form default values
    if 'age' not in st.session_state:
        st.session_state.age = 30
    
    if 'gender' not in st.session_state:
        st.session_state.gender = "male"
    
    if 'bmi' not in st.session_state:
        st.session_state.bmi = 25.0
    
    if 'children' not in st.session_state:
        st.session_state.children = 0
    
    if 'smoker' not in st.session_state:
        st.session_state.smoker = "no"
    
    if 'region' not in st.session_state:
        st.session_state.region = "northeast"
    
    # Create tabs
    tabs = ["Predict", "History", "Insights"]
    
    # Display tabs and set active tab
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Predict", use_container_width=True):
            st.session_state.active_tab = "Predict"
    
    with col2:
        if st.button("History", use_container_width=True):
            st.session_state.active_tab = "History"
    
    with col3:
        if st.button("Insights", use_container_width=True):
            st.session_state.active_tab = "Insights"
    
    st.markdown(f"**Current Tab:** {st.session_state.active_tab}")
    st.markdown("---")
    
    # Display content based on active tab
    if st.session_state.active_tab == "Predict":
        # Create a form for user inputs
        with st.form("prediction_form"):
            st.subheader("Enter Your Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.number_input("Age", min_value=18, max_value=100, value=st.session_state.age, key="age")
                st.selectbox("Gender", options=["male", "female"], index=0 if st.session_state.gender == "male" else 1, key="gender")
                st.number_input("BMI", min_value=10.0, max_value=50.0, value=st.session_state.bmi, step=0.1, key="bmi")
            
            with col2:
                st.number_input("Number of Children", min_value=0, max_value=10, value=st.session_state.children, key="children")
                st.selectbox("Smoker", options=["yes", "no"], index=0 if st.session_state.smoker == "yes" else 1, key="smoker")
                st.selectbox("Region", options=["northeast", "northwest", "southeast", "southwest"], 
                             index=["northeast", "northwest", "southeast", "southwest"].index(st.session_state.region), key="region")
            
            # Submit button
            submitted = st.form_submit_button("Calculate Risk")
            
            if submitted:
                make_prediction()
        
        # Display prediction results if available
        if st.session_state.prediction_made:
            st.markdown("---")
            st.subheader("Prediction Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Predicted Insurance Charges", f"${st.session_state.prediction:.2f}")
                st.metric("Risk Score", f"{st.session_state.risk_score}/10")
            
            with col2:
                # Risk gauge visualization
                risk_gauge = plot_risk_gauge(st.session_state.risk_score)
                st.pyplot(risk_gauge)
            
            # Comparison with average
            st.markdown("---")
            st.subheader("Comparison with Average")
            
            avg_charges = 13270.42  # Example average value
            comparison_fig = plot_prediction_comparison(st.session_state.prediction, avg_charges)
            st.pyplot(comparison_fig)
            
            # Risk factors explanation
            st.markdown("---")
            st.subheader("Risk Factors")
            
            # Simplified risk factor explanation
            if st.session_state.smoker == "yes":
                st.warning("Being a smoker significantly increases your insurance risk.")
            
            if st.session_state.bmi > 30:
                st.warning("A BMI over 30 (considered obese) increases health risks and insurance costs.")
            
            if st.session_state.age > 50:
                st.info("Age is a factor in insurance pricing, with older individuals typically paying more.")
            
            # Action to make a new prediction
            if st.button("Make a New Prediction"):
                st.session_state.prediction_made = False
                st.rerun()
    
    elif st.session_state.active_tab == "History":
        view_predictions()
    
    elif st.session_state.active_tab == "Insights":
        display_model_insights()

if __name__ == "__main__":
    main()