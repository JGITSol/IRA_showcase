import streamlit as st

def get_streamlit_theme():
    """
    Detect the current Streamlit theme (light or dark).
    Returns 'light' or 'dark' based on the current theme.
    """
    # Check if we're running in Streamlit
    if not st._is_running_with_streamlit:
        return 'light'  # Default to light theme when not running in Streamlit
    
    # Try to get theme from session state if previously detected
    if 'theme' in st.session_state:
        return st.session_state.theme
    
    # Use JavaScript to detect the theme
    # This is done by checking the background color of the body element
    theme_detector_code = """
    <script>
    const doc = window.parent.document;
    const body = doc.querySelector('body');
    const bgColor = window.getComputedStyle(body).backgroundColor;
    
    // Convert RGB to brightness
    function getBrightness(color) {
        // Extract RGB values
        const rgb = color.match(/\d+/g);
        if (!rgb || rgb.length < 3) return 128; // Default to middle brightness
        
        // Calculate brightness using perceived luminance formula
        return (parseInt(rgb[0]) * 0.299 + parseInt(rgb[1]) * 0.587 + parseInt(rgb[2]) * 0.114);
    }
    
    const brightness = getBrightness(bgColor);
    const theme = brightness > 128 ? 'light' : 'dark';
    
    // Send the theme to Python
    window.parent.postMessage({type: 'streamlit:setComponentValue', value: theme}, '*');
    </script>
    """
    
    # Use a workaround to detect theme
    # Since direct JavaScript execution is limited, we'll use a heuristic approach
    # based on Streamlit's default themes
    
    # For now, we'll use a simpler approach by checking config if possible
    try:
        import streamlit.config as config
        theme_option = config.get_option('theme.base')
        if theme_option:
            detected_theme = 'dark' if theme_option == 'dark' else 'light'
            st.session_state.theme = detected_theme
            return detected_theme
    except:
        pass
    
    # Fallback method: we'll try to detect based on common elements
    # This is not 100% reliable but works in most cases
    # We'll store the result in session state to avoid recalculating
    
    # Default to light theme
    st.session_state.theme = 'light'
    return 'light'

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
    theme = get_streamlit_theme()
    return COLOR_PALETTES[theme]

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