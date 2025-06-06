# File: app/ui/widgets/log_viewer.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QPushButton, QLineEdit, QComboBox, QLabel, QCheckBox,
                             QSplitter, QListWidget, QListWidgetItem, QFileDialog,
                             QMessageBox, QGroupBox)
from PySide6.QtCore import Qt, Signal as pyqtSignal, QTimer, QThread, Slot as pyqtSlot
from PySide6.QtGui import QTextCharFormat, QColor, QFont, QTextCursor
import re
import os
from datetime import datetime
from typing import List, Dict, Optional

class LogEntry:
    """Represents a single log entry."""
    
    def __init__(self, timestamp: str, level: str, component: str, message: str, full_line: str):
        self.timestamp = timestamp
        self.level = level
        self.component = component
        self.message = message
        self.full_line = full_line
        
    def matches_filter(self, level_filter: str, text_filter: str, component_filter: str) -> bool:
        """Check if this entry matches the given filters."""
        # Level filter
        if level_filter != "All" and self.level != level_filter:
            return False
            
        # Component filter
        if component_filter != "All" and self.component != component_filter:
            return False
            
        # Text filter (case insensitive)
        if text_filter and text_filter.lower() not in self.message.lower():
            return False
            
        return True

class LogFileWatcher(QThread):
    """Thread for watching log files for changes."""
    
    new_entries = pyqtSignal(list)  # List of LogEntry objects
    
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.last_position = 0
        self.running = True
        
    def run(self):
        """Monitor the log file for changes."""
        while self.running:
            try:
                if os.path.exists(self.file_path):
                    file_size = os.path.getsize(self.file_path)
                    
                    if file_size > self.last_position:
                        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            f.seek(self.last_position)
                            new_lines = f.readlines()
                            self.last_position = f.tell()
                            
                        if new_lines:
                            entries = self.parse_log_lines(new_lines)
                            if entries:
                                self.new_entries.emit(entries)
                                
                self.msleep(1000)  # Check every second
            except Exception as e:
                print(f"Error watching log file: {e}")
                self.msleep(5000)  # Wait longer on error
                
    def parse_log_lines(self, lines: List[str]) -> List[LogEntry]:
        """Parse log lines into LogEntry objects."""
        entries = []
        
        # Common log patterns
        patterns = [
            # Pattern: [2023-12-01 10:30:45] INFO [ComponentName] Message
            r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+(\w+)\s+\[([^\]]+)\]\s+(.*)',
            # Pattern: 2023-12-01 10:30:45 - INFO - ComponentName - Message
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+-\s+(\w+)\s+-\s+([^\s]+)\s+-\s+(.*)',
            # Pattern: INFO:ComponentName:Message
            r'(\w+):([^:]+):(.*)',
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            entry = None
            
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()
                    if len(groups) == 4:
                        timestamp, level, component, message = groups
                        entry = LogEntry(timestamp, level, component, message, line)
                    elif len(groups) == 3:
                        # For pattern 3, add current timestamp
                        level, component, message = groups
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        entry = LogEntry(timestamp, level, component, message, line)
                    break
                    
            if not entry:
                # Fallback for unmatched lines
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                entry = LogEntry(timestamp, "INFO", "Unknown", line, line)
                
            entries.append(entry)
            
        return entries
        
    def stop(self):
        """Stop watching the file."""
        self.running = False

class LogViewer(QWidget):
    """Advanced log viewer widget with filtering and search capabilities."""
    
    entry_selected = pyqtSignal(LogEntry)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_entries: List[LogEntry] = []
        self.filtered_entries: List[LogEntry] = []
        self.current_file = None
        self.file_watcher = None
        self.auto_scroll = True
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)
        
        # Control panel
        controls_group = QGroupBox("Log Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Log File:"))
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        file_layout.addWidget(self.file_path_edit)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_log_file)
        file_layout.addWidget(self.browse_btn)
        
        self.watch_btn = QPushButton("Start Watching")
        self.watch_btn.clicked.connect(self.toggle_watching)
        file_layout.addWidget(self.watch_btn)
        
        controls_layout.addLayout(file_layout)
        
        # Filters
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Level:"))
        self.level_filter = QComboBox()
        self.level_filter.addItems(["All", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.level_filter)
        
        filter_layout.addWidget(QLabel("Component:"))
        self.component_filter = QComboBox()
        self.component_filter.addItem("All")
        self.component_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.component_filter)
        
        filter_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in messages...")
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_input)
        
        self.auto_scroll_cb = QCheckBox("Auto-scroll")
        self.auto_scroll_cb.setChecked(True)
        self.auto_scroll_cb.toggled.connect(self.set_auto_scroll)
        filter_layout.addWidget(self.auto_scroll_cb)
        
        controls_layout.addLayout(filter_layout)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_logs)
        action_layout.addWidget(self.clear_btn)
        
        self.export_btn = QPushButton("Export...")
        self.export_btn.clicked.connect(self.export_logs)
        action_layout.addWidget(self.export_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_logs)
        action_layout.addWidget(self.refresh_btn)
        
        action_layout.addStretch()
        
        controls_layout.addLayout(action_layout)
        
        main_layout.addWidget(controls_group)
        
        # Log display area
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Log entries list
        self.log_list = QListWidget()
        self.log_list.itemClicked.connect(self.on_entry_selected)
        splitter.addWidget(self.log_list)
        
        # Log detail view
        detail_group = QGroupBox("Entry Details")
        detail_layout = QVBoxLayout(detail_group)
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setFont(QFont("Consolas", 10))
        detail_layout.addWidget(self.detail_text)
        
        splitter.addWidget(detail_group)
        
        # Set initial splitter sizes (70% list, 30% details)
        splitter.setSizes([700, 300])
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_label = QLabel("No log file loaded")
        self.status_label.setObjectName("status-info")
        main_layout.addWidget(self.status_label)
        
    def browse_log_file(self):
        """Browse for a log file to open."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Log File", "", 
            "Log Files (*.log *.txt);;All Files (*)"
        )
        
        if file_path:
            self.load_log_file(file_path)
            
    def load_log_file(self, file_path: str):
        """Load a log file."""
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Not Found", f"The file '{file_path}' does not exist.")
            return
            
        self.current_file = file_path
        self.file_path_edit.setText(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            # Parse all lines
            if self.file_watcher:
                entries = self.file_watcher.parse_log_lines(lines)
            else:
                # Create temporary watcher for parsing
                temp_watcher = LogFileWatcher(file_path)
                entries = temp_watcher.parse_log_lines(lines)
                
            self.log_entries = entries
            self.update_component_filter()
            self.apply_filters()
            
            self.status_label.setText(f"Loaded {len(entries)} log entries from {os.path.basename(file_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load log file: {str(e)}")
            
    def toggle_watching(self):
        """Toggle file watching on/off."""
        if self.file_watcher and self.file_watcher.isRunning():
            # Stop watching
            self.file_watcher.stop()
            self.file_watcher.wait()
            self.file_watcher = None
            self.watch_btn.setText("Start Watching")
            self.status_label.setText("Stopped watching file")
        else:
            # Start watching
            if self.current_file:
                self.file_watcher = LogFileWatcher(self.current_file)
                self.file_watcher.new_entries.connect(self.add_new_entries)
                self.file_watcher.start()
                self.watch_btn.setText("Stop Watching")
                self.status_label.setText("Watching file for changes...")
            else:
                QMessageBox.warning(self, "No File", "Please select a log file first.")
                
    @pyqtSlot(list)
    def add_new_entries(self, entries: List[LogEntry]):
        """Add new log entries from file watcher."""
        self.log_entries.extend(entries)
        self.update_component_filter()
        self.apply_filters()
        
        if self.auto_scroll:
            self.log_list.scrollToBottom()
            
    def update_component_filter(self):
        """Update the component filter dropdown with unique components."""
        components = set()
        for entry in self.log_entries:
            components.add(entry.component)
            
        current_selection = self.component_filter.currentText()
        self.component_filter.clear()
        self.component_filter.addItem("All")
        
        for component in sorted(components):
            self.component_filter.addItem(component)
            
        # Restore selection if it still exists
        index = self.component_filter.findText(current_selection)
        if index >= 0:
            self.component_filter.setCurrentIndex(index)
            
    def apply_filters(self):
        """Apply current filters to the log entries."""
        level_filter = self.level_filter.currentText()
        component_filter = self.component_filter.currentText()
        text_filter = self.search_input.text()
        
        self.filtered_entries = [
            entry for entry in self.log_entries
            if entry.matches_filter(level_filter, text_filter, component_filter)
        ]
        
        self.update_log_display()
        
    def update_log_display(self):
        """Update the log list display."""
        self.log_list.clear()
        
        for entry in self.filtered_entries:
            item = QListWidgetItem()
            
            # Format the display text
            display_text = f"[{entry.timestamp}] {entry.level} [{entry.component}] {entry.message}"
            item.setText(display_text)
            item.setData(Qt.ItemDataRole.UserRole, entry)
            
            # Color code by level
            if entry.level == "ERROR":
                item.setForeground(QColor("red"))
            elif entry.level == "WARNING":
                item.setForeground(QColor("orange"))
            elif entry.level == "DEBUG":
                item.setForeground(QColor("#6b7280"))
            elif entry.level == "CRITICAL":
                item.setForeground(QColor("darkred"))
                
            self.log_list.addItem(item)
            
        self.status_label.setText(
            f"Showing {len(self.filtered_entries)} of {len(self.log_entries)} entries"
        )
        
    def on_entry_selected(self, item: QListWidgetItem):
        """Handle log entry selection."""
        entry = item.data(Qt.ItemDataRole.UserRole)
        if entry:
            # Display detailed information
            detail_text = f"""Timestamp: {entry.timestamp}
Level: {entry.level}
Component: {entry.component}
Message: {entry.message}

Full Line:
{entry.full_line}"""
            
            self.detail_text.setPlainText(detail_text)
            self.entry_selected.emit(entry)
            
    def set_auto_scroll(self, enabled: bool):
        """Set auto-scroll behavior."""
        self.auto_scroll = enabled
        
    def clear_logs(self):
        """Clear all log entries."""
        reply = QMessageBox.question(
            self, "Clear Logs",
            "Are you sure you want to clear all log entries?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.log_entries.clear()
            self.filtered_entries.clear()
            self.log_list.clear()
            self.detail_text.clear()
            self.status_label.setText("Log entries cleared")
            
    def export_logs(self):
        """Export filtered log entries to a file."""
        if not self.filtered_entries:
            QMessageBox.information(self, "No Data", "No log entries to export.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Logs", "", 
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    if file_path.endswith('.csv'):
                        # CSV format
                        f.write("Timestamp,Level,Component,Message\n")
                        for entry in self.filtered_entries:
                            f.write(f'"{entry.timestamp}","{entry.level}","{entry.component}","{entry.message}"\n')
                    else:
                        # Plain text format
                        for entry in self.filtered_entries:
                            f.write(f"[{entry.timestamp}] {entry.level} [{entry.component}] {entry.message}\n")
                            
                QMessageBox.information(self, "Export Complete", f"Exported {len(self.filtered_entries)} entries to {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Could not export logs: {str(e)}")
                
    def refresh_logs(self):
        """Refresh logs from the current file."""
        if self.current_file:
            self.load_log_file(self.current_file)
        else:
            QMessageBox.information(self, "No File", "Please select a log file first.")
            
    def closeEvent(self, event):
        """Handle widget close event."""
        if self.file_watcher and self.file_watcher.isRunning():
            self.file_watcher.stop()
            self.file_watcher.wait()
        event.accept()
