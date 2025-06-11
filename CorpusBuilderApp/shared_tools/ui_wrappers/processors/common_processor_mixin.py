from PySide6.QtCore import Signal as pyqtSignal
from shared_tools.ui_wrappers.base_wrapper import BaseWrapper

class ProcessorMixin:
    """Mixin that provides processor functionality without inheritance conflicts"""
    
    def __init__(self, config, task_queue_manager=None):
        # Create a BaseWrapper instance as a component rather than inheriting from it
        self._base_wrapper = BaseWrapper(config, task_queue_manager=task_queue_manager)
        
        # Expose BaseWrapper attributes and methods directly
        self.config = self._base_wrapper.config
        self.worker = self._base_wrapper.worker
        self._is_running = self._base_wrapper._is_running
        self.logger = self._base_wrapper.logger
        self.activity_log_service = self._base_wrapper.activity_log_service
        self.task_history_service = self._base_wrapper.task_history_service
        self._task_id = self._base_wrapper._task_id
        self.task_queue_manager = self._base_wrapper.task_queue_manager
        self._progress = self._base_wrapper._progress
        self._test_mode = self._base_wrapper._test_mode
        
        # Expose BaseWrapper signals directly
        self.progress_updated = self._base_wrapper.progress_updated
        self.status_updated = self._base_wrapper.status_updated
        self.error_occurred = self._base_wrapper.error_occurred
        self.completed = self._base_wrapper.completed
        
        # Add processor-specific signal manually (this needs to be on the QWidget)
        # We'll set this up in the wrapper classes that inherit from QWidget
        self.file_processed = None  # Will be set up by the QWidget subclass
    
    def _create_target_object(self):
        """Delegate to BaseWrapper"""
        return self._base_wrapper._create_target_object()
    
    def _get_operation_type(self):
        """Delegate to BaseWrapper"""
        return self._base_wrapper._get_operation_type()
    
    def start(self, **kwargs):
        """Delegate to BaseWrapper"""
        return self._base_wrapper.start(**kwargs)
    
    def stop(self):
        """Delegate to BaseWrapper"""
        return self._base_wrapper.stop()
    
    def get_status(self):
        """Delegate to BaseWrapper"""
        return self._base_wrapper.get_status()
    
    def is_running(self):
        """Delegate to BaseWrapper"""
        return self._base_wrapper.is_running()
    
    def set_test_mode(self, enabled=True):
        """Delegate to BaseWrapper"""
        return self._base_wrapper.set_test_mode(enabled)
    
    def refresh_config(self):
        """Delegate to BaseWrapper"""
        return self._base_wrapper.refresh_config()
    
    def get_processing_stats(self):
        """Get processing statistics"""
        if hasattr(self, 'target') and hasattr(self.target, 'get_stats'):
            return self.target.get_stats()
        return {"files_processed": 0, "success_rate": 0.0} 