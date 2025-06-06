"""
Batch Text Extractor Enhanced Pre-refactor Wrapper for UI Integration
Provides comprehensive batch text extraction with advanced preprocessing
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple, Union
from PySide6.QtCore import QObject, QThread, Signal as pyqtSignal, Slot as pyqtSlot, QMutex, QTimer, Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QProgressBar, QLabel, QTextEdit, QFileDialog, QCheckBox, 
                           QSpinBox, QGroupBox, QGridLayout, QComboBox, QDoubleSpinBox,
                           QTabWidget, QListWidget, QSplitter, QFormLayout)
from shared_tools.ui_wrappers.base_wrapper import BaseWrapper
from shared_tools.processors.batch_text_extractor_enhanced_prerefactor import BatchTextExtractorEnhancedPrerefactor
from shared_tools.processors.mixins.processor_wrapper_mixin import ProcessorWrapperMixin
from ...project_config import ProjectConfig


class BatchTextExtractorWorker(QThread):
    """Worker thread for batch text extraction operations"""
    
    progress_updated = pyqtSignal(int, str, dict)  # progress, current file, stats
    file_processed = pyqtSignal(str, bool, str, dict)  # file path, success, message, metadata
    batch_completed = pyqtSignal(dict)  # final statistics
    error_occurred = pyqtSignal(str, str)  # error type, error message
    quality_report = pyqtSignal(str, dict)  # file path, quality metrics
    
    def __init__(self, input_path: str, output_path: str, options: Dict[str, Any]):
        super().__init__()
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
        supported_extensions = ['.txt', '.text', '.log', '.csv', '.tsv', '.json', '.xml', '.html', '.htm']
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


class BatchTextExtractorEnhancedPrerefactorWrapper(ProcessorWrapperMixin):
    """Wrapper for BatchTextExtractorEnhancedPrerefactor with UI controls"""
    
    def __init__(self, parent: Optional[QWidget] = None, project_config: Optional[Union[str, ProjectConfig]] = None):
        """Initialize the wrapper
        
        Args:
            parent: Parent widget
            project_config: Optional project configuration
        """
        super().__init__(parent, project_config)
        self.processor = BatchTextExtractorEnhancedPrerefactor(project_config=project_config)
        self._init_ui()
    
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
        # Update processor config with current UI values
        self.processor.config.update(self.get_config())
        return self.processor.process_directory(input_dir, output_dir)
    
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


class BatchTextExtractorWrapper(BaseWrapper, ProcessorWrapperMixin):
    """UI Wrapper for Batch Text Extractor Enhanced Pre-refactor"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.processed_files = []
        self.quality_reports = []
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Initialize the user interface components"""
        layout = QVBoxLayout(self)
        
        # Create tab widget for organized interface
        self.tab_widget = QTabWidget()
        
        # Configuration Tab
        config_tab = self._create_configuration_tab()
        self.tab_widget.addTab(config_tab, "Configuration")
        
        # Processing Tab
        processing_tab = self._create_processing_tab()
        self.tab_widget.addTab(processing_tab, "Processing")
        
        # Results Tab
        results_tab = self._create_results_tab()
        self.tab_widget.addTab(results_tab, "Results")
        
        layout.addWidget(self.tab_widget)
        
    def _create_configuration_tab(self) -> QWidget:
        """Create the configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Input/Output Configuration
        io_group = QGroupBox("Input/Output Configuration")
        io_layout = QGridLayout(io_group)
        
        self.input_label = QLabel("Input Directory:")
        self.input_path_display = QLabel("No directory selected")
        self.input_browse_btn = QPushButton("Browse...")
        
        self.output_label = QLabel("Output Directory:")
        self.output_path_display = QLabel("No directory selected")
        self.output_browse_btn = QPushButton("Browse...")
        
        io_layout.addWidget(self.input_label, 0, 0)
        io_layout.addWidget(self.input_path_display, 0, 1)
        io_layout.addWidget(self.input_browse_btn, 0, 2)
        io_layout.addWidget(self.output_label, 1, 0)
        io_layout.addWidget(self.output_path_display, 1, 1)
        io_layout.addWidget(self.output_browse_btn, 1, 2)
        
        # Text Processing Options
        text_group = QGroupBox("Text Processing Options")
        text_layout = QGridLayout(text_group)
        
        self.encoding_detection_cb = QCheckBox("Auto-detect Encoding")
        self.encoding_detection_cb.setChecked(True)
        
        self.clean_whitespace_cb = QCheckBox("Clean Whitespace")
        self.clean_whitespace_cb.setChecked(True)
        
        self.normalize_unicode_cb = QCheckBox("Normalize Unicode")
        self.normalize_unicode_cb.setChecked(True)
        
        self.preserve_linebreaks_cb = QCheckBox("Preserve Line Breaks")
        self.preserve_linebreaks_cb.setChecked(False)
        
        self.extract_structure_cb = QCheckBox("Extract Document Structure")
        self.extract_structure_cb.setChecked(False)
        
        self.language_detection_cb = QCheckBox("Detect Language")
        self.language_detection_cb.setChecked(True)
        
        text_layout.addWidget(self.encoding_detection_cb, 0, 0)
        text_layout.addWidget(self.clean_whitespace_cb, 0, 1)
        text_layout.addWidget(self.normalize_unicode_cb, 1, 0)
        text_layout.addWidget(self.preserve_linebreaks_cb, 1, 1)
        text_layout.addWidget(self.extract_structure_cb, 2, 0)
        text_layout.addWidget(self.language_detection_cb, 2, 1)
        
        # Quality and Performance Options
        quality_group = QGroupBox("Quality and Performance")
        quality_layout = QGridLayout(quality_group)
        
        self.quality_threshold_label = QLabel("Quality Threshold:")
        self.quality_threshold_spin = QDoubleSpinBox()
        self.quality_threshold_spin.setRange(0.0, 1.0)
        self.quality_threshold_spin.setSingleStep(0.1)
        self.quality_threshold_spin.setValue(0.7)
        
        self.max_file_size_label = QLabel("Max File Size (MB):")
        self.max_file_size_spin = QSpinBox()
        self.max_file_size_spin.setRange(1, 500)
        self.max_file_size_spin.setValue(50)
        
        self.batch_size_label = QLabel("Batch Size:")
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 100)
        self.batch_size_spin.setValue(20)
        
        quality_layout.addWidget(self.quality_threshold_label, 0, 0)
        quality_layout.addWidget(self.quality_threshold_spin, 0, 1)
        quality_layout.addWidget(self.max_file_size_label, 1, 0)
        quality_layout.addWidget(self.max_file_size_spin, 1, 1)
        quality_layout.addWidget(self.batch_size_label, 2, 0)
        quality_layout.addWidget(self.batch_size_spin, 2, 1)
        
        layout.addWidget(io_group)
        layout.addWidget(text_group)
        layout.addWidget(quality_group)
        layout.addStretch()
        
        return tab
        
    def _create_processing_tab(self) -> QWidget:
        """Create the processing tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Control Buttons
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Extraction")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.cancel_btn)
        control_layout.addStretch()
        
        # Progress Display
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("Ready to start")
        
        # Statistics Display
        stats_layout = QGridLayout()
        self.total_files_label = QLabel("Total Files: 0")
        self.processed_files_label = QLabel("Processed: 0")
        self.successful_files_label = QLabel("Successful: 0")
        self.failed_files_label = QLabel("Failed: 0")
        self.total_chars_label = QLabel("Total Characters: 0")
        self.processing_time_label = QLabel("Processing Time: 0s")
        
        stats_layout.addWidget(self.total_files_label, 0, 0)
        stats_layout.addWidget(self.processed_files_label, 0, 1)
        stats_layout.addWidget(self.successful_files_label, 1, 0)
        stats_layout.addWidget(self.failed_files_label, 1, 1)
        stats_layout.addWidget(self.total_chars_label, 2, 0)
        stats_layout.addWidget(self.processing_time_label, 2, 1)
        
        # Status Display
        self.status_display = QTextEdit()
        self.status_display.setMaximumHeight(200)
        self.status_display.setReadOnly(True)
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addLayout(stats_layout)
        progress_layout.addWidget(QLabel("Processing Log:"))
        progress_layout.addWidget(self.status_display)
        
        layout.addLayout(control_layout)
        layout.addWidget(progress_group)
        
        return tab
        
    def _create_results_tab(self) -> QWidget:
        """Create the results tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create splitter for results
        splitter = QSplitter()
        
        # File Results List
        files_group = QGroupBox("Processed Files")
        files_layout = QVBoxLayout(files_group)
        self.files_list = QListWidget()
        files_layout.addWidget(self.files_list)
        
        # Quality Reports
        quality_group = QGroupBox("Quality Reports")
        quality_layout = QVBoxLayout(quality_group)
        self.quality_display = QTextEdit()
        self.quality_display.setReadOnly(True)
        quality_layout.addWidget(self.quality_display)
        
        splitter.addWidget(files_group)
        splitter.addWidget(quality_group)
        splitter.setSizes([400, 400])
        
        # Export Results Button
        export_layout = QHBoxLayout()
        self.export_results_btn = QPushButton("Export Results")
        self.export_results_btn.setEnabled(False)
        export_layout.addWidget(self.export_results_btn)
        export_layout.addStretch()
        
        layout.addWidget(splitter)
        layout.addLayout(export_layout)
        
        return tab
        
    def setup_connections(self):
        """Setup signal-slot connections"""
        self.input_browse_btn.clicked.connect(self.browse_input_directory)
        self.output_browse_btn.clicked.connect(self.browse_output_directory)
        self.start_btn.clicked.connect(self.start_extraction)
        self.cancel_btn.clicked.connect(self.cancel_extraction)
        self.export_results_btn.clicked.connect(self.export_results)
        self.files_list.currentRowChanged.connect(self.show_file_quality_report)
        
    @pyqtSlot()
    def browse_input_directory(self):
        """Browse for input directory"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Input Directory",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.input_path_display.setText(directory)
            
    @pyqtSlot()
    def browse_output_directory(self):
        """Browse for output directory"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Output Directory",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.output_path_display.setText(directory)
            
    @pyqtSlot()
    def start_extraction(self):
        """Start the batch extraction process"""
        input_path = self.input_path_display.text()
        output_path = self.output_path_display.text()
        
        if input_path == "No directory selected" or output_path == "No directory selected":
            self.show_error("Configuration Error", "Please select both input and output directories")
            return
            
        # Prepare options
        options = {
            'encoding_detection': self.encoding_detection_cb.isChecked(),
            'quality_threshold': self.quality_threshold_spin.value(),
            'clean_whitespace': self.clean_whitespace_cb.isChecked(),
            'normalize_unicode': self.normalize_unicode_cb.isChecked(),
            'extract_structure': self.extract_structure_cb.isChecked(),
            'language_detection': self.language_detection_cb.isChecked(),
            'preserve_linebreaks': self.preserve_linebreaks_cb.isChecked(),
            'max_file_size': self.max_file_size_spin.value(),
            'batch_size': self.batch_size_spin.value()
        }
        
        # Create and start worker
        self.worker = BatchTextExtractorWorker(input_path, output_path, options)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.file_processed.connect(self.file_processed)
        self.worker.batch_completed.connect(self.batch_completed)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.quality_report.connect(self.add_quality_report)
        
        # Update UI state
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_display.clear()
        self.files_list.clear()
        self.quality_display.clear()
        self.processed_files.clear()
        self.quality_reports.clear()
        
        # Switch to processing tab
        self.tab_widget.setCurrentIndex(1)
        
        self.worker.start()
        
    @pyqtSlot()
    def cancel_extraction(self):
        """Cancel extraction process"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(3000)
            self.extraction_finished()
            
    @pyqtSlot(int, str, dict)
    def update_progress(self, percentage: int, message: str, stats: dict):
        """Update progress display"""
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(message)
        
        # Update statistics
        self.total_files_label.setText(f"Total Files: {stats.get('total_files', 0)}")
        self.processed_files_label.setText(f"Processed: {stats.get('processed_files', 0)}")
        self.successful_files_label.setText(f"Successful: {stats.get('successful_files', 0)}")
        self.failed_files_label.setText(f"Failed: {stats.get('failed_files', 0)}")
        self.total_chars_label.setText(f"Total Characters: {stats.get('total_characters', 0):,}")
        
    @pyqtSlot(str, bool, str, dict)
    def file_processed(self, file_path: str, success: bool, message: str, metadata: dict):
        """Handle individual file processing result"""
        filename = os.path.basename(file_path)
        status = "✓" if success else "✗"
        self.status_display.append(f"{status} {filename}: {message}")
        
        # Add to files list
        self.files_list.addItem(f"{status} {filename}")
        self.processed_files.append((file_path, success, message, metadata))
        
    @pyqtSlot(str, dict)
    def add_quality_report(self, file_path: str, quality_metrics: dict):
        """Add quality report for a file"""
        self.quality_reports.append((file_path, quality_metrics))
        
    @pyqtSlot(dict)
    def batch_completed(self, stats: dict):
        """Handle batch completion"""
        self.extraction_finished()
        
        # Update final statistics
        self.processing_time_label.setText(f"Processing Time: {stats.get('processing_time', 0):.1f}s")
        
        # Show completion summary
        summary = f"Batch extraction completed:\n"
        summary += f"Total files: {stats.get('total_files', 0)}\n"
        summary += f"Successful: {stats.get('successful_files', 0)}\n"
        summary += f"Failed: {stats.get('failed_files', 0)}\n"
        summary += f"Total characters extracted: {stats.get('total_characters', 0):,}\n"
        summary += f"Total words extracted: {stats.get('total_words', 0):,}\n"
        summary += f"Processing time: {stats.get('processing_time', 0):.1f} seconds"
        
        self.progress_label.setText("Extraction completed")
        self.status_display.append("\n" + "="*50)
        self.status_display.append(summary)
        
        # Enable export button
        self.export_results_btn.setEnabled(True)
        
        # Switch to results tab
        self.tab_widget.setCurrentIndex(2)
        
    @pyqtSlot(str, str)
    def handle_error(self, error_type: str, error_message: str):
        """Handle processing errors"""
        self.extraction_finished()
        self.show_error(error_type, error_message)
        
    @pyqtSlot(int)
    def show_file_quality_report(self, row: int):
        """Show quality report for selected file"""
        if 0 <= row < len(self.quality_reports):
            file_path, quality_metrics = self.quality_reports[row]
            filename = os.path.basename(file_path)
            
            report = f"Quality Report for: {filename}\n"
            report += "="*50 + "\n\n"
            
            for metric, value in quality_metrics.items():
                if isinstance(value, float):
                    report += f"{metric}: {value:.3f}\n"
                else:
                    report += f"{metric}: {value}\n"
                    
            self.quality_display.setText(report)
            
    @pyqtSlot()
    def export_results(self):
        """Export processing results to JSON"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            "extraction_results.json",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                results = {
                    'processed_files': self.processed_files,
                    'quality_reports': self.quality_reports,
                    'timestamp': time.time()
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                    
                self.show_info("Export Successful", f"Results exported to {filename}")
                
            except Exception as e:
                self.show_error("Export Error", f"Failed to export results: {str(e)}")
        
    def extraction_finished(self):
        """Reset UI state after extraction completion"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
            
    def get_processing_results(self) -> List[tuple]:
        """Get results of processed files"""
        return self.processed_files.copy()
        
    def get_quality_reports(self) -> List[tuple]:
        """Get quality reports"""
        return self.quality_reports.copy()
        
    def is_processing(self) -> bool:
        """Check if processing is currently active"""
        return self.worker is not None and self.worker.isRunning()
