import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import pickle
import os
from plotly.subplots import make_subplots

def load_model():
    """Load the trained model."""
    model_path = 'models/insurance_model.pkl'
    
    if not os.path.exists(model_path):
        st.error("Model file not found. Please train the model first.")
        return None
    
    with open(model_path, 'rb') as file:
        model = pickle.load(file)
    
    return model

def predict_insurance_charges(model, age, gender, bmi, children, smoker, region):
    """Make a prediction using the trained model."""
    if model is None:
        return None
    
    # Create a DataFrame with the input data
    input_data = pd.DataFrame({
        'age': [age],
        'gender': [gender],
        'bmi': [bmi],
        'children': [children],
        'smoker': [smoker],
        'region': [region]
    })
    
    # Make prediction
    prediction = model.predict(input_data)[0]
    
    return prediction

def generate_risk_score(prediction, max_charge=50000):
    """Generate a risk score from 1-10 based on the predicted charges."""
    # Normalize the prediction to a score between 1 and 10
    score = min(10, max(1, round((prediction / max_charge) * 10)))
    return score

def plot_risk_gauge(risk_score):
    """Create an interactive gauge chart to visualize risk score using Plotly."""
    # Define color scale based on risk score
    if risk_score <= 3:
        color = "#00CC00"  # Brighter green
    elif risk_score <= 7:
        color = "#FFA500"  # Brighter orange
    else:
        color = "#FF3333"  # Brighter red
    
    # Create gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Risk Score", 'font': {'size': 24, 'color': '#333333'}},
        number={'font': {'size': 40, 'color': color, 'weight': 'bold'}},
        gauge={
            'axis': {'range': [0, 10], 'tickwidth': 2, 'tickcolor': "#333333", 'tickfont': {'size': 14}},
            'bar': {'color': color, 'thickness': 0.8},
            'bgcolor': "#F8F9FA",
            'borderwidth': 2,
            'bordercolor': "#666666",
            'steps': [
                {'range': [0, 3], 'color': "rgba(0, 204, 0, 0.4)"},
                {'range': [3, 7], 'color': "rgba(255, 165, 0, 0.4)"},
                {'range': [7, 10], 'color': "rgba(255, 51, 51, 0.4)"}
            ],
            'threshold': {
                'line': {'color': "#333333", 'width': 4},
                'thickness': 0.8,
                'value': risk_score
            }
        }
    ))
    
    # Update layout for better appearance
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",  # Transparent background to work with any theme
        font={'color': "#333333", 'family': "Arial"},
        plot_bgcolor="rgba(0,0,0,0)"
    )
    
    return fig

def plot_feature_importance(model):
    """Plot feature importance for the model using Plotly."""
    if not hasattr(model, 'named_steps'):
        return None
    
    if 'regressor' not in model.named_steps:
        return None
    
    regressor = model.named_steps['regressor']
    
    if not hasattr(regressor, 'feature_importances_'):
        return None
    
    # Get feature names after preprocessing
    preprocessor = model.named_steps['preprocessor']
    categorical_features = ['gender', 'smoker', 'region']
    numerical_features = ['age', 'bmi', 'children']
    
    # Get the one-hot encoded feature names
    cat_encoder = preprocessor.named_transformers_['cat']
    encoded_features = []
    
    for i, feature in enumerate(categorical_features):
        categories = cat_encoder.categories_[i][1:]  # Skip the first category (dropped)
        encoded_features.extend([f"{feature}_{category}" for category in categories])
    
    feature_names = numerical_features + encoded_features
    
    # Get feature importances
    importances = regressor.feature_importances_
    
    # Sort features by importance
    indices = np.argsort(importances)[::-1]
    
    # Create DataFrame for plotting
    importance_df = pd.DataFrame({
        'Feature': [feature_names[i] for i in indices],
        'Importance': importances[indices]
    })
    
    # Create color scale based on importance
    colors = px.colors.sequential.Plasma  # Better contrast color scale
    
    # Plot with Plotly
    fig = px.bar(
        importance_df,
        x='Importance',
        y='Feature',
        orientation='h',
        color='Importance',
        color_continuous_scale=colors,
        title='Feature Importance'
    )
    
    # Update layout for better appearance
    fig.update_layout(
        height=500,
        xaxis_title="Importance Score",
        yaxis_title="Feature",
        font=dict(family="Arial", size=14, color="#333333"),
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",  # Transparent background
        plot_bgcolor="rgba(240, 240, 240, 0.7)",  # More opaque for better visibility
        title={
            'text': 'Feature Importance',
            'font': {'size': 20, 'color': '#333333'},
            'x': 0.5,
            'xanchor': 'center'
        }
    )
    
    # Add grid lines for better readability
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128, 128, 128, 0.5)', title_font={'color': '#333333'}, tickfont={'color': '#333333'})
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128, 128, 128, 0.5)', title_font={'color': '#333333'}, tickfont={'color': '#333333'})
    
    return fig

def plot_prediction_comparison(prediction, avg_charges):
    """Plot the prediction compared to average charges using Plotly."""
    # Create data for plotting
    categories = ['Your Prediction', 'Average Charges']
    values = [prediction, avg_charges]
    
    # Determine colors based on values with better contrast
    colors = ['#4285F4', '#34A853']  # Brighter blue and green
    if prediction > avg_charges:
        colors[0] = '#EA4335'  # Brighter red for higher than average
    
    # Create bar chart
    fig = go.Figure()
    
    # Add bars
    fig.add_trace(go.Bar(
        x=categories,
        y=values,
        text=[f'${v:,.2f}' for v in values],
        textposition='auto',
        marker_color=colors,
        hoverinfo='y+text',
        hovertemplate='%{y:$,.2f}<extra></extra>'
    ))
    
    # Add a line for the average
    fig.add_shape(
        type="line",
        x0=-0.5,
        y0=avg_charges,
        x1=1.5,
        y1=avg_charges,
        line=dict(color="#FBBC05", width=3, dash="dash")
    )
    
    # Update layout for better appearance
    fig.update_layout(
        title={
            'text': 'Prediction vs. Average Charges',
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20, 'color': '#333333'}
        },
        yaxis_title="Insurance Charges ($)",
        font=dict(family="Arial", size=14, color="#333333"),
        margin=dict(l=20, r=20, t=80, b=20),
        paper_bgcolor="rgba(0,0,0,0)",  # Transparent background
        plot_bgcolor="rgba(240, 240, 240, 0.7)",  # More opaque for better visibility
        height=400
    )
    
    # Add grid lines for better readability
    fig.update_yaxes(
        showgrid=True, 
        gridwidth=1, 
        gridcolor='rgba(128, 128, 128, 0.5)',
        title_font={'color': '#333333'},
        tickfont={'color': '#333333'},
        tickprefix='$',
        tickformat=','
    )
    
    # Add annotations
    fig.add_annotation(
        x=1.5,
        y=avg_charges,
        text="Industry Average",
        showarrow=False,
        font=dict(size=14, color="#FBBC05", family="Arial"),
        xshift=10,
        yshift=10,
        bgcolor="rgba(255,255,255,0.7)",
        bordercolor="#FBBC05",
        borderwidth=1,
        borderpad=4,
        opacity=0.9
    )
    
    return fig