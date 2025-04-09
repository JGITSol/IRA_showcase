import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import pickle
import os

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
    """Create a gauge chart to visualize risk score."""
    fig, ax = plt.subplots(figsize=(6, 3), subplot_kw={'projection': 'polar'})
    
    # Configure the gauge
    angles = np.linspace(0, 1.5*np.pi, 11)
    angles = np.append(angles, [1.5*np.pi])
    
    # Set the labels
    labels = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '']
    
    # Plot the gauge
    ax.set_thetagrids(angles[:-1] * 180/np.pi, labels)
    
    # Add colored regions for different risk levels
    ax.fill_between(np.linspace(0, 0.5*np.pi, 100), 0.9, 1, alpha=0.1, color='green')
    ax.fill_between(np.linspace(0.5*np.pi, np.pi, 100), 0.9, 1, alpha=0.1, color='yellow')
    ax.fill_between(np.linspace(np.pi, 1.5*np.pi, 100), 0.9, 1, alpha=0.1, color='red')
    
    # Plot the needle
    angle = (risk_score - 1) / 10 * 1.5 * np.pi
    ax.plot([0, angle], [0, 0.8], color='black', linewidth=2)
    ax.plot([angle, angle], [0.8, 0.9], color='black', linewidth=2)
    
    # Add a circle at the center
    ax.plot(0, 0, 'o', color='black', markersize=5)
    
    # Remove unnecessary parts of the plot
    ax.set_rticks([])
    ax.set_title('Risk Score', pad=20)
    ax.grid(True)
    
    return fig

def plot_feature_importance(model):
    """Plot feature importance for the model."""
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
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=importance_df, ax=ax)
    ax.set_title('Feature Importance')
    
    return fig

def plot_prediction_comparison(prediction, avg_charges):
    """Plot the prediction compared to average charges."""
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Create data for plotting
    categories = ['Your Prediction', 'Average Charges']
    values = [prediction, avg_charges]
    
    # Plot
    bars = ax.bar(categories, values, color=['#3498db', '#2ecc71'])
    
    # Add labels
    ax.set_ylabel('Insurance Charges ($)')
    ax.set_title('Prediction vs. Average Charges')
    
    # Add values on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 500,
                f'${height:.2f}', ha='center', va='bottom')
    
    return fig