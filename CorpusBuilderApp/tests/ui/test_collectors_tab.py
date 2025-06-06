# File: tests/ui/test_collectors_tab.py

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.ui.tabs.collectors_tab import CollectorsTab
from shared_tools.ui_wrappers.collectors.isda_wrapper import ISDAWrapper

class TestCollectorsTab:
    """UI tests for the CollectorsTab class."""
    
    @pytest.fixture
    def mock_project_config(self):
        """Create a mock project config."""
        config = MagicMock()
        return config
    
    @pytest.fixture
    def app(self, qtbot):
        """Create a QApplication instance."""
        return QApplication.instance() or QApplication([])
    
    @pytest.fixture
    def collectors_tab(self, qtbot, mock_project_config, app):
        """Create a CollectorsTab instance with mocked collectors."""
        with patch('shared_tools.ui_wrappers.collectors.annas_archive_wrapper.AnnasArchiveWrapper') as mock_anna, \
             patch('app.ui.tabs.collectors_tab.ISDAWrapper') as mock_isda, \
             patch('app.ui.tabs.collectors_tab.GitHubWrapper') as mock_github:
            
            # Configure mocks
            mock_isda.return_value = MagicMock()
            mock_github.return_value = MagicMock()
            mock_anna.return_value = MagicMock()
            
            tab = CollectorsTab(mock_project_config)
            qtbot.addWidget(tab)
            yield tab
    
    def test_tab_initialization(self, collectors_tab):
        """Test that the tab initializes correctly."""
        # Check that the tab has the expected collector tabs
        assert collectors_tab.collector_tabs.count() >= 3
        assert collectors_tab.collector_tabs.tabText(0) == "ISDA"
        assert collectors_tab.collector_tabs.tabText(1) == "GitHub"
        
        # Check that the collector wrappers were initialized
        assert 'isda' in collectors_tab.collector_wrappers
        assert 'github' in collectors_tab.collector_wrappers
        assert 'anna' in collectors_tab.collector_wrappers
    
    def test_isda_collection_start(self, collectors_tab, qtbot):
        """Test starting ISDA collection."""
        # Setup mock collector
        isda_wrapper = collectors_tab.collector_wrappers['isda']
        
        # Set keywords in the UI
        collectors_tab.isda_keywords.setText("derivatives, protocol")
        
        # Set max sources in the UI
        collectors_tab.isda_max_sources.setValue(30)
        
        # Click the start button
        qtbot.mouseClick(collectors_tab.isda_start_btn, Qt.MouseButton.LeftButton)
        
        # Check that the wrapper was called with correct parameters
        isda_wrapper.set_search_keywords.assert_called_once()
        assert isda_wrapper.set_search_keywords.call_args[0][0] == ["derivatives", "protocol"]
        isda_wrapper.set_max_sources.assert_called_once_with(30)
        isda_wrapper.start.assert_called_once()
        
        # Check that UI state was updated
        assert not collectors_tab.isda_start_btn.isEnabled()
        assert collectors_tab.isda_stop_btn.isEnabled()
    
    def test_isda_collection_stop(self, collectors_tab, qtbot):
        """Test stopping ISDA collection."""
        # Setup mock collector
        isda_wrapper = collectors_tab.collector_wrappers['isda']
        
        # Simulate collection in progress
        collectors_tab.isda_start_btn.setEnabled(False)
        collectors_tab.isda_stop_btn.setEnabled(True)
        
        # Click the stop button
        qtbot.mouseClick(collectors_tab.isda_stop_btn, Qt.MouseButton.LeftButton)
        
        # Check that the wrapper's stop method was called
        isda_wrapper.stop.assert_called_once()
        
        # Check that UI state was updated
        assert collectors_tab.isda_start_btn.isEnabled()
        assert not collectors_tab.isda_stop_btn.isEnabled()
    
    def test_stop_all_collectors(self, collectors_tab, qtbot):
        """Test stopping all collectors."""
        # Setup mock collectors
        isda_wrapper = collectors_tab.collector_wrappers['isda']
        github_wrapper = collectors_tab.collector_wrappers['github']
        anna_wrapper = collectors_tab.collector_wrappers['anna']
        
        # Simulate collection in progress
        collectors_tab.isda_start_btn.setEnabled(False)
        collectors_tab.isda_stop_btn.setEnabled(True)
        collectors_tab.github_start_btn.setEnabled(False)
        collectors_tab.github_stop_btn.setEnabled(True)
        
        # Click the stop all button
        qtbot.mouseClick(collectors_tab.stop_all_btn, Qt.MouseButton.LeftButton)
        
        # Check that all wrappers' stop methods were called
        isda_wrapper.stop.assert_called_once()
        github_wrapper.stop.assert_called_once()
        anna_wrapper.stop.assert_called_once()
        
        # Check that UI state was updated
        assert collectors_tab.isda_start_btn.isEnabled()
        assert not collectors_tab.isda_stop_btn.isEnabled()
        assert collectors_tab.github_start_btn.isEnabled()
        assert not collectors_tab.github_stop_btn.isEnabled()
        
        # Check that status was updated
        assert "stopped" in collectors_tab.collection_status_label.text().lower()
    
    def test_collection_completed_handler(self, collectors_tab):
        """Test handling of collection completion."""
        # Simulate collection in progress
        collectors_tab.isda_start_btn.setEnabled(False)
        collectors_tab.isda_stop_btn.setEnabled(True)
        
        # Simulate completion signal
        results = {'documents': [{'id': 1, 'title': 'Doc 1'}, {'id': 2, 'title': 'Doc 2'}]}
        collectors_tab.on_isda_collection_completed(results)
        
        # Check that UI state was updated
        assert collectors_tab.isda_start_btn.isEnabled()
        assert not collectors_tab.isda_stop_btn.isEnabled()
        
        # Check that status was updated
        assert "2 documents" in collectors_tab.collection_status_label.text()
