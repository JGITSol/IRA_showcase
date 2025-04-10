# Test Coverage Report

## Overview

Current overall test coverage: 63%

## Coverage by Module

### High Coverage (90%+)
- `run_tests.py`: 100%
- `database.py`: 98%
- `model.py`: 94%
- `tests/test_app.py`: 93%
- `tests/test_database.py`: 99%
- `tests/test_model.py`: 92%
- `tests/test_utils.py`: 89%

### Medium Coverage (50-89%)
- `theme_utils.py`: 56%
- `utils.py`: 61%

### Low Coverage (<50%)
- `app.py`: 25%
- `utils_plotly.py`: 19%

## Areas Needing Improvement

### app.py (25% coverage)
Missing coverage in:
- Lines 68-69: App initialization
- Lines 91-138: UI components and layout
- Lines 142-183: User input handling
- Lines 188-316: Visualization and display logic
- Line 319: Main entry point

### utils_plotly.py (19% coverage)
Missing coverage in:
- Lines 13-22: Theme detection
- Lines 26-42: Plot initialization
- Lines 47-48: Color handling
- Lines 53-98: Gauge chart creation
- Lines 103-178: Feature importance plotting
- Lines 183-263: Comparison chart generation

### utils.py (61% coverage)
Missing coverage in:
- Lines 11-20: Utility functions
- Lines 84-127: Visualization helpers

## Test Failures

1. `test_make_prediction` in `test_app.py`:
   - Expected 'add_prediction' to be called once but was called 0 times

2. Database binding error in `test_database.py`:
   - Error binding parameter 1: type 'MagicMock' is not supported

## Recommendations

1. Increase coverage for `app.py`:
   - Add tests for UI components
   - Test user input validation
   - Cover visualization logic

2. Improve `utils_plotly.py` coverage:
   - Add unit tests for theme detection
   - Test plot generation with different themes
   - Cover all visualization functions

3. Fix test failures:
   - Review mock setup in `test_app.py`
   - Fix parameter binding in database tests

4. Add integration tests for:
   - Theme switching
   - End-to-end prediction flow
   - Database operations with real data