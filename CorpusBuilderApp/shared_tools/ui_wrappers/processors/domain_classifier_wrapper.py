# File: shared_tools/ui_wrappers/processors/domain_classifier_wrapper.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, QThread
from shared_tools.processors.domain_classifier import DomainClassifier

class DomainClassifierWrapper(QWidget):
    """
    UI wrapper for the Domain Classifier processor.
    - Inherit ONLY from QWidget
    - No BaseWrapper, no ProcessorMixin, no super() calls
    - Use explicit delegation for all signals, properties, and methods
    - Store config directly
    - Set up UI in setup_ui()
    """

    document_classified = Signal(str, str, float)  # doc_id, domain, confidence
    status_updated = Signal(str)
    progress_updated = Signal(int)
    batch_completed = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, project_config, parent=None, **kwargs):
        QWidget.__init__(self, parent)
        if project_config is None:
            raise RuntimeError("DomainClassifierWrapper requires a non-None ProjectConfig")
        self.project_config = project_config
        self._processor = DomainClassifier(project_config=project_config)
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

    def start(self, documents=None, **kwargs):
        if not self._enabled:
            self.status_updated.emit("Domain classifier disabled")
            return False
        if self._is_running:
            self.status_updated.emit("Domain classification already in progress")
            return False
        self._is_running = True
        self.status_updated.emit("Starting domain classification...")
        self.worker_thread = DomainClassifierWorkerThread(self._processor, documents, **kwargs)
        self.worker_thread.progress_updated.connect(self.progress_updated.emit)
        self.worker_thread.status_updated.connect(self.status_updated.emit)
        self.worker_thread.document_classified.connect(self.document_classified.emit)
        self.worker_thread.processing_completed.connect(self._on_processing_completed)
        self.worker_thread.error_occurred.connect(self.error_occurred.emit)
        self.worker_thread.start()
        return True

    def stop(self):
        if not self._is_running:
            return False
        if self.worker_thread:
            self.worker_thread.requestInterruption()
            self.status_updated.emit("Stopping domain classification...")
        return True

    def get_status(self):
        return {
            "is_running": self._is_running,
            "processor_type": "domain_classifier"
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
        self.status_updated.emit(f"Domain classification completed: {len(results)} documents processed")

    def _on_error(self, error_message):
        self.status_label.setText(f"Error: {error_message}")
        self._is_running = False

class DomainClassifierWorkerThread(QThread):
    progress_updated = Signal(int)
    status_updated = Signal(str)
    document_classified = Signal(str, str, float)
    processing_completed = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, processor, documents, **kwargs):
        QThread.__init__(self)
        self.processor = processor
        self.documents = documents or {}
        self.kwargs = kwargs

    def run(self):
        try:
            results = {}
            total_docs = len(self.documents)
            for i, (doc_id, doc_data) in enumerate(self.documents.items()):
                if self.isInterruptionRequested():
                    break
                progress = int(((i + 1) / total_docs) * 100) if total_docs > 0 else 100
                self.progress_updated.emit(progress)
                self.status_updated.emit(f"Classifying document {doc_id}...")
                try:
                    text = doc_data.get('text', '')
                    title = doc_data.get('metadata', {}).get('title', None)
                    classification = self.processor.classify(text, title)
                    domain = classification.get('domain', 'unknown')
                    confidence = classification.get('confidence', 0.0)
                    self.document_classified.emit(doc_id, domain, confidence)
                    results[doc_id] = classification
                except Exception as e:
                    self.error_occurred.emit(f"Error classifying {doc_id}: {str(e)}")
            self.processing_completed.emit(results)
        except Exception as e:
            self.error_occurred.emit(f"Domain classification error: {str(e)}")
