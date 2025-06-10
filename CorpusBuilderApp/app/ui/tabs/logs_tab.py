from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QFileDialog,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PySide6.QtCore import Qt, QTimer, Slot as pyqtSlot
from PySide6.QtGui import QColor, QTextCharFormat, QBrush
import logging
from app.ui.widgets.card_wrapper import CardWrapper
from app.ui.widgets.section_header import SectionHeader
from app.ui.widgets.status_dot import StatusDot
from shared_tools.services.activity_log_service import ActivityLogService
from shared_tools.utils.log_file_parser import LogFileParser
from app.ui.theme.theme_constants import PAGE_MARGIN

import os
import re
from datetime import datetime


class LogsTab(QWidget):
    def __init__(self, project_config, activity_log_service: ActivityLogService | None = None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.project_config = project_config
        self.activity_log_service = activity_log_service
        self.log_parser = LogFileParser()
        self.log_files = {}
        self.current_log = None
        self.update_timer = None
        self.setup_ui()
        self.scan_log_directory()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
        main_layout.setSpacing(PAGE_MARGIN)

        header = SectionHeader("Logs")
        main_layout.addWidget(header)

        # Log navigation and filtering controls
        controls_card = CardWrapper()
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)
        controls_card.body_layout.addLayout(controls_layout)
        
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

        # Module/component filter
        controls_layout.addWidget(QLabel("Module:"))
        self.module_filter = QComboBox()
        self.module_filter.addItem("All")
        self.module_filter.currentIndexChanged.connect(self.apply_filters)
        controls_layout.addWidget(self.module_filter)
        
        # Date range (simplified for now)
        self.today_only = QCheckBox("Today Only")
        self.today_only.stateChanged.connect(self.apply_filters)
        controls_layout.addWidget(self.today_only)
        
        main_layout.addWidget(controls_card)
        
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
        self.log_table.setAlternatingRowColors(True)
        self.log_table.clicked.connect(self.on_log_entry_selected)
        
        table_card = CardWrapper(title="Entries")
        table_card.body_layout.addWidget(self.log_table)
        splitter.addWidget(table_card)
        
        # Log detail view
        self.log_detail = QTextEdit()
        self.log_detail.setReadOnly(True)
        detail_card = CardWrapper(title="Details")
        detail_card.body_layout.addWidget(self.log_detail)
        splitter.addWidget(detail_card)
        
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
        log_dir = self.project_config.get_logs_dir()

        self.log_files = {}
        if os.path.isdir(log_dir):
            for fname in sorted(os.listdir(log_dir)):
                if fname.lower().endswith(".log"):
                    self.log_files[fname] = {"path": os.path.join(log_dir, fname), "type": "app"}
        
        self.log_files = {}

        if os.path.isdir(log_dir):
            for name in sorted(os.listdir(log_dir)):
                if not name.lower().endswith((".log", ".txt")):
                    continue
                path = os.path.join(log_dir, name)
                log_type = "app"
                if name.startswith("collector"):
                    log_type = "collector"
                elif name.startswith("processor"):
                    log_type = "processor"
                elif "error" in name:
                    log_type = "error"
                self.log_files[name] = {"path": path, "type": log_type}

        if self.activity_log_service:
            self.activity_log_service.log("LogsTab", f"Found {len(self.log_files)} log files")

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
            return

        path = self.current_log.get("path")
        log_entries = self.log_parser.parse_file(path)
        self.log_entries = log_entries
        self.update_module_filter(log_entries)

        filtered_entries = self.filter_log_entries(log_entries)
        self.filtered_entries = filtered_entries
        self.populate_log_table(filtered_entries)

        if self.activity_log_service:
            self.activity_log_service.log(
                "LogsTab",
                f"Loaded {len(log_entries)} entries from {os.path.basename(path)}",
            )

    def update_module_filter(self, entries):
        modules = sorted({e.get("component", "") for e in entries if e.get("component")})
        current = self.module_filter.currentText()
        self.module_filter.blockSignals(True)
        self.module_filter.clear()
        self.module_filter.addItem("All")
        for m in modules:
            self.module_filter.addItem(m)
        index = self.module_filter.findText(current)
        if index >= 0:
            self.module_filter.setCurrentIndex(index)
        self.module_filter.blockSignals(False)
    
    def parse_log_line(self, line):
        """Parse a single log line into a dictionary."""
        m = re.match(r"\[(?P<time>[^\]]+)\]\s+(?P<level>\w+)\s+(?P<component>[^\s]+)\s*-\s*(?P<rest>.*)", line)
        if not m:
            return None
        msg = m.group("rest")
        details = ""
        if "|" in msg:
            msg, details = [part.strip() for part in msg.split("|", 1)]
        return {
            "time": m.group("time"),
            "level": m.group("level"),
            "component": m.group("component"),
            "message": msg,
            "details": details,
        }

    def parse_log_file(self, path):
        """Return a list of parsed log entries from the file."""
        entries = []
        if not path or not os.path.exists(path):
            return entries
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                parsed = self.parse_log_line(line)
                if parsed:
                    entries.append(parsed)
        return entries

    def apply_filters(self):
        """Apply all current filters to the log entries."""
        if not hasattr(self, "log_entries"):
            return
          
        # Get current filter values
        level_filter = self.level_filter.currentText()
        # component_filter is not present in your UI, so skip it
        text_filter = self.filter_input.text().lower()
        filtered_entries = [
          entry for entry in self.log_entries
          if (level_filter == "All" or entry.get("level") == level_filter)
          and (not text_filter or text_filter in entry.get("message", "").lower())
        ]
        self.filtered_entries = filtered_entries  # <-- Ensure this is set for export
        # Update the table
        self.populate_log_table(filtered_entries)

    def filter_log_entries(self, entries):
        """Apply filters to the log entries."""
        # Defensive check for None entries
        if entries is None:
            self.logger.info("DEBUG: filter_log_entries received None, returning empty list")
            return []
        
        if not isinstance(entries, list):
            self.logger.info("DEBUG: filter_log_entries received %s, converting to list", type(entries))
            entries = list(entries) if entries else []

        level_filter = self.level_filter.currentText()
        module_filter = self.module_filter.currentText()
        text_filter = self.filter_input.text().lower()
        today_only = self.today_only.isChecked()

        filtered = []
        for entry in entries:
            # Level filter
            if level_filter != "All" and entry.get("level") != level_filter:
                continue
            # Module filter
            if module_filter != "All" and entry.get("component") != module_filter:
                continue
            # Text filter
            if text_filter and text_filter not in entry.get("message", "").lower():
                continue
            if today_only:
                try:
                    entry_date = datetime.strptime(entry.get("time", ""), "%Y-%m-%d %H:%M:%S").date()
                    if entry_date != datetime.now().date():
                        continue
                except Exception as exc:
                    self.logger.info("Failed to parse entry date: %s", exc)
            filtered.append(entry)
        
        return filtered

    def populate_log_table(self, entries):
        """Populate the log table with entries."""
        self.log_table.setRowCount(len(entries))
        for i, entry in enumerate(entries):
            # Time
            time_item = QTableWidgetItem(entry.get("time", ""))
            self.log_table.setItem(i, 0, time_item)
            # Level with status dot
            level_widget = StatusDot(entry.get("level", ""), entry.get("level", "").lower())
            self.log_table.setCellWidget(i, 1, level_widget)
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
        if hasattr(self, 'module_filter'):
            self.module_filter.setCurrentText("All")
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
            self.logger.info("DEBUG: Auto-refresh enabled")
        else:
            if self.update_timer:
                self.update_timer.stop()
            self.logger.info("DEBUG: Auto-refresh disabled")

    def clear_log_view(self):
        """Clear the current log view"""
        self.log_table.setRowCount(0)
        self.log_detail.clear()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_logs()

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
                self.logger.info("DEBUG: Exported %s entries to %s", len(self.filtered_entries), file_path)
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Export Error", f"Could not export logs: {str(e)}")
