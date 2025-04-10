# TODO List for Insurance Risk Predictor

## High Priority

### Test Coverage Improvements
- [ ] Increase app.py coverage (currently 25%)
  - Add tests for UI components and layout
  - Test user input validation
  - Cover visualization logic
  - Test main entry point
- [ ] Improve utils_plotly.py coverage (currently 19%)
  - Add unit tests for theme detection
  - Test plot generation with different themes
  - Cover all visualization functions
- [ ] Fix test failures
  - Review mock setup in test_app.py
  - Fix parameter binding in database tests
- [ ] Add integration tests
  - Theme switching functionality
  - End-to-end prediction flow
  - Database operations with real data

### Documentation
- [ ] Add comprehensive docstrings to all functions
- [ ] Update developer documentation with test coverage information
- [ ] Document the database schema and operations
- [ ] Create user manual with screenshots
- [ ] Document the model training process and parameters

## Medium Priority

### Theme and Visibility
- [ ] Implement theme detection to automatically adjust visualization colors
- [ ] Fix dark mode visibility issues in all Plotly charts
- [ ] Update gauge chart to use theme-aware colors
- [ ] Ensure text elements have sufficient contrast in both light and dark modes
- [ ] Make feature importance plot background transparent
- [ ] Adjust comparison chart colors based on current theme
- [ ] Create theme-aware color palettes

### Code Improvements
- [ ] Refactor utils_plotly.py to detect and adapt to Streamlit theme
- [ ] Add theme parameter to all visualization functions
- [ ] Implement consistent error handling across all modules
- [ ] Add input validation for all user inputs
- [ ] Optimize database queries for better performance

## Implementation Guidelines

### Theme Detection

```python
def get_streamlit_theme():
    """Detect current Streamlit theme (light or dark)."""
    try:
        dark_theme = st.config.get_option("theme.base") == "dark"
        return "dark" if dark_theme else "light"
    except:
        return "light"

def plot_with_theme_awareness(data, theme=None):
    """Create a plot with colors adapted to the current theme."""
    if theme is None:
        theme = get_streamlit_theme()
    
    colors = {
        "dark": {
            "background": "rgba(0,0,0,0)",
            "text": "#FFFFFF",
            "grid": "rgba(255,255,255,0.1)"
        },
        "light": {
            "background": "rgba(0,0,0,0)",
            "text": "#333333",
            "grid": "rgba(0,0,0,0.1)"
        }
    }
    
    theme_colors = colors[theme]
    # Create and return the plot with theme-aware styling
```

### Test Coverage Tracking

To monitor test coverage improvements:
1. Run coverage: `coverage run run_tests.py`
2. Generate report: `coverage report -m`
3. Update TEST_COVERAGE.md with new metrics
4. Focus on modules with < 80% coverage