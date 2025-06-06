"""
Batch Non-PDF Extractor Enhanced Wrapper for UI Integration
Provides comprehensive batch processing capabilities for non-PDF documents
"""

import os
import time
from typing import Dict, List, Optional, Any
from PySide6.QtCore import QObject, QThread, Signal as pyqtSignal, Slot as pyqtSlot, QMutex, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar, QLabel, QTextEdit, QFileDialog, QCheckBox, QSpinBox, QGroupBox, QGridLayout
from shared_tools.ui_wrappers.base_wrapper import BaseWrapper, ProcessorWrapperMixin
from shared_tools.processors.batch_nonpdf_extractor_enhanced import BatchNonPDFExtractorEnhanced


class BatchNonPDFExtractorWorker(QThread):
    """Worker thread for batch non-PDF extraction operations"""
    
    progress_updated = pyqtSignal(int, str)  # progress percentage, current file
    file_processed = pyqtSignal(str, bool, str)  # file path, success, message
    batch_completed = pyqtSignal(int, int, list)  # total files, successful, errors
    error_occurred = pyqtSignal(str, str)  # error type, error message
    
    def __init__(self, input_path: str, output_path: str, options: Dict[str, Any]):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.options = options
        self.extractor = BatchNonPDFExtractorEnhanced()
        self._is_cancelled = False
        self._mutex = QMutex()
        
    def run(self):
        """Execute batch extraction process"""
        try:
            # Initialize extraction parameters
            self.extractor.configure(
                preserve_formatting=self.options.get('preserve_formatting', True),
                extract_metadata=self.options.get('extract_metadata', True),
                handle_tables=self.options.get('handle_tables', True),
                max_file_size=self.options.get('max_file_size', 100),
                batch_size=self.options.get('batch_size', 10)
            )
            
            # Get list of files to process
            files_to_process = self._get_files_to_process()
            total_files = len(files_to_process)
            
            if total_files == 0:
                self.error_occurred.emit("No Files", "No compatible files found in the specified directory")
                return
                
            successful_files = 0
            error_files = []
            
            for i, file_path in enumerate(files_to_process):
                if self._is_cancelled:
                    break
                    
                # Update progress
                progress = int((i / total_files) * 100)
                filename = os.path.basename(file_path)
                self.progress_updated.emit(progress, f"Processing: {filename}")
                
                try:
                    # Process individual file
                    success = self.extractor.extract_file(file_path, self.output_path)
                    
                    if success:
                        successful_files += 1
                        self.file_processed.emit(file_path, True, "Successfully extracted")
                    else:
                        error_files.append(file_path)
                        self.file_processed.emit(file_path, False, "Extraction failed")
                        
                except Exception as e:
                    error_files.append(file_path)
                    self.file_processed.emit(file_path, False, str(e))
                    
            # Final progress update
            self.progress_updated.emit(100, "Batch processing completed")
            self.batch_completed.emit(total_files, successful_files, error_files)
            
        except Exception as e:
            self.error_occurred.emit("Processing Error", str(e))
            
    def cancel(self):
        """Cancel the current operation"""
        self._mutex.lock()
        self._is_cancelled = True
        self._mutex.unlock()
        
    def _get_files_to_process(self) -> List[str]:
        """Get list of compatible files to process"""
        supported_extensions = ['.docx', '.doc', '.rtf', '.txt', '.html', '.htm', '.xml']
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


class BatchNonPDFExtractorEnhancedWrapper(BaseWrapper, ProcessorWrapperMixin):
    """UI Wrapper for Batch Non-PDF Extractor Enhanced"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.processed_files = []
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Initialize the user interface components"""
        layout = QVBoxLayout(self)
        
        # Input/Output Selection
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
        
        # Processing Options
        options_group = QGroupBox("Processing Options")
        options_layout = QGridLayout(options_group)
        
        self.preserve_formatting_cb = QCheckBox("Preserve Formatting")
        self.preserve_formatting_cb.setChecked(True)
        
        self.extract_metadata_cb = QCheckBox("Extract Metadata")
        self.extract_metadata_cb.setChecked(True)
        
        self.handle_tables_cb = QCheckBox("Handle Tables")
        self.handle_tables_cb.setChecked(True)
        
        self.max_file_size_label = QLabel("Max File Size (MB):")
        self.max_file_size_spin = QSpinBox()
        self.max_file_size_spin.setRange(1, 1000)
        self.max_file_size_spin.setValue(100)
        
        self.batch_size_label = QLabel("Batch Size:")
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 100)
        self.batch_size_spin.setValue(10)
        
        options_layout.addWidget(self.preserve_formatting_cb, 0, 0)
        options_layout.addWidget(self.extract_metadata_cb, 0, 1)
        options_layout.addWidget(self.handle_tables_cb, 1, 0)
        options_layout.addWidget(self.max_file_size_label, 2, 0)
        options_layout.addWidget(self.max_file_size_spin, 2, 1)
        options_layout.addWidget(self.batch_size_label, 3, 0)
        options_layout.addWidget(self.batch_size_spin, 3, 1)
        
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
        self.status_display = QTextEdit()
        self.status_display.setMaximumHeight(150)
        self.status_display.setReadOnly(True)
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_display)
        
        # Add all groups to main layout
        layout.addWidget(io_group)
        layout.addWidget(options_group)
        layout.addLayout(control_layout)
        layout.addWidget(progress_group)
        
    def setup_connections(self):
        """Setup signal-slot connections"""
        self.input_browse_btn.clicked.connect(self.browse_input_directory)
        self.output_browse_btn.clicked.connect(self.browse_output_directory)
        self.start_btn.clicked.connect(self.start_extraction)
        self.cancel_btn.clicked.connect(self.cancel_extraction)
        
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
            
        if not os.path.exists(input_path):
            self.show_error("Path Error", "Input directory does not exist")
            return
            
        # Prepare options
        options = {
            'preserve_formatting': self.preserve_formatting_cb.isChecked(),
            'extract_metadata': self.extract_metadata_cb.isChecked(),
            'handle_tables': self.handle_tables_cb.isChecked(),
            'max_file_size': self.max_file_size_spin.value(),
            'batch_size': self.batch_size_spin.value()
        }
        
        # Create and start worker thread
        self.worker = BatchNonPDFExtractorWorker(input_path, output_path, options)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.file_processed.connect(self.file_processed)
        self.worker.batch_completed.connect(self.batch_completed)
        self.worker.error_occurred.connect(self.handle_error)
        
        # Update UI state
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_display.clear()
        self.processed_files.clear()
        
        self.worker.start()
        
    @pyqtSlot()
    def cancel_extraction(self):
        """Cancel the current extraction process"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(3000)  # Wait up to 3 seconds
            self.extraction_finished()
            
    @pyqtSlot(int, str)
    def update_progress(self, percentage: int, message: str):
        """Update progress display"""
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(message)
        
    @pyqtSlot(str, bool, str)
    def file_processed(self, file_path: str, success: bool, message: str):
        """Handle individual file processing result"""
        filename = os.path.basename(file_path)
        status = "✓" if success else "✗"
        self.status_display.append(f"{status} {filename}: {message}")
        self.processed_files.append((file_path, success, message))
        
    @pyqtSlot(int, int, list)
    def batch_completed(self, total_files: int, successful_files: int, error_files: list):
        """Handle batch completion"""
        self.extraction_finished()
        
        # Show completion summary
        error_count = len(error_files)
        summary = f"Batch extraction completed:\n"
        summary += f"Total files: {total_files}\n"
        summary += f"Successful: {successful_files}\n"
        summary += f"Errors: {error_count}"
        
        self.progress_label.setText("Extraction completed")
        self.status_display.append("\n" + "="*50)
        self.status_display.append(summary)
        
        if error_count > 0:
            self.status_display.append("\nFiles with errors:")
            for error_file in error_files[:10]:  # Show first 10 errors
                self.status_display.append(f"  • {os.path.basename(error_file)}")
            if error_count > 10:
                self.status_display.append(f"  ... and {error_count - 10} more")
                
    @pyqtSlot(str, str)
    def handle_error(self, error_type: str, error_message: str):
        """Handle processing errors"""
        self.extraction_finished()
        self.show_error(error_type, error_message)
        
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
        
    def is_processing(self) -> bool:
        """Check if processing is currently active"""
        return self.worker is not None and self.worker.isRunning()
