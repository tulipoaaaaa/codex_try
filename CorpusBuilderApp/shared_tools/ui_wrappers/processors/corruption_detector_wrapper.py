"""
Corruption Detector Wrapper for UI Integration
Provides comprehensive file corruption detection capabilities
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from PySide6.QtCore import QObject, QThread, Signal as pyqtSignal, Slot as pyqtSlot, QMutex
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QProgressBar, QLabel, QTextEdit, QFileDialog, QCheckBox, 
                           QSpinBox, QGroupBox, QGridLayout, QComboBox, QListWidget,
                           QSplitter, QTabWidget, QTableWidget, QTableWidgetItem,
                           QHeaderView)
from shared_tools.ui_wrappers.base_wrapper import BaseWrapper
from shared_tools.processors.corruption_detector import CorruptionDetector
from shared_tools.processors.mixins.processor_wrapper_mixin import ProcessorWrapperMixin


class CorruptionDetectorWorker(QThread):
    """Worker thread for corruption detection operations"""
    
    progress_updated = pyqtSignal(int, str)  # progress percentage, current file
    file_checked = pyqtSignal(str, dict)  # file path, corruption report
    scan_completed = pyqtSignal(dict)  # final statistics
    error_occurred = pyqtSignal(str, str)  # error type, error message
    
    def __init__(self, input_path: str, options: Dict[str, Any]):
        super().__init__()
        self.input_path = input_path
        self.options = options
        self.detector = CorruptionDetector()
        self._is_cancelled = False
        self._mutex = QMutex()
        self.stats = {
            'total_files': 0,
            'checked_files': 0,
            'corrupted_files': 0,
            'suspicious_files': 0,
            'clean_files': 0,
            'error_files': 0
        }
        
    def run(self):
        """Execute corruption detection scan"""
        try:
            # Configure detector
            self.detector.configure(
                check_file_headers=self.options.get('check_file_headers', True),
                verify_checksums=self.options.get('verify_checksums', True),
                deep_scan=self.options.get('deep_scan', False),
                check_encoding=self.options.get('check_encoding', True),
                validate_structure=self.options.get('validate_structure', True),
                max_file_size=self.options.get('max_file_size', 100)
            )
            
            # Get files to scan
            files_to_scan = self._get_files_to_scan()
            self.stats['total_files'] = len(files_to_scan)
            
            if self.stats['total_files'] == 0:
                self.error_occurred.emit("No Files", "No files found to scan")
                return
                
            # Scan each file
            for i, file_path in enumerate(files_to_scan):
                if self._is_cancelled:
                    break
                    
                # Update progress
                progress = int((i / self.stats['total_files']) * 100)
                filename = os.path.basename(file_path)
                self.progress_updated.emit(progress, f"Scanning: {filename}")
                
                try:
                    # Check file for corruption
                    report = self.detector.check_file(file_path)
                    self.file_checked.emit(file_path, report)
                    
                    # Update statistics
                    if report['status'] == 'corrupted':
                        self.stats['corrupted_files'] += 1
                    elif report['status'] == 'suspicious':
                        self.stats['suspicious_files'] += 1
                    elif report['status'] == 'clean':
                        self.stats['clean_files'] += 1
                    else:
                        self.stats['error_files'] += 1
                        
                    self.stats['checked_files'] += 1
                    
                except Exception as e:
                    self.stats['error_files'] += 1
                    self.stats['checked_files'] += 1
                    error_report = {
                        'status': 'error',
                        'error': str(e),
                        'checks': {},
                        'confidence': 0.0
                    }
                    self.file_checked.emit(file_path, error_report)
                    
            # Final progress update
            self.progress_updated.emit(100, "Corruption scan completed")
            self.scan_completed.emit(self.stats)
            
        except Exception as e:
            self.error_occurred.emit("Scan Error", str(e))
            
    def cancel(self):
        """Cancel the current scan"""
        self._mutex.lock()
        self._is_cancelled = True
        self._mutex.unlock()
        
    def _get_files_to_scan(self) -> List[str]:
        """Get list of files to scan for corruption"""
        files = []
        
        if os.path.isfile(self.input_path):
            files.append(self.input_path)
        else:
            for root, dirs, filenames in os.walk(self.input_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    # Skip hidden files and very large files if configured
                    if not filename.startswith('.'):
                        try:
                            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                            if file_size <= self.options.get('max_file_size', 100):
                                files.append(file_path)
                        except OSError:
                            pass  # Skip files we can't access
                            
        return files


class CorruptionDetectorWrapper(BaseWrapper, ProcessorWrapperMixin):
    """UI Wrapper for Corruption Detector"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.scan_results = []
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
        
        # Scanning Tab
        scanning_tab = self._create_scanning_tab()
        self.tab_widget.addTab(scanning_tab, "Scanning")
        
        # Results Tab
        results_tab = self._create_results_tab()
        self.tab_widget.addTab(results_tab, "Results")
        
        layout.addWidget(self.tab_widget)
        
    def _create_configuration_tab(self) -> QWidget:
        """Create the configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Input Selection
        input_group = QGroupBox("Scan Target")
        input_layout = QGridLayout(input_group)
        
        self.input_label = QLabel("Directory/File to Scan:")
        self.input_path_display = QLabel("No path selected")
        self.input_browse_btn = QPushButton("Browse...")
        
        input_layout.addWidget(self.input_label, 0, 0)
        input_layout.addWidget(self.input_path_display, 0, 1)
        input_layout.addWidget(self.input_browse_btn, 0, 2)
        
        # Detection Options
        detection_group = QGroupBox("Detection Options")
        detection_layout = QGridLayout(detection_group)
        
        self.check_headers_cb = QCheckBox("Check File Headers")
        self.check_headers_cb.setChecked(True)
        self.check_headers_cb.setToolTip("Verify file headers match expected format")
        
        self.verify_checksums_cb = QCheckBox("Verify Checksums")
        self.verify_checksums_cb.setChecked(True)
        self.verify_checksums_cb.setToolTip("Calculate and verify file checksums")
        
        self.deep_scan_cb = QCheckBox("Deep Scan")
        self.deep_scan_cb.setChecked(False)
        self.deep_scan_cb.setToolTip("Perform thorough content analysis (slower)")
        
        self.check_encoding_cb = QCheckBox("Check Text Encoding")
        self.check_encoding_cb.setChecked(True)
        self.check_encoding_cb.setToolTip("Validate text file encoding")
        
        self.validate_structure_cb = QCheckBox("Validate Structure")
        self.validate_structure_cb.setChecked(True)
        self.validate_structure_cb.setToolTip("Check document structure integrity")
        
        detection_layout.addWidget(self.check_headers_cb, 0, 0)
        detection_layout.addWidget(self.verify_checksums_cb, 0, 1)
        detection_layout.addWidget(self.deep_scan_cb, 1, 0)
        detection_layout.addWidget(self.check_encoding_cb, 1, 1)
        detection_layout.addWidget(self.validate_structure_cb, 2, 0)
        
        # Performance Options
        performance_group = QGroupBox("Performance Options")
        performance_layout = QGridLayout(performance_group)
        
        self.max_file_size_label = QLabel("Max File Size (MB):")
        self.max_file_size_spin = QSpinBox()
        self.max_file_size_spin.setRange(1, 1000)
        self.max_file_size_spin.setValue(100)
        self.max_file_size_spin.setToolTip("Skip files larger than this size")
        
        performance_layout.addWidget(self.max_file_size_label, 0, 0)
        performance_layout.addWidget(self.max_file_size_spin, 0, 1)
        
        layout.addWidget(input_group)
        layout.addWidget(detection_group)
        layout.addWidget(performance_group)
        layout.addStretch()
        
        return tab
        
    def _create_scanning_tab(self) -> QWidget:
        """Create the scanning tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Control Buttons
        control_layout = QHBoxLayout()
        self.start_scan_btn = QPushButton("Start Scan")
        self.cancel_scan_btn = QPushButton("Cancel")
        self.cancel_scan_btn.setEnabled(False)
        
        control_layout.addWidget(self.start_scan_btn)
        control_layout.addWidget(self.cancel_scan_btn)
        control_layout.addStretch()
        
        # Progress Display
        progress_group = QGroupBox("Scan Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("Ready to start scan")
        
        # Statistics Display
        stats_layout = QGridLayout()
        self.total_files_label = QLabel("Total Files: 0")
        self.checked_files_label = QLabel("Checked: 0")
        self.corrupted_files_label = QLabel("Corrupted: 0")
        self.suspicious_files_label = QLabel("Suspicious: 0")
        self.clean_files_label = QLabel("Clean: 0")
        self.error_files_label = QLabel("Errors: 0")
        
        stats_layout.addWidget(self.total_files_label, 0, 0)
        stats_layout.addWidget(self.checked_files_label, 0, 1)
        stats_layout.addWidget(self.corrupted_files_label, 1, 0)
        stats_layout.addWidget(self.suspicious_files_label, 1, 1)
        stats_layout.addWidget(self.clean_files_label, 2, 0)
        stats_layout.addWidget(self.error_files_label, 2, 1)
        
        # Scan Log
        self.scan_log = QTextEdit()
        self.scan_log.setMaximumHeight(200)
        self.scan_log.setReadOnly(True)
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addLayout(stats_layout)
        progress_layout.addWidget(QLabel("Scan Log:"))
        progress_layout.addWidget(self.scan_log)
        
        layout.addLayout(control_layout)
        layout.addWidget(progress_group)
        
        return tab
        
    def _create_results_tab(self) -> QWidget:
        """Create the results tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create splitter for results
        splitter = QSplitter()
        
        # Results Table
        table_group = QGroupBox("Scan Results")
        table_layout = QVBoxLayout(table_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["File", "Status", "Confidence", "Issues"])
        
        # Configure table
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        table_layout.addWidget(self.results_table)
        
        # Detail Display
        detail_group = QGroupBox("File Details")
        detail_layout = QVBoxLayout(detail_group)
        self.detail_display = QTextEdit()
        self.detail_display.setReadOnly(True)
        detail_layout.addWidget(self.detail_display)
        
        splitter.addWidget(table_group)
        splitter.addWidget(detail_group)
        splitter.setSizes([500, 300])
        
        # Export and Filter Controls
        controls_layout = QHBoxLayout()
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Files", "Corrupted Only", "Suspicious Only", "Clean Only", "Errors Only"])
        
        self.export_results_btn = QPushButton("Export Results")
        self.export_results_btn.setEnabled(False)
        
        self.export_report_btn = QPushButton("Generate Report")
        self.export_report_btn.setEnabled(False)
        
        controls_layout.addWidget(QLabel("Filter:"))
        controls_layout.addWidget(self.filter_combo)
        controls_layout.addStretch()
        controls_layout.addWidget(self.export_results_btn)
        controls_layout.addWidget(self.export_report_btn)
        
        layout.addWidget(splitter)
        layout.addLayout(controls_layout)
        
        return tab
        
    def setup_connections(self):
        """Setup signal-slot connections"""
        self.input_browse_btn.clicked.connect(self.browse_input_path)
        self.start_scan_btn.clicked.connect(self.start_scan)
        self.cancel_scan_btn.clicked.connect(self.cancel_scan)
        self.export_results_btn.clicked.connect(self.export_results)
        self.export_report_btn.clicked.connect(self.generate_report)
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        self.results_table.currentRowChanged.connect(self.show_file_details)
        
    @pyqtSlot()
    def browse_input_path(self):
        """Browse for input path (file or directory)"""
        # Allow selection of both files and directories
        path = QFileDialog.getExistingDirectory(
            self, 
            "Select Directory to Scan",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        # If no directory selected, try file selection
        if not path:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select File to Scan",
                "",
                "All Files (*)"
            )
            
        if path:
            self.input_path_display.setText(path)
            
    @pyqtSlot()
    def start_scan(self):
        """Start the corruption detection scan"""
        input_path = self.input_path_display.text()
        
        if input_path == "No path selected":
            self.show_error("Configuration Error", "Please select a file or directory to scan")
            return
            
        if not os.path.exists(input_path):
            self.show_error("Path Error", "Selected path does not exist")
            return
            
        # Prepare options
        options = {
            'check_file_headers': self.check_headers_cb.isChecked(),
            'verify_checksums': self.verify_checksums_cb.isChecked(),
            'deep_scan': self.deep_scan_cb.isChecked(),
            'check_encoding': self.check_encoding_cb.isChecked(),
            'validate_structure': self.validate_structure_cb.isChecked(),
            'max_file_size': self.max_file_size_spin.value()
        }
        
        # Create and start worker
        self.worker = CorruptionDetectorWorker(input_path, options)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.file_checked.connect(self.file_checked)
        self.worker.scan_completed.connect(self.scan_completed)
        self.worker.error_occurred.connect(self.handle_error)
        
        # Update UI state
        self.start_scan_btn.setEnabled(False)
        self.cancel_scan_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.scan_log.clear()
        self.results_table.setRowCount(0)
        self.detail_display.clear()
        self.scan_results.clear()
        
        # Switch to scanning tab
        self.tab_widget.setCurrentIndex(1)
        
        self.worker.start()
        
    @pyqtSlot()
    def cancel_scan(self):
        """Cancel the current scan"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(3000)
            self.scan_finished()
            
    @pyqtSlot(int, str)
    def update_progress(self, percentage: int, message: str):
        """Update progress display"""
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(message)
        
    @pyqtSlot(str, dict)
    def file_checked(self, file_path: str, report: dict):
        """Handle file check result"""
        filename = os.path.basename(file_path)
        status = report.get('status', 'unknown')
        confidence = report.get('confidence', 0.0)
        
        # Determine status icon
        if status == 'corrupted':
            status_icon = "❌"
        elif status == 'suspicious':
            status_icon = "⚠️"
        elif status == 'clean':
            status_icon = "✅"
        else:
            status_icon = "❓"
            
        # Add to scan log
        self.scan_log.append(f"{status_icon} {filename}: {status} (confidence: {confidence:.2f})")
        
        # Store result
        self.scan_results.append((file_path, report))
        
        # Add to results table
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        self.results_table.setItem(row, 0, QTableWidgetItem(filename))
        self.results_table.setItem(row, 1, QTableWidgetItem(f"{status_icon} {status}"))
        self.results_table.setItem(row, 2, QTableWidgetItem(f"{confidence:.2f}"))
        
        # Create issues summary
        issues = []
        checks = report.get('checks', {})
        for check_name, check_result in checks.items():
            if not check_result.get('passed', True):
                issues.append(check_name)
                
        issues_text = ", ".join(issues) if issues else "None"
        self.results_table.setItem(row, 3, QTableWidgetItem(issues_text))
        
        # Update statistics in worker callback
        
    @pyqtSlot(dict)
    def scan_completed(self, stats: dict):
        """Handle scan completion"""
        self.scan_finished()
        
        # Update final statistics
        self.total_files_label.setText(f"Total Files: {stats.get('total_files', 0)}")
        self.checked_files_label.setText(f"Checked: {stats.get('checked_files', 0)}")
        self.corrupted_files_label.setText(f"Corrupted: {stats.get('corrupted_files', 0)}")
        self.suspicious_files_label.setText(f"Suspicious: {stats.get('suspicious_files', 0)}")
        self.clean_files_label.setText(f"Clean: {stats.get('clean_files', 0)}")
        self.error_files_label.setText(f"Errors: {stats.get('error_files', 0)}")
        
        # Show completion summary
        summary = f"Corruption scan completed:\n"
        summary += f"Files scanned: {stats.get('checked_files', 0)}/{stats.get('total_files', 0)}\n"
        summary += f"Corrupted files found: {stats.get('corrupted_files', 0)}\n"
        summary += f"Suspicious files found: {stats.get('suspicious_files', 0)}"
        
        self.progress_label.setText("Scan completed")
        self.scan_log.append("\n" + "="*50)
        self.scan_log.append(summary)
        
        # Enable export buttons
        self.export_results_btn.setEnabled(True)
        self.export_report_btn.setEnabled(True)
        
        # Switch to results tab
        self.tab_widget.setCurrentIndex(2)
        
    @pyqtSlot(str, str)
    def handle_error(self, error_type: str, error_message: str):
        """Handle scan errors"""
        self.scan_finished()
        self.show_error(error_type, error_message)
        
    @pyqtSlot(str)
    def apply_filter(self, filter_text: str):
        """Apply filter to results table"""
        for row in range(self.results_table.rowCount()):
            show_row = True
            
            if filter_text != "All Files":
                status_item = self.results_table.item(row, 1)
                if status_item:
                    status = status_item.text().lower()
                    
                    if filter_text == "Corrupted Only" and "corrupted" not in status:
                        show_row = False
                    elif filter_text == "Suspicious Only" and "suspicious" not in status:
                        show_row = False
                    elif filter_text == "Clean Only" and "clean" not in status:
                        show_row = False
                    elif filter_text == "Errors Only" and "error" not in status:
                        show_row = False
                        
            self.results_table.setRowHidden(row, not show_row)
            
    @pyqtSlot(int)
    def show_file_details(self, row: int):
        """Show detailed information for selected file"""
        if 0 <= row < len(self.scan_results):
            file_path, report = self.scan_results[row]
            filename = os.path.basename(file_path)
            
            detail_text = f"Corruption Report for: {filename}\n"
            detail_text += f"Path: {file_path}\n"
            detail_text += "="*60 + "\n\n"
            
            detail_text += f"Status: {report.get('status', 'unknown')}\n"
            detail_text += f"Confidence: {report.get('confidence', 0.0):.3f}\n\n"
            
            if 'error' in report:
                detail_text += f"Error: {report['error']}\n\n"
                
            checks = report.get('checks', {})
            if checks:
                detail_text += "Detailed Checks:\n"
                detail_text += "-" * 20 + "\n"
                
                for check_name, check_result in checks.items():
                    passed = check_result.get('passed', True)
                    status_icon = "✅" if passed else "❌"
                    detail_text += f"{status_icon} {check_name}: "
                    
                    if 'message' in check_result:
                        detail_text += f"{check_result['message']}\n"
                    else:
                        detail_text += f"{'Passed' if passed else 'Failed'}\n"
                        
                    if 'details' in check_result:
                        detail_text += f"   Details: {check_result['details']}\n"
                        
            self.detail_display.setText(detail_text)
            
    @pyqtSlot()
    def export_results(self):
        """Export scan results to JSON"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Scan Results",
            "corruption_scan_results.json",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                export_data = {
                    'scan_results': self.scan_results,
                    'timestamp': time.time(),
                    'scan_options': {
                        'check_file_headers': self.check_headers_cb.isChecked(),
                        'verify_checksums': self.verify_checksums_cb.isChecked(),
                        'deep_scan': self.deep_scan_cb.isChecked(),
                        'check_encoding': self.check_encoding_cb.isChecked(),
                        'validate_structure': self.validate_structure_cb.isChecked(),
                        'max_file_size': self.max_file_size_spin.value()
                    }
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                    
                self.show_info("Export Successful", f"Results exported to {filename}")
                
            except Exception as e:
                self.show_error("Export Error", f"Failed to export results: {str(e)}")
                
    @pyqtSlot()
    def generate_report(self):
        """Generate a human-readable corruption report"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Corruption Report",
            "corruption_report.txt",
            "Text Files (*.txt)"
        )
        
        if filename:
            try:
                report = self._generate_text_report()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                    
                self.show_info("Report Generated", f"Report saved to {filename}")
                
            except Exception as e:
                self.show_error("Report Error", f"Failed to generate report: {str(e)}")
                
    def _generate_text_report(self) -> str:
        """Generate a formatted text report"""
        import time
        
        report = "FILE CORRUPTION SCAN REPORT\n"
        report += "="*50 + "\n\n"
        report += f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Scan Target: {self.input_path_display.text()}\n\n"
        
        # Statistics summary
        total = self.total_files_label.text().split(': ')[1]
        checked = self.checked_files_label.text().split(': ')[1]
        corrupted = self.corrupted_files_label.text().split(': ')[1]
        suspicious = self.suspicious_files_label.text().split(': ')[1]
        clean = self.clean_files_label.text().split(': ')[1]
        errors = self.error_files_label.text().split(': ')[1]
        
        report += "SUMMARY STATISTICS\n"
        report += "-" * 20 + "\n"
        report += f"Total files found: {total}\n"
        report += f"Files checked: {checked}\n"
        report += f"Corrupted files: {corrupted}\n"
        report += f"Suspicious files: {suspicious}\n"
        report += f"Clean files: {clean}\n"
        report += f"Files with errors: {errors}\n\n"
        
        # Detailed results
        if int(corrupted) > 0:
            report += "CORRUPTED FILES\n"
            report += "-" * 15 + "\n"
            for file_path, file_report in self.scan_results:
                if file_report.get('status') == 'corrupted':
                    report += f"• {os.path.basename(file_path)}\n"
                    report += f"  Path: {file_path}\n"
                    report += f"  Confidence: {file_report.get('confidence', 0.0):.3f}\n"
                    
                    checks = file_report.get('checks', {})
                    failed_checks = [name for name, result in checks.items() 
                                   if not result.get('passed', True)]
                    if failed_checks:
                        report += f"  Failed checks: {', '.join(failed_checks)}\n"
                    report += "\n"
                    
        if int(suspicious) > 0:
            report += "SUSPICIOUS FILES\n"
            report += "-" * 16 + "\n"
            for file_path, file_report in self.scan_results:
                if file_report.get('status') == 'suspicious':
                    report += f"• {os.path.basename(file_path)}\n"
                    report += f"  Path: {file_path}\n"
                    report += f"  Confidence: {file_report.get('confidence', 0.0):.3f}\n\n"
                    
        return report
        
    def scan_finished(self):
        """Reset UI state after scan completion"""
        self.start_scan_btn.setEnabled(True)
        self.cancel_scan_btn.setEnabled(False)
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
            
    def get_scan_results(self) -> List[Tuple[str, dict]]:
        """Get scan results"""
        return self.scan_results.copy()
        
    def is_scanning(self) -> bool:
        """Check if scan is currently active"""
        return self.worker is not None and self.worker.isRunning()
