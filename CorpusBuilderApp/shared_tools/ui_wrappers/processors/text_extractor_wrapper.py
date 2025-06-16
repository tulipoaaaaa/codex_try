"""
Text Extractor Wrapper for UI Integration
Provides text extraction capabilities with UI controls
"""

from PySide6.QtCore import Signal as pyqtSignal, QThread
import time
from shared_tools.processors.text_extractor import TextExtractor
from shared_tools.project_config import ProjectConfig
from typing import List, Dict, Any
from pathlib import Path
from PySide6.QtWidgets import QWidget

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

class TextExtractorWrapper(QWidget):
    """UI wrapper for Non-PDF Text Extractor (migrated to QWidget-only, explicit delegation)"""
    status_updated = pyqtSignal(str)
    file_processed = pyqtSignal(str, bool)  # filepath, success
    mime_type_detected = pyqtSignal(str, str)  # filepath, mime_type

    def __init__(self, project_config, parent=None):
        QWidget.__init__(self, parent)
        if project_config is None:
            raise RuntimeError("TextExtractorWrapper requires a non-None ProjectConfig")
        self.project_config = project_config
        self.config = project_config.get('processors.text_extractor', {})
        self.logger = None  # Set up logger if needed
        self.extractor = None
        self.worker_threads = 4
        self.worker = None
        self._is_running = False
        # All signal-slot connections are made explicitly in methods

    def _create_target_object(self):
        """Create Text extractor instance"""
        if not self.extractor:
            self.extractor = TextExtractor(
                output_dir=str(self.config.get('nonpdf_extracted_dir', '')),
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
            return {"formats_processed": getattr(self.extractor, 'format_counts', {})}
        return {"formats_processed": {}}

    def refresh_config(self):
        """Reload parameters from ``self.config``."""
        cfg = {}
        if hasattr(self.project_config, 'get'):
            cfg = self.project_config.get('processors.text_extractor', {})
        for k, v in cfg.items():
            method = f'set_{k}'
            if hasattr(self, method):
                try:
                    getattr(self, method)(v)
                    continue
                except Exception:
                    if self.logger:
                        self.logger.debug('Failed to apply %s via wrapper', k)
            if hasattr(self.extractor, method):
                try:
                    getattr(self.extractor, method)(v)
                    continue
                except Exception:
                    if self.logger:
                        self.logger.debug('Failed to apply %s via extractor', k)
            if hasattr(self.extractor, k):
                setattr(self.extractor, k, v)
            elif hasattr(self, k):
                setattr(self, k, v)
        # No configuration_changed signal in this wrapper, so skip emit

    # ------------------------------------------------------------------
    # Dummy slots so connections from worker don't fail when running headless
    # ------------------------------------------------------------------
    def _on_progress(self, current: int, total: int, msg: str):
        if self.logger:
            self.logger.info("Text progress %d/%d: %s", current, total, msg)

    def _on_error(self, msg: str):
        if self.logger:
            self.logger.error(msg)

    def _on_finished(self, results: dict):
        if self.logger:
            self.logger.info("Text extraction finished – %d files", len(results))
        self._is_running = False

    # ------------------------------------------------------------------
    # Convenience entry-point for CLI (mirrors PDF wrapper)
    # ------------------------------------------------------------------
    def start(self):
        """Detect non-PDF files under raw_dir and process them."""
        try:
            raw_dir = self.project_config.get_raw_dir()
        except Exception:
            raw_dir = Path(self.project_config.get('environments.local.raw_data_dir', '.'))

        if not raw_dir:
            self.status_updated.emit("No raw directory configured – skipping text extraction")
            return

        from pathlib import Path
        # Consider common text-like extensions excluding PDFs
        patterns = ['*.txt', '*.md', '*.html', '*.htm']
        files = []
        for pat in patterns:
            files.extend(Path(raw_dir).rglob(pat))
        files = [str(p) for p in files if p.suffix.lower() != '.pdf']

        if not files:
            self.status_updated.emit("No non-PDF text files found – nothing to extract")
            return

        self.start_batch_processing(files)
