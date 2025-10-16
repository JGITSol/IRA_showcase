import streamlit as st
import plotly.express as px

import pandas as pd
import numpy as np
import time
import os

# Import custom modules
from database import Database
from utils_plotly import (
    load_model,
    plot_feature_importance,
    plot_prediction_comparison,
    plot_risk_gauge,
    predict_insurance_charges,
)

# Set page configuration
st.set_page_config(
    page_title="Insurance Risk Predictor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Arial', sans-serif;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .css-1v3fvcr {
        background-color: #f8f9fa;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize the database
db = Database()

# Define functions
def make_prediction():
    """Make a prediction based on user inputs and save to database."""
    # Load model bundle
    bundle = load_model()
    
    if bundle is None:
        st.error("Failed to load model. Please ensure the model has been trained.")
        return False
    
    # Get user inputs
    age = st.session_state.age
    gender = st.session_state.gender
    bmi = st.session_state.bmi
    children = st.session_state.children
    smoker = st.session_state.smoker
    region = st.session_state.region
    
    # Make prediction
    prediction_result = predict_insurance_charges(bundle, age, gender, bmi, children, smoker, region)
    
    if prediction_result is not None:
        predicted_charges = prediction_result["predicted_charges"]
        risk_score = prediction_result["risk_score"]
        confidence = prediction_result["confidence"]
        confidence_interval = prediction_result["confidence_interval"]

        # Update session state
        st.session_state.prediction = predicted_charges
        st.session_state.risk_score = risk_score
        st.session_state.confidence = confidence
        st.session_state.confidence_interval = confidence_interval
        st.session_state.prediction_details = prediction_result
        
        # Save prediction to database
        prediction_id = db.add_prediction(
            age,
            gender,
            bmi,
            children,
            smoker,
            region,
            predicted_charges,
            risk_score,
            confidence,
            confidence_interval.get("lower") if confidence_interval else None,
            confidence_interval.get("upper") if confidence_interval else None,
        )
        
        st.session_state.prediction_made = True
        
        # Show success message
        st.success(f"Prediction saved with ID: {prediction_id}")
        return True
    else:
        st.error("Failed to make prediction.")
        return False

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
    if 'risk_score' in df.columns:
        df['risk_score'] = df['risk_score'].apply(lambda x: f"{x:.0f}/100" if x is not None else "-")
    if 'confidence' in df.columns:
        df['confidence'] = df['confidence'].apply(lambda x: f"{x*100:.1f}%" if x is not None else "-")
    
    # Display as table with modern styling
    st.write("### Prediction History")
    st.dataframe(df, use_container_width=True)
    
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
    
    confidence_interval = {
        "lower": prediction.get('ci_lower'),
        "upper": prediction.get('ci_upper')
    }
    
    # Display prediction details in a modern card layout
    st.write("### Prediction Details")
    
    # Create a container with custom styling
    details_container = st.container()
    
    with details_container:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h4 style="color: #4CAF50;">Input Parameters</h4>
            </div>
            """, unsafe_allow_html=True)
            st.write(f"**Age:** {prediction['age']}")
            st.write(f"**Gender:** {prediction['gender']}")
            st.write(f"**BMI:** {prediction['bmi']:.2f}")
            st.write(f"**Children:** {prediction['children']}")
            st.write(f"**Smoker:** {prediction['smoker']}")
            st.write(f"**Region:** {prediction['region']}")
        
        with col2:
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h4 style="color: #4CAF50;">Prediction Result</h4>
            </div>
            """, unsafe_allow_html=True)
            st.write(f"**Predicted Charges:** ${prediction['predicted_charges']:.2f}")
            st.write(f"**Prediction Date:** {prediction['prediction_date']}")
            
            risk_score_value = prediction.get('risk_score')
            if risk_score_value is not None:
                st.write(f"**Risk Percentile:** {risk_score_value:.0f}/100")
            confidence_value = prediction.get('confidence')
            if confidence_value is not None:
                st.write(f"**Model Confidence:** {confidence_value*100:.1f}%")
            if confidence_interval['lower'] is not None and confidence_interval['upper'] is not None:
                st.write(
                    f"**Confidence Interval (95%):** ${confidence_interval['lower']:.2f} – ${confidence_interval['upper']:.2f}"
                )
    
    # Show actions for this prediction
    st.write("### Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Load this prediction for editing", key="load_btn"):
            # Set session state variables to this prediction's values
            st.session_state.age = prediction['age']
            st.session_state.gender = prediction['gender']
            st.session_state.bmi = prediction['bmi']
            st.session_state.children = prediction['children']
            st.session_state.smoker = prediction['smoker']
            st.session_state.region = prediction['region']
            
            # Switch to the prediction tab
            st.session_state.active_tab = "Predict"
            st.rerun()
    
    with col2:
        if st.button("Delete this prediction", key="delete_btn"):
            if db.delete_prediction(prediction_id):
                st.success(f"Prediction with ID {prediction_id} deleted.")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"Failed to delete prediction with ID {prediction_id}.")

def display_model_insights():
    """Display insights and visualizations about the model."""
    bundle = load_model()
    
    if bundle is None:
        st.error("Failed to load model. Please ensure the model has been trained.")
        return
    
    st.write("## Model Insights")
    
    # Feature importance
    st.write("### Feature Importance")
    st.write("This chart shows which factors have the most influence on insurance charges:")
    
    feature_imp_fig = plot_feature_importance(bundle)
    
    if feature_imp_fig:
        st.plotly_chart(feature_imp_fig, use_container_width=True)
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
        result = predict_insurance_charges(
            bundle,
            profile["age"],
            profile["gender"],
            profile["bmi"],
            profile["children"],
            profile["smoker"],
            profile["region"],
        )
        if result:
            results.append({"Profile": profile["name"], "Predicted Charges": result["predicted_charges"]})
    
    # Create a DataFrame for visualization
    results_df = pd.DataFrame(results)
    
    # Create a bar chart for profile comparisons
    fig = px.bar(
        results_df, 
        x="Profile", 
        y="Predicted Charges",
        color="Profile",
        text_auto=True,
        labels={"Predicted Charges": "Insurance Charges ($)"},
        title="Insurance Charges by Profile",
        color_discrete_sequence=px.colors.qualitative.G10
    )
    
    # Update layout for better appearance
    fig.update_layout(
        xaxis_title="Customer Profile",
        yaxis_title="Insurance Charges ($)",
        font=dict(family="Arial", size=14),
        height=500,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    # Format y-axis as currency
    fig.update_yaxes(tickprefix="$", tickformat=",.2f")
    
    # Add value labels on top of bars
    fig.update_traces(
        texttemplate="$%{y:,.2f}",
        textposition="outside"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add explanatory text
    st.markdown("""
    #### Key Insights:
    - **Smoking** has the most significant impact on insurance charges
    - **Age** is the second most important factor
    - **BMI** (especially values over 30) can significantly increase costs
    - **Number of children** has a moderate impact on insurance charges
    """, unsafe_allow_html=True)

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
    if 'confidence' not in st.session_state:
        st.session_state.confidence = None
    if 'confidence_interval' not in st.session_state:
        st.session_state.confidence_interval = None
    if 'prediction_details' not in st.session_state:
        st.session_state.prediction_details = None
    
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
    
    # Create tabs using Streamlit's native tab component
    tabs = st.tabs(["Predict", "History", "Insights"])
    
    # Predict tab
    with tabs[0]:
        # Always set active tab to Predict when this tab is selected
        st.session_state.active_tab = "Predict"
        
        # Split the tab into two sections - form and results
        # Always show the form
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
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Predicted Charges", f"${st.session_state.prediction:.2f}")
                with col2:
                    st.metric("Risk Percentile", f"{st.session_state.risk_score:.0f}/100")
                with col3:
                    if st.session_state.confidence is not None:
                        st.metric("Model Confidence", f"{st.session_state.confidence*100:.1f}%")
                    else:
                        st.metric("Model Confidence", "N/A")
                
                col_gauge, col_interval = st.columns((1, 1))
                with col_gauge:
                    risk_gauge = plot_risk_gauge(st.session_state.risk_score)
                    st.plotly_chart(risk_gauge, use_container_width=True)
                with col_interval:
                    ci = st.session_state.confidence_interval
                    if ci:
                        st.markdown(
                            f"""
                            **95% Confidence Interval**
                            
                            - Lower bound: `${ci['lower']:.2f}`
                            - Upper bound: `${ci['upper']:.2f}`
                            """
                        )
                    else:
                        st.info("Confidence interval unavailable for this prediction.")
                
                # Comparison with average
                st.markdown("---")
                st.subheader("Comparison with Average")
                
                avg_charges = 13270.42  # Example average value
                comparison_fig = plot_prediction_comparison(st.session_state.prediction, avg_charges)
                st.plotly_chart(comparison_fig, use_container_width=True)
                
                # Risk factors explanation
                st.markdown("---")
                st.subheader("Risk Factors")
                
                # Create a modern risk factor card layout
                risk_factors = []
                
                if st.session_state.smoker == "yes":
                    risk_factors.append({
                        "factor": "Smoking",
                        "impact": "High",
                        "description": "Being a smoker significantly increases your insurance risk.",
                        "icon": "🚬",
                        "color": "#FF6B6B"
                    })
                
                if st.session_state.bmi > 30:
                    risk_factors.append({
                        "factor": "BMI",
                        "impact": "Medium",
                        "description": "A BMI over 30 (considered obese) increases health risks and insurance costs.",
                        "icon": "⚖️",
                        "color": "#FFD166"
                    })
                
                if st.session_state.age > 50:
                    risk_factors.append({
                        "factor": "Age",
                        "impact": "Medium",
                        "description": "Age is a factor in insurance pricing, with older individuals typically paying more.",
                        "icon": "🗓️",
                        "color": "#06D6A0"
                    })
                
                if not risk_factors:
                    risk_factors.append({
                        "factor": "Low Risk Profile",
                        "impact": "Low",
                        "description": "Your profile shows relatively low risk factors.",
                        "icon": "✅",
                        "color": "#118AB2"
                    })
                
                # Display risk factors in a grid
                cols = st.columns(len(risk_factors))
                
                for i, factor in enumerate(risk_factors):
                    with cols[i]:
                        st.markdown(f"""
                        <div style="background-color: {factor['color']}; padding: 20px; border-radius: 10px; color: white; height: 200px;">
                            <h1 style="font-size: 2rem; margin-bottom: 10px;">{factor['icon']}</h1>
                            <h3>{factor['factor']}</h3>
                            <p><strong>Impact: {factor['impact']}</strong></p>
                            <p>{factor['description']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Action to make a new prediction
                st.markdown("")
        
        # This button needs to be outside the form
    if st.button("Make a New Prediction"):
            st.session_state.prediction_made = False
            st.rerun()
    
    # History tab
    with tabs[1]:
        if st.session_state.active_tab == "History":
            view_predictions()
        else:
            # Set active tab to History when this tab is clicked
            st.session_state.active_tab = "History"
            view_predictions()
    
    # Insights tab
    with tabs[2]:
        if st.session_state.active_tab == "Insights":
            display_model_insights()
        else:
            # Set active tab to Insights when this tab is clicked
            st.session_state.active_tab = "Insights"
            display_model_insights()

if __name__ == "__main__":
    main()