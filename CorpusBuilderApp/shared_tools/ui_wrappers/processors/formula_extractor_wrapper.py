# File: shared_tools/ui_wrappers/processors/formula_extractor_wrapper.py

from PySide6.QtCore import Signal as pyqtSignal, QThread
from shared_tools.processors.formula_extractor import FormulaExtractor
from shared_tools.ui_wrappers.base_wrapper import BaseWrapper
from shared_tools.processors.mixins.processor_wrapper_mixin import ProcessorWrapperMixin

class FormulaExtractorWrapper(BaseWrapper, ProcessorWrapperMixin):
    """UI wrapper for the Formula Extractor processor."""
    
    formula_extracted = pyqtSignal(str, list)  # file_path, formulas
    
    def __init__(self, project_config):
        super().__init__(project_config)
        self.processor = FormulaExtractor(project_config)
        self._is_running = False
        self.worker_thread = None
        
    def start(self, file_paths=None, **kwargs):
        """Start formula extraction on the specified files."""
        if self._is_running:
            self.status_updated.emit("Formula extraction already in progress")
            return False
            
        self._is_running = True
        self.status_updated.emit("Starting formula extraction...")
        
        # Create and configure worker thread
        self.worker_thread = FormulaExtractorWorkerThread(
            self.processor, 
            file_paths,
            **kwargs
        )
        
        # Connect signals
        self.worker_thread.progress_updated.connect(self._on_progress_updated)
        self.worker_thread.status_updated.connect(self._on_status_updated)
        self.worker_thread.formula_extracted.connect(self._on_formula_extracted)
        self.worker_thread.processing_completed.connect(self._on_processing_completed)
        self.worker_thread.error_occurred.connect(self._on_error)
        
        # Start the thread
        self.worker_thread.start()
        return True
        
    def stop(self):
        """Stop the formula extraction processing."""
        if not self._is_running:
            return False
            
        if self.worker_thread:
            self.worker_thread.requestInterruption()
            self.status_updated.emit("Stopping formula extraction...")
            
        return True
        
    def get_status(self):
        """Get the current status of the processor."""
        return {
            "is_running": self._is_running,
            "processor_type": "formula_extractor"
        }
        
    def _on_formula_extracted(self, file_path, formulas):
        """Handle formula extraction result."""
        self.formula_extracted.emit(file_path, formulas)
        
    def _on_processing_completed(self, results):
        """Handle completion of formula extraction."""
        self._is_running = False
        self.batch_completed.emit(results)
        total_formulas = sum(len(formulas) for formulas in results.values())
        self.status_updated.emit(
            f"Formula extraction completed: {total_formulas} formulas extracted from {len(results)} files"
        )

class FormulaExtractorWorkerThread(QThread):
    """Worker thread for formula extraction processing."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    formula_extracted = pyqtSignal(str, list)
    processing_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, processor, file_paths, **kwargs):
        super().__init__()
        self.processor = processor
        self.file_paths = file_paths or []
        self.kwargs = kwargs
        
    def run(self):
        """Run the formula extraction processing."""
        try:
            results = {}
            
            for i, file_path in enumerate(self.file_paths):
                # Check for interruption
                if self.isInterruptionRequested():
                    break
                    
                # Update progress
                progress = int(((i + 1) / len(self.file_paths)) * 100)
                self.progress_updated.emit(progress)
                self.status_updated.emit(f"Extracting formulas from {file_path}...")
                
                try:
                    # Extract formulas from the file
                    formulas = self.processor.extract_formulas(file_path, **self.kwargs)
                    
                    # Emit the extraction result
                    self.formula_extracted.emit(file_path, formulas)
                    
                    # Store result
                    results[file_path] = formulas
                    
                except Exception as e:
                    self.status_updated.emit(f"Error extracting formulas from {file_path}: {str(e)}")
                    results[file_path] = []
            
            # Complete processing
            self.processing_completed.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(f"Formula extraction error: {str(e)}")
