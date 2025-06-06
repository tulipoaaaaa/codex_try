"""
Recent Activity Widget for Dashboard
Shows recent activities in a compact format for the 4-column dashboard layout
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QScrollArea, QPushButton)
from PySide6.QtCore import Qt, QTimer, Signal as pyqtSignal
from PySide6.QtGui import QFont, QColor
from datetime import datetime, timedelta
import logging

class RecentActivity(QWidget):
    """Widget showing recent activities in compact format"""
    
    activity_clicked = pyqtSignal(dict)  # Signal for when activity is clicked
    view_all_requested = pyqtSignal()  # Signal for when View All is clicked
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.init_ui()
        
        # Setup auto-refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_activities)
        self.refresh_timer.start(30000)  # Update every 30 seconds
        
        # Initial load
        self.refresh_activities()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        self.setObjectName("card")
        self.setStyleSheet("background-color: #1a1f2e; border-radius: 12px; border: 1px solid #2d3748; max-width: 400px;")

        # Header with consistent styling and better spacing
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        header = QLabel("Recent Activity")
        header.setObjectName("dashboard-section-header")
        header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setStyleSheet("color: #06b6d4; font-size: 18px; font-weight: 600; margin-bottom: 8px;")
        header_layout.addWidget(header)
        view_all_btn = QPushButton("View All")
        view_all_btn.setObjectName("btn--link")
        view_all_btn.setStyleSheet("QPushButton#btn--link { background: transparent; border: none; color: #32B8C6; font-size: 12px; text-decoration: underline; margin: 2px; } QPushButton#btn--link:hover { color: #2DA6B2; }")
        view_all_btn.clicked.connect(self.on_view_all_clicked)
        header_layout.addWidget(view_all_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(header_layout)

        # Scroll area for activities list with better sizing
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background: transparent;")
        scroll_area.setMinimumHeight(320)
        self.activities_container = QWidget()
        self.activities_layout = QVBoxLayout(self.activities_container)
        self.activities_layout.setContentsMargins(8, 2, 8, 8)
        self.activities_layout.setSpacing(10)
        self.activities_container.setStyleSheet("background: transparent;")
        scroll_area.setWidget(self.activities_container)
        layout.addWidget(scroll_area, 1)
    
    def refresh_activities(self):
        """Refresh the recent activities display"""
        # Clear existing activities
        self.clear_activities()
        
        # Get recent activities data (limit to 8 for compact view)
        activities = self.get_recent_activities(limit=8)
        
        if not activities:
            # Show "no recent activity" message
            no_activity_label = QLabel("No recent activity")
            no_activity_label.setObjectName("status--info")
            no_activity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.activities_layout.addWidget(no_activity_label)
        else:
            # Add each activity
            for activity in activities:
                activity_widget = self.create_activity_widget(activity)
                self.activities_layout.addWidget(activity_widget)
        
        # Add stretch to push content to top
        self.activities_layout.addStretch()
    
    def clear_activities(self):
        """Clear all activity widgets"""
        while self.activities_layout.count():
            child = self.activities_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def create_activity_widget(self, activity):
        """Create a compact widget for a single activity"""
        container = QFrame()
        container.setStyleSheet("background-color: #0f1419; border-radius: 8px; border: 1px solid #374151; padding: 8px; margin-bottom: 8px;")
        container.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(3)
        
        # Top row: time and status
        top_layout = QHBoxLayout()
        
        time_label = QLabel(activity['time'])
        time_label.setStyleSheet("color: #C5C7C7; font-size: 11px; font-weight: 500;")
        top_layout.addWidget(time_label)
        
        top_layout.addStretch()
        
        status_label = QLabel(activity['status'])
        if activity['status'] == 'success':
            status_label.setObjectName("status--success")
        elif activity['status'] == 'running':
            status_label.setObjectName("status--warning")
        elif activity['status'] == 'error':
            status_label.setObjectName("status--error")
        else:
            status_label.setObjectName("status--info")
        
        top_layout.addWidget(status_label)
        layout.addLayout(top_layout)
        
        # Action description
        action_label = QLabel(activity['action'])
        action_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        action_label.setWordWrap(True)
        layout.addWidget(action_label)
        
        # Details (if available)
        if 'details' in activity and activity['details']:
            details_label = QLabel(activity['details'])
            details_label.setStyleSheet("color: #C5C7C7; font-size: 11px;")
            details_label.setWordWrap(True)
            layout.addWidget(details_label)
        
        # Make clickable
        container.mousePressEvent = lambda event: self.activity_clicked.emit(activity)
        
        return container
    
    def on_view_all_clicked(self):
        """Handle View All button click"""
        self.logger.info("User requested full activity log view")
        self.view_all_requested.emit()
        
    def show_full_activity_log(self):
        """Signal to show the full activity log (e.g., switch to a different tab)"""
        # This could emit a signal to the main window to switch tabs
        self.logger.info("User requested full activity log view")
    
    def get_recent_activities(self, limit=8):
        """Get list of recent activities"""
        # In a real application, this would query the actual activity log
        # For demo purposes, return mock data
        
        now = datetime.now()
        
        activities = [
            {
                "time": (now - timedelta(minutes=2)).strftime("%H:%M"),
                "action": "GitHub collection started",
                "status": "running",
                "details": "Processing 67 repositories"
            },
            {
                "time": (now - timedelta(minutes=8)).strftime("%H:%M"),
                "action": "arXiv processing completed",
                "status": "success",
                "details": "263 PDFs processed successfully"
            },
            {
                "time": (now - timedelta(minutes=15)).strftime("%H:%M"),
                "action": "Domain rebalancing completed",
                "status": "success",
                "details": "8 domains rebalanced"
            },
            {
                "time": (now - timedelta(minutes=23)).strftime("%H:%M"),
                "action": "ISDA collection completed",
                "status": "success",
                "details": "12 documents collected"
            },
            {
                "time": (now - timedelta(minutes=35)).strftime("%H:%M"),
                "action": "Quality analysis completed",
                "status": "success",
                "details": "2,234 documents analyzed"
            },
            {
                "time": (now - timedelta(minutes=47)).strftime("%H:%M"),
                "action": "Corpus backup created",
                "status": "success",
                "details": "45.8 GB backed up to cloud"
            },
            {
                "time": (now - timedelta(minutes=63)).strftime("%H:%M"),
                "action": "Weekly report generated",
                "status": "success",
                "details": "Report exported to PDF"
            },
            {
                "time": (now - timedelta(hours=1, minutes=15)).strftime("%H:%M"),
                "action": "System maintenance",
                "status": "success",
                "details": "Cache cleared, indexes rebuilt"
            }
        ]
        
        return activities[:limit] 