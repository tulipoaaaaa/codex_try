from PySide6.QtCore import Signal as pyqtSignal, QThread
from ..base_wrapper import BaseWrapper, ProcessorWrapperMixin
from shared_tools.processors.pdf_extractor import PDFExtractor
from typing import List, Dict, Any
from pathlib import Path

class PDFExtractorWorker(QThread):
    """Worker thread for PDF Extraction"""
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
        """Run PDF extraction on multiple files"""
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

class PDFExtractorWrapper(BaseWrapper, ProcessorWrapperMixin):
    """UI wrapper for PDF Extractor"""
    
    file_processed = pyqtSignal(str, bool)  # filepath, success
    total_pages_processed = pyqtSignal(int)  # Total pages processed
    ocr_used = pyqtSignal(str, bool)  # filepath, ocr_used
    
    def __init__(self, config):
        super().__init__(config)
        self.extractor = None
        self.enable_ocr = True
        self.extract_tables = True
        self.extract_formulas = True
        
    def _create_target_object(self):
        """Create PDF extractor instance"""
        if not self.extractor:
            self.extractor = PDFExtractor(
                input_dir=str(self.config.raw_data_dir),
                output_dir=str(self.config.pdf_extracted_dir),
                num_workers=4
            )
        return self.extractor
        
    def _get_operation_type(self):
        return "extract_text"
        
    def set_ocr_enabled(self, enabled):
        """Set OCR enabled/disabled"""
        self.enable_ocr = enabled
        
    def set_table_extraction(self, enabled):
        """Set table extraction enabled/disabled"""
        self.extract_tables = enabled
        
    def set_formula_extraction(self, enabled):
        """Set formula extraction enabled/disabled"""
        self.extract_formulas = enabled
        
    def start_batch_processing(self, files_to_process: List[str]):
        """Start batch processing of PDF files"""
        if self._is_running:
            self.status_updated.emit("Processing already in progress")
            return
            
        self._is_running = True
        self.status_updated.emit(f"Starting PDF processing of {len(files_to_process)} files...")
        
        # Create extractor instance
        extractor = self._create_target_object()
        
        # Create worker thread
        self.worker = PDFExtractorWorker(
            extractor, 
            files_to_process,
            enable_ocr=self.enable_ocr,
            extract_tables=self.extract_tables,
            extract_formulas=self.extract_formulas
        )
        
        # Connect signals
        self.worker.progress.connect(self._on_progress)
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(self._on_finished)
        self.worker.file_processed.connect(self.file_processed)
        
        # Start worker
        self.worker.start()
        
    def get_ocr_stats(self):
        """Get OCR usage statistics"""
        if self.extractor:
            return {"files_processed": self.extractor.files_processed,
                    "ocr_used_count": self.extractor.ocr_used_count}
        return {"files_processed": 0, "ocr_used_count": 0}
