import streamlit as st
import re  # For hex validation

# Default theme settings
DEFAULT_LIGHT_THEME = {
    'primaryColor': '#FF4B4B',
    'backgroundColor': '#FFFFFF',
    'secondaryBackgroundColor': '#F0F2F6',
    'textColor': '#262730',
    'font': 'sans serif',
}

DEFAULT_DARK_THEME = {
    'primaryColor': '#FF4B4B',
    'backgroundColor': '#0E1117',
    'secondaryBackgroundColor': '#262730',
    'textColor': '#FAFAFA',
    'font': 'sans serif',
}

# Define color palettes
LIGHT_PALETTE = {
    'primary': '#FF4B4B',
    'background': '#FFFFFF',
    'secondary_background': '#F0F2F6',
    'text': '#262730',
    'grid': '#DDDDDD',
    'success': '#198754',
    'warning': '#FFC107',
    'danger': '#DC3545',
    'info': '#0DCAF0',
    'importance_scale': 'Blues',
}

DARK_PALETTE = {
    'primary': '#FF4B4B',
    'background': '#0E1117',
    'secondary_background': '#262730',
    'text': '#FAFAFA',
    'grid': '#444444',
    'success': '#28A745',
    'warning': '#FFC107',
    'danger': '#DC3545',
    'info': '#17A2B8',
    'importance_scale': 'Viridis',
}


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
        return "light"  # Default to light theme as a safe fallback


def get_color_palette(theme: str = None) -> dict:
    """
    Returns a color palette dictionary based on the current Streamlit theme.

    Args:
        theme: Optional theme override ('light' or 'dark')

    Returns:
        dict: A dictionary of color mappings
    """
    if theme is None:
        theme = get_streamlit_theme()
    
    if theme == "dark":
        return DARK_PALETTE
    else:
        return LIGHT_PALETTE


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    """
    Converts a HEX color string to an RGBA string.

    Args:
        hex_color (str): The hex color string (e.g., "#RRGGBB", "RRGGBB")
        alpha (float): The alpha transparency value (0.0 to 1.0)

    Returns:
        str: The RGBA color string (e.g., "rgba(r,g,b,a)")
    """
    # Remove '#' if present
    hex_color = hex_color.lstrip('#')
    
    # Validate hex color
    if not re.match(r'^[0-9A-Fa-f]{6}$', hex_color):
        raise ValueError(f"Invalid hex color: {hex_color}")
    
    # Convert to RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # Validate alpha
    if not 0.0 <= alpha <= 1.0:
        raise ValueError(f"Alpha must be between 0.0 and 1.0, got: {alpha}")
    
    return f"rgba({r},{g},{b},{alpha})"


def get_color(color_name: str, theme: str = None) -> str:
    """
    Get a specific color from the current theme's palette.
    
    Args:
        color_name: The name of the color to get
        theme: Optional theme override
        
    Returns:
        The color value as a string
    """
    palette = get_color_palette(theme)
    return palette.get(color_name, palette['primary'])  # Default to primary if color not found