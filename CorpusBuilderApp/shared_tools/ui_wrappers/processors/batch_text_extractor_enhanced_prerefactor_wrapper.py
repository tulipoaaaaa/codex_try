"""
Batch Text Extractor Enhanced Pre-refactor Wrapper for UI Integration
Provides comprehensive batch text extraction with advanced preprocessing
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple, Union
from PySide6.QtCore import QObject, QThread, Signal as pyqtSignal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QProgressBar, QLabel, QTextEdit, QFileDialog, QCheckBox, 
                           QSpinBox, QGroupBox, QGridLayout, QComboBox, QDoubleSpinBox,
                           QTabWidget, QListWidget, QSplitter, QFormLayout)
from shared_tools.processors.batch_text_extractor_enhanced_prerefactor import BatchTextExtractorEnhancedPrerefactor  # type: ignore
from ...project_config import ProjectConfig
from pathlib import Path

# Handle environments where 'Slot' symbol may not be exported at module level
try:
    from PySide6.QtCore import Slot as pyqtSlot
except ImportError:  # pragma: no cover – fallback for some PySide builds
    def pyqtSlot(*types, **kwargs):  # type: ignore
        """No-op decorator replacement when QtCore.Slot is unavailable."""
        def decorator(func):
            return func
        return decorator

# Optional Qt symbols that may be unavailable in minimal/headless builds
try:
    from PySide6.QtCore import QMutex, QTimer  # type: ignore
except ImportError:  # pragma: no cover – provide stubs for CLI mode
    class _QtStub:  # pylint: disable=too-few-public-methods
        def __init__(self, *_, **__):
            pass

        def lock(self):
            pass

        def unlock(self):
            pass

        def start(self, *_, **__):
            pass

        def stop(self):
            pass

    QMutex = QTimer = _QtStub  # type: ignore

#
# We already used ``_QtStub`` earlier for ``QMutex`` stubs.  Re-using the same
# name confuses static analysers, so we create a distinct stub class for the Qt
# enum namespace.
#
except ImportError:  # pragma: no cover
    class _QtEnumStub:
        Horizontal = 0
        Vertical = 1
        AlignLeft = AlignRight = AlignHCenter = AlignVCenter = 0
    Qt = _QtEnumStub  # type: ignore

# Detect whether we are running in a head-less environment where real Qt widget
# classes are not available (i.e. they have been stubbed to plain ``object`` by
# the fallback logic above). We test for a well-known method present on real
# widgets – ``addItems`` on ``QComboBox`` – which is missing from the stub.
_HEADLESS_CLI = not hasattr(QComboBox, "addItems")

class BatchTextExtractorWorker(QThread):
    """Worker thread for batch text extraction operations"""
    
    progress_updated = pyqtSignal(int, str, dict)  # progress, current file, stats
    file_processed = pyqtSignal(str, bool, str, dict)  # file path, success, message, metadata
    batch_completed = pyqtSignal(dict)  # final statistics
    error_occurred = pyqtSignal(str, str)  # error type, error message
    quality_report = pyqtSignal(str, dict)  # file path, quality metrics
    
    def __init__(self, input_path: str, output_path: str, options: Dict[str, Any]):
        QThread.__init__(self)  # Initialize QThread explicitly
        self.input_path = input_path
        self.output_path = output_path
        self.options = options
        self.extractor = BatchTextExtractorEnhancedPrerefactor()
        self._is_cancelled = False
        self._mutex = QMutex()
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'total_characters': 0,
            'total_words': 0,
            'processing_time': 0.0
        }
        
    def run(self):
        """Execute batch text extraction process"""
        import time
        start_time = time.time()
        
        try:
            # Configure extractor
            self.extractor.configure(
                encoding_detection=self.options.get('encoding_detection', True),
                quality_threshold=self.options.get('quality_threshold', 0.7),
                clean_whitespace=self.options.get('clean_whitespace', True),
                normalize_unicode=self.options.get('normalize_unicode', True),
                extract_structure=self.options.get('extract_structure', False),
                language_detection=self.options.get('language_detection', True),
                preserve_linebreaks=self.options.get('preserve_linebreaks', False),
                max_file_size=self.options.get('max_file_size', 50),
                batch_size=self.options.get('batch_size', 20)
            )
            
            # Get files to process
            files_to_process = self._get_files_to_process()
            self.stats['total_files'] = len(files_to_process)
            
            if self.stats['total_files'] == 0:
                self.error_occurred.emit("No Files", "No compatible text files found")
                return
                
            # Process files in batches
            batch_size = self.options.get('batch_size', 20)
            for i in range(0, len(files_to_process), batch_size):
                if self._is_cancelled:
                    break
                    
                batch = files_to_process[i:i + batch_size]
                self._process_batch(batch)
                
            # Calculate final statistics
            self.stats['processing_time'] = time.time() - start_time
            self.batch_completed.emit(self.stats)
            
        except Exception as e:
            self.error_occurred.emit("Processing Error", str(e))
            
    def _process_batch(self, batch: List[str]):
        """Process a batch of files"""
        for file_path in batch:
            if self._is_cancelled:
                break
                
            try:
                # Update progress
                progress = int((self.stats['processed_files'] / self.stats['total_files']) * 100)
                filename = os.path.basename(file_path)
                self.progress_updated.emit(progress, f"Processing: {filename}", self.stats.copy())
                
                # Extract text and metadata
                result = self.extractor.extract_file(file_path, self.output_path)
                
                if result['success']:
                    self.stats['successful_files'] += 1
                    self.stats['total_characters'] += result.get('character_count', 0)
                    self.stats['total_words'] += result.get('word_count', 0)
                    
                    # Emit quality report if available
                    if 'quality_metrics' in result:
                        self.quality_report.emit(file_path, result['quality_metrics'])
                        
                    self.file_processed.emit(
                        file_path, 
                        True, 
                        "Successfully extracted", 
                        result.get('metadata', {})
                    )
                else:
                    self.stats['failed_files'] += 1
                    self.file_processed.emit(
                        file_path, 
                        False, 
                        result.get('error', 'Unknown error'), 
                        {}
                    )
                    
                self.stats['processed_files'] += 1
                
            except Exception as e:
                self.stats['failed_files'] += 1
                self.stats['processed_files'] += 1
                self.file_processed.emit(file_path, False, str(e), {})
                
    def cancel(self):
        """Cancel the current operation"""
        self._mutex.lock()
        self._is_cancelled = True
        self._mutex.unlock()
        
    def _get_files_to_process(self) -> List[str]:
        """Get list of text files to process"""
        supported_extensions = ['.txt', '.text', '.log', '.csv', '.tsv', '.json', '.xml', '.html', '.htm', '.pdf']
        files = []
        
        if os.path.isfile(self.input_path):
            if any(self.input_path.lower().endswith(ext) for ext in supported_extensions):
                files.append(self.input_path)
        else:
            for root, dirs, filenames in os.walk(self.input_path):
                for filename in filenames:
                    if any(filename.lower().endswith(ext) for ext in supported_extensions):
                        files.append(os.path.join(root, filename))
                        
        return files


class BatchTextExtractorEnhancedPrerefactorWrapper(QWidget):
    """Wrapper for BatchTextExtractorEnhancedPrerefactor with UI controls (migrated to QWidget-only, explicit delegation)"""
    def __init__(self, project_config, parent=None):
        # ``QWidget`` may be an ``object`` stub when running without a GUI
        # backend.  Calling its constructor with extra arguments would raise a
        # ``TypeError``.  We therefore guard the initialisation so that it is
        # only invoked with a parent when real Qt is available.
        try:
            QWidget.__init__(self, parent)
        except TypeError:
            # Stubbed ``object`` does not accept *parent* – fall back to default
            try:
                QWidget.__init__(self)
            except Exception:
                # Completely stubbed, nothing to do
                pass
        if project_config is None:
            raise RuntimeError("BatchTextExtractorEnhancedPrerefactorWrapper requires a non-None ProjectConfig")
        self.project_config = project_config
        self.config = project_config.get('processors.batch_text_extractor_enhanced_prerefactor', {})
        self.logger = None  # Set up logger if needed
        self.processor = BatchTextExtractorEnhancedPrerefactor(project_config=project_config)
        self._is_running = False
        self.worker_thread = None
        self._enabled = True
        # In head-less CLI mode the Qt widgets are dummy ``object`` instances.
        # Building the UI would therefore raise ``AttributeError`` (as seen in
        # issue report). We skip UI initialisation entirely in that scenario.
        if not _HEADLESS_CLI:
            self._init_ui()
        # All signal-slot connections are made explicitly in setup_connections()
    
    def _init_ui(self):
        """Initialize the UI controls"""
        # Create main layout
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Chunking mode
        self.chunking_mode = QComboBox()
        self.chunking_mode.addItems(['page', 'token'])
        self.chunking_mode.setCurrentText(self.processor.config.get('chunking_mode', 'page'))
        form_layout.addRow("Chunking Mode:", self.chunking_mode)
        
        # Chunk overlap
        self.chunk_overlap = QSpinBox()
        self.chunk_overlap.setRange(0, 10)
        self.chunk_overlap.setValue(self.processor.config.get('chunk_overlap', 1))
        form_layout.addRow("Chunk Overlap:", self.chunk_overlap)
        
        # Min token threshold
        self.min_token_threshold = QSpinBox()
        self.min_token_threshold.setRange(10, 1000)
        self.min_token_threshold.setValue(self.processor.config.get('min_token_threshold', 50))
        form_layout.addRow("Min Token Threshold:", self.min_token_threshold)
        
        # Low quality token threshold
        self.low_quality_token_threshold = QSpinBox()
        self.low_quality_token_threshold.setRange(100, 2000)
        self.low_quality_token_threshold.setValue(self.processor.config.get('low_quality_token_threshold', 200))
        form_layout.addRow("Low Quality Token Threshold:", self.low_quality_token_threshold)
        
        # Timeout
        self.timeout = QSpinBox()
        self.timeout.setRange(30, 600)
        self.timeout.setValue(self.processor.config.get('timeout', 300))
        form_layout.addRow("Timeout (seconds):", self.timeout)
        
        # Max retries
        self.max_retries = QSpinBox()
        self.max_retries.setRange(1, 5)
        self.max_retries.setValue(self.processor.config.get('max_retries', 2))
        form_layout.addRow("Max Retries:", self.max_retries)
        
        # Batch size
        self.batch_size = QSpinBox()
        self.batch_size.setRange(1, 50)
        self.batch_size.setValue(self.processor.config.get('batch_size', 20))
        form_layout.addRow("Batch Size:", self.batch_size)
        
        # Verbose mode
        self.verbose = QCheckBox()
        self.verbose.setChecked(self.processor.config.get('verbose', False))
        form_layout.addRow("Verbose Mode:", self.verbose)
        
        # Auto normalize
        self.auto_normalize = QCheckBox()
        self.auto_normalize.setChecked(self.processor.config.get('auto_normalize', True))
        form_layout.addRow("Auto Normalize:", self.auto_normalize)
        
        # Add form layout to main layout
        main_layout.addLayout(form_layout)
        
        # Add stretch to push everything to the top
        main_layout.addStretch()
        
        # Set the main layout
        self.setLayout(main_layout)
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration from UI controls
        
        Returns:
            dict: Current configuration
        """
        return {
            'chunking_mode': self.chunking_mode.currentText(),
            'chunk_overlap': self.chunk_overlap.value(),
            'min_token_threshold': self.min_token_threshold.value(),
            'low_quality_token_threshold': self.low_quality_token_threshold.value(),
            'timeout': self.timeout.value(),
            'max_retries': self.max_retries.value(),
            'batch_size': self.batch_size.value(),
            'verbose': self.verbose.isChecked(),
            'auto_normalize': self.auto_normalize.isChecked()
        }
    
    def set_config(self, config: Dict[str, Any]):
        """Set the configuration and update UI controls
        
        Args:
            config: Configuration to set
        """
        if 'chunking_mode' in config:
            self.chunking_mode.setCurrentText(config['chunking_mode'])
        if 'chunk_overlap' in config:
            self.chunk_overlap.setValue(config['chunk_overlap'])
        if 'min_token_threshold' in config:
            self.min_token_threshold.setValue(config['min_token_threshold'])
        if 'low_quality_token_threshold' in config:
            self.low_quality_token_threshold.setValue(config['low_quality_token_threshold'])
        if 'timeout' in config:
            self.timeout.setValue(config['timeout'])
        if 'max_retries' in config:
            self.max_retries.setValue(config['max_retries'])
        if 'batch_size' in config:
            self.batch_size.setValue(config['batch_size'])
        if 'verbose' in config:
            self.verbose.setChecked(config['verbose'])
        if 'auto_normalize' in config:
            self.auto_normalize.setChecked(config['auto_normalize'])
        
        # Update processor config
        self.processor.config.update(config)
    
    def process_directory(self, input_dir: str, output_dir: str) -> Dict[str, Any]:
        """Process a directory of files
        
        Args:
            input_dir: Input directory path
            output_dir: Output directory path
            
        Returns:
            dict: Processing results
        """
        try:
            # Update processor config with current UI values
            self.processor.config.update(self.get_config())

            # Fast-path: if the directory contains PDFs, delegate to multiprocessing extractor directly
            pdf_found = any(Path(input_dir).rglob('*.pdf'))
            if pdf_found:
                return self.processor.process_directory(input_dir, output_dir)
            
            # Create worker with current configuration
            options = {
                'encoding_detection': self.processor.config.get('encoding_detection', True),
                'quality_threshold': self.processor.config.get('quality_threshold', 0.7),
                'clean_whitespace': self.processor.config.get('clean_whitespace', True),
                'normalize_unicode': self.processor.config.get('normalize_unicode', True),
                'extract_structure': self.processor.config.get('extract_structure', False),
                'language_detection': self.processor.config.get('language_detection', True),
                'preserve_linebreaks': self.processor.config.get('preserve_linebreaks', False),
                'max_file_size': self.processor.config.get('max_file_size', 50),
                'batch_size': self.processor.config.get('batch_size', 20)
            }
            
            # Create and run worker
            worker = BatchTextExtractorWorker(input_dir, output_dir, options)
            
            # Create a queue to collect results
            from queue import Queue
            from typing import Dict as _Dict, Any as _Any
            result_queue: "Queue[_Dict[str, _Any]]" = Queue()
            
            # Connect signals
            def on_batch_completed(stats):
                result_queue.put({
                    'success': True,
                    'files_processed': stats['processed_files'],
                    'successful': stats['successful_files'],
                    'failed': stats['failed_files'],
                    'total_characters': stats['total_characters'],
                    'total_words': stats['total_words'],
                    'processing_time': stats['processing_time']
                })
            
            def on_error(error_type, error_msg):
                result_queue.put({
                    'success': False,
                    'error': f"{error_type}: {error_msg}",
                    'files_processed': 0,
                    'successful': 0,
                    'failed': 0
                })
            
            worker.batch_completed.connect(on_batch_completed)
            worker.error_occurred.connect(on_error)
            
            # Run the worker
            worker.run()
            
            # Get results
            return result_queue.get()
            
        except Exception as e:
            self.logger.error(f"Error in process_directory: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'files_processed': 0,
                'successful': 0,
                'failed': 0
            }
    
    def process_file(self, file_path: str, output_dir: str) -> Dict[str, Any]:
        """Process a single file
        
        Args:
            file_path: Input file path
            output_dir: Output directory path
            
        Returns:
            dict: Processing results
        """
        # Update processor config with current UI values
        self.processor.config.update(self.get_config())
        return self.processor.process_file(file_path, output_dir)

    # --- Properties and Methods for explicit delegation ---
    @property
    def is_running(self):
        return self._is_running

    @is_running.setter
    def is_running(self, value):
        self._is_running = value

    def refresh_config(self):
        """Reload parameters from ``self.config``."""
        cfg = {}
        if hasattr(self.project_config, 'get'):
            cfg = self.project_config.get('processors.batch_text_extractor_enhanced_prerefactor', {})
        for k, v in cfg.items():
            method = f'set_{k}'
            if hasattr(self, method):
                try:
                    getattr(self, method)(v)
                    continue
                except Exception:
                    if self.logger:
                        self.logger.debug('Failed to apply %s via wrapper', k)
            if hasattr(self.processor, method):
                try:
                    getattr(self.processor, method)(v)
                    continue
                except Exception:
                    if self.logger:
                        self.logger.debug('Failed to apply %s via processor', k)
            if hasattr(self.processor, k):
                setattr(self.processor, k, v)
            elif hasattr(self, k):
                setattr(self, k, v)
        # No configuration_changed signal in this wrapper, so skip emit

    # ------------------------------------------------------------------
    # Convenience entry-point for CLI execution (mirrors PDF/Text wrappers)
    # ------------------------------------------------------------------
    def start(self):
        """Process all PDF files found under ``project_config.get_raw_dir()``.

        This method is called by the non-GUI CLI runner.  It MUST NOT rely on
        any Qt widgets – it directly uses the underlying multiprocessing
        processor to perform the extraction and therefore works fine even when
        all Qt classes are stubbed out.
        """
        from pathlib import Path

        # Resolve raw / processed directories as robustly as possible
        try:
            raw_dir = Path(self.project_config.get_raw_dir())
        except Exception:
            raw_dir = Path(self.project_config.get('environments.local.raw_data_dir', '.'))

        try:
            processed_dir = Path(self.project_config.get_processed_dir())
        except Exception:
            processed_dir = Path(self.project_config.get('environments.local.processed_dir', './processed'))

        if not raw_dir.exists():
            if self.logger:
                self.logger.warning("Raw directory '%s' does not exist – skipping batch PDF extraction", raw_dir)
            return

        processed_dir.mkdir(parents=True, exist_ok=True)

        # Delegate to the enhanced multiprocessing extractor directly
        stats = self.processor.process_directory(str(raw_dir), str(processed_dir))

        if self.logger:
            self.logger.info("Batch PDF extraction completed: %s", stats)

        return stats
