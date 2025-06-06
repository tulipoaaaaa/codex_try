# File: tests/unit/test_quality_control_wrapper.py

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt
from shared_tools.ui_wrappers.processors.quality_control_wrapper import QualityControlWrapper

class TestQualityControlWrapper:
    """Unit tests for the QualityControlWrapper class."""
    
    @pytest.fixture
    def mock_project_config(self):
        """Create a mock project config."""
        config = MagicMock()
        return config
    
    @pytest.fixture
    def wrapper(self, mock_project_config):
        """Create a QualityControlWrapper instance with a mock processor."""
        wrapper = QualityControlWrapper(mock_project_config)
        wrapper.processor = MagicMock()
        return wrapper
    
    def test_initialization(self, wrapper, mock_project_config):
        """Test wrapper initialization."""
        assert wrapper.project_config == mock_project_config
        assert wrapper._is_running == False
        assert wrapper.quality_threshold == 70
    
    def test_set_quality_threshold(self, wrapper):
        """Test setting quality threshold."""
        wrapper.set_quality_threshold(85)
        assert wrapper.quality_threshold == 85
    
    def test_get_status(self, wrapper):
        """Test get_status method."""
        wrapper._is_running = True
        status = wrapper.get_status()
        assert status['is_running'] == True
        assert status['processor_type'] == 'quality_control'
        assert status['threshold'] == 70
    
    def test_start_already_running(self, wrapper):
        """Test start method when already running."""
        wrapper._is_running = True
        
        # Mock the signal
        wrapper.status_updated = MagicMock()
        
        result = wrapper.start(['file1.pdf'])
        
        assert result == False
        wrapper.status_updated.emit.assert_called_once()
    
    def test_start_success(self, wrapper):
        """Test successful start."""
        # Mock signals
        wrapper.status_updated = MagicMock()
        
        # Patch QThread to avoid actually starting a thread
        with patch('shared_tools.ui_wrappers.processors.quality_control_wrapper.QCWorkerThread'):
            result = wrapper.start(['file1.pdf', 'file2.pdf'])
            
            assert result == True
            assert wrapper._is_running == True
            wrapper.status_updated.emit.assert_called_once()
    
    def test_stop_not_running(self, wrapper):
        """Test stop when not running."""
        wrapper._is_running = False
        result = wrapper.stop()
        assert result == False
    
    def test_stop_success(self, wrapper):
        """Test successful stop."""
        wrapper._is_running = True
        wrapper.worker_thread = MagicMock()
        wrapper.status_updated = MagicMock()
        
        result = wrapper.stop()
        
        assert result == True
        wrapper.worker_thread.requestInterruption.assert_called_once()
        wrapper.status_updated.emit.assert_called_once()
    
    def test_on_processing_completed(self, wrapper):
        """Test processing completed handler."""
        wrapper._is_running = True
        wrapper.batch_completed = MagicMock()
        wrapper.status_updated = MagicMock()
        
        results = {'processed_files': ['file1.pdf', 'file2.pdf']}
        wrapper._on_processing_completed(results)
        
        assert wrapper._is_running == False
        wrapper.batch_completed.emit.assert_called_once_with(results)
        wrapper.status_updated.emit.assert_called_once()
