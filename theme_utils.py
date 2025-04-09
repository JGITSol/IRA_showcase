import streamlit as st

def get_streamlit_theme():
    """
    Get the current Streamlit theme or return a default theme.
    Returns a dictionary with theme properties.
    """
    # Return default theme instead of checking private attribute
    # This avoids the AttributeError: module 'streamlit' has no attribute '_is_running_with_streamlit'
    return {
        'primaryColor': '#FF4B4B',
        'backgroundColor': '#FFFFFF',
        'secondaryBackgroundColor': '#F0F2F6',
        'textColor': '#262730',
        'font': 'sans serif',
    }

# Define color palettes for light and dark themes
COLOR_PALETTES = {
    'light': {
        # Main colors
        'primary': '#4285F4',  # Blue
        'secondary': '#34A853',  # Green
        'accent': '#FBBC05',  # Yellow
        'warning': '#EA4335',  # Red
        
        # Background colors
        'background': '#FFFFFF',
        'surface': '#F8F9FA',
        'plot_bg': 'rgba(240, 240, 240, 0.7)',
        
        # Text colors
        'text': '#333333',
        'text_secondary': '#666666',
        
        # Chart specific colors
        'grid': 'rgba(128, 128, 128, 0.5)',
        'gauge_low': 'rgba(0, 204, 0, 0.4)',  # Green
        'gauge_medium': 'rgba(255, 165, 0, 0.4)',  # Orange
        'gauge_high': 'rgba(255, 51, 51, 0.4)',  # Red
        
        # Feature importance color scale
        'importance_scale': 'Plasma',
        
        # Comparison chart colors
        'comparison_default': '#4285F4',  # Blue
        'comparison_good': '#34A853',  # Green
        'comparison_bad': '#EA4335',  # Red
    },
    'dark': {
        # Main colors
        'primary': '#8AB4F8',  # Lighter Blue
        'secondary': '#81C995',  # Lighter Green
        'accent': '#FDD663',  # Lighter Yellow
        'warning': '#F28B82',  # Lighter Red
        
        # Background colors
        'background': '#121212',
        'surface': '#1E1E1E',
        'plot_bg': 'rgba(30, 30, 30, 0.7)',
        
        # Text colors
        'text': '#E8EAED',
        'text_secondary': '#9AA0A6',
        
        # Chart specific colors
        'grid': 'rgba(169, 169, 169, 0.5)',
        'gauge_low': 'rgba(129, 201, 149, 0.4)',  # Lighter Green
        'gauge_medium': 'rgba(253, 214, 99, 0.4)',  # Lighter Yellow
        'gauge_high': 'rgba(242, 139, 130, 0.4)',  # Lighter Red
        
        # Feature importance color scale
        'importance_scale': 'Plasma',
        
        # Comparison chart colors
        'comparison_default': '#8AB4F8',  # Lighter Blue
        'comparison_good': '#81C995',  # Lighter Green
        'comparison_bad': '#F28B82',  # Lighter Red
    }
}

def get_color_palette():
    """
    Get the color palette based on the current theme.
    Returns a dictionary of colors for the current theme.
    """
    # Always use light theme for now since we can't reliably detect theme
    # This avoids the error by not calling the problematic function
    return COLOR_PALETTES['light']

def get_color(color_name):
    """
    Get a specific color from the current theme's palette.
    
    Args:
        color_name: The name of the color to get
        
    Returns:
        The color value as a string
    """
    palette = get_color_palette()
    return palette.get(color_name, palette['primary'])  # Default to primary if color not found