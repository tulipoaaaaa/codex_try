# File: shared_tools/ui_wrappers/processors/deduplicator_wrapper.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, QThread
from shared_tools.processors.deduplicator import Deduplicator

class DeduplicatorWrapper(QWidget):
    """
    UI wrapper for the Deduplicator processor.
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
    duplicate_found = Signal(str, str, float)

    def __init__(self, project_config, parent=None):
        QWidget.__init__(self, parent)
        self.project_config = project_config
        self.config = project_config.get('processors.deduplicator', {})
        self.logger = None  # Set up logger if needed
        self._is_running = False
        self.worker_thread = None
        self.similarity_threshold = 0.85  # Default threshold
        self._enabled = True
        self.processor = Deduplicator(project_config=project_config)
        self.setup_ui()
        self.setup_connections()

    def set_enabled(self, enabled: bool):
        self._enabled = bool(enabled)
        
    def set_similarity_threshold(self, threshold):
        self.similarity_threshold = threshold

    def start(self, file_paths=None, **kwargs):
        if not self._enabled:
            self.status_updated.emit("Deduplicator disabled")
            return False
        if self._is_running:
            self.status_updated.emit("Deduplication already in progress")
            return False
        self._is_running = True
        self.status_updated.emit("Starting deduplication processing...")
        self.worker_thread = DeduplicatorWorker(self.processor, file_paths, similarity_threshold=self.similarity_threshold, **kwargs)
        self.worker_thread.progress_updated.connect(self.progress_updated)
        self.worker_thread.status_updated.connect(self.status_updated)
        self.worker_thread.duplicate_found.connect(self.duplicate_found)
        self.worker_thread.processing_completed.connect(self._on_processing_completed)
        self.worker_thread.error_occurred.connect(self.error_occurred)
        self.worker_thread.start()
        return True
        
    def stop(self):
        if not self._is_running:
            return False
        if self.worker_thread:
            self.worker_thread.requestInterruption()
            self.status_updated.emit("Stopping deduplication processing...")
        return True
        
    def get_status(self):
        return {
            "is_running": self._is_running,
            "processor_type": "deduplicator",
            "threshold": self.similarity_threshold
        }
        
    def _on_processing_completed(self, results):
        self._is_running = False
        self.batch_completed.emit(results)
        self.status_updated.emit(
            f"Deduplication completed: {len(results.get('duplicate_sets', []))} duplicate sets found"
        )

    def refresh_config(self):
        cfg = self.project_config.get('processors.deduplicator', {})
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
        layout.addWidget(QLabel("Deduplicator UI"))

    def setup_connections(self):
        pass
        
class DeduplicatorWorker(QThread):
    progress_updated = Signal(int)
    status_updated = Signal(str)
    duplicate_found = Signal(str, str, float)
    processing_completed = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, processor, file_paths, similarity_threshold=0.85, **kwargs):
        super().__init__()
        self.processor = processor
        self.file_paths = file_paths or []
        self.similarity_threshold = similarity_threshold
        self.kwargs = kwargs
        
    def run(self):
        try:
            results = {"duplicate_sets": [], "total_comparisons": 0}
            self.status_updated.emit(f"Analyzing {len(self.file_paths)} files for duplicates...")
            duplicate_sets = self.processor.find_duplicates(
                self.file_paths, 
                threshold=self.similarity_threshold
            )
            for i, dup_set in enumerate(duplicate_sets):
                if self.isInterruptionRequested():
                    break
                progress = int(((i + 1) / len(duplicate_sets) if duplicate_sets else 1) * 100)
                self.progress_updated.emit(progress)
                for j in range(len(dup_set['files']) - 1):
                    for k in range(j + 1, len(dup_set['files'])):
                        file1 = dup_set['files'][j]
                        file2 = dup_set['files'][k]
                        similarity = dup_set['similarity']
                        self.duplicate_found.emit(file1, file2, similarity)
                results["duplicate_sets"].append(dup_set)
            n = len(self.file_paths)
            results["total_comparisons"] = (n * (n - 1)) // 2
            self.processing_completed.emit(results)
        except Exception as e:
            self.error_occurred.emit(str(e))
