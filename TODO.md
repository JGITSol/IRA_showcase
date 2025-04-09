# TODO List for Insurance Risk Predictor

## For Version 1.1.0

### Theme and Visibility Issues
- [ ] Implement theme detection to automatically adjust visualization colors
- [ ] Fix dark mode visibility issues in all Plotly charts
- [ ] Update gauge chart to use theme-aware colors
- [ ] Ensure text elements have sufficient contrast in both light and dark modes
- [ ] Make feature importance plot background transparent and text visible in dark mode
- [ ] Adjust comparison chart colors based on current theme
- [ ] Create theme-aware color palettes for all visualizations

### Documentation
- [ ] Add comprehensive docstrings to all functions
- [ ] Create developer documentation for the codebase
- [ ] Document the database schema and operations
- [ ] Add setup instructions in README.md
- [ ] Create user manual with screenshots
- [ ] Document the model training process and parameters

### Code Improvements
- [ ] Refactor utils_plotly.py to detect and adapt to Streamlit theme
- [ ] Add theme parameter to all visualization functions
- [ ] Implement consistent error handling across all modules
- [ ] Add input validation for all user inputs
- [ ] Optimize database queries for better performance

### Testing
- [ ] Add unit tests for theme-aware visualizations
- [ ] Test application in both light and dark modes
- [ ] Create automated tests for UI components
- [ ] Test on different screen sizes and devices

## How to Implement Theme Detection

```python
# Example code for detecting Streamlit theme
def get_streamlit_theme():
    """Detect current Streamlit theme (light or dark)."""
    try:
        # This is a workaround as Streamlit doesn't provide direct theme detection
        # Check if dark theme is active by inspecting CSS variables
        dark_theme = st.config.get_option("theme.base") == "dark"
        return "dark" if dark_theme else "light"
    except:
        # Default to light theme if detection fails
        return "light"

# Then in visualization functions:
def plot_with_theme_awareness(data, theme=None):
    """Create a plot with colors adapted to the current theme."""
    if theme is None:
        theme = get_streamlit_theme()
    
    # Use appropriate colors based on theme
    if theme == "dark":
        background_color = "rgba(0,0,0,0)"
        text_color = "#FFFFFF"
        grid_color = "rgba(255,255,255,0.1)"
    else:
        background_color = "rgba(0,0,0,0)"
        text_color = "#333333"
        grid_color = "rgba(0,0,0,0.1)"
    
    # Create and return the plot with theme-aware styling
    # ...
```