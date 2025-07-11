# File: shared_tools/ui_wrappers/processors/deduplicator_wrapper.py

from PySide6.QtCore import Signal as pyqtSignal, QThread, Slot as pyqtSlot
from PySide6.QtWidgets import QWidget
from shared_tools.processors.deduplicator import Deduplicator
from shared_tools.ui_wrappers.processors.processor_mixin import ProcessorMixin
import subprocess
import sys

class DeduplicatorWrapper(QWidget):
    """UI wrapper for the Deduplicator processor."""
    
    duplicate_found = pyqtSignal(str, str, float)  # file1, file2, similarity
    
    def __init__(self, config, task_queue_manager=None, parent=None):
        """
        Parameters
        ----------
        config : ProjectConfig | str
            Mandatory. Passed straight to ProcessorMixin.
        task_queue_manager : TaskQueueManager | None
        parent : QWidget | None
        """
        # Initialize base classes in correct order
        QWidget.__init__(self, parent)  # Initialize QWidget first
        ProcessorMixin.__init__(self, config, task_queue_manager=task_queue_manager)  # Then initialize ProcessorMixin
        
        # Set up delegation for frequently used attributes
        self.config = self._bw.config  # delegation
        self.logger = self._bw.logger  # delegation
        
        # Delegate signals from BaseWrapper
        self.status_updated = self._bw.status_updated
        self.batch_completed = self._bw.completed
        
        self.processor = Deduplicator(config)
        self._is_running = False
        self.worker_thread = None
        self.similarity_threshold = 0.85  # Default threshold
        self._enabled = True

    def set_enabled(self, enabled: bool):
        """Enable or disable the wrapper."""
        self._enabled = bool(enabled)
        
    def start(self, file_paths=None, **kwargs):
        """Start deduplication processing on the specified files."""
        if not self._enabled:
            self.status_updated.emit("Deduplicator disabled")
            return False
        if self._is_running:
            self.status_updated.emit("Deduplication already in progress")
            return False
            
        self._is_running = True
        self.status_updated.emit("Starting deduplication processing...")
        
        # Create and configure worker thread
        self.worker_thread = DeduplicatorWorkerThread(
            self.processor, 
            file_paths,
            similarity_threshold=self.similarity_threshold,
            **kwargs
        )
        
        # Connect signals
        self.worker_thread.progress_updated.connect(self._on_progress_updated)
        self.worker_thread.status_updated.connect(self._on_status_updated)
        self.worker_thread.duplicate_found.connect(self._on_duplicate_found)
        self.worker_thread.processing_completed.connect(self._on_processing_completed)
        self.worker_thread.error_occurred.connect(self._on_error)
        
        # Start the thread
        self.worker_thread.start()
        return True
        
    def stop(self):
        """Stop the deduplication processing."""
        if not self._is_running:
            return False
            
        if self.worker_thread:
            self.worker_thread.requestInterruption()
            self.status_updated.emit("Stopping deduplication processing...")
            
        return True
        
    def get_status(self):
        """Get the current status of the processor."""
        return {
            "is_running": self._is_running,
            "processor_type": "deduplicator",
            "threshold": self.similarity_threshold
        }
        
    def set_similarity_threshold(self, threshold):
        """Set the similarity threshold for duplicate detection."""
        self.similarity_threshold = threshold
        
    def _on_duplicate_found(self, file1, file2, similarity):
        """Handle detection of a duplicate file pair."""
        self.duplicate_found.emit(file1, file2, similarity)
        
    def _on_processing_completed(self, results):
        """Handle completion of deduplication processing."""
        self._is_running = False
        self.batch_completed.emit(results)
        self.status_updated.emit(
            f"Deduplication completed: {len(results.get('duplicate_sets', []))} duplicate sets found"
        )

    def refresh_config(self):
        """Reload parameters from ``self.config``."""
        cfg = {}
        if hasattr(self.config, 'get_processor_config'):
            cfg = self.config.get_processor_config('deduplicator') or {}
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

    @pyqtSlot()
    def start_deduplication(self):
        # Automatically generate title cache before deduplication
        corpus_dir = self.input_directory_edit.text() if hasattr(self, 'input_directory_edit') else self.options.get('input_directory', '.')
        output_dir = corpus_dir  # Or set to a specific cache/output directory if needed
        try:
            subprocess.run([sys.executable, 'shared_tools/processors/generate_title_cache.py', corpus_dir, output_dir], check=True)
        except Exception as e:
            self.handle_error('Title Cache Generation Error', str(e))
        # Proceed with deduplication as usual
        # ... existing deduplication logic ...
        
class DeduplicatorWorkerThread(QThread):
    """Worker thread for deduplication processing."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    duplicate_found = pyqtSignal(str, str, float)
    processing_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, processor, file_paths, **kwargs):
        super().__init__()
        self.processor = processor
        self.file_paths = file_paths or []
        self.kwargs = kwargs
        
    def run(self):
        """Run the deduplication processing."""
        try:
            results = {"duplicate_sets": [], "total_comparisons": 0}
            
            # Update status
            self.status_updated.emit(f"Analyzing {len(self.file_paths)} files for duplicates...")
            
            # Process the files
            duplicate_sets = self.processor.find_duplicates(
                self.file_paths, 
                threshold=self.kwargs.get('similarity_threshold', 0.85)
            )
            
            # Process each duplicate set
            for i, dup_set in enumerate(duplicate_sets):
                # Check for interruption
                if self.isInterruptionRequested():
                    break
                    
                # Update progress
                progress = int(((i + 1) / len(duplicate_sets) if duplicate_sets else 1) * 100)
                self.progress_updated.emit(progress)
                
                # Emit duplicate information
                for j in range(len(dup_set['files']) - 1):
                    for k in range(j + 1, len(dup_set['files'])):
                        file1 = dup_set['files'][j]
                        file2 = dup_set['files'][k]
                        similarity = dup_set['similarity']
                        self.duplicate_found.emit(file1, file2, similarity)
                
                # Add to results
                results["duplicate_sets"].append(dup_set)
            
            # Update total comparisons
            n = len(self.file_paths)
            results["total_comparisons"] = (n * (n - 1)) // 2
            
            # Complete processing
            self.processing_completed.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(f"Deduplication error: {str(e)}")
