"""
Deduplicate Non-PDF Outputs Wrapper for UI Integration
Provides comprehensive deduplication capabilities for non-PDF documents
"""

import os
import hashlib
import subprocess
import sys
from typing import Dict, List, Optional, Any, Set, Tuple
from PySide6.QtCore import QObject, QThread, Signal as pyqtSignal, Slot as pyqtSlot, QMutex
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QProgressBar, QLabel, QTextEdit, QFileDialog, QCheckBox, 
                           QSpinBox, QGroupBox, QGridLayout, QComboBox, QListWidget,
                           QSplitter, QTabWidget, QTableWidget, QTableWidgetItem,
                           QHeaderView, QSlider)
from shared_tools.ui_wrappers.base_wrapper import BaseWrapper
from shared_tools.processors.deduplicate_nonpdf_outputs import DeduplicateNonPDFOutputs
from shared_tools.processors.mixins.processor_wrapper_mixin import ProcessorWrapperMixin


class DeduplicationWorker(QThread):
    """Worker thread for non-PDF deduplication operations"""
    
    progress_updated = pyqtSignal(int, str, dict)  # progress, message, stats
    duplicate_found = pyqtSignal(str, str, float)  # original_file, duplicate_file, similarity
    deduplication_completed = pyqtSignal(dict)  # final statistics
    error_occurred = pyqtSignal(str, str)  # error_type, error_message
    
    def __init__(self, input_directory: str, options: Dict[str, Any]):
        super().__init__()
        self.input_directory = input_directory
        self.options = options
        self.deduplicator = DeduplicateNonPDFOutputs()
        self._is_cancelled = False
        self._mutex = QMutex()
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'duplicates_found': 0,
            'duplicates_removed': 0,
            'space_saved': 0,
            'processing_time': 0.0
        }
        
    def run(self):
        """Execute deduplication process"""
        import time
        start_time = time.time()
        
        try:
            # Configure deduplicator
            self.deduplicator.configure(
                similarity_threshold=self.options.get('similarity_threshold', 0.95),
                hash_algorithm=self.options.get('hash_algorithm', 'sha256'),
                content_comparison=self.options.get('content_comparison', True),
                preserve_newest=self.options.get('preserve_newest', True),
                backup_duplicates=self.options.get('backup_duplicates', False),
                max_file_size=self.options.get('max_file_size', 100)
            )
            
            # Get files to process
            files_to_process = self._get_files_to_process()
            self.stats['total_files'] = len(files_to_process)
            
            if self.stats['total_files'] == 0:
                self.error_occurred.emit("No Files", "No files found for deduplication")
                return
                
            # Process files for duplicates
            duplicates_map = self._find_duplicates(files_to_process)
            
            # Remove duplicates if requested
            if self.options.get('auto_remove', False):
                self._remove_duplicates(duplicates_map)
                
            # Calculate final statistics
            self.stats['processing_time'] = time.time() - start_time
            self.deduplication_completed.emit(self.stats)
            
        except Exception as e:
            self.error_occurred.emit("Deduplication Error", str(e))
            
    def _get_files_to_process(self) -> List[str]:
        """Get list of non-PDF files to process"""
        supported_extensions = ['.txt', '.docx', '.doc', '.rtf', '.html', '.htm', '.xml', '.csv']
        files = []
        
        for root, dirs, filenames in os.walk(self.input_directory):
            for filename in filenames:
                if any(filename.lower().endswith(ext) for ext in supported_extensions):
                    files.append(os.path.join(root, filename))
                    
        return files
        
    def _find_duplicates(self, files: List[str]) -> Dict[str, List[str]]:
        """Find duplicate files using various comparison methods"""
        duplicates_map = {}
        file_hashes = {}
        
        for i, file_path in enumerate(files):
            if self._is_cancelled:
                break
                
            try:
                # Update progress
                progress = int((i / len(files)) * 100)
                filename = os.path.basename(file_path)
                self.progress_updated.emit(progress, f"Analyzing: {filename}", self.stats.copy())
                
                # Calculate file hash
                file_hash = self._calculate_file_hash(file_path)
                
                if file_hash in file_hashes:
                    # Potential duplicate found
                    original_file = file_hashes[file_hash]
                    similarity = self._compare_content(original_file, file_path)
                    
                    if similarity >= self.options.get('similarity_threshold', 0.95):
                        # Confirmed duplicate
                        self.duplicate_found.emit(original_file, file_path, similarity)
                        
                        if original_file not in duplicates_map:
                            duplicates_map[original_file] = []
                        duplicates_map[original_file].append(file_path)
                        
                        self.stats['duplicates_found'] += 1
                else:
                    file_hashes[file_hash] = file_path
                    
                self.stats['processed_files'] += 1
                
            except Exception as e:
                # Log error but continue processing
                continue
                
        return duplicates_map
        
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate hash for file content"""
        hash_algo = self.options.get('hash_algorithm', 'sha256')
        
        if hash_algo == 'md5':
            hasher = hashlib.md5()
        elif hash_algo == 'sha1':
            hasher = hashlib.sha1()
        else:
            hasher = hashlib.sha256()
            
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return f"error_{file_path}"
            
    def _compare_content(self, file1: str, file2: str) -> float:
        """Compare content similarity between two files"""
        if not self.options.get('content_comparison', True):
            return 1.0  # Assume identical based on hash
            
        try:
            # Simple content comparison (in real implementation, use more sophisticated methods)
            with open(file1, 'r', encoding='utf-8', errors='ignore') as f1:
                content1 = f1.read()
            with open(file2, 'r', encoding='utf-8', errors='ignore') as f2:
                content2 = f2.read()
                
            # Basic similarity calculation
            if content1 == content2:
                return 1.0
            else:
                # Use simple character-based similarity
                shorter_len = min(len(content1), len(content2))
                longer_len = max(len(content1), len(content2))
                
                if longer_len == 0:
                    return 1.0
                    
                common_chars = sum(1 for c1, c2 in zip(content1, content2) if c1 == c2)
                return common_chars / longer_len
                
        except Exception:
            return 0.0
            
    def _remove_duplicates(self, duplicates_map: Dict[str, List[str]]):
        """Remove duplicate files based on policy"""
        backup_dir = None
        if self.options.get('backup_duplicates', False):
            backup_dir = os.path.join(self.input_directory, '.duplicates_backup')
            os.makedirs(backup_dir, exist_ok=True)
            
        for original_file, duplicates in duplicates_map.items():
            for duplicate_file in duplicates:
                try:
                    file_size = os.path.getsize(duplicate_file)
                    
                    if backup_dir:
                        # Move to backup directory
                        backup_filename = f"{os.path.basename(duplicate_file)}_{int(time.time())}"
                        backup_path = os.path.join(backup_dir, backup_filename)
                        os.rename(duplicate_file, backup_path)
                    else:
                        # Permanently delete
                        os.remove(duplicate_file)
                        
                    self.stats['duplicates_removed'] += 1
                    self.stats['space_saved'] += file_size
                    
                except Exception as e:
                    continue
                    
    def cancel(self):
        """Cancel the current operation"""
        self._mutex.lock()
        self._is_cancelled = True
        self._mutex.unlock()


class DeduplicateNonPDFOutputsWrapper(BaseWrapper, ProcessorWrapperMixin):
    """UI Wrapper for Non-PDF Deduplication"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.duplicates_found = []
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Initialize the user interface components"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Configuration Tab
        config_tab = self._create_configuration_tab()
        self.tab_widget.addTab(config_tab, "Configuration")
        
        # Processing Tab
        processing_tab = self._create_processing_tab()
        self.tab_widget.addTab(processing_tab, "Deduplication")
        
        # Results Tab
        results_tab = self._create_results_tab()
        self.tab_widget.addTab(results_tab, "Results")
        
        layout.addWidget(self.tab_widget)
        
    def _create_configuration_tab(self) -> QWidget:
        """Create the configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Input Selection
        input_group = QGroupBox("Input Directory")
        input_layout = QGridLayout(input_group)
        
        self.input_label = QLabel("Directory to Process:")
        self.input_path_display = QLabel("No directory selected")
        self.input_browse_btn = QPushButton("Browse...")
        
        input_layout.addWidget(self.input_label, 0, 0)
        input_layout.addWidget(self.input_path_display, 0, 1)
        input_layout.addWidget(self.input_browse_btn, 0, 2)
        
        # Deduplication Options
        options_group = QGroupBox("Deduplication Options")
        options_layout = QGridLayout(options_group)
        
        # Similarity threshold
        self.similarity_label = QLabel("Similarity Threshold:")
        self.similarity_slider = QSlider(Qt.Orientation.Horizontal)
        self.similarity_slider.setRange(50, 100)
        self.similarity_slider.setValue(95)
        self.similarity_value_label = QLabel("95%")
        self.similarity_slider.valueChanged.connect(
            lambda v: self.similarity_value_label.setText(f"{v}%")
        )
        
        options_layout.addWidget(self.similarity_label, 0, 0)
        options_layout.addWidget(self.similarity_slider, 0, 1)
        options_layout.addWidget(self.similarity_value_label, 0, 2)
        
        # Hash algorithm
        self.hash_label = QLabel("Hash Algorithm:")
        self.hash_combo = QComboBox()
        self.hash_combo.addItems(["sha256", "sha1", "md5"])
        
        options_layout.addWidget(self.hash_label, 1, 0)
        options_layout.addWidget(self.hash_combo, 1, 1)
        
        # Content comparison
        self.content_comparison_cb = QCheckBox("Enable Content Comparison")
        self.content_comparison_cb.setChecked(True)
        options_layout.addWidget(self.content_comparison_cb, 2, 0, 1, 2)
        
        # Preserve policy
        self.preserve_newest_cb = QCheckBox("Preserve Newest Files")
        self.preserve_newest_cb.setChecked(True)
        options_layout.addWidget(self.preserve_newest_cb, 3, 0, 1, 2)
        
        # Backup duplicates
        self.backup_duplicates_cb = QCheckBox("Backup Duplicates Before Removal")
        self.backup_duplicates_cb.setChecked(False)
        options_layout.addWidget(self.backup_duplicates_cb, 4, 0, 1, 2)
        
        # Auto remove
        self.auto_remove_cb = QCheckBox("Automatically Remove Duplicates")
        self.auto_remove_cb.setChecked(False)
        options_layout.addWidget(self.auto_remove_cb, 5, 0, 1, 2)
        
        # File size limit
        self.max_size_label = QLabel("Max File Size (MB):")
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(1, 1000)
        self.max_size_spin.setValue(100)
        
        options_layout.addWidget(self.max_size_label, 6, 0)
        options_layout.addWidget(self.max_size_spin, 6, 1)
        
        layout.addWidget(input_group)
        layout.addWidget(options_group)
        layout.addStretch()
        
        return tab
        
    def _create_processing_tab(self) -> QWidget:
        """Create the processing tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Control Buttons
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Deduplication")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.cancel_btn)
        control_layout.addStretch()
        
        # Progress Display
        progress_group = QGroupBox("Deduplication Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("Ready to start deduplication")
        
        # Statistics Display
        stats_layout = QGridLayout()
        self.total_files_label = QLabel("Total Files: 0")
        self.processed_files_label = QLabel("Processed: 0")
        self.duplicates_found_label = QLabel("Duplicates Found: 0")
        self.duplicates_removed_label = QLabel("Duplicates Removed: 0")
        self.space_saved_label = QLabel("Space Saved: 0 MB")
        self.processing_time_label = QLabel("Processing Time: 0s")
        
        stats_layout.addWidget(self.total_files_label, 0, 0)
        stats_layout.addWidget(self.processed_files_label, 0, 1)
        stats_layout.addWidget(self.duplicates_found_label, 1, 0)
        stats_layout.addWidget(self.duplicates_removed_label, 1, 1)
        stats_layout.addWidget(self.space_saved_label, 2, 0)
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
        
        # Results Table
        results_group = QGroupBox("Duplicate Files Found")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Original File", "Duplicate File", "Similarity", "Size"])
        
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        results_layout.addWidget(self.results_table)
        
        # Action Buttons
        action_layout = QHBoxLayout()
        self.remove_selected_btn = QPushButton("Remove Selected Duplicates")
        self.remove_selected_btn.setEnabled(False)
        self.export_results_btn = QPushButton("Export Results")
        self.export_results_btn.setEnabled(False)
        
        action_layout.addWidget(self.remove_selected_btn)
        action_layout.addWidget(self.export_results_btn)
        action_layout.addStretch()
        
        results_layout.addLayout(action_layout)
        
        layout.addWidget(results_group)
        
        return tab
        
    def setup_connections(self):
        """Setup signal-slot connections"""
        self.input_browse_btn.clicked.connect(self.browse_input_directory)
        self.start_btn.clicked.connect(self.start_deduplication)
        self.cancel_btn.clicked.connect(self.cancel_deduplication)
        self.remove_selected_btn.clicked.connect(self.remove_selected_duplicates)
        self.export_results_btn.clicked.connect(self.export_results)
        
    @pyqtSlot()
    def browse_input_directory(self):
        """Browse for input directory"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Directory for Deduplication",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.input_path_display.setText(directory)
            
    @pyqtSlot()
    def start_deduplication(self):
        """Start the deduplication process"""
        input_path = self.input_path_display.text()
        
        if input_path == "No directory selected":
            self.show_error("Configuration Error", "Please select a directory to process")
            return
            
        # Automatically generate title cache before deduplication
        corpus_dir = input_path
        output_dir = corpus_dir  # Or set to a specific cache/output directory if needed
        try:
            subprocess.run([sys.executable, 'shared_tools/processors/generate_title_cache.py', corpus_dir, output_dir], check=True)
        except Exception as e:
            self.handle_error('Title Cache Generation Error', str(e))
            return
            
        # Prepare options
        options = {
            'similarity_threshold': self.similarity_slider.value() / 100.0,
            'hash_algorithm': self.hash_combo.currentText(),
            'content_comparison': self.content_comparison_cb.isChecked(),
            'preserve_newest': self.preserve_newest_cb.isChecked(),
            'backup_duplicates': self.backup_duplicates_cb.isChecked(),
            'auto_remove': self.auto_remove_cb.isChecked(),
            'max_file_size': self.max_size_spin.value()
        }
        
        # Create and start worker
        self.worker = DeduplicationWorker(input_path, options)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.duplicate_found.connect(self.add_duplicate_result)
        self.worker.deduplication_completed.connect(self.deduplication_completed)
        self.worker.error_occurred.connect(self.handle_error)
        
        # Update UI state
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_display.clear()
        self.results_table.setRowCount(0)
        self.duplicates_found.clear()
        
        # Switch to processing tab
        self.tab_widget.setCurrentIndex(1)
        
        self.worker.start()
        
    @pyqtSlot()
    def cancel_deduplication(self):
        """Cancel deduplication process"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(3000)
            self.deduplication_finished()
            
    @pyqtSlot(int, str, dict)
    def update_progress(self, percentage: int, message: str, stats: dict):
        """Update progress display"""
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(message)
        
        # Update statistics
        self.total_files_label.setText(f"Total Files: {stats.get('total_files', 0)}")
        self.processed_files_label.setText(f"Processed: {stats.get('processed_files', 0)}")
        self.duplicates_found_label.setText(f"Duplicates Found: {stats.get('duplicates_found', 0)}")
        
    @pyqtSlot(str, str, float)
    def add_duplicate_result(self, original_file: str, duplicate_file: str, similarity: float):
        """Add duplicate result to table"""
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        # Get file sizes
        try:
            original_size = os.path.getsize(original_file)
            duplicate_size = os.path.getsize(duplicate_file)
            size_text = f"{duplicate_size:,} bytes"
        except:
            size_text = "Unknown"
            
        self.results_table.setItem(row, 0, QTableWidgetItem(os.path.basename(original_file)))
        self.results_table.setItem(row, 1, QTableWidgetItem(os.path.basename(duplicate_file)))
        self.results_table.setItem(row, 2, QTableWidgetItem(f"{similarity:.2%}"))
        self.results_table.setItem(row, 3, QTableWidgetItem(size_text))
        
        # Store full paths
        self.duplicates_found.append((original_file, duplicate_file, similarity))
        
        # Update log
        self.status_display.append(f"Duplicate found: {os.path.basename(duplicate_file)} (similarity: {similarity:.2%})")
        
    @pyqtSlot(dict)
    def deduplication_completed(self, stats: dict):
        """Handle deduplication completion"""
        self.deduplication_finished()
        
        # Update final statistics
        self.duplicates_removed_label.setText(f"Duplicates Removed: {stats.get('duplicates_removed', 0)}")
        space_saved_mb = stats.get('space_saved', 0) / (1024 * 1024)
        self.space_saved_label.setText(f"Space Saved: {space_saved_mb:.1f} MB")
        self.processing_time_label.setText(f"Processing Time: {stats.get('processing_time', 0):.1f}s")
        
        # Show completion summary
        summary = f"Deduplication completed:\n"
        summary += f"Files processed: {stats.get('processed_files', 0)}\n"
        summary += f"Duplicates found: {stats.get('duplicates_found', 0)}\n"
        summary += f"Duplicates removed: {stats.get('duplicates_removed', 0)}\n"
        summary += f"Space saved: {space_saved_mb:.1f} MB"
        
        self.progress_label.setText("Deduplication completed")
        self.status_display.append("\n" + "="*50)
        self.status_display.append(summary)
        
        # Enable action buttons
        if self.duplicates_found:
            self.remove_selected_btn.setEnabled(True)
            self.export_results_btn.setEnabled(True)
            
        # Switch to results tab
        self.tab_widget.setCurrentIndex(2)
        
    @pyqtSlot(str, str)
    def handle_error(self, error_type: str, error_message: str):
        """Handle processing errors"""
        self.deduplication_finished()
        self.show_error(error_type, error_message)
        
    def deduplication_finished(self):
        """Reset UI state after completion"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
            
    @pyqtSlot()
    def remove_selected_duplicates(self):
        """Remove selected duplicate files"""
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())
            
        if not selected_rows:
            self.show_error("Selection Error", "Please select duplicates to remove")
            return
            
        # Confirm removal
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove {len(selected_rows)} duplicate files?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            removed_count = 0
            for row in sorted(selected_rows, reverse=True):
                try:
                    if row < len(self.duplicates_found):
                        _, duplicate_file, _ = self.duplicates_found[row]
                        os.remove(duplicate_file)
                        self.results_table.removeRow(row)
                        removed_count += 1
                except Exception as e:
                    continue
                    
            self.show_info("Removal Complete", f"Successfully removed {removed_count} duplicate files")
            
    @pyqtSlot()
    def export_results(self):
        """Export deduplication results"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Deduplication Results",
            "deduplication_results.csv",
            "CSV Files (*.csv);;Text Files (*.txt)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    if filename.endswith('.csv'):
                        f.write("Original File,Duplicate File,Similarity,Action\n")
                        for original, duplicate, similarity in self.duplicates_found:
                            f.write(f'"{original}","{duplicate}",{similarity:.3f},Found\n')
                    else:
                        f.write("DEDUPLICATION RESULTS\n")
                        f.write("="*50 + "\n\n")
                        for i, (original, duplicate, similarity) in enumerate(self.duplicates_found, 1):
                            f.write(f"{i}. Duplicate: {duplicate}\n")
                            f.write(f"   Original: {original}\n")
                            f.write(f"   Similarity: {similarity:.2%}\n\n")
                            
                self.show_info("Export Successful", f"Results exported to {filename}")
                
            except Exception as e:
                self.show_error("Export Error", f"Failed to export results: {str(e)}")
                
    def get_deduplication_results(self) -> List[Tuple[str, str, float]]:
        """Get deduplication results"""
        return self.duplicates_found.copy()
        
    def is_processing(self) -> bool:
        """Check if processing is currently active"""
        return self.worker is not None and self.worker.isRunning()
