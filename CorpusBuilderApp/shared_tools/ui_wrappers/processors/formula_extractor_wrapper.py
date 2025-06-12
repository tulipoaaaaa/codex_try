# File: shared_tools/ui_wrappers/processors/formula_extractor_wrapper.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, QThread
from shared_tools.processors.formula_extractor import FormulaExtractor

class FormulaExtractorWrapper(QWidget):
    """
    UI wrapper for the Formula Extractor processor.
    - Inherit ONLY from QWidget
    - No BaseWrapper, no ProcessorMixin, no super() calls
    - Use explicit delegation for all signals, properties, and methods
    - Store config directly
    - Set up UI in setup_ui()
    """

    status_updated = Signal(str)
    batch_completed = Signal(dict)
    progress_updated = Signal(int)
    error_occurred = Signal(str)
    formula_extracted = Signal(str, list)

    def __init__(self, project_config, parent=None):
        QWidget.__init__(self, parent)
        self.project_config = project_config
        self.config = project_config.get('processors.specialized.formulas', {})
        self.logger = None  # Set up logger if needed
        self._is_running = False
        self.worker_thread = None
        self._enabled = True
        self.processor = FormulaExtractor(config=self.config, project_config=project_config)
        self.setup_ui()
        self.setup_connections()

    def set_enabled(self, enabled: bool):
        self._enabled = bool(enabled)
        
    def start(self, file_paths=None, **kwargs):
        if not self._enabled:
            self.status_updated.emit("Formula extractor disabled")
            return False
        if self._is_running:
            self.status_updated.emit("Formula extraction already in progress")
            return False
        self._is_running = True
        self.status_updated.emit("Starting formula extraction...")
        self.worker_thread = FormulaExtractorWorkerThread(self.processor, file_paths, **kwargs)
        self.worker_thread.progress_updated.connect(self.progress_updated)
        self.worker_thread.status_updated.connect(self.status_updated)
        self.worker_thread.formula_extracted.connect(self.formula_extracted)
        self.worker_thread.processing_completed.connect(self._on_processing_completed)
        self.worker_thread.error_occurred.connect(self.error_occurred)
        self.worker_thread.start()
        return True
        
    def stop(self):
        if not self._is_running:
            return False
        if self.worker_thread:
            self.worker_thread.requestInterruption()
            self.status_updated.emit("Stopping formula extraction...")
        return True
        
    def get_status(self):
        return {
            "is_running": self._is_running,
            "processor_type": "formula_extractor"
        }
        
    def _on_processing_completed(self, results):
        self._is_running = False
        self.batch_completed.emit(results)
        total_formulas = sum(len(formulas) for formulas in results.values())
        self.status_updated.emit(
            f"Formula extraction completed: {total_formulas} formulas extracted from {len(results)} files"
        )

    def refresh_config(self):
        cfg = self.project_config.get('processors.specialized.formulas', {})
        for k, v in cfg.items():
            method = f'set_{k}'
            if hasattr(self, method):
                try:
                    getattr(self, method)(v)
                    continue
                except Exception:
                    pass
            if hasattr(self.processor, method):
                try:
                    getattr(self.processor, method)(v)
                    continue
                except Exception:
                    pass
            if hasattr(self.processor, k):
                setattr(self.processor, k, v)
            elif hasattr(self, k):
                setattr(self, k, v)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Formula Extractor UI"))

    def setup_connections(self):
        pass

class FormulaExtractorWorkerThread(QThread):
    progress_updated = Signal(int)
    status_updated = Signal(str)
    formula_extracted = Signal(str, list)
    processing_completed = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, processor, file_paths, **kwargs):
        super().__init__()
        self.processor = processor
        self.file_paths = file_paths or []
        self.kwargs = kwargs
        
    def run(self):
        try:
            results = {}
            for i, file_path in enumerate(self.file_paths):
                if self.isInterruptionRequested():
                    break
                progress = int(((i + 1) / len(self.file_paths)) * 100)
                self.progress_updated.emit(progress)
                self.status_updated.emit(f"Extracting formulas from {file_path}...")
                try:
                    formulas = self.processor.extract_formulas(file_path, **self.kwargs)
                    self.formula_extracted.emit(file_path, formulas)
                    results[file_path] = formulas
                except Exception as e:
                    self.error_occurred.emit(str(e))
            self.processing_completed.emit(results)
        except Exception as e:
            self.error_occurred.emit(str(e))
