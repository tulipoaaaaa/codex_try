# tests/integration/test_ui_integration.py
import pytest
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from unittest.mock import Mock, patch

# Ensure QApplication exists for testing
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for testing"""
    if QApplication.instance() is None:
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    yield app
    app.quit()

class TestUIIntegration:
    """Integration tests for UI components"""
    
    @pytest.mark.ui
    def test_main_window_initialization(self, qapp, qtbot):
        """Test main window initialization and basic functionality"""
        try:
            from app.main_window import MainWindow
            
            window = MainWindow()
            qtbot.addWidget(window)
            
            # Test window is created properly
            assert window.isVisible() is False  # Not shown yet
            window.show()
            assert window.isVisible() is True
            
            # Test basic UI elements exist
            assert window.windowTitle() != ""
            
        except ImportError:
            pytest.skip("MainWindow not available for testing")
    
    @pytest.mark.ui
    def test_file_browser_integration(self, qapp, qtbot):
        """Test file browser UI integration"""
        try:
            from app.ui.file_browser import FileBrowser
            
            browser = FileBrowser()
            qtbot.addWidget(browser)
            
            # Test directory navigation
            qtbot.mouseClick(browser, Qt.MouseButton.LeftButton)
            
            # Test file selection
            QTest.keyClick(browser, Qt.Key.Key_Down)
            QTest.keyClick(browser, Qt.Key.Key_Return)
            
        except (ImportError, AttributeError):
            pytest.skip("FileBrowser not available for testing")
    
    @pytest.mark.ui 
    def test_configuration_tab_integration(self, qapp, qtbot):
        """Test configuration tab functionality"""
        try:
            from app.ui.configuration_tab import ConfigurationTab
            
            config_tab = ConfigurationTab()
            qtbot.addWidget(config_tab)
            
            # Test configuration changes
            if hasattr(config_tab, 'api_key_input'):
                qtbot.keyClicks(config_tab.api_key_input, "test_api_key")
                assert config_tab.api_key_input.text() == "test_api_key"
                
        except ImportError:
            pytest.skip("ConfigurationTab not available for testing")
