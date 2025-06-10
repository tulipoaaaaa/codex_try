"""
Active Operations Widget for Dashboard
Shows currently running collectors, processors, and other operations
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QFrame,
    QPushButton,
    QScrollArea,
)
from PySide6.QtCore import Qt, QTimer, Signal as pyqtSignal
from PySide6.QtGui import QFont, QColor
from app.ui.widgets.card_wrapper import CardWrapper
from app.ui.widgets.status_dot import StatusDot
from datetime import datetime, timedelta
import logging

class ActiveOperations(CardWrapper):
    """Widget showing active operations and their status"""
    
    def __init__(self, config, parent=None):
        super().__init__(title="Active Operations", parent=parent)
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        self.init_ui()
        
        # Setup auto-refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_operations)
        self.refresh_timer.start(5000)  # Update every 5 seconds
        
        # Initial load
        self.refresh_operations()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = self.body_layout

        # Scroll area for operations list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background: transparent;")

        # Container for operations
        self.operations_container = QWidget()
        self.operations_layout = QVBoxLayout(self.operations_container)
        self.operations_layout.setContentsMargins(5, 5, 5, 5)
        self.operations_layout.setSpacing(12)
        self.operations_container.setStyleSheet("background: transparent;")

        scroll_area.setWidget(self.operations_container)
        layout.addWidget(scroll_area)
    
    def refresh_operations(self):
        """Refresh the active operations display"""
        # Clear existing operations
        self.clear_operations()
        
        # Get active operations data
        operations = self.get_active_operations()
        
        if not operations:
            # Show "no active operations" message
            no_ops_label = StatusDot("No active operations", "info")
            self.operations_layout.addWidget(no_ops_label)
        else:
            # Add each operation
            for operation in operations:
                op_widget = self.create_operation_widget(operation)
                self.operations_layout.addWidget(op_widget)
        
        # Add stretch to push content to top
        self.operations_layout.addStretch()
    
    def clear_operations(self):
        """Clear all operation widgets"""
        while self.operations_layout.count():
            child = self.operations_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def create_operation_widget(self, operation):
        """Create a widget for a single operation"""
        container = CardWrapper()
        layout = container.body_layout
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)
        
        # Operation name and status
        header_layout = QHBoxLayout()
        
        name_label = QLabel(operation['name'])
        name_label.setStyleSheet("font-weight: 600; font-size: 15px; color: #00B7EB; background: transparent;")
        header_layout.addWidget(name_label)
        
        status = operation['status'].lower()
        status_widget = StatusDot(operation['status'],
                                 'success' if status == 'running' else status)
        header_layout.addWidget(status_widget)
        layout.addLayout(header_layout)
        
        # Progress bar (if applicable)
        if 'progress' in operation:
            progress_bar = QProgressBar()
            progress_bar.setValue(operation['progress'])
            progress_bar.setTextVisible(True)
            progress_bar.setFormat(f"{operation['progress']}%")
            layout.addWidget(progress_bar)
        
        # Details
        if 'details' in operation:
            details_label = QLabel(operation['details'])
            details_label.setStyleSheet("color: #C5C7C7; font-size: 12px;")
            details_label.setWordWrap(True)
            layout.addWidget(details_label)
        
        # Duration
        if 'start_time' in operation:
            duration = self.format_duration(operation['start_time'])
            duration_label = QLabel(f"Running for: {duration}")
            duration_label.setStyleSheet("color: #C5C7C7; font-size: 11px;")
            layout.addWidget(duration_label)
        
        return container
    
    def format_duration(self, start_time):
        """Format operation duration"""
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        
        duration = datetime.now() - start_time
        
        if duration.days > 0:
            return f"{duration.days}d {duration.seconds // 3600}h"
        elif duration.seconds >= 3600:
            return f"{duration.seconds // 3600}h {(duration.seconds % 3600) // 60}m"
        elif duration.seconds >= 60:
            return f"{duration.seconds // 60}m"
        else:
            return f"{duration.seconds}s"
    
    def get_active_operations(self):
        """Return active operations from ``TaskQueueManager`` if available."""
        if hasattr(self, "task_queue_manager") and self.task_queue_manager:
            try:
                operations = []
                for tid, info in self.task_queue_manager.tasks.items():
                    operations.append({
                        "name": info.get("name", tid),
                        "status": info.get("status", "pending"),
                        "progress": info.get("progress", 0),
                        "details": info.get("details", ""),
                        "start_time": info.get("start_time", datetime.now()),
                    })
                return operations
            except Exception as exc:  # pragma: no cover
                self.logger.warning("Failed to retrieve operations: %s", exc)
        return []


class ActiveOperationsWidget(ActiveOperations):
    """Backwards compatible wrapper accepting a task queue manager."""

    def __init__(self, task_queue_manager=None, parent=None):
        super().__init__(config=None, parent=parent)
        self.task_queue_manager = task_queue_manager
