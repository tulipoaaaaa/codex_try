from PySide6.QtCore import Signal as pyqtSignal, QThread
import time
from shared_tools.processors.pdf_extractor import PDFExtractor
from shared_tools.project_config import ProjectConfig
from PySide6.QtWidgets import QWidget
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

class PDFExtractorWrapper(QWidget):
    """UI wrapper for PDF Extractor (migrated to QWidget-only, explicit delegation)"""
    # Signals expected by other components / wrappers
    status_updated = pyqtSignal(str)
    file_processed = pyqtSignal(str, bool)  # filepath, success
    total_pages_processed = pyqtSignal(int)  # Total pages processed
    ocr_used = pyqtSignal(str, bool)  # filepath, ocr_used

    def __init__(self, project_config, parent=None):
        QWidget.__init__(self, parent)
        if project_config is None:
            raise RuntimeError("PDFExtractorWrapper requires a non-None ProjectConfig")
        self.project_config = project_config
        self.config = project_config.get('processors.pdf_extractor', {})
        self.logger = None  # Set up logger if needed
        self.extractor = None
        self.enable_ocr = True
        self.extract_tables = True
        self.extract_formulas = True
        self.worker_threads = 4
        self.worker = None
        self._is_running = False
        # All signal-slot connections are made explicitly in methods

    def _create_target_object(self):
        """Create PDF extractor instance"""
        if not self.extractor:
            self.extractor = PDFExtractor(
                project_config=self.project_config,
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
            return {"files_processed": getattr(self.extractor, 'files_processed', 0),
                    "ocr_used_count": getattr(self.extractor, 'ocr_used_count', 0)}
        return {"files_processed": 0, "ocr_used_count": 0}

    def refresh_config(self):
        """Reload parameters from ``self.config``."""
        cfg = {}
        if hasattr(self.project_config, 'get'):
            cfg = self.project_config.get('processors.pdf_extractor', {})
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
    # Dummy Qt-slot placeholders so signal connections don't fail in CLI
    # context (no UI event loop needed).
    # ------------------------------------------------------------------
    def _on_progress(self, current: int, total: int, msg: str):
        if self.logger:
            self.logger.info("PDF progress %d/%d: %s", current, total, msg)

    def _on_error(self, msg: str):
        if self.logger:
            self.logger.error(msg)

    def _on_finished(self, results: dict):
        if self.logger:
            self.logger.info("PDF extraction finished – %d files", len(results))
        # Optional auto-organise the freshly extracted outputs
        try:
            if self.project_config.get('post_extract_organise.enabled', False):
                from shared_tools.processors.post_extract_organiser import organise_extracted
                moved, domains = organise_extracted(self.project_config)
                if self.logger:
                    self.logger.info("Organised %d files into %d domains", moved, domains)
        except Exception as exc:  # pragma: no cover – defensive guard
            if self.logger:
                self.logger.warning("Organiser failed: %s", exc)
        finally:
            self._is_running = False

    # ------------------------------------------------------------------
    # Convenience entry-point so CLI (run_processors) can simply call
    # wrapper.start() without knowing UI-specific batch methods.
    # ------------------------------------------------------------------
    def start(self):
        """Detect PDF files under project_config.get_raw_dir() and process them."""
        raw_dir = None
        try:
            raw_dir = self.project_config.get_raw_dir()
        except Exception:
            # Fallback – look for raw_data_dir in config dict
            raw_dir = Path(self.project_config.get('environments.local.raw_data_dir', '.'))
        if not raw_dir:
            self.status_updated.emit("No raw directory configured – skipping PDF extraction")
            return

        from pathlib import Path
        pdf_files = [str(p) for pat in ['*.pdf', '*.PDF'] for p in Path(raw_dir).rglob(pat)]
        if not pdf_files:
            self.status_updated.emit("No PDF files found – nothing to extract")
            return

        self.start_batch_processing(pdf_files)
