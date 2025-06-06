# File: tests/unit/test_file_browser.py

import pytest
import os
from PySide6.QtCore import QDir
from PySide6.QtWidgets import QApplication
from app.ui.widgets.file_browser import FileBrowser

class TestFileBrowser:
    """Unit tests for the FileBrowser widget."""
    
    def test_initialization(self, qapp, temp_dir):
        """Test FileBrowser initialization."""
        browser = FileBrowser()
        assert browser.current_directory == QDir.homePath()
        assert browser.history == []
        assert browser.history_index == -1
        
    def test_set_directory(self, qapp, temp_dir):
        """Test setting directory."""
        browser = FileBrowser()
        browser.set_directory(temp_dir)
        
        assert browser.current_directory == temp_dir
        assert browser.address_bar.text() == temp_dir
        assert len(browser.history) == 1
        assert browser.history[0] == temp_dir
        
    def test_navigation_history(self, qapp, temp_dir):
        """Test navigation history functionality."""
        browser = FileBrowser()
        
        # Navigate to directories
        dir1 = temp_dir
        dir2 = os.path.join(temp_dir, 'subdir')
        os.makedirs(dir2)
        
        browser.set_directory(dir1)
        browser.set_directory(dir2)
        
        assert len(browser.history) == 2
        assert browser.history_index == 1
        
        # Test back navigation
        browser.go_back()
        assert browser.current_directory == dir1
        assert browser.history_index == 0
        
        # Test forward navigation
        browser.go_forward()
        assert browser.current_directory == dir2
        assert browser.history_index == 1
        
    def test_file_selection(self, qapp, sample_files):
        """Test file selection functionality."""
        browser = FileBrowser()
        selected_files = []
        
        def on_file_selected(file_path):
            selected_files.append(file_path)
            
        browser.file_selected.connect(on_file_selected)
        
        # Simulate file selection
        browser.set_directory(os.path.dirname(sample_files['text']))
        # Note: Actual file selection would require user interaction simulation
        
    def test_drag_drop_handling(self, qapp, sample_files):
        """Test drag and drop handling."""
        browser = FileBrowser()
        dropped_files = []
        
        def on_files_dropped(file_paths):
            dropped_files.extend(file_paths)
            
        browser.files_dropped.connect(on_files_dropped)
        
        # Note: Actual drag-drop testing would require QTest or similar
        assert browser.acceptDrops() == True
