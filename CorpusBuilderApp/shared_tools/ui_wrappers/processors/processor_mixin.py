from shared_tools.ui_wrappers.base_wrapper import BaseWrapper
from shared_tools.processors.mixins.processor_wrapper_mixin import ProcessorWrapperMixin
from PySide6.QtCore import Signal as pyqtSignal

class ProcessorMixin:
    """Logic mix-in (no Qt). Holds BaseWrapper + ProcessorWrapperMixin via composition."""
    
    # Define file_processed signal as a placeholder (will be overridden in each wrapper)
    file_processed = pyqtSignal(str, bool)  # filepath, success
    
    def __init__(self, config, task_queue_manager=None):
        self._bw = BaseWrapper(config, task_queue_manager=task_queue_manager)
        ProcessorWrapperMixin.__init__(self)

    # Delegate frequently-used attributes
    @property
    def config(self):
        return self._bw.config

    @property
    def logger(self):
        return self._bw.logger

    @property
    def completed(self):
        return self._bw.completed

    @property
    def status_updated(self):
        return self._bw.status_updated

    @property
    def progress_updated(self):
        return self._bw.progress_updated

    @property
    def error_occurred(self):
        return self._bw.error_occurred

    @property
    def _is_running(self):
        return self._bw._is_running
    
    @_is_running.setter
    def _is_running(self, value):
        self._bw._is_running = value

    @property
    def worker(self):
        return self._bw.worker
    
    @worker.setter
    def worker(self, value):
        self._bw.worker = value

    @property
    def task_history_service(self):
        """Delegate task_history_service if it exists"""
        return getattr(self._bw, 'task_history_service', None)

    @property
    def activity_log_service(self):
        """Delegate activity_log_service if it exists"""
        return getattr(self._bw, 'activity_log_service', None)

    @property
    def _task_id(self):
        """Delegate _task_id if it exists"""
        return getattr(self._bw, '_task_id', None)
    
    @_task_id.setter
    def _task_id(self, value):
        if hasattr(self._bw, '_task_id'):
            self._bw._task_id = value

    @property
    def task_queue_manager(self):
        """Delegate task_queue_manager from BaseWrapper"""
        return getattr(self._bw, 'task_queue_manager', None)
    
    @task_queue_manager.setter  
    def task_queue_manager(self, value):
        """Set task_queue_manager on BaseWrapper"""
        self._bw.task_queue_manager = value

    @property
    def batch_completed(self):
        """Delegate batch_completed signal - many wrappers alias this to completed"""
        return self._bw.completed

    @property
    def processor(self):
        """Delegate processor attribute - some wrappers have this"""
        return getattr(self, '_processor', None)
    
    @processor.setter
    def processor(self, value):
        """Set processor attribute"""
        self._processor = value

    @property
    def target(self):
        """Delegate target attribute - used by get_processing_stats and some tests"""
        return getattr(self._bw, 'target', None)
    
    @target.setter  
    def target(self, value):
        """Set target attribute on BaseWrapper"""
        if hasattr(self._bw, 'target'):
            self._bw.target = value

    @property
    def _progress(self):
        """Delegate _progress from BaseWrapper - used for internal progress tracking"""
        return getattr(self._bw, '_progress', 0)
    
    @_progress.setter
    def _progress(self, value):
        """Set _progress on BaseWrapper"""
        if hasattr(self._bw, '_progress'):
            self._bw._progress = value

    @property  
    def _test_mode(self):
        """Delegate _test_mode from BaseWrapper - used by test framework"""
        return getattr(self._bw, '_test_mode', False)

    @_test_mode.setter
    def _test_mode(self, value):
        """Set _test_mode on BaseWrapper""" 
        if hasattr(self._bw, '_test_mode'):
            self._bw._test_mode = value

    def __getattr__(self, name):
        """
        Automatic delegation fallback for any missing attributes.
        This follows composition best practices by transparently 
        delegating to the composed BaseWrapper instance.
        """
        # First try BaseWrapper delegation
        if hasattr(self._bw, name):
            attr = getattr(self._bw, name)
            # Cache frequently-accessed attributes for performance
            if not name.startswith('_') and not callable(attr):
                setattr(self, name, attr)
            return attr
        
        # If not found, raise AttributeError as normal
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    # Delegate callback methods from BaseWrapper
    def _on_progress(self, current, total, message):
        return self._bw._on_progress(current, total, message)
    
    def _on_error(self, error_message):
        return self._bw._on_error(error_message)

    def _on_finished(self, results):
        return self._bw._on_finished(results)
    
    # Delegate common methods from BaseWrapper
    def _create_target_object(self):
        return self._bw._create_target_object()
    
    def _get_operation_type(self):
        return self._bw._get_operation_type()
    
    def start(self, **kwargs):
        return self._bw.start(**kwargs)
    
    def stop(self):
        return self._bw.stop()
    
    def get_status(self):
        return self._bw.get_status()
    
    def is_running(self):
        return self._bw.is_running()
    
    def set_test_mode(self, enabled=True):
        return self._bw.set_test_mode(enabled)
    
    def refresh_config(self):
        return self._bw.refresh_config()

    # Delegate ProcessorWrapperMixin methods
    def get_processing_stats(self):
        """Get processing statistics"""
        return ProcessorWrapperMixin.get_processing_stats(self) 