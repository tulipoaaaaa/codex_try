from shared_tools.ui_helpers import theme_manager

def test_load_theme_returns_qss_string():
    result = theme_manager.load_theme("dark")
    assert isinstance(result, str)
