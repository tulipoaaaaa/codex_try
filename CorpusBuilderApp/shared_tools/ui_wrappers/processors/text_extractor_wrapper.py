"""
Text Extractor Wrapper for UI Integration
Provides text extraction capabilities with UI controls
"""

from PySide6.QtCore import Signal as pyqtSignal, QThread
import time
from shared_tools.processors.text_extractor import TextExtractor
from shared_tools.ui_wrappers.processors.processor_mixin import ProcessorMixin
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

class TextExtractorWrapper:
    """UI wrapper for Non-PDF Text Extractor"""
    
    file_processed = pyqtSignal(str, bool)  # filepath, success
    mime_type_detected = pyqtSignal(str, str)  # filepath, mime_type
    
    def __init__(self, config, task_queue_manager=None):
        ProcessorMixin.__init__(self, config, task_queue_manager=task_queue_manager)
        
        # Set up delegation for frequently used attributes
        self.config = self._bw.config  # delegation
        self.logger = self._bw.logger  # delegation
        
        self.extractor = None
        self.worker_threads = 4
        
    def _create_target_object(self):
        """Create Text extractor instance"""
        if not self.extractor:
            self.extractor = TextExtractor(
                input_dir=str(self.config.raw_data_dir),
                output_dir=str(self.config.nonpdf_extracted_dir),
                num_workers=self.worker_threads
            )
        return self.extractor
        
    def _get_operation_type(self):
        return "extract_text"

    def set_worker_threads(self, count: int):
        """Set the number of worker threads for processing"""
        self.worker_threads = count
        if self.extractor:
            self.extractor.num_workers = count
        
    def start_batch_processing(self, files_to_process: List[str]):
        """Start batch processing of non-PDF files"""
        if self._is_running:
            self.status_updated.emit("Processing already in progress")
            return

        self._is_running = True
        self.status_updated.emit(f"Starting non-PDF processing of {len(files_to_process)} files...")
        if self.task_history_service:
            self._current_task_id = f"TextExtractor_{int(time.time()*1000)}"
            self.task_history_service.start_task(self._current_task_id, "Text Batch")

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

    def refresh_config(self):
        """Reload parameters from ``self.config``."""
        cfg = {}
        if hasattr(self.config, 'get_processor_config'):
            cfg = self.config.get_processor_config('text_extractor') or {}
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
