# File: shared_tools/ui_wrappers/processors/financial_symbol_processor_wrapper.py

from PySide6.QtCore import Signal as pyqtSignal, QThread
from PySide6.QtWidgets import QWidget
from shared_tools.processors.financial_symbol_processor import FinancialSymbolProcessor
from shared_tools.ui_wrappers.processors.processor_mixin import ProcessorMixin

class FinancialSymbolProcessorWrapper(QWidget):
    """UI wrapper for the Financial Symbol Processor."""
    
    symbols_extracted = pyqtSignal(str, list)  # file_path, symbols
    
    def __init__(self, config, task_queue_manager=None, parent=None):
        """
        Parameters
        ----------
        config : ProjectConfig | str
            Mandatory. Passed straight to BaseWrapper.
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
        
        self.processor = FinancialSymbolProcessor(config)
        self._is_running = False
        self.worker_thread = None
        self._enabled = True

    def set_enabled(self, enabled: bool):
        """Enable or disable the wrapper."""
        self._enabled = bool(enabled)
        
    def start(self, file_paths=None, **kwargs):
        """Start financial symbol extraction on the specified files."""
        if not self._enabled:
            self.status_updated.emit("Financial symbol processor disabled")
            return False
        if self._is_running:
            self.status_updated.emit("Financial symbol extraction already in progress")
            return False
            
        self._is_running = True
        self.status_updated.emit("Starting financial symbol extraction...")
        
        # Create and configure worker thread
        self.worker_thread = FinancialSymbolWorkerThread(
            self.processor, 
            file_paths,
            **kwargs
        )
        
        # Connect signals
        self.worker_thread.progress_updated.connect(self._on_progress_updated)
        self.worker_thread.status_updated.connect(self._on_status_updated)
        self.worker_thread.symbols_extracted.connect(self._on_symbols_extracted)
        self.worker_thread.processing_completed.connect(self._on_processing_completed)
        self.worker_thread.error_occurred.connect(self._on_error)
        
        # Start the thread
        self.worker_thread.start()
        return True
        
    def stop(self):
        """Stop the financial symbol extraction processing."""
        if not self._is_running:
            return False
            
        if self.worker_thread:
            self.worker_thread.requestInterruption()
            self.status_updated.emit("Stopping financial symbol extraction...")
            
        return True
        
    def get_status(self):
        """Get the current status of the processor."""
        return {
            "is_running": self._is_running,
            "processor_type": "financial_symbol_processor"
        }
        
    def _on_symbols_extracted(self, file_path, symbols):
        """Handle financial symbol extraction result."""
        self.symbols_extracted.emit(file_path, symbols)
        
    def _on_processing_completed(self, results):
        """Handle completion of financial symbol extraction."""
        self._is_running = False
        self.batch_completed.emit(results)
        total_symbols = sum(len(symbols) for symbols in results.values())
        self.status_updated.emit(
            f"Financial symbol extraction completed: {total_symbols} symbols extracted from {len(results)} files"
        )

    def refresh_config(self):
        """Reload parameters from ``self.config``."""
        cfg = {}
        if hasattr(self.config, 'get_processor_config'):
            cfg = self.config.get_processor_config('financial_symbol_processor') or {}
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

class FinancialSymbolWorkerThread(QThread):
    """Worker thread for financial symbol extraction processing."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    symbols_extracted = pyqtSignal(str, list)
    processing_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, processor, file_paths, **kwargs):
        super().__init__()
        self.processor = processor
        self.file_paths = file_paths or []
        self.kwargs = kwargs
        
    def run(self):
        """Run the financial symbol extraction processing."""
        try:
            results = {}
            
            for i, file_path in enumerate(self.file_paths):
                # Check for interruption
                if self.isInterruptionRequested():
                    break
                    
                # Update progress
                progress = int(((i + 1) / len(self.file_paths)) * 100)
                self.progress_updated.emit(progress)
                self.status_updated.emit(f"Extracting financial symbols from {file_path}...")
                
                try:
                    # Extract financial symbols from the file
                    symbols = self.processor.extract_symbols(file_path, **self.kwargs)
                    
                    # Emit the extraction result
                    self.symbols_extracted.emit(file_path, symbols)
                    
                    # Store result
                    results[file_path] = symbols
                    
                except Exception as e:
                    self.status_updated.emit(f"Error extracting symbols from {file_path}: {str(e)}")
                    results[file_path] = []
            
            # Complete processing
            self.processing_completed.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(f"Financial symbol extraction error: {str(e)}")
