# File: app/ui/widgets/activity_log.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
                             QLabel, QHBoxLayout, QPushButton, QComboBox, QMenu, QFileDialog, QApplication, QMessageBox)
from PySide6.QtGui import QAction, QIcon, QColor, QFont, QClipboard
from PySide6.QtCore import Qt, Signal as pyqtSignal, QDateTime
from app.helpers.icon_manager import IconManager
import csv

import datetime

class ActivityLogItem(QListWidgetItem):
    """Custom list widget item for activity log entries."""
    
    def __init__(self, timestamp, activity_type, message, details=None):
        super().__init__()
        self.timestamp = timestamp
        self.activity_type = activity_type
        self.message = message
        self.details = details
        
        # Set display text
        time_str = timestamp.toString("hh:mm:ss")
        self.setText(f"[{time_str}] {activity_type}: {message}")
        
        # Set icon based on activity type using IconManager
        icon_manager = IconManager()
        icon_map = {
            "Collection": ('Data collection and processing', 'Function'),
            "Processing": ('Start/play operation control', 'Function'),
            "Error": ('Warning and alert notifications', 'Function'),
            "Warning": ('Warning and alert notifications', 'Function'),
            "Success": ('Success status and completion indicator', 'Function'),
            "Info": ('Information and help messages', 'Function'),
        }
        icon_info = icon_map.get(activity_type, ('Information and help messages', 'Function'))
        icon_path = icon_manager.get_icon_path(*icon_info)
        if icon_path:
            self.setIcon(QIcon(icon_path))
        if activity_type == "Error":
            self.setForeground(QColor("red"))
        elif activity_type == "Warning":
            self.setForeground(QColor("orange"))
        elif activity_type == "Success":
            self.setForeground(QColor("green"))

class ActivityLog(QWidget):
    """Widget for displaying activity log entries."""
    
    item_selected = pyqtSignal(ActivityLogItem)
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setObjectName("card")
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        header_label = QLabel("Activity Log")
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        # Filter by type
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "Collection", "Processing", "Error", "Warning", "Success", "Info"])
        self.type_filter.currentTextChanged.connect(self.apply_filters)
        header_layout.addWidget(self.type_filter)
        
        # Clear button
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_log)
        header_layout.addWidget(clear_button)
        
        # Export button
        export_button = QPushButton("Export")
        export_button.clicked.connect(self.export_log)
        header_layout.addWidget(export_button)
        
        main_layout.addLayout(header_layout)
        
        # Log list
        self.log_list = QListWidget()
        self.log_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.log_list.customContextMenuRequested.connect(self.show_context_menu)
        self.log_list.itemClicked.connect(self.on_item_clicked)
        main_layout.addWidget(self.log_list)
    
    def add_activity(self, activity_type, message, details=None):
        """Add a new activity to the log."""
        timestamp = QDateTime.currentDateTime()
        item = ActivityLogItem(timestamp, activity_type, message, details)
        
        # Add to the top of the list (most recent first)
        self.log_list.insertItem(0, item)
        
        # Apply current filter
        self.apply_filters()
        
        return item
    
    def apply_filters(self):
        """Apply filters to the log list."""
        filter_type = self.type_filter.currentText()
        
        for i in range(self.log_list.count()):
            item = self.log_list.item(i)
            if isinstance(item, ActivityLogItem):
                if filter_type == "All" or item.activity_type == filter_type:
                    item.setHidden(False)
                else:
                    item.setHidden(True)
    
    def clear_log(self):
        """Clear all log entries."""
        self.log_list.clear()
    
    def export_log(self):
        """Export the log entries to a file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Log", "", "CSV Files (*.csv);;Text Files (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "Type", "Message", "Details"])
                    
                    for i in range(self.log_list.count()):
                        item = self.log_list.item(i)
                        if isinstance(item, ActivityLogItem):
                            writer.writerow([
                                item.timestamp.toString("yyyy-MM-dd hh:mm:ss"),
                                item.activity_type,
                                item.message,
                                item.details or ""
                            ])
                
                self.add_activity("Success", f"Log exported to {file_path}")
            except Exception as e:
                self.add_activity("Error", f"Failed to export log: {str(e)}")
    
    def on_item_clicked(self, item):
        """Handle item click."""
        if isinstance(item, ActivityLogItem):
            self.item_selected.emit(item)
    
    def show_context_menu(self, position):
        """Show context menu for log items."""
        item = self.log_list.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        
        # Copy action
        copy_action = QAction("Copy Message", self)
        copy_action.triggered.connect(lambda: self.copy_item_text(item))
        menu.addAction(copy_action)
        
        # View details action (if details exist)
        if isinstance(item, ActivityLogItem) and item.details:
            view_details_action = QAction("View Details", self)
            view_details_action.triggered.connect(lambda: self.view_item_details(item))
            menu.addAction(view_details_action)
        
        # Delete action
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_item(item))
        menu.addAction(delete_action)
        
        menu.exec(self.log_list.mapToGlobal(position))
    
    def copy_item_text(self, item):
        """Copy the item text to clipboard."""
        QApplication.clipboard().setText(item.text())
    
    def view_item_details(self, item):
        """View the details of an item."""
        if isinstance(item, ActivityLogItem) and item.details:
            QMessageBox.information(
                self, 
                f"{item.activity_type} Details",
                item.details
            )
    
    def delete_item(self, item):
        """Delete an item from the log."""
        row = self.log_list.row(item)
        if row >= 0:
            self.log_list.takeItem(row)
            
    def update_activity_log(self, activity_data):
        """Update the activity log with new data."""
        # Clear existing entries
        self.log_list.clear()
        
        # Add new entries
        for entry in activity_data:
            if isinstance(entry, dict):
                activity_type = entry.get('status', 'Info')
                message = entry.get('action', 'Unknown action')
                details = entry.get('details', '')
                
                # Map status to activity type
                if activity_type == 'running':
                    activity_type = 'Info'
                elif activity_type == 'success':
                    activity_type = 'Success'
                elif activity_type == 'error':
                    activity_type = 'Error'
                
                self.add_activity(activity_type, message, details)
