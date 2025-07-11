# File: shared_tools/ui_wrappers/processors/quality_control_wrapper.py

from PySide6.QtCore import Signal as pyqtSignal, QObject, QThread
from PySide6.QtWidgets import QWidget
from shared_tools.processors.quality_control import QualityControl
from shared_tools.ui_wrappers.processors.processor_mixin import ProcessorMixin
import logging, traceback

class QualityControlWrapper(QWidget):
    """UI wrapper for the Quality Control processor."""
    
    quality_score_calculated = pyqtSignal(str, float)  # file_path, score
    
    def __init__(
        self,
        config,
        task_queue_manager=None,
        parent=None,
    ):
        """
        Parameters
        ----------
        config : ProjectConfig | str
            Mandatory. Passed straight to BaseWrapper.
        task_queue_manager : TaskQueueManager | None
        parent : QWidget | None
        """
        # Initialize base classes in correct order
        QWidget.__init__(self, parent)  # Initialize QWidget first
        ProcessorMixin.__init__(self, config, task_queue_manager=task_queue_manager)  # Then initialize ProcessorMixin
        
        # Set up delegation for frequently used attributes
        self.config = self._bw.config  # delegation
        self.logger = self._bw.logger  # delegation
        
        # Delegate signals from BaseWrapper
        self.status_updated = self._bw.status_updated
        self.progress_updated = self._bw.progress_updated
        self.batch_completed = self._bw.completed
        
        # Delegate task tracking attributes
        self.task_history_service = self._bw.task_history_service
        self._task_id = self._bw._task_id

        # 2. guard: refuse to run without config
        if config is None:
            logging.error("QualityControlWrapper called with config=None")
            traceback.print_stack(limit=8)
            raise RuntimeError("QualityControlWrapper requires a non-None config")

        self.task_queue_manager = task_queue_manager
        self.project_config = config  # Ensure attribute exists for tests
        self.processor = QualityControl(config)
        self._is_running = False
        self.worker_thread = None
        self.quality_threshold = 70  # Default threshold
        
    def start(self, file_paths=None, **kwargs):
        """Start quality control processing on the specified files."""
        if self._is_running:
            self.status_updated.emit("Quality control already in progress")
            return False
            
        self._is_running = True
        self.status_updated.emit("Starting quality control processing...")
        
        # Create and configure worker thread
        self.worker_thread = QCWorkerThread(
            self.processor, 
            file_paths,
            quality_threshold=self.quality_threshold,
            **kwargs
        )
        
        # Connect signals
        self.worker_thread.progress_updated.connect(self._on_progress_updated)
        self.worker_thread.status_updated.connect(self._on_status_updated)
        self.worker_thread.quality_score_calculated.connect(self._on_quality_score)
        self.worker_thread.processing_completed.connect(self._on_processing_completed)
        self.worker_thread.error_occurred.connect(self._on_error)
        
        # Start the thread
        self.worker_thread.start()
        return True
        
    def stop(self):
        """Stop the quality control processing."""
        if not self._is_running:
            return False
            
        if self.worker_thread:
            self.worker_thread.requestInterruption()
            self.status_updated.emit("Stopping quality control processing...")
            
        return True
        
    def get_status(self):
        """Get the current status of the processor."""
        return {
            "is_running": self._is_running,
            "processor_type": "quality_control",
            "threshold": self.quality_threshold
        }
        
    def set_quality_threshold(self, threshold):
        """Set the quality threshold for document evaluation."""
        self.quality_threshold = threshold
        
    def _on_quality_score(self, file_path, score):
        """Handle quality score calculation for a file."""
        self.quality_score_calculated.emit(file_path, score)
        
    def _on_processing_completed(self, results):
        """Handle completion of quality control processing."""
        self._is_running = False
        self.batch_completed.emit(results)
        self.status_updated.emit(
            f"Quality control completed: {len(results.get('processed_files', []))} files processed"
        )
        
    def _on_progress_updated(self, progress):
        """Handle progress updates from worker thread."""
        self.progress_updated.emit(progress)
        
    def _on_status_updated(self, message: str) -> None:
        """Propagate status messages and update task history."""
        # Re-emit the status message
        self.status_updated.emit(message)

        # Update task log if we have a task id
        if getattr(self, "task_history_service", None) and getattr(self, "_task_id", None):
            try:
                self.task_history_service.update_task(self._task_id, details=message)
            except Exception:
                pass

        # If a status widget is available, append the message for visibility
        for attr in ("status_display", "status_widget", "status_list_widget"):
            widget = getattr(self, attr, None)
            if widget is not None and hasattr(widget, "append"):
                if not hasattr(widget, "isVisible") or widget.isVisible():
                    try:
                        widget.append(message)
                    except Exception:
                        pass

    def refresh_config(self):
        """Reload parameters from ``self.config``."""
        cfg = {}
        if hasattr(self.config, 'get_processor_config'):
            cfg = self.config.get_processor_config('quality_control') or {}
        for k, v in cfg.items():
            method = f'set_{k}'
            if hasattr(self, method):
                try:
                    getattr(self, method)(v)
                    continue
                except Exception:
                    self.logger.debug('Failed to apply %s via wrapper', k)
            if hasattr(self.processor, method):
                try:
                    getattr(self.processor, method)(v)
                    continue
                except Exception:
                    self.logger.debug('Failed to apply %s via processor', k)
            if hasattr(self.processor, k):
                setattr(self.processor, k, v)
            elif hasattr(self, k):
                setattr(self, k, v)
        if cfg and hasattr(self, 'configuration_changed'):
            self.configuration_changed.emit(cfg)

class QCWorkerThread(QThread):
    """Worker thread for quality control processing."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    quality_score_calculated = pyqtSignal(str, float)
    processing_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, processor, file_paths, **kwargs):
        QThread.__init__(self)  # Initialize QThread explicitly
        self.processor = processor
        self.file_paths = file_paths or []
        self.kwargs = kwargs
        
    def run(self):
        """Run the quality control processing."""
        try:
            results = {"processed_files": [], "success_count": 0, "fail_count": 0}
            
            for i, file_path in enumerate(self.file_paths):
                # Check for interruption
                if self.isInterruptionRequested():
                    break
                    
                # Update progress
                progress = int(((i + 1) / len(self.file_paths)) * 100)
                self.progress_updated.emit(progress)
                self.status_updated.emit(f"Processing {file_path}...")
                
                try:
                    # Process the file
                    score = self.processor.evaluate_quality(file_path, **self.kwargs)
                    
                    # Emit the quality score
                    self.quality_score_calculated.emit(file_path, score)
                    
                    # Update results
                    results["processed_files"].append({
                        "file_path": file_path,
                        "quality_score": score
                    })
                    results["success_count"] += 1
                    
                except Exception as e:
                    self.status_updated.emit(f"Error processing {file_path}: {str(e)}")
                    results["fail_count"] += 1
            
            # Complete processing
            self.processing_completed.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(f"Quality control error: {str(e)}")
