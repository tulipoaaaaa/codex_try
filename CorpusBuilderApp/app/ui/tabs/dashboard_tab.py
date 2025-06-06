"""
Dashboard Tab for CryptoFinance Corpus Builder
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                            QLabel, QProgressBar, QFrame, QSplitter, QPushButton,
                            QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, QTimer, Signal as pyqtSignal, Slot as pyqtSlot, QSize, QThread
from PySide6.QtGui import QColor, QIcon, QFont
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

import logging
from pathlib import Path
import time
from datetime import datetime, timedelta
import math
import json
import threading

# Import UI components
from app.ui.widgets.corpus_statistics import CorpusStatistics
from app.ui.widgets.activity_log import ActivityLog
from app.ui.widgets.domain_distribution import DomainDistribution
from app.ui.widgets.active_operations import ActiveOperations
from app.ui.widgets.recent_activity import RecentActivity
from app.ui.theme.theme_constants import (
    DEFAULT_FONT_SIZE,
    CARD_MARGIN,
    BUTTON_COLOR_PRIMARY,
    BUTTON_COLOR_DANGER,
    BUTTON_COLOR_GRAY,
)
# from ..widgets.storage_usage import StorageUsageWidget

class DashboardTab(QWidget):
    """Dashboard Tab with overview of corpus and activities"""
    
    update_needed = pyqtSignal()
    view_all_activity_requested = pyqtSignal()  # Signal to request full activity tab
    
    def __init__(self, project_config, parent=None):
        print(f"DEBUG: DashboardTab received config type: {type(project_config)}")
        print(f"DEBUG: DashboardTab received config value: {project_config}")
        super().__init__(parent)
        self.config = project_config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setFont(QFont("", DEFAULT_FONT_SIZE))
        
        # UI setup
        self.init_ui()
        
        # Setup periodic update timer
        self.setup_update_timer()
        
        # Initial data load
        self.load_data()
    
    def init_ui(self):
        """Completely refactor the dashboard layout to a true two-column grid with large, prominent cards and correct space usage."""
        # --- Instantiate all widgets first (do not break logic) ---
        self.corpus_stats_widget = CorpusStatistics(self.config)
        self.corpus_stats_widget.setObjectName("card")
        self.domain_distribution_widget = DomainDistribution(self.config)
        self.domain_distribution_widget.setObjectName("card")
        self.active_operations_widget = ActiveOperations(self.config)
        self.active_operations_widget.setObjectName("card")
        self.recent_activity_widget = RecentActivity(self.config)
        self.recent_activity_widget.setObjectName("card")
        self.activity_log_widget = ActivityLog(self.config)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(CARD_MARGIN * 2, CARD_MARGIN * 2, CARD_MARGIN * 2, CARD_MARGIN * 2)
        main_layout.setSpacing(CARD_MARGIN * 2)

        # Header
        header_label = QLabel("Corpus Overview Dashboard")
        header_label.setObjectName("dashboard-header")
        header_label.setStyleSheet(
            f"font-size: {DEFAULT_FONT_SIZE * 2 + 4}px; font-weight: 800; color: #fff; letter-spacing: -0.025em; margin-bottom: 2px;"
        )
        header_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        main_layout.addWidget(header_label)

        subtitle_label = QLabel("Real-time monitoring and analytics for your document corpus")
        subtitle_label.setStyleSheet(
            f"font-size: {DEFAULT_FONT_SIZE + 4}px; color: #9ca3af; font-weight: 400; margin-bottom: 12px;"
        )
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        main_layout.addWidget(subtitle_label)

        # --- True two-column grid layout ---
        grid = QGridLayout()
        grid.setSpacing(CARD_MARGIN * 2)
        grid.setContentsMargins(0, 0, 0, 0)

        # Left column (stats bar, chart card)
        left_col = QVBoxLayout()
        left_col.setSpacing(CARD_MARGIN * 2)
        left_col.setContentsMargins(0, 0, 0, 0)

        # Stats bar (horizontal row of stat cards, large and bold)
        stats_bar = QHBoxLayout()
        stats_bar.setSpacing(CARD_PADDING)
        stats_bar.setContentsMargins(0, 0, 0, 0)
        stats = self.corpus_stats_widget.get_dashboard_stats() if hasattr(self.corpus_stats_widget, 'get_dashboard_stats') else [
            {"value": "2,570", "label": "Total Documents", "unit": "", "objectName": "stat-docs"},
            {"value": "0.08", "label": "Total Size", "unit": "GB", "objectName": "stat-size"},
            {"value": "678", "label": "Active Domains", "unit": "", "objectName": "stat-domains"},
            {"value": "2.5%", "label": "Storage Usage", "unit": "", "objectName": "stat-usage"},
            {"value": "3", "label": "Running Operations", "unit": "", "objectName": "stat-ops"},
        ]
        for stat in stats:
            card = QWidget()
            card.setObjectName("stat-card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(
                CARD_PADDING + CARD_MARGIN // 2,
                CARD_PADDING + CARD_MARGIN // 4,
                CARD_PADDING + CARD_MARGIN // 2,
                CARD_PADDING + CARD_MARGIN // 4,
            )
            card_layout.setSpacing(6)
            value_label = QLabel(stat["value"])
            value_label.setObjectName("stat-value")
            value_label.setStyleSheet("font-size: 36px; font-weight: 800; color: #06b6d4;")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(value_label)
            if stat["unit"]:
                unit_label = QLabel(stat["unit"])
                unit_label.setObjectName("stat-unit")
                unit_label.setStyleSheet("font-size: 20px; color: #d1d5db; font-weight: 600;")
                unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                card_layout.addWidget(unit_label)
            label_label = QLabel(stat["label"])
            label_label.setObjectName("stat-label")
            label_label.setStyleSheet("font-size: 15px; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 700;")
            label_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(label_label)
            card.setMinimumWidth(220)
            card.setMaximumWidth(260)
            stats_bar.addWidget(card)
        left_col.addLayout(stats_bar)

        # Chart card (centered chart, summary below)
        chart_card = QWidget()
        chart_card.setObjectName("card")
        chart_card.setStyleSheet("background-color: #1a1f2e; border-radius: 16px; border: 1.5px solid #2d3748; padding: 32px 32px 24px 32px;")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setSpacing(CARD_PADDING)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        chart_layout.addWidget(self.domain_distribution_widget, 1)
        left_col.addWidget(chart_card, 2)

        grid.addLayout(left_col, 0, 0)

        # Right column (sidebar: operations, activity)
        right_col = QVBoxLayout()
        right_col.setSpacing(CARD_MARGIN * 2)
        right_col.setContentsMargins(0, 0, 0, 0)
        self.active_operations_widget.setMinimumWidth(420)
        self.active_operations_widget.setMaximumWidth(520)
        self.recent_activity_widget.setMinimumWidth(420)
        self.recent_activity_widget.setMaximumWidth(520)
        right_col.addWidget(self.active_operations_widget)
        right_col.addWidget(self.recent_activity_widget)
        grid.addLayout(right_col, 0, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        main_layout.addLayout(grid, 1)

        # Legacy activity log (hidden by default, accessible via View All)
        self.activity_log_widget.hide()

        # Connect signals
        self.update_needed.connect(self.on_update_needed)
        self.recent_activity_widget.activity_clicked.connect(self.handle_activity_click)
        self.recent_activity_widget.view_all_requested.connect(self.handle_view_all_request)
    
    def setup_update_timer(self):
        """Setup timer for periodic updates"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(30000)  # Update every 30 seconds
    
    def load_data(self):
        """Load initial data for dashboard"""
        try:
            # Load corpus statistics
            corpus_stats = self.get_corpus_statistics()
            self.corpus_stats_widget.update_statistics(corpus_stats)
            
            # Load storage usage
            storage_usage = self.get_storage_usage()
            # self.storage_usage_widget.update_storage_usage(storage_usage)
            
            # Load domain distribution
            domain_distribution = self.get_domain_distribution()
            self.domain_distribution_widget.update_distribution_data(domain_distribution)
            
            # Load activity log
            activity_log = self.get_activity_log()
            self.activity_log_widget.update_activity_log(activity_log)
            
            self.logger.info("Dashboard data loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading dashboard data: {e}")
    
    def update_data(self):
        """Update dashboard data"""
        # Emit signal to update data in the UI thread
        self.update_needed.emit()
    
    @pyqtSlot()
    def on_update_needed(self):
        """Handle update signal"""
        try:
            # Update corpus statistics
            corpus_stats = self.get_corpus_statistics()
            self.corpus_stats_widget.update_statistics(corpus_stats)
            
            # Update storage usage
            storage_usage = self.get_storage_usage()
            # self.storage_usage_widget.update_storage_usage(storage_usage)
            
            # Update domain distribution
            domain_distribution = self.get_domain_distribution()
            self.domain_distribution_widget.update_distribution_data(domain_distribution)
            
            # Update activity log
            activity_log = self.get_activity_log()
            self.activity_log_widget.update_activity_log(activity_log)
            
            # Note: Active Operations and Recent Activity have their own auto-refresh timers
            # so they don't need manual updates here
            
        except Exception as e:
            self.logger.error(f"Error updating dashboard data: {e}")
    
    def handle_activity_click(self, activity):
        """Handle when an activity item is clicked"""
        # This could show a detailed view or switch to the full activity log
        self.logger.info(f"Activity clicked: {activity.get('action', 'Unknown')}")
        # For now, just log it - could be extended to show details dialog
    
    def handle_view_all_request(self):
        """Handle when View All is requested from Recent Activity"""
        self.logger.info("View All activity requested from dashboard")
        self.view_all_activity_requested.emit()
    
    def get_corpus_statistics(self):
        """Get corpus statistics"""
        # In a production app, this would query the actual corpus
        # For now, we'll return mock data for demonstration
        return {
            "total_documents": 2570,
            "total_size_gb": 45.8,
            "processed_documents": 2234,
            "pending_processing": 336,
            "average_quality": 0.82,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def get_storage_usage(self):
        """Get storage usage statistics"""
        # In a production app, this would query the actual disk usage
        # For now, we'll return mock data for demonstration
        return {
            "total_space_gb": 100.0,
            "used_space_gb": 45.8,
            "free_space_gb": 54.2,
            "usage_by_type": {
                "PDF": 32.5,
                "HTML": 8.2,
                "Code": 3.6,
                "Other": 1.5
            }
        }
    
    def get_domain_distribution(self):
        """Get domain distribution statistics"""
        # In a production app, this would query the actual domain distribution
        # For now, we'll return mock data for demonstration
        return {
            "Crypto Derivatives": {"allocation": 0.20, "current": 0.18, "documents": 456, "quality": 0.85},
            "DeFi": {"allocation": 0.12, "current": 0.15, "documents": 289, "quality": 0.82},
            "High Frequency Trading": {"allocation": 0.15, "current": 0.13, "documents": 378, "quality": 0.88},
            "Market Microstructure": {"allocation": 0.15, "current": 0.16, "documents": 423, "quality": 0.79},
            "Portfolio Construction": {"allocation": 0.10, "current": 0.09, "documents": 234, "quality": 0.76},
            "Regulation & Compliance": {"allocation": 0.05, "current": 0.04, "documents": 145, "quality": 0.91},
            "Risk Management": {"allocation": 0.15, "current": 0.17, "documents": 467, "quality": 0.83},
            "Valuation Models": {"allocation": 0.08, "current": 0.08, "documents": 178, "quality": 0.77},
        }
    
    def get_activity_log(self):
        """Get recent activity log"""
        # In a production app, this would query the actual activity log
        # For now, we'll return mock data for demonstration
        
        # Get current time for more realistic timestamps
        now = datetime.now()
        
        return [
            {"time": (now - timedelta(minutes=2)).strftime("%H:%M"), 
             "action": "GitHub collection started", 
             "status": "running"},
            {"time": (now - timedelta(minutes=15)).strftime("%H:%M"), 
             "action": "PDF processing completed", 
             "status": "success", 
             "details": "45 files processed"},
            {"time": (now - timedelta(minutes=30)).strftime("%H:%M"), 
             "action": "arXiv collection completed", 
             "status": "success", 
             "details": "23 papers collected"},
            {"time": (now - timedelta(minutes=47)).strftime("%H:%M"), 
             "action": "ISDA collection completed", 
             "status": "success", 
             "details": "12 documents collected"},
            {"time": (now - timedelta(minutes=63)).strftime("%H:%M"), 
             "action": "Domain rebalancing started", 
             "status": "success",
             "details": "8 domains rebalanced"}
        ]
