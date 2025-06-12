# File: shared_tools/ui_wrappers/processors/language_confidence_detector_wrapper.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, QThread
from shared_tools.processors.language_confidence_detector import LanguageConfidenceDetector

class LanguageConfidenceDetectorWrapper(QWidget):
    """
    UI wrapper for the Language Confidence Detector processor.
    - Inherit ONLY from QWidget
    - No BaseWrapper, no ProcessorMixin, no super() calls
    - Use explicit delegation for all signals, properties, and methods
    - Store config directly
    - Set up UI in setup_ui()
    """

    language_detected = Signal(str, str, float)
    status_updated = Signal(str)
    progress_updated = Signal(int)
    batch_completed = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, project_config, parent=None, **kwargs):
        QWidget.__init__(self, parent)
        if project_config is None:
            raise RuntimeError("LanguageConfidenceDetectorWrapper requires a non-None ProjectConfig")
        self.project_config = project_config
        self._processor = LanguageConfidenceDetector(project_config=project_config)
        self._is_running = False
        self.worker_thread = None
        self._enabled = True
        self.setup_ui()
        self.setup_connections()

    # --- Properties to Delegate ---
    @property
    def config(self):
        return self._processor.config

    @property
    def logger(self):
        return getattr(self._processor, 'logger', None)

    # --- Methods to Delegate ---
    def set_enabled(self, enabled: bool):
        self._enabled = bool(enabled)

    def start(self, file_paths=None, **kwargs):
        if not self._enabled:
            self.status_updated.emit("Language confidence detector disabled")
            return False
        if self._is_running:
            self.status_updated.emit("Language detection already in progress")
            return False
        self._is_running = True
        self.status_updated.emit("Starting language detection...")
        self.worker_thread = LanguageDetectorWorkerThread(self._processor, file_paths, **kwargs)
        self.worker_thread.progress_updated.connect(self.progress_updated.emit)
        self.worker_thread.status_updated.connect(self.status_updated.emit)
        self.worker_thread.language_detected.connect(self.language_detected.emit)
        self.worker_thread.processing_completed.connect(self._on_processing_completed)
        self.worker_thread.error_occurred.connect(self.error_occurred.emit)
        self.worker_thread.start()
        return True

    def stop(self):
        if not self._is_running:
            return False
        if self.worker_thread:
            self.worker_thread.requestInterruption()
            self.status_updated.emit("Stopping language detection...")
        return True

    def get_status(self):
        return {
            "is_running": self._is_running,
            "processor_type": "language_confidence_detector"
        }

    def refresh_config(self):
        if hasattr(self._processor, 'refresh_config'):
            return self._processor.refresh_config()
        return None

    # --- UI Setup ---
    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    def setup_connections(self):
        self.status_updated.connect(self._on_status_updated)
        self.progress_updated.connect(self._on_progress_updated)

    def _on_status_updated(self, message):
        self.status_label.setText(message)

    def _on_progress_updated(self, value):
        # Optionally update progress in the UI
        pass

    def _on_processing_completed(self, results):
        self._is_running = False
        self.batch_completed.emit(results)
        self.status_updated.emit(f"Language detection completed: {len(results)} files processed")

    def _on_error(self, error_message):
        self.status_label.setText(f"Error: {error_message}")
        self._is_running = False

class LanguageDetectorWorkerThread(QThread):
    progress_updated = Signal(int)
    status_updated = Signal(str)
    language_detected = Signal(str, str, float)
    processing_completed = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, processor, file_paths, **kwargs):
        QThread.__init__(self)
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
                self.status_updated.emit(f"Detecting language for {file_path}...")
                try:
                    # Detect language for the file (simulate with dummy values)
                    # Replace with actual detection logic as needed
                    result = self.processor.detect(file_path)
                    language = result.get('language', 'unknown')
                    confidence = result.get('confidence', 0.0)
                    self.language_detected.emit(file_path, language, confidence)
                    results[file_path] = result
                except Exception as e:
                    self.error_occurred.emit(f"Error detecting language for {file_path}: {str(e)}")
            self.processing_completed.emit(results)
        except Exception as e:
            self.error_occurred.emit(f"Language detection error: {str(e)}")
