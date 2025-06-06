"""
Text Extractor Wrapper for UI Integration
Provides text extraction capabilities with UI controls
"""

from PySide6.QtCore import Signal as pyqtSignal, QThread
from ..base_wrapper import BaseWrapper, ProcessorWrapperMixin
from shared_tools.processors.text_extractor import TextExtractor
from typing import List, Dict, Any
from pathlib import Path

class TextExtractorWorker(QThread):
    """Worker thread for Non-PDF Text Extraction"""
    progress = pyqtSignal(int, int, str)  # current, total, message
    error = pyqtSignal(str)
    finished = pyqtSignal(dict)
    file_processed = pyqtSignal(str, bool)  # filepath, success
    
    def __init__(self, extractor, files_to_process, **kwargs):
        super().__init__()
        self.extractor = extractor
        self.files = files_to_process
        self.kwargs = kwargs
        self._should_stop = False
        
    def run(self):
        """Run text extraction on multiple files"""
        results = {}
        for i, file_path in enumerate(self.files):
            if self._should_stop:
                break
                
            try:
                # Emit progress
                self.progress.emit(i+1, len(self.files), f"Processing {Path(file_path).name}")
                
                # Process the file
                text, metadata = self.extractor.extract_text(file_path, **self.kwargs)
                
                # Store results
                results[file_path] = {
                    "success": True,
                    "text_length": len(text),
                    "metadata": metadata
                }
                
                # Emit success
                self.file_processed.emit(file_path, True)
                
            except Exception as e:
                # Handle error
                error_msg = f"Error processing {Path(file_path).name}: {str(e)}"
                self.error.emit(error_msg)
                
                results[file_path] = {
                    "success": False,
                    "error": str(e)
                }
                
                # Emit failure
                self.file_processed.emit(file_path, False)
                
        # Emit finished with all results
        self.finished.emit(results)
            
    def stop(self):
        """Stop processing"""
        self._should_stop = True

class TextExtractorWrapper(BaseWrapper, ProcessorWrapperMixin):
    """UI wrapper for Non-PDF Text Extractor"""
    
    file_processed = pyqtSignal(str, bool)  # filepath, success
    mime_type_detected = pyqtSignal(str, str)  # filepath, mime_type
    
    def __init__(self, config):
        super().__init__(config)
        self.extractor = None
        
    def _create_target_object(self):
        """Create Text extractor instance"""
        if not self.extractor:
            self.extractor = TextExtractor(
                input_dir=str(self.config.raw_data_dir),
                output_dir=str(self.config.nonpdf_extracted_dir),
                num_workers=4
            )
        return self.extractor
        
    def _get_operation_type(self):
        return "extract_text"
        
    def start_batch_processing(self, files_to_process: List[str]):
        """Start batch processing of non-PDF files"""
        if self._is_running:
            self.status_updated.emit("Processing already in progress")
            return
            
        self._is_running = True
        self.status_updated.emit(f"Starting non-PDF processing of {len(files_to_process)} files...")
        
        # Create extractor instance
        extractor = self._create_target_object()
        
        # Create worker thread
        self.worker = TextExtractorWorker(
            extractor, 
            files_to_process
        )
        
        # Connect signals
        self.worker.progress.connect(self._on_progress)
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(self._on_finished)
        self.worker.file_processed.connect(self.file_processed)
        
        # Start worker
        self.worker.start()
        
    def get_format_stats(self):
        """Get statistics about processed file formats"""
        if self.extractor:
            return {"formats_processed": self.extractor.format_counts}
        return {"formats_processed": {}}