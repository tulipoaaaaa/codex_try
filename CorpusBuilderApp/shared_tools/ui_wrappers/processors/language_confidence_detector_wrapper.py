# File: shared_tools/ui_wrappers/processors/language_confidence_detector_wrapper.py

from PySide6.QtCore import Signal as pyqtSignal, QThread
from shared_tools.processors.language_confidence_detector import LanguageConfidenceDetector
from shared_tools.ui_wrappers.base_wrapper import BaseWrapper
from shared_tools.processors.mixins.processor_wrapper_mixin import ProcessorWrapperMixin

class LanguageConfidenceDetectorWrapper(BaseWrapper, ProcessorWrapperMixin):
    """UI wrapper for the Language Confidence Detector processor."""
    
    language_detected = pyqtSignal(str, str, float)  # file_path, language, confidence
    
    def __init__(self, project_config):
        super().__init__(project_config)
        self.processor = LanguageConfidenceDetector(project_config)
        self._is_running = False
        self.worker_thread = None
        
    def start(self, file_paths=None, **kwargs):
        """Start language detection on the specified files."""
        if self._is_running:
            self.status_updated.emit("Language detection already in progress")
            return False
            
        self._is_running = True
        self.status_updated.emit("Starting language detection...")
        
        # Create and configure worker thread
        self.worker_thread = LanguageDetectorWorkerThread(
            self.processor, 
            file_paths,
            **kwargs
        )
        
        # Connect signals
        self.worker_thread.progress_updated.connect(self._on_progress_updated)
        self.worker_thread.status_updated.connect(self._on_status_updated)
        self.worker_thread.language_detected.connect(self._on_language_detected)
        self.worker_thread.processing_completed.connect(self._on_processing_completed)
        self.worker_thread.error_occurred.connect(self._on_error)
        
        # Start the thread
        self.worker_thread.start()
        return True
        
    def stop(self):
        """Stop the language detection processing."""
        if not self._is_running:
            return False
            
        if self.worker_thread:
            self.worker_thread.requestInterruption()
            self.status_updated.emit("Stopping language detection...")
            
        return True
        
    def get_status(self):
        """Get the current status of the processor."""
        return {
            "is_running": self._is_running,
            "processor_type": "language_confidence_detector"
        }
        
    def _on_language_detected(self, file_path, language, confidence):
        """Handle language detection result."""
        self.language_detected.emit(file_path, language, confidence)
        
    def _on_processing_completed(self, results):
        """Handle completion of language detection."""
        self._is_running = False
        self.batch_completed.emit(results)
        self.status_updated.emit(
            f"Language detection completed: {len(results)} files processed"
        )

class LanguageDetectorWorkerThread(QThread):
    """Worker thread for language detection processing."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    language_detected = pyqtSignal(str, str, float)
    processing_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, processor, file_paths, **kwargs):
        super().__init__()
        self.processor = processor
        self.file_paths = file_paths or []
        self.kwargs = kwargs
        
    def run(self):
        """Run the language detection processing."""
        try:
            results = {}
            
            for i, file_path in enumerate(self.file_paths):
                # Check for interruption
                if self.isInterruptionRequested():
                    break
                    
                # Update progress
                progress = int(((i + 1) / len(self.file_paths)) * 100)
                self.progress_updated.emit(progress)
                self.status_updated.emit(f"Detecting language for {file_path}...")
                
                try:
                    # Detect language for the file
                    result = self.processor.detect_language(file_path, **self.kwargs)
                    
                    language = result.get('language', 'unknown')
                    confidence = result.get('confidence', 0.0)
                    
                    # Emit the detection result
                    self.language_detected.emit(file_path, language, confidence)
                    
                    # Store result
                    results[file_path] = result
                    
                except Exception as e:
                    self.status_updated.emit(f"Error detecting language for {file_path}: {str(e)}")
                    results[file_path] = {'language': 'unknown', 'confidence': 0.0, 'error': str(e)}
            
            # Complete processing
            self.processing_completed.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(f"Language detection error: {str(e)}")
