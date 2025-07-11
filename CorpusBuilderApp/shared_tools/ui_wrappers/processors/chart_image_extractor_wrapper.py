# File: shared_tools/ui_wrappers/processors/chart_image_extractor_wrapper.py

from PySide6.QtCore import Signal as pyqtSignal, QThread
from PySide6.QtWidgets import QWidget
from shared_tools.processors.chart_image_extractor import ChartImageExtractor
from shared_tools.ui_wrappers.processors.processor_mixin import ProcessorMixin

class ChartImageExtractorWrapper(QWidget):
    """UI wrapper for the Chart Image Extractor processor."""
    
    chart_extracted = pyqtSignal(str, list)  # file_path, chart_images
    
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
        
        self.processor = ChartImageExtractor(config)
        self._is_running = False
        self.worker_thread = None
        
    def start(self, file_paths=None, **kwargs):
        """Start chart extraction on the specified files."""
        if self._is_running:
            self.status_updated.emit("Chart extraction already in progress")
            return False
            
        self._is_running = True
        self.status_updated.emit("Starting chart extraction...")
        
        # Create and configure worker thread
        self.worker_thread = ChartExtractorWorkerThread(
            self.processor, 
            file_paths,
            **kwargs
        )
        
        # Connect signals
        self.worker_thread.progress_updated.connect(self._on_progress_updated)
        self.worker_thread.status_updated.connect(self._on_status_updated)
        self.worker_thread.chart_extracted.connect(self._on_chart_extracted)
        self.worker_thread.processing_completed.connect(self._on_processing_completed)
        self.worker_thread.error_occurred.connect(self._on_error)
        
        # Start the thread
        self.worker_thread.start()
        return True
        
    def stop(self):
        """Stop the chart extraction processing."""
        if not self._is_running:
            return False
            
        if self.worker_thread:
            self.worker_thread.requestInterruption()
            self.status_updated.emit("Stopping chart extraction...")
            
        return True
        
    def get_status(self):
        """Get the current status of the processor."""
        return {
            "is_running": self._is_running,
            "processor_type": "chart_image_extractor"
        }
        
    def _on_chart_extracted(self, file_path, charts):
        """Handle chart extraction result."""
        self.chart_extracted.emit(file_path, charts)
        
    def _on_processing_completed(self, results):
        """Handle completion of chart extraction."""
        self._is_running = False
        self.batch_completed.emit(results)
        total_charts = sum(len(charts) for charts in results.values())
        self.status_updated.emit(
            f"Chart extraction completed: {total_charts} charts extracted from {len(results)} files"
        )

    def refresh_config(self):
        """Reload parameters from ``self.config``."""
        cfg = {}
        if hasattr(self.config, 'get_processor_config'):
            cfg = self.config.get_processor_config('chart_extraction') or {}
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

class ChartExtractorWorkerThread(QThread):
    """Worker thread for chart extraction processing."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    chart_extracted = pyqtSignal(str, list)
    processing_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, processor, file_paths, **kwargs):
        super().__init__()
        self.processor = processor
        self.file_paths = file_paths or []
        self.kwargs = kwargs
        
    def run(self):
        """Run the chart extraction processing."""
        try:
            results = {}
            
            for i, file_path in enumerate(self.file_paths):
                # Check for interruption
                if self.isInterruptionRequested():
                    break
                    
                # Update progress
                progress = int(((i + 1) / len(self.file_paths)) * 100)
                self.progress_updated.emit(progress)
                self.status_updated.emit(f"Extracting charts from {file_path}...")
                
                try:
                    # Extract charts from the file
                    charts = self.processor.extract_charts(file_path, **self.kwargs)
                    
                    # Emit the extraction result
                    self.chart_extracted.emit(file_path, charts)
                    
                    # Store result
                    results[file_path] = charts
                    
                except Exception as e:
                    self.status_updated.emit(f"Error extracting charts from {file_path}: {str(e)}")
                    results[file_path] = []
            
            # Complete processing
            self.processing_completed.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(f"Chart extraction error: {str(e)}")
