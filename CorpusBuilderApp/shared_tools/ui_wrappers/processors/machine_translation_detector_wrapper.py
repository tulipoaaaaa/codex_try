# File: shared_tools/ui_wrappers/processors/machine_translation_detector_wrapper.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, QThread
from shared_tools.processors.machine_translation_detector import MachineTranslationDetector

class MachineTranslationDetectorWrapper(QWidget):
    """
    UI wrapper for the Machine Translation Detector processor.
    - Inherit ONLY from QWidget
    - No BaseWrapper, no ProcessorMixin, no super() calls
    - Use explicit delegation for all signals, properties, and methods
    - Store config directly
    - Set up UI in setup_ui()
    """

    # Define all signals you need to expose
    status_updated = Signal(str)
    batch_completed = Signal(dict)
    progress_updated = Signal(int)
    error_occurred = Signal(str)
    translation_detected = Signal(str, bool, float)

    def __init__(self, project_config, parent=None):
        QWidget.__init__(self, parent)
        self.project_config = project_config
        self.config = project_config.get('processors.quality_control.checks.translation', {})
        self.logger = None  # Set up logger if needed
        self._is_running = False
        self.worker_thread = None
        self._enabled = True
        self.processor = MachineTranslationDetector(config=self.config, project_config=project_config)
        self.setup_ui()
        self.setup_connections()

    def set_enabled(self, enabled: bool):
        self._enabled = bool(enabled)
        
    def start(self, file_paths=None, **kwargs):
        if not self._enabled:
            self.status_updated.emit("Machine translation detector disabled")
            return False
        if self._is_running:
            self.status_updated.emit("Machine translation detection already in progress")
            return False
        self._is_running = True
        self.status_updated.emit("Starting machine translation detection...")
        self.worker_thread = MTDetectorWorkerThread(self.processor, file_paths, **kwargs)
        self.worker_thread.progress_updated.connect(self.progress_updated)
        self.worker_thread.status_updated.connect(self.status_updated)
        self.worker_thread.translation_detected.connect(self.translation_detected)
        self.worker_thread.processing_completed.connect(self._on_processing_completed)
        self.worker_thread.error_occurred.connect(self.error_occurred)
        self.worker_thread.start()
        return True
        
    def stop(self):
        if not self._is_running:
            return False
        if self.worker_thread:
            self.worker_thread.requestInterruption()
            self.status_updated.emit("Stopping machine translation detection...")
        return True
        
    def get_status(self):
        return {
            "is_running": self._is_running,
            "processor_type": "machine_translation_detector"
        }
        
    def _on_processing_completed(self, results):
        self._is_running = False
        self.batch_completed.emit(results)
        translated_count = sum(1 for result in results.values() if result.get('is_translated', False))
        self.status_updated.emit(
            f"Machine translation detection completed: {translated_count} translated documents found in {len(results)} files"
        )

    def refresh_config(self):
        cfg = self.project_config.get('processors.quality_control.checks.translation', {})
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
        layout.addWidget(QLabel("Machine Translation Detector UI"))

    def setup_connections(self):
        pass

class MTDetectorWorkerThread(QThread):
    progress_updated = Signal(int)
    status_updated = Signal(str)
    translation_detected = Signal(str, bool, float)
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
                self.status_updated.emit(f"Checking translation for {file_path}...")
                try:
                    result = self.processor.detect_machine_translation(file_path, **self.kwargs)
                    is_translated = result.get('is_translated', False)
                    confidence = result.get('confidence', 0.0)
                    self.translation_detected.emit(file_path, is_translated, confidence)
                    results[file_path] = result
                except Exception as e:
                    self.error_occurred.emit(str(e))
            self.processing_completed.emit(results)
        except Exception as e:
            self.error_occurred.emit(str(e))
