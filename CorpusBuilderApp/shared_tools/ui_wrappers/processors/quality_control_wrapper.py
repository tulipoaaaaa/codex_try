# File: shared_tools/ui_wrappers/processors/quality_control_wrapper.py

from PySide6.QtCore import Signal as pyqtSignal, QObject, QThread
from shared_tools.processors.quality_control import QualityControl
from shared_tools.ui_wrappers.base_wrapper import BaseWrapper
from shared_tools.processors.mixins.processor_wrapper_mixin import ProcessorWrapperMixin

class QualityControlWrapper(BaseWrapper, ProcessorWrapperMixin):
    """UI wrapper for the Quality Control processor."""
    
    quality_score_calculated = pyqtSignal(str, float)  # file_path, score
    
    def __init__(self, project_config):
        super().__init__(project_config)
        self.project_config = project_config  # Ensure attribute exists for tests
        self.processor = QualityControl(project_config)
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
        
    def _on_status_updated(self, *args, **kwargs):
        pass
        
class QCWorkerThread(QThread):
    """Worker thread for quality control processing."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    quality_score_calculated = pyqtSignal(str, float)
    processing_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, processor, file_paths, **kwargs):
        super().__init__()
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
