# File: shared_tools/ui_wrappers/processors/quality_control_wrapper.py

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal
from shared_tools.processors.quality_control import QualityControl
import logging

class QualityControlWrapper(QWidget):
    """UI wrapper for Quality Control processor."""
    
    # Signals to expose
    quality_score_calculated = Signal(str, float)
    status_updated = Signal(str)
    progress_updated = Signal(int)
    batch_completed = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, project_config, parent=None, **kwargs):
        print(f"[DEBUG] QualityControlWrapper.__init__ called")
        QWidget.__init__(self, parent)
        if project_config is None:
            raise RuntimeError("QualityControlWrapper requires a non-None ProjectConfig")
        self.project_config = project_config
        self._processor = QualityControl(project_config=project_config)
        print("[DEBUG] QualityControl processor created successfully")

        # Connect processor signals to wrapper signals (if processor emits them)
        # (Assume you will connect these externally if needed, or extend processor to emit Qt signals)
        # If processor is not a QObject, you may need to emit these manually in your wrapper methods.

        # State variables
        self._is_running = False
        self.worker_thread = None
        self.quality_threshold = 70  # Default threshold
        
        # Set up UI
        self.setup_ui()
        print("[DEBUG] QualityControlWrapper initialization completed")
    
    # --- Properties to Delegate ---
    @property
    def config(self):
        return self._processor.config
    
    @property
    def logger(self):
        return getattr(self._processor, 'logger', None)
    
    @property
    def task_history_service(self):
        return getattr(self._processor, 'task_history_service', None)
    
    @property
    def activity_log_service(self):
        return getattr(self._processor, 'activity_log_service', None)
    
    @property
    def _task_id(self):
        return getattr(self._processor, '_task_id', None)
    
    @_task_id.setter
    def _task_id(self, value):
        if hasattr(self._processor, '_task_id'):
            self._processor._task_id = value
    
    @property
    def task_queue_manager(self):
        return getattr(self._processor, 'task_queue_manager', None)
    
    @task_queue_manager.setter
    def task_queue_manager(self, value):
        if hasattr(self._processor, 'task_queue_manager'):
            self._processor.task_queue_manager = value
    
    @property
    def target(self):
        return getattr(self._processor, 'target', None)
    
    @target.setter
    def target(self, value):
        if hasattr(self._processor, 'target'):
            self._processor.target = value
    
    @property
    def _progress(self):
        return getattr(self._processor, '_progress', 0)
    
    @_progress.setter
    def _progress(self, value):
        if hasattr(self._processor, '_progress'):
            self._processor._progress = value
    
    @property
    def _test_mode(self):
        return getattr(self._processor, '_test_mode', False)
    
    @_test_mode.setter
    def _test_mode(self, value):
        if hasattr(self._processor, '_test_mode'):
            self._processor._test_mode = value
    
    @property
    def is_running(self):
        return self._is_running
    
    @is_running.setter
    def is_running(self, value):
        self._is_running = value
    
    # --- Methods to Delegate ---
    def start(self, *args, **kwargs):
        # You may want to emit signals here as needed
        self._is_running = True
        # If your processor has a start method, call it
        if hasattr(self._processor, 'start'):
            return self._processor.start(*args, **kwargs)
        return None
    
    def stop(self, *args, **kwargs):
        self._is_running = False
        if hasattr(self._processor, 'stop'):
            return self._processor.stop(*args, **kwargs)
        return None
    
    def get_status(self, *args, **kwargs):
        if hasattr(self._processor, 'get_status'):
            return self._processor.get_status(*args, **kwargs)
        return None
    
    def set_test_mode(self, enabled=True):
        if hasattr(self._processor, 'set_test_mode'):
            return self._processor.set_test_mode(enabled)
        return None

    def refresh_config(self):
        if hasattr(self._processor, 'refresh_config'):
            return self._processor.refresh_config()
        return None
    
    def get_processing_stats(self):
        if hasattr(self._processor, 'get_processing_stats'):
            return self._processor.get_processing_stats()
        return None
    
    # Example: delegate a method to the processor
    def process_batch(self, *args, **kwargs):
        if hasattr(self._processor, 'process_batch'):
            return self._processor.process_batch(*args, **kwargs)
        return None
    
    # --- UI Setup ---
    def setup_ui(self):
        layout = QVBoxLayout(self)
        # Add your UI components here
        # (Preserve any previous UI logic here)
                    
    # Add any other methods or signal handlers as needed, preserving previous logic
