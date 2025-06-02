import streamlit as st
import re # For hex validation

# Default theme settings (can be expanded and customized)
DEFAULT_LIGHT_THEME = {
    'primaryColor': '#FF4B4B',
    'backgroundColor': '#FFFFFF',
    'secondaryBackgroundColor': '#F0F2F6',
    'textColor': '#262730',
    'font': 'sans serif',
}

DEFAULT_DARK_THEME = {
    'primaryColor': '#FF4B4B', # Adjust if a different primary color is desired for dark theme
    'backgroundColor': '#0E1117',
    'secondaryBackgroundColor': '#262730',
    'textColor': '#FAFAFA',
    'font': 'sans serif',
}

# Define color palettes (ensure these match your actual project's palettes)
LIGHT_PALETTE = [
    "#000080", "#0000CD", "#0000FF", "#1E90FF", "#4169E1", 
    "#6495ED", "#87CEEB", "#ADD8E6", "#B0E0E6", "#E0FFFF"
]

DARK_PALETTE = [
    "#4B0082", "#8A2BE2", "#9370DB", "#BA55D3", "#DA70D6", 
    "#FF00FF", "#FF69B4", "#FFB6C1", "#FFC0CB", "#FFE4E1"
]

def get_streamlit_theme() -> str:
    """
    Detects the current Streamlit theme (light or dark).

    Tries to use `st.get_option("theme.base")` first. If that fails (e.g., due to
    an older Streamlit version or if not in a Streamlit context), it falls back to 
    `st.config.get_option("theme.base")`. If both methods fail, it defaults to "light".

    Returns:
        str: The detected theme, either "dark" or "light".
    """
    try:
        # Recommended way for Streamlit 1.18.0+
        theme_config = st.get_option("theme.base")
        if theme_config == "dark":
            return "dark"
        else:
            # Covers 'light' and any other non-dark themes
            return "light"
    except AttributeError:
        # Fallback for older Streamlit versions or if st.get_option is not available
        try:
            theme_config = st.config.get_option("theme.base")
            if theme_config == "dark":
                return "dark"
            else:
                return "light"
        except Exception:
            # Final fallback if all methods fail (e.g. not in streamlit context)
            return "light" 
    except Exception:
        # Catch any other unexpected errors during theme detection
        return "light" # Default to light theme as a safe fallback

def get_color_palette() -> list[str]:
    """
    Returns a list of hex color codes based on the current Streamlit theme.

    Uses `get_streamlit_theme()` to determine the active theme and returns
    either DARK_PALETTE or LIGHT_PALETTE accordingly.

    Returns:
        list[str]: A list of hex color strings.
    """
    theme = get_streamlit_theme()
    if theme == "dark":
        return DARK_PALETTE
    else:
        return LIGHT_PALETTE

def hex_to_rgba(hex_color: str, alpha: float) -> str:
    """
    Converts a HEX color string (with or without '#', 3 or 6 digits) to an RGBA string.

    Args:
        hex_color (str): The hex color string (e.g., "#RRGGBB", "RRGGBB", "#RGB", "RGB").
        alpha (float): The alpha transparency value (0.0 to 1.0).

    Returns:
        str: The RGBA color string (e.g., "rgba(r,g,b,a)").

    Raises:
        ValueError: If the hex_color string is invalid or alpha is out
    """
    current_theme_mode = get_streamlit_theme_config() # Use the robust theme detection

    if current_theme_mode == "dark":
        return {
            'primary': DEFAULT_DARK_THEME.get('primaryColor'),
            'background': DEFAULT_DARK_THEME.get('backgroundColor'),
            'secondary_background': DEFAULT_DARK_THEME.get('secondaryBackgroundColor'),
            'text': DEFAULT_DARK_THEME.get('textColor'),
            'grid': '#444444', # Example grid color for dark theme
            'success': '#28A745',
            'warning': '#FFC107',
            'danger': '#DC3545',
            'info': '#17A2B8',
        }
    else: # Light theme (default)
        return {
            'primary': DEFAULT_LIGHT_THEME.get('primaryColor'),
            'background': DEFAULT_LIGHT_THEME.get('backgroundColor'),
            'secondary_background': DEFAULT_LIGHT_THEME.get('secondaryBackgroundColor'),
            'text': DEFAULT_LIGHT_THEME.get('textColor'),
            'grid': '#DDDDDD', # Example grid color for light theme
            'success': '#198754',
            'warning': '#FFC107',
            'danger': '#DC3545',
            'info': '#0DCAF0',
        }

# The original problematic function (around line 9 in your traceback) would have been:
# def get_streamlit_theme():
#     if not st._is_running_with_streamlit: # This caused the AttributeError
#         # ...
# This function is now effectively replaced by get_streamlit_theme_config().
# Ensure any calls to a previous get_streamlit_theme() are updated if they expected a different return type.
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