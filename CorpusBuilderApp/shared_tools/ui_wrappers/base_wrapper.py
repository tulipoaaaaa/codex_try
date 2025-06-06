from PySide6.QtCore import QObject, Signal as pyqtSignal, QThread, QTimer
from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, Optional
from pathlib import Path

class BaseWorkerThread(QThread):
    """Base worker thread for all collectors/processors"""
    progress = pyqtSignal(int, int, str)  # current, total, message
    error = pyqtSignal(str)
    finished = pyqtSignal(dict)
    
    def __init__(self, target_object, operation_type="collect", **kwargs):
        super().__init__()
        self.target = target_object
        self.operation_type = operation_type
        self.kwargs = kwargs
        self._should_stop = False
        
    def run(self):
        try:
            if self.operation_type == "collect":
                results = self.target.collect(**self.kwargs)
            elif self.operation_type == "extract":
                results = self.target.extract_text(**self.kwargs)
            elif self.operation_type == "process":
                results = self.target.process(**self.kwargs)
            else:
                results = getattr(self.target, self.operation_type)(**self.kwargs)
                
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        self._should_stop = True

class BaseWrapper(QObject):
    """Base wrapper for all collectors and processors"""
    
    # Standard UI signals
    progress_updated = pyqtSignal(int)  # 0-100 percentage
    status_updated = pyqtSignal(str)    # Status message
    error_occurred = pyqtSignal(str)    # Error message
    completed = pyqtSignal(dict)        # Results dictionary
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.worker = None
        self._is_running = False
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
    @abstractmethod
    def _create_target_object(self):
        """Create the actual collector/processor object"""
        pass
        
    @abstractmethod
    def _get_operation_type(self):
        """Get the operation type for the worker thread"""
        pass
        
    def start(self, **kwargs):
        """Start the collection/processing operation"""
        if self._is_running:
            self.status_updated.emit("Operation already in progress")
            return
            
        self._is_running = True
        self.status_updated.emit("Starting operation...")
        
        target_obj = self._create_target_object()
        operation_type = self._get_operation_type()
        
        self.worker = BaseWorkerThread(target_obj, operation_type, **kwargs)
        self.worker.progress.connect(self._on_progress)
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
        
    def _on_progress(self, current: int, total: int, message: str):
        """Handle progress updates"""
        if total > 0:
            percentage = min(100, int((current / total) * 100))
            self.progress_updated.emit(percentage)
        if message:
            self.status_updated.emit(message)
            
    def _on_error(self, error_message: str):
        """Handle errors"""
        self._is_running = False
        self.error_occurred.emit(error_message)
        self.status_updated.emit(f"Error: {error_message}")
        
    def _on_finished(self, results: Dict[str, Any]):
        """Handle completion"""
        self._is_running = False
        self.completed.emit(results)
        self.status_updated.emit("Operation completed successfully")
        
    def stop(self):
        """Stop the operation"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            self._is_running = False
            self.status_updated.emit("Operation stopped")
            
    def get_status(self) -> Dict[str, Any]:
        """Get current operation status"""
        return {
            "is_running": self._is_running,
            "type": self.__class__.__name__
        }
        
    def is_running(self) -> bool:
        """Check if operation is currently running"""
        return self._is_running

class CollectorWrapperMixin:
    """Mixin for collector-specific functionality"""
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        if hasattr(self, 'target') and hasattr(self.target, 'get_stats'):
            return self.target.get_stats()
        return {"documents_collected": 0, "last_run": None}

class ProcessorWrapperMixin:
    """Mixin for processor-specific functionality"""
    
    file_processed = pyqtSignal(str, bool)  # filepath, success
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        if hasattr(self, 'target') and hasattr(self.target, 'get_stats'):
            return self.target.get_stats()
        return {"files_processed": 0, "success_rate": 0.0}