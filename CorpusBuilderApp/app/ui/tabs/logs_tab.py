from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QPushButton, QTextEdit, QComboBox,
                             QLineEdit, QCheckBox, QFileDialog, QSplitter,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, QTimer, Slot as pyqtSlot
from PySide6.QtGui import QColor, QTextCharFormat, QBrush

import os
import re
from datetime import datetime


class LogsTab(QWidget):
    def __init__(self, project_config, parent=None):
        super().__init__(parent)
        self.project_config = project_config
        self.log_files = {}
        self.current_log = None
        self.update_timer = None
        self.setup_ui()
        self.scan_log_directory()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Log navigation and filtering controls
        controls_layout = QHBoxLayout()
        
        # Log selector
        controls_layout.addWidget(QLabel("Log:"))
        self.log_selector = QComboBox()
        self.log_selector.setMinimumWidth(250)
        self.log_selector.currentIndexChanged.connect(self.on_log_selected)
        controls_layout.addWidget(self.log_selector)
        
        # Filter
        controls_layout.addWidget(QLabel("Filter:"))
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter logs (regex supported)")
        self.filter_input.textChanged.connect(self.apply_filters)
        controls_layout.addWidget(self.filter_input)
        
        # Level filter
        controls_layout.addWidget(QLabel("Level:"))
        self.level_filter = QComboBox()
        self.level_filter.addItems(["All", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_filter.currentIndexChanged.connect(self.apply_filters)
        controls_layout.addWidget(self.level_filter)
        
        # Date range (simplified for now)
        self.today_only = QCheckBox("Today Only")
        self.today_only.stateChanged.connect(self.apply_filters)
        controls_layout.addWidget(self.today_only)
        
        main_layout.addLayout(controls_layout)
        
        # Create a splitter for log table and details
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Log entries table
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(5)
        self.log_table.setHorizontalHeaderLabels(["Time", "Level", "Component", "Message", "Details"])
        
        # Configure table properties
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.log_table.clicked.connect(self.on_log_entry_selected)
        
        splitter.addWidget(self.log_table)
        
        # Log detail view
        self.log_detail = QTextEdit()
        self.log_detail.setReadOnly(True)
        splitter.addWidget(self.log_detail)
        
        # Set initial splitter sizes (70% table, 30% details)
        splitter.setSizes([700, 300])
        
        main_layout.addWidget(splitter, 1)
        
        # Controls at the bottom
        bottom_layout = QHBoxLayout()
        
        self.auto_refresh = QCheckBox("Auto-refresh")
        self.auto_refresh.setChecked(True)
        self.auto_refresh.stateChanged.connect(self.toggle_auto_refresh)
        bottom_layout.addWidget(self.auto_refresh)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_logs)
        bottom_layout.addWidget(self.refresh_btn)
        
        self.clear_filter_btn = QPushButton("Clear Filter")
        self.clear_filter_btn.clicked.connect(self.clear_filters)
        bottom_layout.addWidget(self.clear_filter_btn)
        
        self.export_btn = QPushButton("Export Logs")
        self.export_btn.clicked.connect(self.export_logs)
        bottom_layout.addWidget(self.export_btn)
        
        self.clear_logs_btn = QPushButton("Clear Log View")
        self.clear_logs_btn.clicked.connect(self.clear_log_view)
        bottom_layout.addWidget(self.clear_logs_btn)
        
        main_layout.addLayout(bottom_layout)
        
        # Set up auto-refresh timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.refresh_logs)
        self.update_timer.start(5000)  # Refresh every 5 seconds
    
    def scan_log_directory(self):
        """Scan for log files in the configured log directory"""
        # In a real implementation, this would use project_config to get the log directory
        # For now, use a placeholder path
        try:
            log_dir = self.project_config.get_logs_dir()
        except:
            log_dir = os.path.expanduser("~/.cryptofinance/logs")
        
        # Placeholder - in a real implementation this would scan the actual directory
        # For demonstration, populate with sample log files
        self.log_files = {
            "collectors.log": {"path": f"{log_dir}/collectors.log", "type": "collector"},
            "processors.log": {"path": f"{log_dir}/processors.log", "type": "processor"},
            "app.log": {"path": f"{log_dir}/app.log", "type": "app"},
            "errors.log": {"path": f"{log_dir}/errors.log", "type": "error"}
        }
        
        # Update the log selector
        self.log_selector.clear()
        for log_name in self.log_files:
            self.log_selector.addItem(log_name)
        
        # Load the first log if available
        if self.log_selector.count() > 0:
            self.on_log_selected(0)
    
    def on_log_selected(self, index):
        """Handle log file selection"""
        if index >= 0:
            log_name = self.log_selector.currentText()
            self.current_log = self.log_files.get(log_name)
            self.refresh_logs()
    
    def refresh_logs(self):
        """Refresh the current log view"""
        if not self.current_log:
            print("DEBUG: No current log set, skipping refresh")
            return
            
        # Generate sample logs (ensure it returns a list, not None)
        log_entries = self.generate_sample_logs(self.current_log.get("type", "app"))
        
        # Defensive check
        if log_entries is None:
            print("DEBUG: generate_sample_logs returned None, using empty list")
            log_entries = []
        
        # Apply filters
        filtered_entries = self.filter_log_entries(log_entries)
        
        # Update the table
        self.populate_log_table(filtered_entries)
    
    def generate_sample_logs(self, log_type):
        """Generate sample log entries for demonstration"""
        entries = []
        
        # Current time as base
        now = datetime.now()
        
        # Different log patterns based on log type
        if log_type == "collector":
            components = ["ISDACollector", "GitHubCollector", "AnnaArchiveCollector", "ArxivCollector"]
            messages = [
                "Started collection process",
                "Connecting to API",
                "Retrieved document list",
                "Downloaded document",
                "Collection completed",
                "Error connecting to API",
                "Rate limit exceeded",
                "Authentication failed"
            ]
            
            # Generate 20 sample entries
            for i in range(20):
                # Randomize time within the last day
                time_offset = i * 30  # 30 minutes between entries
                entry_time = now.replace(
                    hour=(now.hour - (time_offset // 60)) % 24,
                    minute=(now.minute - (time_offset % 60)) % 60
                )
                
                # Randomly select component and message
                component = components[i % len(components)]
                message_index = i % len(messages)
                message = messages[message_index]
                
                # Determine level based on message
                if "Error" in message or "failed" in message:
                    level = "ERROR"
                elif "exceeded" in message:
                    level = "WARNING"
                elif "Started" in message:
                    level = "INFO"
                else:
                    level = "DEBUG"
                
                # Create details
                if level == "ERROR":
                    details = f"Exception occurred: ConnectionError\nTraceback: File \"collector.py\", line 120\nCannot connect to server"
                else:
                    details = f"Additional information for {message.lower()}"
                
                entries.append({
                    "time": entry_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "level": level,
                    "component": component,
                    "message": message,
                    "details": details
                })
        
        elif log_type == "processor":
            components = ["PDFProcessor", "TextProcessor", "BalancerProcessor", "QualityControl"]
            messages = [
                "Processing file",
                "Extraction complete",
                "Failed to extract text",
                "OCR fallback used",
                "Detected language",
                "Quality score calculated",
                "File categorized",
                "Error processing file"
            ]
            
            # Generate 20 sample entries
            for i in range(20):
                # Randomize time within the last day
                time_offset = i * 15  # 15 minutes between entries
                entry_time = now.replace(
                    hour=(now.hour - (time_offset // 60)) % 24,
                    minute=(now.minute - (time_offset % 60)) % 60
                )
                
                # Randomly select component and message
                component = components[i % len(components)]
                message_index = i % len(messages)
                message = messages[message_index]
                
                # Add a file name to the message
                file_name = f"document_{i+1}.{'pdf' if component == 'PDFProcessor' else 'txt'}"
                full_message = f"{message}: {file_name}"
                
                # Determine level based on message
                if "Error" in message or "Failed" in message:
                    level = "ERROR"
                elif "fallback" in message:
                    level = "WARNING"
                elif "Processing" in message:
                    level = "INFO"
                else:
                    level = "DEBUG"
                
                # Create details
                if level == "ERROR":
                    details = f"Exception occurred: ProcessingError\nTraceback: File \"{component.lower()}.py\", line 87\nCannot process file {file_name}"
                elif "language" in message.lower():
                    details = f"Detected language: English\nConfidence: 95%\nAlternatives: None"
                elif "score" in message.lower():
                    details = f"Quality score: 87/100\nFactors:\n- Text quality: 90/100\n- Structure: 85/100\n- Content relevance: 88/100"
                else:
                    details = f"File: {file_name}\nSize: 1.2MB\nPages: 8"
                
                entries.append({
                    "time": entry_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "level": level,
                    "component": component,
                    "message": full_message,
                    "details": details
                })
        
        elif log_type == "app":
            components = ["MainWindow", "CollectorsTab", "ProcessorsTab", "CorpusManager"]
            messages = [
                "Application started",
                "Configuration loaded",
                "Tab initialized",
                "User action: start collection",
                "User action: stop processing",
                "Dialog opened",
                "Settings saved",
                "Application shutdown initiated"
            ]
            
            # Generate 15 sample entries
            for i in range(15):
                # Randomize time within the last day
                time_offset = i * 45  # 45 minutes between entries
                entry_time = now.replace(
                    hour=(now.hour - (time_offset // 60)) % 24,
                    minute=(now.minute - (time_offset % 60)) % 60
                )
                
                # Randomly select component and message
                component = components[i % len(components)]
                message_index = i % len(messages)
                message = messages[message_index]
                
                # Determine level
                level = "INFO"  # Most app logs are INFO level
                
                # Create details
                if "started" in message.lower():
                    details = f"App version: 3.0.1\nPython version: 3.8.10\nPyQt version: 6.6.0"
                elif "configuration" in message.lower():
                    details = f"Config file: config/test.yaml\nEnvironment: test"
                elif "user action" in message.lower():
                    details = f"User: admin\nAction time: {entry_time.strftime('%H:%M:%S')}"
                else:
                    details = ""
                
                entries.append({
                    "time": entry_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "level": level,
                    "component": component,
                    "message": message,
                    "details": details
                })
        
        elif log_type == "error":
            pass  # No sample error log entries defined

    def apply_filters(self):
        """Apply all current filters to the log entries."""
        if not self.current_log:
            return
        # Get current filter values
        level_filter = self.level_filter.currentText()
        # component_filter is not present in your UI, so skip it
        text_filter = self.filter_input.text()
        # Generate new sample data (in real implementation, this would filter existing data)
        log_entries = self.generate_sample_logs(self.current_log["type"])
        # Apply filters
        filtered_entries = self.filter_log_entries(log_entries)
        self.filtered_entries = filtered_entries  # <-- Ensure this is set for export
        # Update the table
        self.populate_log_table(filtered_entries)

    def filter_log_entries(self, entries):
        """Apply filters to the log entries."""
        # Defensive check for None entries
        if entries is None:
            print("DEBUG: filter_log_entries received None, returning empty list")
            return []
        
        if not isinstance(entries, list):
            print(f"DEBUG: filter_log_entries received {type(entries)}, converting to list")
            entries = list(entries) if entries else []
        
        level_filter = self.level_filter.currentText()
        text_filter = self.filter_input.text().lower()
        
        filtered = []
        for entry in entries:
            # Level filter
            if level_filter != "All" and entry.get("level") != level_filter:
                continue
            # Text filter
            if text_filter and text_filter not in entry.get("message", "").lower():
                continue
            filtered.append(entry)
        
        return filtered

    def populate_log_table(self, entries):
        """Populate the log table with entries."""
        self.log_table.setRowCount(len(entries))
        for i, entry in enumerate(entries):
            # Time
            time_item = QTableWidgetItem(entry.get("time", ""))
            self.log_table.setItem(i, 0, time_item)
            # Level
            level_item = QTableWidgetItem(entry.get("level", ""))
            if entry.get("level") == "ERROR":
                level_item.setForeground(QColor("red"))
            elif entry.get("level") == "WARNING":
                level_item.setForeground(QColor("orange"))
            self.log_table.setItem(i, 1, level_item)
            # Component
            component_item = QTableWidgetItem(entry.get("component", ""))
            self.log_table.setItem(i, 2, component_item)
            # Message
            message_item = QTableWidgetItem(entry.get("message", ""))
            self.log_table.setItem(i, 3, message_item)
            # Details
            details_item = QTableWidgetItem(entry.get("details", ""))
            self.log_table.setItem(i, 4, details_item)

    def on_log_entry_selected(self, index):
        """Handle log entry selection in the table."""
        if not index.isValid():
            return
        row = index.row()
        if row >= self.log_table.rowCount():
            return
        # Get the log entry data from the selected row
        time_item = self.log_table.item(row, 0)
        level_item = self.log_table.item(row, 1)
        component_item = self.log_table.item(row, 2)
        message_item = self.log_table.item(row, 3)
        details_item = self.log_table.item(row, 4)
        if not all([time_item, level_item, component_item, message_item]):
            return
        # Create a detailed view of the selected entry
        details_text = f"""Log Entry Details\n═══════════════════\n\nTime: {time_item.text()}\nLevel: {level_item.text()}\nComponent: {component_item.text()}\nMessage: {message_item.text()}\n\nDetails:\n{details_item.text() if details_item else 'No additional details'}\n\n═══════════════════"""
        # Display in the detail view
        self.log_detail.setPlainText(details_text)

    def clear_filters(self):
        """Clear all filters and show all log entries."""
        # Reset filter controls
        self.level_filter.setCurrentText("All")
        # If you have a component_filter, reset it too
        if hasattr(self, 'component_filter'):
            self.component_filter.setCurrentText("All")
        self.filter_input.clear()
        # Clear the today only checkbox if you have one
        if hasattr(self, 'today_only'):
            self.today_only.setChecked(False)
        # Refresh the display
        self.apply_filters()

    def toggle_auto_refresh(self, enabled):
        """Toggle auto-refresh on/off"""
        if enabled:
            if self.update_timer:
                self.update_timer.start(5000)  # Refresh every 5 seconds
            print("DEBUG: Auto-refresh enabled")
        else:
            if self.update_timer:
                self.update_timer.stop()
            print("DEBUG: Auto-refresh disabled")

    def clear_log_view(self):
        """Clear the current log view"""
        self.log_table.setRowCount(0)
        self.log_detail.clear()

    def export_logs(self):
        """Export filtered log entries to a file"""
        if not hasattr(self, 'filtered_entries') or not self.filtered_entries:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "No Data", "No log entries to export.")
            return

        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Logs", "",
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    if file_path.endswith('.csv'):
                        import csv
                        writer = csv.writer(f)
                        writer.writerow(["Time", "Level", "Component", "Message", "Details"])
                        for entry in self.filtered_entries:
                            writer.writerow([
                                entry.get("time", ""),
                                entry.get("level", ""),
                                entry.get("component", ""),
                                entry.get("message", ""),
                                entry.get("details", "")
                            ])
                    else:
                        for entry in self.filtered_entries:
                            f.write(f"[{entry.get('time','')}] {entry.get('level','')} [{entry.get('component','')}] {entry.get('message','')}\nDetails: {entry.get('details','')}\n\n")
                print(f"DEBUG: Exported {len(self.filtered_entries)} entries to {file_path}")
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Export Error", f"Could not export logs: {str(e)}")
