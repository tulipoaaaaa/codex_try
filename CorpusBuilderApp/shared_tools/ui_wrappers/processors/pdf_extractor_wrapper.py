from PySide6.QtCore import Signal as pyqtSignal, QThread
import time
from shared_tools.processors.pdf_extractor import PDFExtractor
from shared_tools.ui_wrappers.processors.processor_mixin import ProcessorMixin
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

class PDFExtractorWrapper:
    """UI wrapper for PDF Extractor"""
    
    file_processed = pyqtSignal(str, bool)  # filepath, success
    total_pages_processed = pyqtSignal(int)  # Total pages processed
    ocr_used = pyqtSignal(str, bool)  # filepath, ocr_used
    
    def __init__(self, config, task_queue_manager=None):
        ProcessorMixin.__init__(self, config, task_queue_manager=task_queue_manager)
        
        # Set up delegation for frequently used attributes
        self.config = self._bw.config  # delegation
        self.logger = self._bw.logger  # delegation
        
        self.extractor = None
        self.enable_ocr = True
        self.extract_tables = True
        self.extract_formulas = True
        self.worker_threads = 4
        
    def _create_target_object(self):
        """Create PDF extractor instance"""
        if not self.extractor:
            self.extractor = PDFExtractor(
                input_dir=str(self.config.raw_data_dir),
                output_dir=str(self.config.pdf_extracted_dir),
                num_workers=self.worker_threads
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

    def set_worker_threads(self, count: int):
        """Set the number of worker threads for processing"""
        self.worker_threads = count
        if self.extractor:
            self.extractor.num_workers = count
        
    def start_batch_processing(self, files_to_process: List[str]):
        """Start batch processing of PDF files"""
        if self._is_running:
            self.status_updated.emit("Processing already in progress")
            return

        self._is_running = True
        self.status_updated.emit(f"Starting PDF processing of {len(files_to_process)} files...")
        if self.task_history_service:
            self._current_task_id = f"PDFExtractor_{int(time.time()*1000)}"
            self.task_history_service.start_task(self._current_task_id, "PDF Batch")

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

    def refresh_config(self):
        """Reload parameters from ``self.config``."""
        cfg = {}
        if hasattr(self.config, 'get_processor_config'):
            cfg = self.config.get_processor_config('pdf_extractor') or {}
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
