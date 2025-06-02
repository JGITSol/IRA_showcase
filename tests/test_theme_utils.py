import unittest
from unittest.mock import patch, MagicMock

# Assuming theme_utils.py is in the project root and tests/ is a subdirectory.
# Adjust import if your project structure is different or uses a src layout.
# For example, if IRA_showcase is added to PYTHONPATH:
# from theme_utils import get_streamlit_theme_config, get_color_palette, DEFAULT_LIGHT_THEME, DEFAULT_DARK_THEME
# Or, if running tests from the root directory:
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from theme_utils import get_streamlit_theme_config, get_color_palette, DEFAULT_LIGHT_THEME, DEFAULT_DARK_THEME

class TestThemeUtils(unittest.TestCase):

    @patch('theme_utils.st')
    def test_get_streamlit_theme_config_st_get_option_light(self, mock_st):
        """Test get_streamlit_theme_config returns 'light' via st.get_option."""
        mock_st.get_option.return_value = "light"
        self.assertEqual(get_streamlit_theme_config(), "light")
        mock_st.get_option.assert_called_once_with("theme.base")

    @patch('theme_utils.st')
    def test_get_streamlit_theme_config_st_get_option_dark(self, mock_st):
        """Test get_streamlit_theme_config returns 'dark' via st.get_option."""
        mock_st.get_option.return_value = "dark"
        self.assertEqual(get_streamlit_theme_config(), "dark")
        mock_st.get_option.assert_called_once_with("theme.base")

    @patch('theme_utils.st')
    def test_get_streamlit_theme_config_fallback_to_st_config_light(self, mock_st):
        """Test fallback to st.config.get_option for light theme."""
        mock_st.get_option.side_effect = AttributeError("st.get_option not found")
        mock_st.config = MagicMock()
        mock_st.config.get_option.return_value = "light"
        # Ensure hasattr(st, 'config') is true and callable(st.config.get_option) is true
        # For MagicMock, methods are callable by default.
        # We need to ensure 'config' is an attribute of mock_st.
        type(mock_st).config = mock_st.config # Make hasattr(mock_st, 'config') behave as expected

        self.assertEqual(get_streamlit_theme_config(), "light")
        mock_st.get_option.assert_called_once_with("theme.base")
        mock_st.config.get_option.assert_called_once_with("theme.base")

    @patch('theme_utils.st')
    def test_get_streamlit_theme_config_fallback_to_st_config_dark(self, mock_st):
        """Test fallback to st.config.get_option for dark theme."""
        mock_st.get_option.side_effect = AttributeError("st.get_option not found")
        mock_st.config = MagicMock()
        mock_st.config.get_option.return_value = "dark"
        type(mock_st).config = mock_st.config

        self.assertEqual(get_streamlit_theme_config(), "dark")
        mock_st.config.get_option.assert_called_once_with("theme.base")

    def test_get_streamlit_theme_config_all_fallbacks_to_default(self):
        """Test fallback to default 'light' theme if all st methods fail."""
        # Test path: st.get_option (AttributeError) -> hasattr(st, 'config') is False
        with patch('theme_utils.st') as mock_st_no_config_attr:
            mock_st_no_config_attr.get_option.side_effect = AttributeError("No st.get_option")
            # For a fresh MagicMock, hasattr(mock, 'config') is False unless 'config' is accessed/set.
            # To be explicit, ensure 'config' is not on the mock:
            if hasattr(mock_st_no_config_attr, 'config'):
                delattr(mock_st_no_config_attr, 'config')
            self.assertEqual(get_streamlit_theme_config(), "light", "Default not returned when st.config attr missing")

        # Test path: st.get_option (AttributeError) -> hasattr(st, 'config') is True -> st.config.get_option fails
        with patch('theme_utils.st') as mock_st_config_fails:
            mock_st_config_fails.get_option.side_effect = AttributeError("No st.get_option")
            mock_st_config_fails.config = MagicMock() # st.config attribute exists
            type(mock_st_config_fails).config = mock_st_config_fails.config # for hasattr
            mock_st_config_fails.config.get_option.side_effect = Exception("st.config.get_option call failed")
            self.assertEqual(get_streamlit_theme_config(), "light", "Default not returned when st.config.get_option fails")

        # Test path: st.get_option itself raises a generic Exception
        with patch('theme_utils.st') as mock_st_get_option_exception:
            mock_st_get_option_exception.get_option.side_effect = Exception("st.get_option general failure")
            self.assertEqual(get_streamlit_theme_config(), "light", "Default not returned when st.get_option has general failure")

    @patch('theme_utils.get_streamlit_theme_config')
    def test_get_color_palette_light_theme(self, mock_get_theme_config):
        """Test get_color_palette returns correct palette for light theme."""
        mock_get_theme_config.return_value = "light"
        palette = get_color_palette()
        self.assertEqual(palette['background'], DEFAULT_LIGHT_THEME['backgroundColor'])
        self.assertEqual(palette['text'], DEFAULT_LIGHT_THEME['textColor'])
        self.assertEqual(palette['primary'], DEFAULT_LIGHT_THEME['primaryColor'])
        # Add more assertions for other colors if needed

    @patch('theme_utils.get_streamlit_theme_config')
    def test_get_color_palette_dark_theme(self, mock_get_theme_config):
        """Test get_color_palette returns correct palette for dark theme."""
        mock_get_theme_config.return_value = "dark"
        palette = get_color_palette()
        self.assertEqual(palette['background'], DEFAULT_DARK_THEME['backgroundColor'])
        self.assertEqual(palette['text'], DEFAULT_DARK_THEME['textColor'])
        self.assertEqual(palette['primary'], DEFAULT_DARK_THEME['primaryColor'])
        # Add more assertions for other colors

if __name__ == '__main__':
    unittest.main()