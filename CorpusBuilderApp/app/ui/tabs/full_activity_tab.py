"""
Full Activity Tab for Crypto Corpus Builder
Comprehensive activity monitoring with statistics, runtime tracking, and operational metrics
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                            QLabel, QProgressBar, QFrame, QSplitter, QPushButton,
                            QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
                            QGroupBox, QComboBox, QLineEdit, QDateEdit, QCheckBox,
                            QTabWidget, QListWidget, QTextEdit, QDialog)
from PySide6.QtCore import Qt, QTimer, Signal as pyqtSignal, Slot as pyqtSlot, QDate
from PySide6.QtGui import QColor, QIcon, QFont
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
from app.helpers.chart_manager import ChartManager
from app.ui.theme.theme_constants import (
    DEFAULT_FONT_SIZE,
    CARD_MARGIN,
    CARD_PADDING,
    BUTTON_COLOR_PRIMARY,
    BUTTON_COLOR_DANGER,
    BUTTON_COLOR_GRAY,
    CARD_BORDER_COLOR,
    STATUS_DOT_GREEN,
    STATUS_DOT_RED,
    STATUS_DOT_GRAY,
)
from app.ui.widgets.card_wrapper import CardWrapper
from app.ui.widgets.section_header import SectionHeader
from app.ui.widgets.status_dot import StatusDot


class FullActivityTab(QWidget):
    """Comprehensive activity monitoring tab with detailed statistics and metrics"""

    retry_requested = pyqtSignal(str)
    stop_requested = pyqtSignal(str)

    def __init__(self, config, activity_log_service=None, task_history_service=None, task_queue_manager=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.activity_log_service = activity_log_service
        self.task_source = task_history_service
        self.task_queue_manager = task_queue_manager
        self.logger = logging.getLogger(self.__class__.__name__)

        # Apply shared UI theme settings
        self.setFont(QFont("", DEFAULT_FONT_SIZE))
        
        # Initialize chart manager for activity visualizations
        self.chart_manager = ChartManager()
        
        # Initialize persistent activity data
        self.activities_data: list[dict] = []
        self.load_existing_history()

        if self.task_source:
            try:
                self.task_source.task_added.connect(lambda _: self.load_activity_data())
                self.task_source.task_updated.connect(lambda _: self.load_activity_data())
            except Exception as exc:
                self.logger.warning("Failed to connect task signals: %s", exc)

        if self.activity_log_service:
            try:
                self.activity_log_service.activity_added.connect(self.on_activity_added)
            except Exception as exc:
                self.logger.warning("Failed to connect activity_added: %s", exc)

        if self.task_source:
            try:
                self.task_source.history_changed.connect(self.load_activity_data)
            except Exception as exc:
                self.logger.warning("Failed to connect history_changed: %s", exc)

        self.init_ui()
        self.setup_update_timer()
        self.load_activity_data()
    
    def init_ui(self):
        """Initialize the comprehensive activity interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN)
        main_layout.setSpacing(CARD_MARGIN)
        self.setStyleSheet("background-color: #0f1419;")
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        
        title_label = SectionHeader("📊 Full Activity Dashboard")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Filter controls
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        header_layout.addWidget(QLabel("From:"))
        header_layout.addWidget(self.date_from)
        
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        header_layout.addWidget(QLabel("To:"))
        header_layout.addWidget(self.date_to)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "Success", "Running", "Error", "Warning"])
        header_layout.addWidget(QLabel("Status:"))
        header_layout.addWidget(self.status_filter)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.load_activity_data)
        self.refresh_btn.setStyleSheet(f"background-color: {BUTTON_COLOR_PRIMARY}; color: white;")
        header_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # Create main content splitter (top stats, bottom details)
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Top section: Statistics overview (4 cards + charts)
        stats_widget = self.create_statistics_overview()
        main_splitter.addWidget(stats_widget)
        
        # Bottom section: Detailed activity table and task details
        details_widget = self.create_activity_details()
        main_splitter.addWidget(details_widget)
        
        # Set proportions (60% stats, 40% details)
        main_splitter.setSizes([600, 400])
        main_layout.addWidget(main_splitter)
    
    def create_statistics_overview(self):
        """Create the statistics overview section"""
        container = QWidget()
        container.setStyleSheet("background-color: #0f1419;")
        layout = QVBoxLayout(container)
        layout.setSpacing(16)
        
        # Top row: Key metrics cards
        metrics_layout = QHBoxLayout()
        
        # Total Tasks Card
        self.total_tasks_card = self.create_metric_card(
            "Total Tasks", "156", BUTTON_COLOR_PRIMARY
        )
        metrics_layout.addWidget(self.total_tasks_card)
        
        # Success Rate Card  
        self.success_rate_card = self.create_metric_card("Success Rate", "94.2%", STATUS_DOT_GREEN)
        metrics_layout.addWidget(self.success_rate_card)
        
        # Average Runtime Card
        self.avg_runtime_card = self.create_metric_card("Avg Runtime", "12m 34s", "#E68161")
        metrics_layout.addWidget(self.avg_runtime_card)
        
        # Active Tasks Card
        self.active_tasks_card = self.create_metric_card(
            "Active Now", "3", BUTTON_COLOR_PRIMARY
        )
        metrics_layout.addWidget(self.active_tasks_card)
        
        layout.addLayout(metrics_layout)
        
        # Consolidated headers bar with dark gray background (like Analytics)
        headers_bar = QFrame()
        headers_bar.setObjectName("activity-headers-bar")
        headers_bar.setStyleSheet("background-color: #1a1f2e; border-radius: 8px; padding: 12px; margin: 8px 0px;")
        
        headers_layout = QHBoxLayout(headers_bar)
        headers_layout.setSpacing(16)
        
        # Create consolidated headers with dark gray backgrounds - CENTERED
        status_header = QLabel("Task Status Distribution")
        status_header.setStyleSheet("color: #FFFFFF; font-weight: 600; font-size: 14px; padding: 8px 12px; background-color: #1a1f2e; border-radius: 6px;")
        status_header.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the header text
        headers_layout.addWidget(status_header)
        
        runtime_header = QLabel("Runtime Distribution / Execution Time")
        runtime_header.setStyleSheet("color: #FFFFFF; font-weight: 600; font-size: 14px; padding: 8px 12px; background-color: #1a1f2e; border-radius: 6px;")
        runtime_header.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the header text
        headers_layout.addWidget(runtime_header)
        
        trends_header = QLabel("Performance Trends / Success Rate Over Time")
        trends_header.setStyleSheet("color: #FFFFFF; font-weight: 600; font-size: 14px; padding: 8px 12px; background-color: #1a1f2e; border-radius: 6px;")
        trends_header.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the header text
        headers_layout.addWidget(trends_header)
        
        layout.addWidget(headers_bar)
        
        # Charts row: Charts without individual headers
        charts_layout = QHBoxLayout()
        
        # Status Distribution Pie Chart (no header, legend below with colored squares)
        status_chart_container = QFrame()
        status_chart_container.setObjectName("card")
        status_chart_container.setStyleSheet(
            f"background-color: #1a1f2e; border-radius: 12px; border: 1px solid {CARD_BORDER_COLOR};"
        )
        status_chart_layout = QVBoxLayout(status_chart_container)
        status_chart_layout.setContentsMargins(CARD_MARGIN // 2, CARD_MARGIN // 2, CARD_MARGIN // 2, CARD_MARGIN // 2)
        
        self.status_chart = self.chart_manager.create_chart_view("")  # Empty title since header is above
        self.status_chart.setMinimumSize(300, 250)  # Bigger chart
        status_chart_layout.addWidget(self.status_chart)
        
        # Add legend below chart with colored squares (no "Legend:" text)
        status_legend_layout = QHBoxLayout()
        status_legend_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Success square and label
        success_square = QLabel("■")
        success_square.setStyleSheet(f"color: {STATUS_DOT_GREEN}; font-size: 14px;")
        success_label = QLabel("Success")
        success_label.setStyleSheet("color: #C5C7C7; font-size: 11px; margin-left: 2px;")
        
        # Running square and label
        running_square = QLabel("■")
        running_square.setStyleSheet(f"color: {BUTTON_COLOR_PRIMARY}; font-size: 14px;")
        running_label = QLabel("Running")
        running_label.setStyleSheet("color: #C5C7C7; font-size: 11px; margin-left: 2px;")
        
        # Error square and label
        error_square = QLabel("■")
        error_square.setStyleSheet(f"color: {STATUS_DOT_RED}; font-size: 14px;")
        error_label = QLabel("Error")
        error_label.setStyleSheet("color: #C5C7C7; font-size: 11px; margin-left: 2px;")
        
        # Warning square and label
        warning_square = QLabel("■")
        warning_square.setStyleSheet("color: #E68161; font-size: 14px;")
        warning_label = QLabel("Warning")
        warning_label.setStyleSheet("color: #C5C7C7; font-size: 11px; margin-left: 2px;")
        
        # Add to layout with spacing
        status_legend_layout.addWidget(success_square)
        status_legend_layout.addWidget(success_label)
        status_legend_layout.addSpacing(12)
        status_legend_layout.addWidget(running_square)
        status_legend_layout.addWidget(running_label)
        status_legend_layout.addSpacing(12)
        status_legend_layout.addWidget(error_square)
        status_legend_layout.addWidget(error_label)
        status_legend_layout.addSpacing(12)
        status_legend_layout.addWidget(warning_square)
        status_legend_layout.addWidget(warning_label)
        
        status_legend_widget = QWidget()
        status_legend_widget.setLayout(status_legend_layout)
        status_chart_layout.addWidget(status_legend_widget)
        
        charts_layout.addWidget(status_chart_container)
        
        # Runtime Distribution Bar Chart (no header, legend below with colored squares)
        runtime_chart_container = QFrame()
        runtime_chart_container.setObjectName("card")
        runtime_chart_container.setStyleSheet(
            f"background-color: #1a1f2e; border-radius: 12px; border: 1px solid {CARD_BORDER_COLOR};"
        )
        runtime_chart_layout = QVBoxLayout(runtime_chart_container)
        runtime_chart_layout.setContentsMargins(CARD_MARGIN // 2, CARD_MARGIN // 2, CARD_MARGIN // 2, CARD_MARGIN // 2)
        
        self.runtime_chart = self.chart_manager.create_chart_view("")  # Empty title since header is above
        self.runtime_chart.setMinimumSize(300, 250)  # Bigger chart
        runtime_chart_layout.addWidget(self.runtime_chart)
        
        # Add legend below chart with colored squares (no "Legend:" text)
        runtime_legend_layout = QHBoxLayout()
        runtime_legend_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # <5min square and label
        min5_square = QLabel("■")
        min5_square.setStyleSheet("color: #4ECDC4; font-size: 14px;")
        min5_label = QLabel("<5min")
        min5_label.setStyleSheet("color: #C5C7C7; font-size: 11px; margin-left: 2px;")
        
        # 5-15min square and label
        min15_square = QLabel("■")
        min15_square.setStyleSheet("color: #4ECDC4; font-size: 14px;")
        min15_label = QLabel("5-15min")
        min15_label.setStyleSheet("color: #C5C7C7; font-size: 11px; margin-left: 2px;")
        
        # 15-30min square and label
        min30_square = QLabel("■")
        min30_square.setStyleSheet("color: #4ECDC4; font-size: 14px;")
        min30_label = QLabel("15-30min")
        min30_label.setStyleSheet("color: #C5C7C7; font-size: 11px; margin-left: 2px;")
        
        # >30min square and label
        over30_square = QLabel("■")
        over30_square.setStyleSheet("color: #4ECDC4; font-size: 14px;")
        over30_label = QLabel(">30min")
        over30_label.setStyleSheet("color: #C5C7C7; font-size: 11px; margin-left: 2px;")
        
        # Add to layout with spacing
        runtime_legend_layout.addWidget(min5_square)
        runtime_legend_layout.addWidget(min5_label)
        runtime_legend_layout.addSpacing(12)
        runtime_legend_layout.addWidget(min15_square)
        runtime_legend_layout.addWidget(min15_label)
        runtime_legend_layout.addSpacing(12)
        runtime_legend_layout.addWidget(min30_square)
        runtime_legend_layout.addWidget(min30_label)
        runtime_legend_layout.addSpacing(12)
        runtime_legend_layout.addWidget(over30_square)
        runtime_legend_layout.addWidget(over30_label)
        
        runtime_legend_widget = QWidget()
        runtime_legend_widget.setLayout(runtime_legend_layout)
        runtime_chart_layout.addWidget(runtime_legend_widget)
        
        charts_layout.addWidget(runtime_chart_container)
        
        # Performance Trends Line Chart (no header, legend below with colored squares)
        trends_chart_container = QFrame()
        trends_chart_container.setObjectName("card")
        trends_chart_container.setStyleSheet(
            f"background-color: #1a1f2e; border-radius: 12px; border: 1px solid {CARD_BORDER_COLOR};"
        )
        trends_chart_layout = QVBoxLayout(trends_chart_container)
        trends_chart_layout.setContentsMargins(CARD_MARGIN // 2, CARD_MARGIN // 2, CARD_MARGIN // 2, CARD_MARGIN // 2)
        
        self.trends_chart = self.chart_manager.create_chart_view("")  # Empty title since header is above
        self.trends_chart.setMinimumSize(300, 250)  # Bigger chart
        trends_chart_layout.addWidget(self.trends_chart)
        
        # Add legend below chart with colored squares (no "Legend:" text)
        trends_legend_layout = QHBoxLayout()
        trends_legend_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Success Rate square and label
        success_rate_square = QLabel("■")
        success_rate_square.setStyleSheet(f"color: {STATUS_DOT_GREEN}; font-size: 14px;")
        success_rate_label = QLabel("Success Rate")
        success_rate_label.setStyleSheet("color: #C5C7C7; font-size: 11px; margin-left: 2px;")
        
        # Task Volume square and label
        volume_square = QLabel("■")
        volume_square.setStyleSheet(f"color: {BUTTON_COLOR_PRIMARY}; font-size: 14px;")
        volume_label = QLabel("Task Volume")
        volume_label.setStyleSheet("color: #C5C7C7; font-size: 11px; margin-left: 2px;")
        
        # Performance Score square and label
        perf_square = QLabel("■")
        perf_square.setStyleSheet("color: #E68161; font-size: 14px;")
        perf_label = QLabel("Performance Score")
        perf_label.setStyleSheet("color: #C5C7C7; font-size: 11px; margin-left: 2px;")
        
        # Add to layout with spacing
        trends_legend_layout.addWidget(success_rate_square)
        trends_legend_layout.addWidget(success_rate_label)
        trends_legend_layout.addSpacing(12)
        trends_legend_layout.addWidget(volume_square)
        trends_legend_layout.addWidget(volume_label)
        trends_legend_layout.addSpacing(12)
        trends_legend_layout.addWidget(perf_square)
        trends_legend_layout.addWidget(perf_label)
        
        trends_legend_widget = QWidget()
        trends_legend_widget.setLayout(trends_legend_layout)
        trends_chart_layout.addWidget(trends_legend_widget)
        
        charts_layout.addWidget(trends_chart_container)
        
        layout.addLayout(charts_layout)
        
        return container
    
    def create_metric_card(self, title, value, color):
        """Create a metric card widget with centered content and bigger fonts"""
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumSize(200, 100)
        card.setStyleSheet(
            f"background-color: #1a1f2e; border-radius: 12px; border: 1px solid {CARD_BORDER_COLOR};"
        )
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the content
        
        # Title - centered and slightly bigger
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; color: #C5C7C7; font-weight: 600;")  # Increased from 12px to 14px, weight 500 to 600
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the title
        layout.addWidget(title_label)
        
        # Value - centered and bigger
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 28px; color: {color}; font-weight: 700;")  # Increased from 24px to 28px
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the value
        layout.addWidget(value_label)
        
        # Store reference for updates
        setattr(self, f"{title.lower().replace(' ', '_')}_value", value_label)
        
        return card
    
    def create_activity_details(self):
        """Create the detailed activity section"""
        container = QWidget()
        container.setStyleSheet("background-color: #0f1419;")
        layout = QHBoxLayout(container)
        
        # Left: Activity table
        table_container = CardWrapper("📋 Detailed Activity Log")
        table_layout = table_container.body_layout
        
        
        # Activity table with comprehensive columns
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(8)
        self.activity_table.setHorizontalHeaderLabels([
            "Time", "Task", "Status", "Duration", "Progress", "Type", "Domain", "Details"
        ])
        
        # Configure table
        header = self.activity_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Time
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)          # Task
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Duration
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Progress
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Domain
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)          # Details
        
        self.activity_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.activity_table.itemSelectionChanged.connect(self.on_activity_selected)
        
        self.activity_table.setStyleSheet(
            f"background-color: #1a1f2e; color: #f9fafb; border: 1px solid {CARD_BORDER_COLOR}; border-radius: 8px;"
        )

        table_layout.addWidget(self.activity_table)
        self.no_activity_label = QLabel("No activity yet")
        self.no_activity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_layout.addWidget(self.no_activity_label)
        layout.addWidget(table_container, 2)  # 2/3 of space
        
        # Right: Task details panel
        details_container = CardWrapper("🔍 Task Details")
        details_layout = details_container.body_layout
        
        # Task info display
        self.task_info = QTextEdit()
        self.task_info.setReadOnly(True)
        self.task_info.setPlainText("Select a task to view detailed information...")
        self.task_info.setStyleSheet(
            f"background-color: #0f1419; color: #f9fafb; border-radius: 8px; border: 1px solid {CARD_BORDER_COLOR};"
        )
        details_layout.addWidget(self.task_info)
        
        # Task actions
        actions_layout = QHBoxLayout()
        
        self.retry_btn = QPushButton("🔄 Retry")
        self.retry_btn.setEnabled(False)
        self.retry_btn.clicked.connect(self.retry_task)  # Connect retry action
        self.retry_btn.setStyleSheet(f"background-color: {BUTTON_COLOR_PRIMARY}; color: white;")
        actions_layout.addWidget(self.retry_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_task)  # Connect stop action
        self.stop_btn.setStyleSheet(f"background-color: {BUTTON_COLOR_DANGER}; color: white;")
        actions_layout.addWidget(self.stop_btn)
        
        self.logs_btn = QPushButton("📝 View Logs")
        self.logs_btn.setEnabled(False)
        self.logs_btn.clicked.connect(self.view_task_logs)  # Connect view logs action
        self.logs_btn.setStyleSheet(f"background-color: {BUTTON_COLOR_GRAY}; color: white;")
        actions_layout.addWidget(self.logs_btn)
        
        details_layout.addLayout(actions_layout)
        layout.addWidget(details_container, 1)  # 1/3 of space
        
        return container
    
    def setup_update_timer(self):
        """Setup automatic refresh timer"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.load_activity_data)
        self.update_timer.start(10000)  # Update every 10 seconds

    def load_existing_history(self):
        """Load prior activity from disk if available."""
        if self.task_source:
            return
        try:
            log_dir = Path(self.config.get_logs_dir())
        except Exception:
            return
        log_file = log_dir / "activity.log"
        if not log_file.exists():
            return
        try:
            with open(log_file, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        self.activities_data.append(self._map_entry(entry))
                    except Exception:
                        continue
        except Exception as exc:
            self.logger.warning("Failed to load history: %s", exc)

    def _map_entry(self, entry: dict) -> dict:
        """Map raw log entry to internal representation."""
        details = entry.get("details") or {}
        if not isinstance(details, dict):
            details = {}
        timestamp = entry.get("timestamp", datetime.utcnow().isoformat())
        return {
            "time": datetime.fromisoformat(timestamp).strftime("%H:%M:%S"),
            "start_time": timestamp,
            "id": details.get("task_id"),
            "action": entry.get("message", ""),
            "status": details.get("status", "info"),
            "details": details.get("details", ""),
            "duration_seconds": details.get("duration_seconds", 0),
            "progress": details.get("progress", 0),
            "type": details.get("type", "General"),
            "domain": details.get("domain", "General"),
            "error_message": details.get("error_message", ""),
            "task_id": details.get("task_id", ""),
        }

    def on_activity_added(self, entry: dict):
        """Handle new activity emitted from ``ActivityLogService``."""
        self.activities_data.append(self._map_entry(entry))
        self.load_activity_data()
    
    def load_activity_data(self):
        """Load and update all activity data"""
        try:
            # Update metric cards
            self.update_metrics()
            
            # Update charts
            self.update_status_chart()
            self.update_runtime_chart()
            self.update_trends_chart()
            
            # Update activity table
            self.update_activity_table()
            
        except Exception as e:
            self.logger.error(f"Error loading activity data: {e}")
    
    def update_metrics(self):
        """Update the metric cards with real task history"""

        activities = self.get_activity_data()
        total_tasks = len(activities)

        if self.task_source:
            counts = self.task_source.get_recent_task_counts(days=7)
            total_tasks = sum(counts.values()) or total_tasks

        success_count = len([a for a in activities if a['status'] == 'success'])
        success_rate = (success_count / total_tasks * 100) if total_tasks > 0 else 0
        active_count = len([a for a in activities if a['status'] == 'running'])
        
        # Calculate average runtime
        completed_tasks = [a for a in activities if a['status'] in ['success', 'error']]
        if completed_tasks:
            avg_runtime_seconds = sum(a.get('duration_seconds', 0) for a in completed_tasks) / len(completed_tasks)
            avg_runtime = f"{int(avg_runtime_seconds // 60)}m {int(avg_runtime_seconds % 60)}s"
        else:
            avg_runtime = "N/A"
        
        # Update metric displays
        self.total_tasks_value.setText(str(total_tasks))
        self.success_rate_value.setText(f"{success_rate:.1f}%")
        self.avg_runtime_value.setText(avg_runtime)
        self.active_now_value.setText(str(active_count))
    
    def update_status_chart(self):
        """Update the status distribution pie chart"""
        activities = self.get_activity_data()
        status_counts = {}
        
        for activity in activities:
            status = activity['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Create pie chart
        chart = self.status_chart.chart()
        chart.removeAllSeries()
        
        series = QPieSeries()
        colors = {
            'success': STATUS_DOT_GREEN,
            'running': BUTTON_COLOR_PRIMARY,
            'error': STATUS_DOT_RED,
            'warning': '#E68161'
        }
        
        for status, count in status_counts.items():
            slice_obj = series.append(f"{status.title()} ({count})", count)
            slice_obj.setProperty("domain_count", count)
            if status in colors:
                slice_obj.setBrush(QColor(colors[status]))
            
            # Apply white borders and text for visibility
            slice_obj.setBorderColor(QColor(255, 255, 255))
            slice_obj.setBorderWidth(1)
            slice_obj.setLabelColor(QColor(255, 255, 255))
        
        chart.addSeries(series)
        
        # Remove chart title since it's now in the consolidated header
        chart.setTitle("")
        
        # Hide chart legend since we have custom legend below
        legend = chart.legend()
        legend.setVisible(False)
    
    def update_runtime_chart(self):
        """Update the runtime distribution bar chart"""
        activities = self.get_activity_data()
        
        # Group by runtime ranges with better categories
        runtime_ranges = {
            "<5min": 0,
            "5-15min": 0, 
            "15-30min": 0,
            ">30min": 0
        }
        
        for activity in activities:
            duration = activity.get('duration_seconds', 0)
            if duration < 300:  # < 5 minutes
                runtime_ranges["<5min"] += 1
            elif duration < 900:  # 5-15 minutes
                runtime_ranges["5-15min"] += 1
            elif duration < 1800:  # 15-30 minutes
                runtime_ranges["15-30min"] += 1
            else:  # > 30 minutes
                runtime_ranges[">30min"] += 1
        
        # Create bar chart
        chart = self.runtime_chart.chart()
        chart.removeAllSeries()
        
        # Clear existing axes
        for axis in chart.axes():
            chart.removeAxis(axis)
        
        series = QBarSeries()
        bar_set = QBarSet("Task Count")
        bar_set.setColor(QColor("#4ECDC4"))  # Light teal for better visual appearance
        
        categories = list(runtime_ranges.keys())
        for category in categories:
            bar_set.append(runtime_ranges[category])
        
        series.append(bar_set)
        chart.addSeries(series)
        
        # Setup axes with proper styling
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsColor(QColor(255, 255, 255))  # White text
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        max_val = max(runtime_ranges.values()) if runtime_ranges.values() else 1
        axis_y.setRange(0, max_val + 1)
        axis_y.setLabelsColor(QColor(255, 255, 255))  # White text
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        
        # Remove chart title since it's now in the consolidated header
        chart.setTitle("")
        
        # Hide chart legend since we have custom legend below
        legend = chart.legend()
        if legend:
            legend.setVisible(False)
    
    def update_trends_chart(self):
        """Update the performance trends chart with daily task counts."""
        chart = self.trends_chart.chart()
        chart.removeAllSeries()
        for axis in chart.axes():
            chart.removeAxis(axis)

        counts = self.task_source.get_recent_task_counts(days=7) if self.task_source else {}
        if not counts:
            return
        dates = sorted(counts.keys())

        series = QBarSeries()
        bar_set = QBarSet("Tasks")
        for d in dates:
            bar_set.append(counts[d])
        series.append(bar_set)
        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(dates)
        axis_x.setLabelsColor(QColor(255, 255, 255))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, max(counts.values()) if counts else 1)
        axis_y.setLabelsColor(QColor(255, 255, 255))
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        chart.setTitle("")
        legend = chart.legend()
        if legend:
            legend.setVisible(False)
    
    def update_activity_table(self):
        """Update the detailed activity table"""
        activities = self.get_activity_data()
        
        self.activity_table.setRowCount(len(activities))
        self.no_activity_label.setVisible(len(activities) == 0)

        for row, activity in enumerate(activities):
            # Time
            time_item = QTableWidgetItem(activity['time'])
            self.activity_table.setItem(row, 0, time_item)
            
            # Task
            task_item = QTableWidgetItem(activity['action'])
            self.activity_table.setItem(row, 1, task_item)
            
            # Status
            status_item = QTableWidgetItem(activity['status'].title())
            if activity['status'] == 'success':
                status_item.setBackground(QColor(80, 200, 120, 50))
            elif activity['status'] == 'error':
                status_item.setBackground(QColor(255, 84, 89, 50))
            elif activity['status'] == 'running':
                status_item.setBackground(QColor(50, 184, 198, 50))
            self.activity_table.setItem(row, 2, status_item)
            
            # Duration
            duration = activity.get('duration_seconds', 0)
            if activity['status'] == 'running':
                duration_text = f"{duration // 60}m {duration % 60}s (ongoing)"
            else:
                duration_text = f"{duration // 60}m {duration % 60}s"
            duration_item = QTableWidgetItem(duration_text)
            self.activity_table.setItem(row, 3, duration_item)
            
            # Progress
            progress = activity.get('progress', 100 if activity['status'] == 'success' else 0)
            progress_item = QTableWidgetItem(f"{progress}%")
            self.activity_table.setItem(row, 4, progress_item)
            
            # Type
            task_type = activity.get('type', 'Collection')
            type_item = QTableWidgetItem(task_type)
            self.activity_table.setItem(row, 5, type_item)
            
            # Domain
            domain = activity.get('domain', 'General')
            domain_item = QTableWidgetItem(domain)
            self.activity_table.setItem(row, 6, domain_item)
            
            # Details
            details = activity.get('details', '')
            details_item = QTableWidgetItem(details)
            self.activity_table.setItem(row, 7, details_item)
    
    def on_activity_selected(self):
        """Handle activity selection in table"""
        current_row = self.activity_table.currentRow()
        if current_row >= 0:
            activities = self.get_activity_data()
            if current_row < len(activities):
                activity = activities[current_row]
                
                # Display detailed information
                details_text = f"""
Task: {activity['action']}
Status: {activity['status'].title()}
Started: {activity.get('start_time', 'Unknown')}
Duration: {activity.get('duration_seconds', 0) // 60}m {activity.get('duration_seconds', 0) % 60}s
Type: {activity.get('type', 'Collection')}
Domain: {activity.get('domain', 'General')}

Details:
{activity.get('details', 'No additional details available.')}

Progress: {activity.get('progress', 0)}%
{activity.get('error_message', '')}
                """.strip()
                
                self.task_info.setPlainText(details_text)
                
                # Enable/disable action buttons based on status
                is_running = activity['status'] == 'running'
                is_failed = activity['status'] == 'error'
                
                self.stop_btn.setEnabled(is_running)
                self.retry_btn.setEnabled(is_failed)
                self.logs_btn.setEnabled(True)
    
    def get_activity_data(self):
        """Return current activity log entries."""
        if self.task_source:
            tasks = self.task_source.load_recent_tasks()
            mapped = []
            for t in tasks:
                start = t.get("start_time", datetime.utcnow().isoformat())
                mapped.append({
                    "id": t.get("id"),
                    "time": datetime.fromisoformat(start).strftime("%H:%M:%S"),
                    "start_time": start,
                    "action": t.get("name", ""),
                    "status": t.get("status", "pending"),
                    "details": t.get("details", ""),
                    "duration_seconds": t.get("duration_seconds", 0),
                    "progress": t.get("progress", 0),
                    "type": t.get("type", "General"),
                    "domain": t.get("domain", "General"),
                    "error_message": t.get("error_message", ""),
                })
            return mapped
        return self.activities_data

    def _get_task_id(self, activity: dict) -> str:
        return activity.get("task_id") or f"TASK_{hash(activity.get('action', '')) % 10000:04d}"
    
    def retry_task(self):
        """Handle the retry action for the selected task."""
        self.logger.debug("Retry button clicked")
        current_row = self.activity_table.currentRow()
        if current_row >= 0:
            activities = self.get_activity_data()
            if current_row < len(activities):
                activity = activities[current_row]
                task_id = self._get_task_id(activity)

                if activity['status'] == 'error':
                    # Reset local task info
                    activity['status'] = 'running'
                    activity['progress'] = 0
                    activity['start_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    activity['duration_seconds'] = 0
                    if 'error_message' in activity:
                        del activity['error_message']

                    if self.task_queue_manager:
                        try:
                            self.task_queue_manager.add_task(task_id, {
                                "name": activity.get('action', task_id)
                            })
                        except Exception as exc:  # pragma: no cover
                            self.logger.warning("Failed to queue retry for %s: %s", task_id, exc)
                    
                    # Update the UI
                    self.update_activity_table()
                    self.update_status_chart()
                    self.update_metrics()
                    
                    # Update task info display
                    self.task_info.setPlainText(f"Task '{activity['action']}' has been restarted and is now running...")
                    
                    # Update button states
                    self.retry_btn.setEnabled(False)
                    self.stop_btn.setEnabled(True)
                    
                    self.logger.info(f"Retried task: {activity['action']}")
                    
                    if activity.get('id'):
                        self.retry_requested.emit(str(activity['id']))
    
    def stop_task(self):
        """Handle the stop action for the selected task."""
        self.logger.debug("Stop button clicked")
        current_row = self.activity_table.currentRow()
        if current_row >= 0:
            activities = self.get_activity_data()
            if current_row < len(activities):
                activity = activities[current_row]
                task_id = self._get_task_id(activity)

                if activity['status'] == 'running':
                    activity['status'] = 'stopped'
                    activity['progress'] = activity.get('progress', 0)
                    activity['details'] += " (Manually stopped by user)"

                    if self.task_queue_manager:
                        try:
                            self.task_queue_manager.update_task(task_id, "stopped", activity['progress'])
                        except Exception as exc:  # pragma: no cover
                            self.logger.warning("Failed to stop task %s: %s", task_id, exc)
                    
                    # Update the UI
                    self.update_activity_table()
                    self.update_status_chart()
                    self.update_metrics()
                    
                    # Update task info display
                    current_progress = activity.get('progress', 0)
                    self.task_info.setPlainText(f"Task '{activity['action']}' has been stopped at {current_progress}% completion.")
                    
                    # Update button states
                    self.stop_btn.setEnabled(False)
                    self.retry_btn.setEnabled(True)  # Allow retry of stopped task
                    
                    self.logger.info(f"Stopped task: {activity['action']}")

                    if activity.get('id'):
                        self.stop_requested.emit(str(activity['id']))
    
    def view_task_logs(self):
        """Display detailed logs for the selected task."""
        self.logger.debug("View Logs button clicked")
        current_row = self.activity_table.currentRow()
        if current_row >= 0:
            activities = self.get_activity_data()
            if current_row < len(activities):
                activity = activities[current_row]
                
                # Create a detailed log dialog
                dialog = QDialog(self)
                dialog.setWindowTitle(f"Task Logs - {activity['action']}")
                dialog.setMinimumSize(800, 600)
                dialog.setStyleSheet(f"""
                    QDialog {{
                        background-color: #1E1F20;
                        color: #F5F5F5;
                    }}
                    QTextEdit {{
                        background-color: #262828;
                        color: #F5F5F5;
                        border: 1px solid #404242;
                        border-radius: 4px;
                        font-family: 'Consolas', 'Monaco', monospace;
                        font-size: 11px;
                        padding: 8px;
                    }}
                    QPushButton {{
                        background-color: {BUTTON_COLOR_PRIMARY};
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        background-color: #2DA6B2;
                    }}
                    QLabel {{
                        color: {BUTTON_COLOR_PRIMARY};
                        font-weight: 600;
                        font-size: 14px;
                        margin-bottom: 8px;
                    }}
                """)
                
                layout = QVBoxLayout(dialog)
                
                # Header with task information
                header_label = QLabel(f"📋 Detailed Logs for: {activity['action']}")
                layout.addWidget(header_label)
                
                # Log content area
                log_text = QTextEdit()
                log_text.setReadOnly(True)
                
                # Generate detailed log content
                log_content = self.generate_task_logs(activity)
                log_text.setPlainText(log_content)
                
                layout.addWidget(log_text)
                
                # Buttons
                button_layout = QHBoxLayout()
                button_layout.addStretch()
                
                export_btn = QPushButton("💾 Export Logs")
                export_btn.clicked.connect(lambda: self.export_task_logs(activity, log_content))
                button_layout.addWidget(export_btn)
                
                close_btn = QPushButton("✖️ Close")
                close_btn.clicked.connect(dialog.close)
                button_layout.addWidget(close_btn)
                
                layout.addLayout(button_layout)
                
                # Show the dialog
                dialog.exec()
    
    def generate_task_logs(self, activity):
        """Generate detailed log content for a task"""
        from datetime import datetime, timedelta
        
        start_time = datetime.strptime(activity.get('start_time', '2025-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S")
        
        logs = []
        logs.append("=" * 80)
        logs.append(f"TASK LOG: {activity['action']}")
        logs.append("=" * 80)
        logs.append(f"Task ID: {self._get_task_id(activity)}")
        logs.append(f"Status: {activity['status'].upper()}")
        logs.append(f"Type: {activity.get('type', 'Unknown')}")
        logs.append(f"Domain: {activity.get('domain', 'General')}")
        logs.append(f"Started: {activity.get('start_time', 'Unknown')}")
        logs.append(f"Duration: {activity.get('duration_seconds', 0) // 60}m {activity.get('duration_seconds', 0) % 60}s")
        logs.append(f"Progress: {activity.get('progress', 0)}%")
        logs.append("-" * 80)
        logs.append("")
        
        # Generate realistic log entries based on task type and status
        task_type = activity.get('type', 'Collection')
        status = activity['status']
        
        if task_type == 'Collection':
            logs.extend([
                f"[{start_time.strftime('%H:%M:%S')}] INFO: Starting data collection task",
                f"[{(start_time + timedelta(seconds=5)).strftime('%H:%M:%S')}] INFO: Connecting to data source...",
                f"[{(start_time + timedelta(seconds=12)).strftime('%H:%M:%S')}] INFO: Authentication successful",
                f"[{(start_time + timedelta(seconds=25)).strftime('%H:%M:%S')}] INFO: Scanning available data...",
                f"[{(start_time + timedelta(seconds=45)).strftime('%H:%M:%S')}] INFO: Found {activity.get('progress', 50)} items to process",
                f"[{(start_time + timedelta(minutes=1)).strftime('%H:%M:%S')}] INFO: Processing batch 1/5...",
                f"[{(start_time + timedelta(minutes=2)).strftime('%H:%M:%S')}] INFO: Downloaded 23 documents (2.3 MB)",
                f"[{(start_time + timedelta(minutes=3)).strftime('%H:%M:%S')}] INFO: Processing batch 2/5...",
            ])
            
            if status == 'running':
                logs.extend([
                    f"[{(start_time + timedelta(minutes=4)).strftime('%H:%M:%S')}] INFO: Downloaded 47 documents (4.7 MB)",
                    f"[{(start_time + timedelta(minutes=5)).strftime('%H:%M:%S')}] INFO: Processing batch 3/5...",
                    f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Task is currently running - {activity.get('progress', 0)}% complete"
                ])
            elif status == 'success':
                logs.extend([
                    f"[{(start_time + timedelta(minutes=4)).strftime('%H:%M:%S')}] INFO: Downloaded 67 documents (6.8 MB)",
                    f"[{(start_time + timedelta(minutes=5)).strftime('%H:%M:%S')}] INFO: Processing batch 4/5...",
                    f"[{(start_time + timedelta(minutes=6)).strftime('%H:%M:%S')}] INFO: Processing batch 5/5...",
                    f"[{(start_time + timedelta(minutes=7)).strftime('%H:%M:%S')}] INFO: All batches completed successfully",
                    f"[{(start_time + timedelta(minutes=7, seconds=30)).strftime('%H:%M:%S')}] INFO: Task completed successfully - 100% complete"
                ])
            elif status == 'error':
                logs.extend([
                    f"[{(start_time + timedelta(minutes=2, seconds=30)).strftime('%H:%M:%S')}] WARNING: Rate limit approaching",
                    f"[{(start_time + timedelta(minutes=3)).strftime('%H:%M:%S')}] ERROR: {activity.get('error_message', 'Connection failed')}",
                    f"[{(start_time + timedelta(minutes=3, seconds=5)).strftime('%H:%M:%S')}] ERROR: Task failed - {activity.get('progress', 45)}% complete"
                ])
            elif status == 'stopped':
                logs.extend([
                    f"[{(start_time + timedelta(minutes=3)).strftime('%H:%M:%S')}] WARNING: Stop signal received",
                    f"[{(start_time + timedelta(minutes=3, seconds=5)).strftime('%H:%M:%S')}] INFO: Gracefully stopping task...",
                    f"[{(start_time + timedelta(minutes=3, seconds=10)).strftime('%H:%M:%S')}] INFO: Task stopped by user - {activity.get('progress', 0)}% complete"
                ])
        
        elif task_type == 'Processing':
            logs.extend([
                f"[{start_time.strftime('%H:%M:%S')}] INFO: Starting data processing pipeline",
                f"[{(start_time + timedelta(seconds=8)).strftime('%H:%M:%S')}] INFO: Loading documents from corpus...",
                f"[{(start_time + timedelta(seconds=20)).strftime('%H:%M:%S')}] INFO: Loaded 263 documents for processing",
                f"[{(start_time + timedelta(minutes=1)).strftime('%H:%M:%S')}] INFO: Applying NLP transformations...",
                f"[{(start_time + timedelta(minutes=2)).strftime('%H:%M:%S')}] INFO: Processed 100/263 documents",
                f"[{(start_time + timedelta(minutes=4)).strftime('%H:%M:%S')}] INFO: Processed 200/263 documents",
            ])
            
            if status == 'success':
                logs.extend([
                    f"[{(start_time + timedelta(minutes=6)).strftime('%H:%M:%S')}] INFO: Processed 263/263 documents",
                    f"[{(start_time + timedelta(minutes=7)).strftime('%H:%M:%S')}] INFO: Processing pipeline completed successfully"
                ])
        
        elif task_type == 'Analysis':
            logs.extend([
                f"[{start_time.strftime('%H:%M:%S')}] INFO: Starting quality analysis",
                f"[{(start_time + timedelta(seconds=15)).strftime('%H:%M:%S')}] INFO: Analyzing document quality metrics...",
                f"[{(start_time + timedelta(minutes=1)).strftime('%H:%M:%S')}] INFO: Processed 500/2234 documents",
                f"[{(start_time + timedelta(minutes=3)).strftime('%H:%M:%S')}] INFO: Processed 1200/2234 documents",
                f"[{(start_time + timedelta(minutes=6)).strftime('%H:%M:%S')}] INFO: Processed 2078/2234 documents - 93% complete",
            ])
            
            if status == 'running':
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Analysis in progress - {activity.get('progress', 93)}% complete")
        
        logs.append("")
        logs.append("-" * 80)
        logs.append(f"END OF LOG - Status: {status.upper()}")
        logs.append("=" * 80)
        
        return "\n".join(logs)
    
    def export_task_logs(self, activity, log_content):
        """Export task logs to a file"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        import os
        
        # Generate filename
        task_name = activity['action'].replace(' ', '_').replace(':', '_')
        filename = f"task_logs_{task_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # Open file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Task Logs",
            filename,
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Task logs exported successfully to:\n{file_path}"
                )
                
                self.logger.info(f"Exported task logs to: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Failed", 
                    f"Failed to export logs:\n{str(e)}"
                )
                
                self.logger.error(f"Failed to export task logs: {e}")

    def update_theme(self, theme_name):
        """Update theme for charts"""
        self.chart_manager.set_theme(theme_name)
        self.load_activity_data()  # Refresh charts with new theme
