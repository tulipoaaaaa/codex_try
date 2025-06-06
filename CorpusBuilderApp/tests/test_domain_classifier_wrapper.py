# File: tests/unit/test_domain_classifier_wrapper.py

"""
Unit tests for Domain Classifier Wrapper

Tests the domain classification functionality and UI integration
for the CryptoFinance Corpus Builder application.
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtCore import QObject, Signal as pyqtSignal
from PySide6.QtWidgets import QApplication

from shared_tools.ui_wrappers.processors.domain_classifier_wrapper import (
    DomainClassifierWrapper,
    DomainClassifierWorkerThread
)
from shared_tools.project_config import ProjectConfig


class TestDomainClassifierWrapper:
    """Test cases for Domain Classifier Wrapper"""
    
    @pytest.fixture
    def qapp(self):
        """Create QApplication instance"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app
        
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        config = Mock(spec=ProjectConfig)
        config.get_all_settings = Mock(return_value={
            'classification_threshold': 0.8,
            'supported_domains': [
                'crypto_derivatives',
                'high_frequency_trading',
                'risk_management'
            ]
        })
        return config
        
    @pytest.fixture
    def mock_classifier(self):
        """Create mock domain classifier"""
        classifier = Mock()
        classifier.classify_document.return_value = {
            'domain': 'crypto_derivatives',
            'confidence': 0.85,
            'features': ['bitcoin', 'trading', 'derivatives'],
            'metadata': {'processed_at': '2024-01-01'}
        }
        classifier.get_supported_domains.return_value = [
            'crypto_derivatives',
            'high_frequency_trading',
            'risk_management'
        ]
        classifier.get_stats.return_value = {
            'documents_classified': 100,
            'accuracy': 0.92
        }
        return classifier
        
    @pytest.fixture
    def wrapper(self, qapp, mock_config):
        """Create wrapper instance with mocked dependencies"""
        with patch('shared_tools.ui_wrappers.processors.domain_classifier_wrapper.DomainClassifier'):
            wrapper = DomainClassifierWrapper(mock_config)
            wrapper.classifier = Mock()  # Override with mock
            return wrapper
            
    def test_wrapper_initialization(self, wrapper, mock_config):
        """Test wrapper initialization"""
        assert wrapper.config == mock_config
        assert wrapper.classifier is not None
        assert not wrapper.is_running()
        
    def test_get_supported_domains(self, wrapper):
        """Test getting supported domains"""
        wrapper.classifier.get_supported_domains.return_value = [
            'crypto_derivatives', 'defi', 'trading'
        ]
        
        domains = wrapper.get_supported_domains()
        assert 'crypto_derivatives' in domains
        assert 'defi' in domains
        assert 'trading' in domains
        
    def test_get_supported_domains_fallback(self, wrapper):
        """Test fallback when classifier doesn't have method"""
        wrapper.classifier = None
        
        domains = wrapper.get_supported_domains()
        assert len(domains) == 8  # Default domains
        assert 'crypto_derivatives' in domains
        assert 'regulation_compliance' in domains
        
    def test_set_classification_threshold(self, wrapper):
        """Test setting classification threshold"""
        wrapper.classifier.set_threshold = Mock()
        
        wrapper.set_classification_threshold(0.9)
        wrapper.classifier.set_threshold.assert_called_once_with(0.9)
        
    def test_get_classification_stats(self, wrapper):
        """Test getting classification statistics"""
        wrapper.classifier.get_stats.return_value = {
            'documents_classified': 150,
            'accuracy': 0.88
        }
        
        stats = wrapper.get_classification_stats()
        assert stats['documents_classified'] == 150
        assert stats['accuracy'] == 0.88
        
    def test_get_status(self, wrapper):
        """Test getting wrapper status"""
        wrapper.classifier.get_supported_domains.return_value = ['crypto', 'defi']
        wrapper.classifier.get_stats.return_value = {'accuracy': 0.9}
        
        status = wrapper.get_status()
        assert status['is_running'] == False
        assert status['classifier_initialized'] == True
        assert 'crypto' in status['supported_domains']
        assert status['classification_stats']['accuracy'] == 0.9
        
    def test_start_classification_no_classifier(self, wrapper):
        """Test starting classification without classifier"""
        wrapper.classifier = None
        
        result = wrapper.start_classification(['test.pdf'])
        assert result == False
        
    def test_start_classification_already_running(self, wrapper):
        """Test starting classification when already running"""
        wrapper._is_running = True
        
        result = wrapper.start_classification(['test.pdf'])
        assert result == False
        
    @patch('shared_tools.ui_wrappers.processors.domain_classifier_wrapper.DomainClassifierWorkerThread')
    def test_start_classification_success(self, mock_worker_class, wrapper):
        """Test successful classification start"""
        mock_worker = Mock()
        mock_worker_class.return_value = mock_worker
        
        files = ['test1.pdf', 'test2.pdf']
        result = wrapper.start_classification(files)
        
        assert result == True
        assert wrapper._is_running == True
        mock_worker_class.assert_called_once()
        mock_worker.start.assert_called_once()
        
    def test_start_classification_exception(self, wrapper):
        """Test classification start with exception"""
        wrapper.classifier.classify_document.side_effect = Exception("Test error")
        
        with patch('shared_tools.ui_wrappers.processors.domain_classifier_wrapper.DomainClassifierWorkerThread') as mock_worker:
            mock_worker.side_effect = Exception("Worker creation failed")
            
            result = wrapper.start_classification(['test.pdf'])
            assert result == False


class TestDomainClassifierWorker:
    """Test cases for Domain Classifier Worker"""
    
    @pytest.fixture
    def mock_classifier(self):
        """Create mock classifier for worker"""
        classifier = Mock()
        classifier.classify_document.return_value = {
            'domain': 'crypto_derivatives',
            'confidence': 0.9,
            'features': ['bitcoin', 'futures']
        }
        return classifier
        
    @pytest.fixture
    def worker(self, mock_classifier):
        """Create worker instance"""
        config = {'classification_threshold': 0.8}
        files = ['test1.pdf', 'test2.pdf']
        return DomainClassifierWorkerThread(mock_classifier, files, config)
        
    def test_worker_initialization(self, worker, mock_classifier):
        """Test worker initialization"""
        assert worker.processor == mock_classifier
        assert len(worker.documents) == 2
        assert worker._is_running == True
        
    def test_worker_stop(self, worker):
        """Test stopping worker"""
        worker.stop()
        assert worker._is_running == False
        
    @patch('shared_tools.ui_wrappers.processors.domain_classifier_wrapper.os.path.basename')
    def test_worker_run_success(self, mock_basename, worker):
        """Test successful worker execution"""
        mock_basename.return_value = 'test.pdf'
        
        # Mock signals
        worker.progress = Mock()
        worker.finished = Mock()
        worker.error = Mock()
        
        # Run worker
        worker.run()
        
        # Verify signals were emitted
        assert worker.progress.emit.call_count >= 2
        worker.finished.emit.assert_called_once()
        worker.error.emit.assert_not_called()
        
        # Check results
        results = worker.finished.emit.call_args[0][0]
        assert results['files_processed'] == 2
        assert results['successful_classifications'] == 2
        assert results['failed_classifications'] == 0
        
    def test_worker_run_with_errors(self, worker):
        """Test worker execution with classification errors"""
        worker.classifier.classify_document.side_effect = [
            {'domain': 'crypto', 'confidence': 0.9},
            Exception("Classification failed")
        ]
        
        # Mock signals
        worker.progress = Mock()
        worker.finished = Mock()
        worker.error = Mock()
        
        # Run worker
        worker.run()
        
        # Check results
        results = worker.finished.emit.call_args[0][0]
        assert results['files_processed'] == 2
        assert results['successful_classifications'] == 1
        assert results['failed_classifications'] == 1
        assert len(results['errors']) == 1
        
    def test_worker_run_stopped_early(self, worker):
        """Test worker execution when stopped early"""
        worker._is_running = False
        
        # Mock signals
        worker.progress = Mock()
        worker.finished = Mock()
        worker.error = Mock()
        
        # Run worker
        worker.run()
        
        # Check that no files were processed
        results = worker.finished.emit.call_args[0][0]
        assert results['files_processed'] == 0
        
    def test_worker_run_exception(self, worker):
        """Test worker execution with general exception"""
        worker.files_to_process = None  # This will cause an exception
        
        # Mock signals
        worker.progress = Mock()
        worker.finished = Mock()
        worker.error = Mock()
        
        # Run worker
        worker.run()
        
        # Verify error was emitted
        worker.error.emit.assert_called_once()
        worker.finished.emit.assert_not_called()


class TestDomainClassifierIntegration:
    """Integration tests for Domain Classifier"""
    
    @pytest.fixture
    def qapp(self):
        """Create QApplication instance"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app
        
    def test_signal_connections(self, qapp):
        """Test that signals are properly connected"""
        config = Mock()
        config.get_all_settings.return_value = {}
        
        with patch('shared_tools.ui_wrappers.processors.domain_classifier_wrapper.DomainClassifier'):
            wrapper = DomainClassifierWrapper(config)
            
            # Test that wrapper has all required signals
            assert hasattr(wrapper, 'progress_updated')
            assert hasattr(wrapper, 'status_updated') 
            assert hasattr(wrapper, 'error_occurred')
            assert hasattr(wrapper, 'completed')
            
    def test_wrapper_workflow(self, qapp):
        """Test complete wrapper workflow"""
        config = Mock()
        config.get_all_settings.return_value = {'threshold': 0.8}
        
        with patch('shared_tools.ui_wrappers.processors.domain_classifier_wrapper.DomainClassifier') as mock_class:
            mock_classifier = Mock()
            mock_class.return_value = mock_classifier
            
            wrapper = DomainClassifierWrapper(config)
            
            # Test initial state
            assert not wrapper.is_running()
            
            # Test starting classification
            with patch('shared_tools.ui_wrappers.processors.domain_classifier_wrapper.DomainClassifierWorkerThread'):
                result = wrapper.start_classification(['test.pdf'])
                assert result == True
                assert wrapper.is_running()
                
            # Test stopping
            wrapper.stop()
            assert not wrapper.is_running()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])