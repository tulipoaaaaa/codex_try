# File: shared_tools/ui_wrappers/processors/machine_translation_detector_wrapper.py

from PySide6.QtCore import Signal as pyqtSignal, QThread
from shared_tools.processors.machine_translation_detector import MachineTranslationDetector
from shared_tools.ui_wrappers.base_wrapper import BaseWrapper
from shared_tools.processors.mixins.processor_wrapper_mixin import ProcessorWrapperMixin

class MachineTranslationDetectorWrapper(BaseWrapper, ProcessorWrapperMixin):
    """UI wrapper for the Machine Translation Detector processor."""
    
    translation_detected = pyqtSignal(str, bool, float)  # file_path, is_translated, confidence
    
    def __init__(self, project_config):
        super().__init__(project_config)
        self.processor = MachineTranslationDetector(project_config)
        self._is_running = False
        self.worker_thread = None
        
    def start(self, file_paths=None, **kwargs):
        """Start machine translation detection on the specified files."""
        if self._is_running:
            self.status_updated.emit("Machine translation detection already in progress")
            return False
            
        self._is_running = True
        self.status_updated.emit("Starting machine translation detection...")
        
        # Create and configure worker thread
        self.worker_thread = MTDetectorWorkerThread(
            self.processor, 
            file_paths,
            **kwargs
        )
        
        # Connect signals
        self.worker_thread.progress_updated.connect(self._on_progress_updated)
        self.worker_thread.status_updated.connect(self._on_status_updated)
        self.worker_thread.translation_detected.connect(self._on_translation_detected)
        self.worker_thread.processing_completed.connect(self._on_processing_completed)
        self.worker_thread.error_occurred.connect(self._on_error)
        
        # Start the thread
        self.worker_thread.start()
        return True
        
    def stop(self):
        """Stop the machine translation detection processing."""
        if not self._is_running:
            return False
            
        if self.worker_thread:
            self.worker_thread.requestInterruption()
            self.status_updated.emit("Stopping machine translation detection...")
            
        return True
        
    def get_status(self):
        """Get the current status of the processor."""
        return {
            "is_running": self._is_running,
            "processor_type": "machine_translation_detector"
        }
        
    def _on_translation_detected(self, file_path, is_translated, confidence):
        """Handle machine translation detection result."""
        self.translation_detected.emit(file_path, is_translated, confidence)
        
    def _on_processing_completed(self, results):
        """Handle completion of machine translation detection."""
        self._is_running = False
        self.batch_completed.emit(results)
        translated_count = sum(1 for result in results.values() if result.get('is_translated', False))
        self.status_updated.emit(
            f"Machine translation detection completed: {translated_count} translated documents found in {len(results)} files"
        )

class MTDetectorWorkerThread(QThread):
    """Worker thread for machine translation detection processing."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    translation_detected = pyqtSignal(str, bool, float)
    processing_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, processor, file_paths, **kwargs):
        super().__init__()
        self.processor = processor
        self.file_paths = file_paths or []
        self.kwargs = kwargs
        
    def run(self):
        """Run the machine translation detection processing."""
        try:
            results = {}
            
            for i, file_path in enumerate(self.file_paths):
                # Check for interruption
                if self.isInterruptionRequested():
                    break
                    
                # Update progress
                progress = int(((i + 1) / len(self.file_paths)) * 100)
                self.progress_updated.emit(progress)
                self.status_updated.emit(f"Checking translation for {file_path}...")
                
                try:
                    # Detect machine translation for the file
                    result = self.processor.detect_machine_translation(file_path, **self.kwargs)
                    
                    is_translated = result.get('is_translated', False)
                    confidence = result.get('confidence', 0.0)
                    
                    # Emit the detection result
                    self.translation_detected.emit(file_path, is_translated, confidence)
                    
                    # Store result
                    results[file_path] = result
                    
                except Exception as e:
                    self.status_updated.emit(f"Error checking translation for {file_path}: {str(e)}")
                    results[file_path] = {'is_translated': False, 'confidence': 0.0, 'error': str(e)}
            
            # Complete processing
            self.processing_completed.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(f"Machine translation detection error: {str(e)}")
