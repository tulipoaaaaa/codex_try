"""Simple dashboard tab showing live metrics and corpus stats."""


from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QFrame,
    QProgressBar,
)
from PySide6.QtCore import Qt, Signal, QMargins
from PySide6.QtGui import QColor, QPainter
import sys
from PySide6.QtCharts import QChart, QChartView, QPieSeries
from datetime import datetime
from app.ui.widgets.card_wrapper import CardWrapper
from app.ui.widgets.section_header import SectionHeader
from app.ui.widgets.recent_activity import RecentActivity
from app.ui.widgets.activity_log import ActivityLog
from app.ui.theme.theme_constants import (
    BUTTON_COLOR_PRIMARY,
    CARD_BORDER_COLOR,
)
from shared_tools.services.corpus_stats_service import CorpusStatsService
from app.ui.utils.ui_helpers import create_styled_progress_bar
from shared_tools.services.task_queue_manager import TaskQueueManager
from shared_tools.services.system_monitor import SystemMonitor
from shared_tools.services.dependency_update_service import DependencyUpdateService
from app.helpers.notifier import Notifier
from app.ui.widgets.active_operations import ActiveOperationsWidget
import os

ICON_PATH = os.path.join(os.path.dirname(__file__), '../../resources/icons')

class DashboardTab(QWidget):
    """Dashboard displaying high level metrics for the corpus."""

    view_all_activity_requested = Signal()
    rebalance_requested = Signal()

    def __init__(self, project_config, activity_log_service=None, task_history_service=None, task_queue_manager=None, parent=None):
        super().__init__(parent)
        self.config = project_config
        self.activity_log_service = activity_log_service
        self.metric_labels = {}
        self.stats_service = CorpusStatsService(project_config)
        self.task_history_service = task_history_service
        self.task_queue_manager = task_queue_manager or TaskQueueManager()
        self.task_queue_manager.queue_counts_changed.connect(self.update_queue_counts)
        self.task_queue_manager.task_progress.connect(self.update_task_progress)
        self._task_bars: dict[str, QProgressBar] = {}
        self.dependency_update_service = DependencyUpdateService()
        self.dependency_update_service.dependency_update_progress.connect(
            self.on_dependency_update_progress
        )
        self.dependency_update_service.dependency_update_completed.connect(
            self.on_dependency_update_completed
        )
        self.dependency_update_service.dependency_update_failed.connect(
            self.on_dependency_update_failed
        )
        self.system_monitor = SystemMonitor()
        self.system_monitor.system_metrics.connect(self.update_system_metrics)
        self.system_monitor.start()
        self._init_ui()
        self.fix_all_label_backgrounds()
        self.stats_service.stats_updated.connect(self.update_overview_metrics)
        self.stats_service.stats_updated.connect(lambda *_: self.update_environment_info())
        self.load_data()
        self.stats_service.refresh_stats()

        if self.task_history_service:
            self.task_history_service.task_added.connect(lambda *_: self.load_data())
            self.task_history_service.task_updated.connect(lambda *_: self.load_data())

        if self.activity_log_service:
            self.activity_log_service.activity_added.connect(
                self.recent_activity_widget.add_activity
            )
            self.activity_log_service.activity_added.connect(
                lambda e: self.activity_log_widget.add_activity(
                    e.get("source", "Info"), e.get("message", ""), e.get("details")
                )
            )

    def _init_ui(self):
        self.setStyleSheet("QWidget, QFrame, QGroupBox { background-color: #0f1419; }")
        container = QWidget()
        container.setStyleSheet("background-color: #0f1419;")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(24, 16, 24, 16)
        main_layout.setSpacing(12)

        # --- Header Section ---
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(24, 16, 24, 4)
        header_row = QHBoxLayout()
        title_label = SectionHeader('📊 Corpus Overview Dashboard')
        header_row.addWidget(title_label)
        header_row.addStretch()
        health_indicator = self.create_system_health_indicator()
        header_row.addWidget(health_indicator)
        header_layout.addLayout(header_row)
        subtitle_label = QLabel('Real-time monitoring and analytics for your document corpus')
        subtitle_label.setStyleSheet('background-color: transparent; font-size: 14px; color: #9ca3af; margin-bottom: 6px;')
        header_layout.addWidget(subtitle_label)
        main_layout.addLayout(header_layout)

        # --- Metrics Bar ---
        metrics_bar = QHBoxLayout()
        metrics_bar.setSpacing(32)
        metrics_bar.setContentsMargins(0, 4, 0, 12)
        summary = self.stats_service.get_summary()
        stat_data = [
            {"value": summary.get("total_files", 0), "label": "Total Docs", "unit": ""},
            {"value": f"{summary.get('total_size_mb', 0):.2f}", "label": "Total Size", "unit": "MB"},
            {"value": summary.get("active_domains", 0), "label": "Active Domains", "unit": ""},
            {"value": summary.get("total_tokens", 0), "label": "Total Tokens", "unit": ""},
        ]
        for stat in stat_data:
            card, _ = self.fix_metric_card_transparency(stat["label"], stat["value"], stat["unit"])
            metrics_bar.addWidget(card)
        main_layout.addLayout(metrics_bar)

        # --- Main 3-Column Layout ---
        columns = QHBoxLayout()
        columns.setSpacing(20)
        # Left (30%)
        left_col = self.create_enhanced_left_column()
        columns.addLayout(left_col, 30)
        # Center (45%)
        center_col = QVBoxLayout()
        center_col.setSpacing(12)
        # Active Operations
        active_card = CardWrapper()
        active_card.setObjectName("active-operations")
        active_card.setStyleSheet(f"""
            QFrame[objectName="active-operations"] {{
                background-color: #1a1f2e;
                border: 1px solid {CARD_BORDER_COLOR};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        active_layout = active_card.body_layout
        active_layout.setContentsMargins(16, 8, 16, 16)
        active_layout.setSpacing(8)
        self.active_operations = ActiveOperationsWidget(
            task_queue_manager=self.task_queue_manager
        )
        active_layout.addWidget(self.active_operations)
        center_col.addWidget(active_card)
        # Enhanced Task Queue
        center_col.addWidget(self.create_refined_task_queue())
        # Performance Metrics
        center_col.addWidget(self.create_horizontal_performance_metrics())
        columns.addLayout(center_col, 45)
        # Right (25%)
        right_col = self.create_reorganized_right_side()
        columns.addLayout(right_col, 25)

        main_layout.addLayout(columns)
        self.activity_log_widget = ActivityLog(self.config)
        self.activity_log_widget.hide()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)
        self.setLayout(layout)

    def create_system_health_indicator(self):
        dot = QLabel()
        dot.setObjectName('health-indicator')
        dot.setFixedSize(14, 14)
        dot.setStyleSheet('background-color: #22c55e; border-radius: 7px;')
        return dot

    def fix_metric_card_transparency(self, title, value, unit=''):
        metric_widget = QWidget()
        metric_widget.setStyleSheet('background-color: transparent; border: none;')
        metric_layout = QVBoxLayout(metric_widget)
        metric_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        metric_layout.setSpacing(4)
        metric_layout.setContentsMargins(16, 16, 16, 16)
        
        if unit:
            value_unit_container = QWidget()
            value_unit_container.setStyleSheet('background-color: transparent;')
            value_unit_layout = QHBoxLayout(value_unit_container)
            value_unit_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value_unit_layout.setSpacing(4)
            value_unit_layout.setContentsMargins(0, 0, 0, 0)
            value_label = QLabel(str(value))
            value_label.setStyleSheet(
                f'font-size: 28px; color: {BUTTON_COLOR_PRIMARY}; font-weight: 700; background-color: transparent;'
            )
            unit_label = QLabel(unit)
            unit_label.setStyleSheet('font-size: 16px; color: #C5C7C7; font-weight: 500; background-color: transparent; margin-top: 8px;')
            value_unit_layout.addWidget(value_label)
            value_unit_layout.addWidget(unit_label)
            metric_layout.addWidget(value_unit_container)
        else:
            value_label = QLabel(str(value))
            value_label.setStyleSheet(
                f'font-size: 28px; color: {BUTTON_COLOR_PRIMARY}; font-weight: 700; text-align: center; background-color: transparent;'
            )
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            metric_layout.addWidget(value_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet('font-size: 14px; color: #C5C7C7; font-weight: 600; text-align: center; background-color: transparent;')
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        metric_layout.addWidget(title_label)

        # keep reference to update later
        self.metric_labels[title] = value_label
        return metric_widget, value_label

    def create_giant_pie_chart(self, domain_data):
        from PySide6.QtCore import Qt
        chart = QChart()
        chart.setBackgroundBrush(QColor('transparent'))
        chart.setMargins(QMargins(0, 0, 0, 0))
        colors = ['#22c55e', '#32B8C6', '#E68161', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#9ca3af']
        series = QPieSeries()
        for i, (domain, percentage) in enumerate(domain_data.items()):
            slice_obj = series.append(f'{domain[:12]}', percentage)
            color = colors[i % len(colors)]
            slice_obj.setBrush(QColor(color))
            slice_obj.setBorderColor(QColor('#1a1f2e'))
            slice_obj.setBorderWidth(2)
            slice_obj.setLabelVisible(False)
        chart.addSeries(series)
        chart.setTitle('')
        chart.legend().setVisible(False)
        chart_view = QChartView(chart)
        chart_view.setFixedSize(300, 300)
        chart_view.setStyleSheet('background-color: transparent; border: none;')
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_container = QWidget()
        chart_container.setStyleSheet('background-color: transparent;')
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_layout.setContentsMargins(10, 10, 10, 10)
        chart_layout.addWidget(chart_view)
        return chart_container

    def create_enhanced_system_status(self):
        container = QFrame()
        container.setObjectName('system-status-narrow')
        container.setStyleSheet(f'''
            QFrame[objectName="system-status-narrow"] {{
                background-color: #1a1f2e;
                border: 1px solid {CARD_BORDER_COLOR};
                border-radius: 12px;
                padding: 16px;
            }}
        ''')
        layout = QVBoxLayout(container)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)
        header = SectionHeader('🖥️ System Status')
        layout.addWidget(header)
        resources = [
            ('CPU', 'cpu_bar', 'cpu_percent', '#32B8C6'),
            ('RAM', 'ram_bar', 'ram_percent', '#E68161'),
            ('Disk', 'disk_bar', 'disk_percent', '#22c55e'),
        ]
        for label, bar_attr, percent_attr, color in resources:
            resource_container = QWidget()
            resource_container.setStyleSheet('background-color: transparent;')
            resource_layout = QHBoxLayout(resource_container)
            resource_layout.setContentsMargins(0, 2, 0, 2)
            resource_layout.setSpacing(8)
            label_widget = QLabel(label)
            label_widget.setFixedWidth(35)
            label_widget.setStyleSheet('color: #f9fafb; font-size: 12px; background-color: transparent;')
            progress_bar = create_styled_progress_bar(0, color, height=6)
            progress_bar.setFixedWidth(80)
            percent_label = QLabel('0%')
            percent_label.setStyleSheet('color: #f9fafb; font-size: 12px; font-weight: 600; background-color: transparent;')
            percent_label.setFixedWidth(30)
            resource_layout.addWidget(label_widget)
            resource_layout.addWidget(progress_bar)
            resource_layout.addWidget(percent_label)
            layout.addWidget(resource_container)
            setattr(self, bar_attr, progress_bar)
            setattr(self, percent_attr, percent_label)
        uptime_label = QLabel('Uptime: 2h 14m')
        uptime_label.setStyleSheet('color: #9ca3af; font-size: 10px; background-color: transparent; margin-top: 4px;')
        layout.addWidget(uptime_label)
        return container

    def create_enhanced_alerts(self):
        container = QFrame()
        container.setObjectName('alerts-narrow')
        container.setMinimumWidth(140)
        container.setStyleSheet(f'''
            QFrame[objectName="alerts-narrow"] {{
                background-color: #1a1f2e;
                border: 1px solid {CARD_BORDER_COLOR};
                border-radius: 12px;
                padding: 16px;
            }}
        ''')
        layout = QVBoxLayout(container)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)
        header = SectionHeader('🔔 Alerts')
        layout.addWidget(header)
        alerts = [('⚠️', 'Storage > 90%', '#E68161'), ('ℹ️', 'Update available', '#32B8C6'), ('✅', 'Backup current', '#22c55e')]
        for icon, text, color in alerts:
            alert_container = QWidget()
            alert_container.setStyleSheet('background-color: transparent;')
            alert_layout = QHBoxLayout(alert_container)
            alert_layout.setContentsMargins(0, 2, 0, 2)
            alert_layout.setSpacing(6)
            icon_label = QLabel(icon)
            icon_label.setFixedSize(12, 12)
            icon_label.setStyleSheet('background-color: transparent;')
            text_label = QLabel(text)
            text_label.setStyleSheet(f'color: {color}; font-size: 11px; background-color: transparent;')
            text_label.setWordWrap(True)
            alert_layout.addWidget(icon_label)
            alert_layout.addWidget(text_label)
            layout.addWidget(alert_container)
        return container

    def create_working_scrollable_activity(self):
        container = QFrame()
        container.setObjectName('recent-activity-tall')
        container.setStyleSheet(f'''
            QFrame[objectName="recent-activity-tall"] {{
                background-color: #1a1f2e;
                border: 1px solid {CARD_BORDER_COLOR};
                border-radius: 12px;
                padding: 16px;
            }}
        ''')
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(0, 0, 0, 0)
        header = SectionHeader('📋 Recent Activity')
        main_layout.addWidget(header)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(
            f'''
            QScrollArea {{ border: none; background-color: transparent; }}
            QScrollBar:vertical {{ background-color: {CARD_BORDER_COLOR}; width: 6px; border-radius: 3px; }}
            QScrollBar::handle:vertical {{ background-color: {BUTTON_COLOR_PRIMARY}; border-radius: 3px; min-height: 20px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ border: none; background: none; }}
        '''
        )
        content_widget = QWidget()
        content_widget.setStyleSheet('background-color: transparent;')
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(6)
        content_layout.setContentsMargins(20, 4, 0, 0)
        activities = [
            ('12:00', 'Document added', 'success'),
            ('11:45', 'Processor run', 'success'),
            ('11:30', 'Error occurred', 'error'),
            ('11:15', 'Backup complete', 'success'),
            ('11:00', 'Collection started', 'running'),
            ('10:45', 'Analysis finished', 'success'),
            ('10:30', 'Warning resolved', 'warning'),
            ('10:15', 'System updated', 'success'),
            ('10:00', 'Maintenance done', 'success'),
            ('09:45', 'Data validated', 'success'),
            ('09:30', 'Backup started', 'running'),
            ('09:15', 'Cache cleared', 'success')
        ]
        for time, text, status in activities:
            activity_item = self.create_centered_activity_item(time, text, status)
            content_layout.addWidget(activity_item)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        # Expose the button for testing and proper signal emission
        self.view_all_btn = QPushButton('View All Activity')
        self.view_all_btn.setStyleSheet(
            f'background-color: {CARD_BORDER_COLOR}; color: {BUTTON_COLOR_PRIMARY}; border: none; border-radius: 4px; padding: 6px 12px; font-size: 11px;'
        )
        self.view_all_btn.clicked.connect(lambda: self.view_all_activity_requested.emit())
        button_layout.addWidget(self.view_all_btn)
        main_layout.addLayout(button_layout)
        return container

    def create_enhanced_performance_metrics(self):
        container = self.create_card_with_styling('📈 Performance Metrics', 'performance-metrics')
        metrics_layout = QVBoxLayout()
        metrics_layout.setSpacing(4)
        metrics_layout.setContentsMargins(0, 4, 0, 0)
        metrics = [
            ('Avg Speed', '45.2 MB/s', '#32B8C6'),
            ('Success Rate', '94.2%', '#22c55e'),
            ('Docs Today', '2,847', '#8b5cf6'),
            ('Queue Length', '12', '#E68161'),
            ('Uptime', '2h 14m', '#f59e0b'),
            ('Storage Growth', '+1.2GB', '#06b6d4')
        ]
        for label, value, color in metrics:
            metric_container = QWidget()
            metric_layout = QHBoxLayout(metric_container)
            metric_layout.setContentsMargins(0, 2, 0, 2)
            metric_layout.setSpacing(12)
            label_widget = QLabel(f'{label}:')
            label_widget.setStyleSheet('color: #C5C7C7; font-size: 11px; font-weight: 500; background-color: transparent;')
            value_widget = QLabel(value)
            value_widget.setStyleSheet(f'color: {color}; font-size: 11px; font-weight: 600; background-color: transparent;')
            metric_layout.addWidget(label_widget)
            metric_layout.addStretch()
            metric_layout.addWidget(value_widget)
            metrics_layout.addWidget(metric_container)
        container.body_layout.addLayout(metrics_layout)
        return container

    def create_enhanced_task_queue(self):
        container = self.create_card_with_styling('📋 Task Queue', 'task-queue-enhanced')
        main_layout = QVBoxLayout()
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(0, 4, 0, 0)
        tasks_label = QLabel('Running Tasks:')
        tasks_label.setStyleSheet('color: #C5C7C7; font-size: 11px; font-weight: 600; background-color: transparent; margin-bottom: 4px;')
        main_layout.addWidget(tasks_label)
        tasks = [
            ('GitHub Collector', 67, '#32B8C6'),
            ('PDF Processor', 89, '#22c55e')
        ]
        for task_name, progress, color in tasks:
            task_container = QWidget()
            task_layout = QVBoxLayout(task_container)
            task_layout.setSpacing(2)
            name_label = QLabel(task_name)
            name_label.setStyleSheet('color: #f9fafb; font-size: 10px; background-color: transparent;')
            progress_bar = create_styled_progress_bar(progress, color, height=4)
            task_layout.addWidget(name_label)
            task_layout.addWidget(progress_bar)
            main_layout.addWidget(task_container)
        stats_label = QLabel('Queue Stats:')
        stats_label.setStyleSheet('color: #C5C7C7; font-size: 11px; font-weight: 600; background-color: transparent; margin-top: 8px; margin-bottom: 4px;')
        main_layout.addWidget(stats_label)
        stats = [('⏳ Pending', '12', '#32B8C6'), ('🔄 Retry', '2', '#E68161'), ('❌ Failed', '1', '#ef4444')]
        for icon_label, count, color in stats:
            stat_container = QWidget()
            stat_layout = QHBoxLayout(stat_container)
            stat_layout.setContentsMargins(0, 1, 0, 1)
            stat_layout.setSpacing(8)
            label_widget = QLabel(icon_label)
            label_widget.setStyleSheet('color: #C5C7C7; font-size: 10px; background-color: transparent;')
            count_widget = QLabel(count)
            count_widget.setStyleSheet(f'color: {color}; font-size: 10px; font-weight: 600; background-color: transparent;')
            stat_layout.addWidget(label_widget)
            stat_layout.addStretch()
            stat_layout.addWidget(count_widget)
            main_layout.addWidget(stat_container)
        container.body_layout.addLayout(main_layout)
        return container

    def create_centered_activity_item(self, time, text, status):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        time_label = QLabel(time)
        time_label.setFixedWidth(40)
        time_label.setStyleSheet("background-color: transparent; font-size: 12px; color: #9ca3af;")
        layout.addWidget(time_label)
        if status == "success":
            color = "#22c55e"
        elif status == "error":
            color = "#ef4444"
        elif status == "warning":
            color = "#f59e0b"
        elif status == "running":
            color = BUTTON_COLOR_PRIMARY
        else:
            color = "#9ca3af"
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color}; font-size: 12px; background-color: transparent;")
        dot.setFixedWidth(12)
        dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(dot)
        text_label = QLabel(text)
        text_label.setStyleSheet("background-color: transparent; font-size: 14px; color: #f9fafb;")
        layout.addWidget(text_label)
        layout.addStretch()
        return row

    def create_enhanced_left_column(self):
        left_column = QVBoxLayout()
        left_column.setSpacing(12)
        quick_actions_card = self.create_styled_quick_actions()
        left_column.addWidget(quick_actions_card)
        domain_summary_card = self.create_corrected_domain_summary()
        left_column.addWidget(domain_summary_card)
        bottom_row_layout = QHBoxLayout()
        bottom_row_layout.setSpacing(16)
        corpus_health_card = self.create_corpus_health_widget()
        corpus_health_card.setMaximumWidth(200)
        quick_stats_card = self.create_wider_quick_stats()
        quick_stats_card.setMaximumWidth(240)
        bottom_row_layout.addWidget(corpus_health_card)
        bottom_row_layout.addWidget(quick_stats_card)
        left_column.addLayout(bottom_row_layout)
        return left_column

    def create_styled_quick_actions(self):
        quick_actions_card = CardWrapper()
        quick_actions_card.setObjectName('quick-actions')
        quick_actions_card.setStyleSheet(f"""
            QFrame[objectName="quick-actions"] {{
                background-color: #1a1f2e;
                border: 1px solid {CARD_BORDER_COLOR};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        quick_actions_layout = quick_actions_card.body_layout
        quick_actions_layout.setContentsMargins(16, 16, 16, 16)
        quick_actions_layout.setSpacing(8)
        quick_actions_header = SectionHeader("Quick Actions")
        quick_actions_header.setStyleSheet("font-size: 16px; font-weight: 600; color: #fff;")
        quick_actions_layout.addWidget(quick_actions_header)
        for text, slot in [
            ("Optimize Corpus", self.start_corpus_optimization),
            ("Run All Collectors", self.start_all_collectors),
            ("Export Report", self.export_report),
            ("Update Dependencies", self.update_dependencies),
        ]:
            btn = QPushButton(text)
            btn.setObjectName("action-btn")
            btn.setStyleSheet(f"""
                QPushButton[objectName="action-btn"] {{
                    background-color: {BUTTON_COLOR_PRIMARY};
                    color: white;
                    border: none;
                    border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 12px 16px;
                }}
                QPushButton[objectName="action-btn"]:hover {{
                    background-color: #2DA6B2;
                    transform: translateY(-1px);
                }}
                QPushButton[objectName="action-btn"]:pressed {{
                    background-color: #248995;
                }}
            """)
            btn.setFixedHeight(40)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(slot)
            quick_actions_layout.addWidget(btn)

        # Rebalance Now quick action
        self.rebalance_now_btn = QPushButton("Rebalance Now")
        self.rebalance_now_btn.setObjectName("action-btn")
        self.rebalance_now_btn.setStyleSheet(f"""
                QPushButton[objectName="action-btn"] {{
                    background-color: {BUTTON_COLOR_PRIMARY};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    padding: 12px 16px;
                }}
                QPushButton[objectName="action-btn"]:hover {{
                    background-color: #2DA6B2;
                    transform: translateY(-1px);
                }}
                QPushButton[objectName="action-btn"]:pressed {{
                    background-color: #248995;
                }}
            """)
        self.rebalance_now_btn.setFixedHeight(40)
        self.rebalance_now_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.rebalance_now_btn.clicked.connect(self.rebalance_requested.emit)
        quick_actions_layout.addWidget(self.rebalance_now_btn)
        return quick_actions_card

    def create_corpus_health_widget(self):
        container = CardWrapper('⚖️ Corpus Health')
        container.setObjectName('corpus-health')
        container.setStyleSheet(f"""
            QFrame[objectName="corpus-health"] {{
                background-color: #1a1f2e;
                border: 1px solid {CARD_BORDER_COLOR};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        layout = container.body_layout
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        health_items = [
            ('Balance', 'Optimal', '#22c55e', '⚖️'),
            ('Quality', '94.2%', '#32B8C6', '📊'),
            ('Cleanliness', 'Clean', '#22c55e', '🧹')
        ]
        for label, value, color, icon in health_items:
            item_layout = QHBoxLayout()
            icon_label = QLabel(icon)
            text_label = QLabel(f'{label}: {value}')
            text_label.setStyleSheet(f'background-color: transparent; color: {color}; font-size: 13px; font-weight: 500;')
            item_layout.addWidget(icon_label)
            item_layout.addWidget(text_label)
            item_layout.addStretch()
            layout.addLayout(item_layout)
        return container

    def create_performance_metrics_widget(self):
        container = CardWrapper('📈 Performance Metrics')
        container.setObjectName('performance-metrics')
        container.setStyleSheet(f"""
            QFrame[objectName="performance-metrics"] {{
                background-color: #1a1f2e;
                border: 1px solid {CARD_BORDER_COLOR};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        layout = container.body_layout
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)
        metrics = [
            ('Avg Speed', '45.2 MB/s', '#32B8C6'),
            ('Success Rate', '94.2%', '#22c55e'),
            ('Uptime', '2h 14m', '#E68161')
        ]
        for label, value, color in metrics:
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(0, 4, 0, 4)
            item_layout.setSpacing(12)
            label_widget = QLabel(f'{label}:')
            label_widget.setStyleSheet('background-color: transparent; color: #C5C7C7; font-size: 12px; font-weight: 500;')
            value_widget = QLabel(value)
            value_widget.setStyleSheet(f'background-color: transparent; color: {color}; font-size: 12px; font-weight: 600;')
            item_layout.addWidget(label_widget)
            item_layout.addStretch()
            item_layout.addWidget(value_widget)
            layout.addWidget(item_widget)
        return container

    def create_environment_info_widget(self):
        container = CardWrapper('🖥️ Environment')
        container.setObjectName('environment-info')
        container.setStyleSheet(f"""
            QFrame[objectName="environment-info"] {{
                background-color: #1a1f2e;
                border: 1px solid {CARD_BORDER_COLOR};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        layout = container.body_layout
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        self.environment_labels = {}
        env_info = self._build_env_info()
        for label, value, color in env_info:
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(0, 3, 0, 3)
            item_layout.setSpacing(12)
            label_widget = QLabel(f'{label}:')
            label_widget.setStyleSheet('background-color: transparent; color: #C5C7C7; font-size: 11px; font-weight: 500;')
            value_widget = QLabel(value)
            value_widget.setStyleSheet(f'background-color: transparent; color: {color}; font-size: 11px; font-weight: 600;')
            self.environment_labels[label] = value_widget
            item_layout.addWidget(label_widget)
            item_layout.addStretch()
            item_layout.addWidget(value_widget)
            layout.addWidget(item_widget)
        return container

    def _build_env_info(self):
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        environment = getattr(self.config, "environment", self.config.get("environment", ""))
        last_updated = self.stats_service.stats.get("last_updated")
        if not last_updated:
            path = self.stats_service._stats_file()
            if path and path.exists():
                last_updated = datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec='seconds')
        if not last_updated:
            last_updated = "N/A"
        return [
            ("Python", py_version, "#32B8C6"),
            ("Environment", environment, "#E68161"),
            ("Last Update", last_updated, "#9ca3af"),
        ]

    def update_environment_info(self):
        if not hasattr(self, "environment_labels"):
            return
        for label, value, color in self._build_env_info():
            widget = self.environment_labels.get(label)
            if widget:
                widget.setText(str(value))
                widget.setStyleSheet(f'background-color: transparent; color: {color}; font-size: 11px; font-weight: 600;')

    def create_wider_quick_stats(self):
        container = QFrame()
        container.setObjectName('quick-stats')
        container.setMinimumWidth(220)
        container.setStyleSheet(f'''
            QFrame[objectName="quick-stats"] {{
                background-color: #1a1f2e;
                border: 1px solid {CARD_BORDER_COLOR};
                border-radius: 12px;
                padding: 16px;
                min-width: 220px;
            }}
        ''')
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        header_label = SectionHeader('📊 Quick Stats')
        header_layout.addWidget(header_label)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(16)
        grid_layout.setContentsMargins(0, 8, 0, 0)
        stats = [
            ('Collection Rate', '12.3/min', '#32B8C6', 0, 0),
            ('Processing Speed', '45 MB/s', '#22c55e', 0, 1),
            ('Error Rate', '0.8%', '#E68161', 1, 0),
            ('System Load', '67%', '#9ca3af', 1, 1)
        ]
        for label, value, color, row, col in stats:
            stat_container = QWidget()
            stat_container.setStyleSheet('background-color: transparent;')
            stat_layout = QVBoxLayout(stat_container)
            stat_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.setSpacing(2)
            value_label = QLabel(value)
            value_label.setStyleSheet(f'color: {color}; font-size: 15px; font-weight: 700; text-align: center; background-color: transparent;')
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label_widget = QLabel(label)
            label_widget.setStyleSheet('color: #C5C7C7; font-size: 10px; text-align: center; background-color: transparent;')
            label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(value_label)
            stat_layout.addWidget(label_widget)
            grid_layout.addWidget(stat_container, row, col)
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(0)
        main_layout.addLayout(header_layout)
        main_layout.addLayout(grid_layout)
        return container

    def create_reorganized_right_side(self):
        right_column = QVBoxLayout()
        right_column.setSpacing(12)
        top_section_layout = QHBoxLayout()
        top_section_layout.setSpacing(12)
        system_status_card = self.create_enhanced_system_status()
        system_status_card.setObjectName('system-status-narrow')
        system_status_card.setMaximumWidth(180)
        alerts_card = self.create_enhanced_alerts()
        alerts_card.setObjectName('alerts-narrow')
        alerts_card.setMaximumWidth(120)
        top_section_layout.addWidget(system_status_card, 60)
        top_section_layout.addWidget(alerts_card, 40)
        right_column.addLayout(top_section_layout)
        self.recent_activity_widget = RecentActivity(self.config)
        self.recent_activity_widget.setObjectName('recent-activity-tall')
        right_column.addWidget(self.recent_activity_widget)
        self.environment_card = self.create_environment_info_widget()
        right_column.addWidget(self.environment_card)
        self.update_environment_info()
        return right_column

    def create_card_with_styling(self, title, object_name):
        container = CardWrapper(title)
        container.setObjectName(object_name)
        container.setStyleSheet(f"""
            QFrame[objectName="{object_name}"] {{
                background-color: #1a1f2e;
                border: 1px solid {CARD_BORDER_COLOR};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        return container

    def load_data(self):
        summary = self.stats_service.get_summary()
        self.update_overview_metrics(summary)

        if self.task_history_service:
            try:
                activities = self.task_history_service.get_recent_tasks()
                self.recent_activity_widget.clear_activities()
                for a in activities:
                    time_str = a.get("time", "")
                    try:
                        dt = datetime.fromisoformat(time_str)
                        time_str = dt.strftime("%H:%M")
                    except Exception:
                        pass
                    self.recent_activity_widget.add_activity(
                        {
                            "time": time_str,
                            "action": a.get("action", ""),
                            "status": a.get("status", "info"),
                            "details": a.get("details", ""),
                        }
                    )
            except Exception:
                pass

    # --- Placeholder methods for actions ---
    def start_corpus_optimization(self):
        """Run the corpus balancer using the wrapper service."""
        from shared_tools.ui_wrappers.processors.corpus_balancer_wrapper import (
            CorpusBalancerWrapper,
        )

        self._balancer_wrapper = CorpusBalancerWrapper(
            self.config,
            activity_log_service=self.activity_log_service,
            task_history_service=self.task_history_service,
            task_queue_manager=self.task_queue_manager,
        )
        self._balancer_wrapper.completed.connect(
            lambda *_: Notifier.notify(
                "Corpus Optimization", "Optimization completed", level="success"
            )
        )
        self._balancer_wrapper.error_occurred.connect(
            lambda msg: Notifier.notify(
                "Optimization Error", msg, level="error"
            )
        )
        self._balancer_wrapper.start_balancing()

    def start_all_collectors(self):
        """Start all enabled collectors via wrapper factory."""
        from shared_tools.ui_wrappers.wrapper_factory import create_collector_wrapper

        names = self.config.get("enabled_collectors") or []
        if not names:
            Notifier.notify("Collectors", "No collectors enabled", level="warning")
            return

        self._collector_wrappers = []
        for name in names:
            try:
                wrapper = create_collector_wrapper(name, self.config)
            except Exception as exc:  # pragma: no cover - defensive
                Notifier.notify(f"{name} Error", str(exc), level="error")
                continue
            wrapper.completed.connect(
                lambda _r, n=name: Notifier.notify(
                    "Collector Finished", f"{n} completed", level="success"
                )
            )
            wrapper.error_occurred.connect(
                lambda msg, n=name: Notifier.notify(
                    f"{n} Error", msg, level="error"
                )
            )
            wrapper.start()
            self._collector_wrappers.append(wrapper)

        if self.activity_log_service:
            self.activity_log_service.log("Collectors", "Started all collectors")

    def export_report(self):
        """Generate and save a corpus analysis report."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from shared_tools.utils.generate_corpus_report import main as gen_report

        report = gen_report(self.config)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Corpus Report",
            "corpus_report.txt",
            "Text Files (*.txt);;All Files (*)",
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8") as fh:
                fh.write(report)
            Notifier.notify("Report Exported", f"Saved to {file_path}", level="success")
            if self.activity_log_service:
                self.activity_log_service.log("Report", f"Exported to {file_path}")
        except Exception as exc:  # pragma: no cover - runtime guard
            QMessageBox.critical(self, "Export Error", str(exc))

    def update_dependencies(self):
        """Ask for confirmation and run the dependency updater service."""
        from PySide6.QtWidgets import QMessageBox, QCheckBox

        dialog = QMessageBox(self)
        dialog.setWindowTitle("Update Dependencies")
        dialog.setText("Run dependency upgrade now?")
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        dry_box = QCheckBox("Dry run (no changes)")
        dialog.setCheckBox(dry_box)
        if dialog.exec() == QMessageBox.StandardButton.Yes:
            dry_run = dry_box.isChecked()
            if self.activity_log_service:
                self.activity_log_service.log(
                    "System", "Starting dependency update", {"dry_run": dry_run}
                )
            self.dependency_update_service.start_update(dry_run)

    def on_dependency_update_progress(self, percent: int, message: str) -> None:
        """Handle progress updates from ``DependencyUpdateService``."""
        if self.activity_log_service:
            self.activity_log_service.log("DependencyUpdate", message)

    def on_dependency_update_completed(self) -> None:
        Notifier.notify("Dependencies Updated", "Update completed", level="success")
        if self.activity_log_service:
            self.activity_log_service.log("System", "Dependency update completed")

    def on_dependency_update_failed(self, msg: str) -> None:
        Notifier.notify("Update Failed", msg, level="error")
        if self.activity_log_service:
            self.activity_log_service.log("System", f"Dependency update failed: {msg}")

    def pause_task(self, task_id):
        print(f"[Stub] Pause {task_id}")
    def stop_task(self, task_id):
        print(f"[Stub] Stop {task_id}")

    def update_overview_metrics(self, stats: dict):
        """Update metric cards from provided corpus stats."""
        total_docs = stats.get("total_files") or stats.get("doc_count") or 0
        total_size = stats.get("total_size_mb") or stats.get("total_size") or 0
        active_domains = len(stats.get("domains", {}))
        total_tokens = stats.get("total_tokens", 0)

        if "Total Docs" in self.metric_labels:
            self.metric_labels["Total Docs"].setText(str(total_docs))
        if "Total Size" in self.metric_labels:
            # display in GB if large
            size_text = f"{total_size:.2f} MB"
            if total_size >= 1024:
                size_text = f"{total_size/1024:.2f} GB"
            self.metric_labels["Total Size"].setText(size_text)
        if "Active Domains" in self.metric_labels:
            self.metric_labels["Active Domains"].setText(str(active_domains))
        if "Total Tokens" in self.metric_labels:
            self.metric_labels["Total Tokens"].setText(str(total_tokens))

    def update_queue_counts(self, pending: int, retry: int, failed: int, completed: int) -> None:
        """Update queue count labels from TaskQueueManager."""
        if hasattr(self, "pending_label"):
            self.pending_label.setText(str(pending))
        if hasattr(self, "retry_label"):
            self.retry_label.setText(str(retry))
        if hasattr(self, "failed_label"):
            self.failed_label.setText(str(failed))

    def update_system_metrics(self, cpu: float, ram: float, disk: float) -> None:
        """Refresh system status bars from SystemMonitor metrics."""
        if hasattr(self, "cpu_bar"):
            self.cpu_bar.setValue(int(cpu))
            self.cpu_percent.setText(f"{int(cpu)}%")
        if hasattr(self, "ram_bar"):
            self.ram_bar.setValue(int(ram))
            self.ram_percent.setText(f"{int(ram)}%")
        if hasattr(self, "disk_bar"):
            self.disk_bar.setValue(int(disk))
            self.disk_percent.setText(f"{int(disk)}%")

    def update_task_progress(self, task_id: str, progress: int) -> None:
        """Update progress bar for a running task."""
        bar = self._task_bars.get(task_id)
        if bar:
            bar.setValue(progress)

    def fix_all_label_backgrounds(self):
        # Fix all existing QLabel widgets to have transparent background
        for label in self.findChildren(QLabel):
            current_style = label.styleSheet()
            if 'background-color' not in current_style:
                label.setStyleSheet(current_style + '; background-color: transparent;')
            else:
                import re
                new_style = re.sub(r'background-color:\s*[^;]+;?', 'background-color: transparent;', current_style)
                label.setStyleSheet(new_style)

    def closeEvent(self, event):
        if hasattr(self, "system_monitor"):
            self.system_monitor.stop()
        super().closeEvent(event)

    def get_real_domain_data(self):
        try:
            return self.stats_service.get_domain_distribution()
        except Exception:
            return {}

    def create_large_pie_chart(self, domain_data):
        from PySide6.QtCore import Qt
        chart = QChart()
        chart.setBackgroundBrush(QColor('transparent'))
        chart.setMargins(QMargins(0, 0, 0, 0))
        colors = ['#22c55e', '#32B8C6', '#E68161', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#9ca3af']
        series = QPieSeries()
        for i, (domain, percentage) in enumerate(domain_data.items()):
            slice_obj = series.append(f'{domain[:15]}', percentage)
            color = colors[i % len(colors)]
            slice_obj.setBrush(QColor(color))
            slice_obj.setBorderColor(QColor('#1a1f2e'))
            slice_obj.setBorderWidth(2)
            slice_obj.setLabelVisible(False)
        chart.addSeries(series)
        chart.setTitle('')
        chart.legend().setVisible(False)
        chart_view = QChartView(chart)
        chart_view.setFixedSize(220, 220)
        chart_view.setStyleSheet('background-color: transparent; border: none;')
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_container = QWidget()
        chart_container.setStyleSheet('background-color: transparent;')
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        chart_layout.addWidget(chart_view)
        return chart_container

    def create_centered_domain_list(self, domain_data):
        domain_list_widget = QWidget()
        domain_list_widget.setStyleSheet('background-color: transparent;')
        domain_list_layout = QVBoxLayout(domain_list_widget)
        domain_list_layout.setSpacing(6)
        domain_list_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        domain_list_layout.setContentsMargins(20, 0, 0, 0)
        colors = ['#22c55e', '#32B8C6', '#E68161', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#9ca3af']
        for i, (domain, percentage) in enumerate(domain_data.items()):
            item_layout = QHBoxLayout()
            item_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            item_layout.setSpacing(8)
            dot = QLabel('●')
            color = colors[i % len(colors)]
            dot.setStyleSheet(f'color: {color}; font-size: 12px; background-color: transparent;')
            dot.setFixedSize(14, 14)
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            text = QLabel(f'{domain}: {percentage}%')
            text.setStyleSheet('color: #f9fafb; font-size: 12px; font-weight: 500; background-color: transparent;')
            item_layout.addWidget(dot)
            item_layout.addWidget(text)
            item_layout.addStretch()
            domain_list_layout.addLayout(item_layout)
        return domain_list_widget

    def create_corrected_domain_summary(self):
        container = self.create_card_with_styling('📂 Domain Summary', 'domain-summary')
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(0, 0, 0, 0)
        domain_list_widget = QWidget()
        domain_list_widget.setStyleSheet('background-color: transparent;')
        domain_list_layout = QVBoxLayout(domain_list_widget)
        domain_list_layout.setSpacing(1)
        domain_list_layout.setContentsMargins(10, 15, 0, 0)
        domain_data = self.get_real_domain_data()
        colors = ['#22c55e', '#32B8C6', '#E68161', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#9ca3af']
        for i, (domain, percentage) in enumerate(domain_data.items()):
            item_layout = QHBoxLayout()
            item_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            item_layout.setSpacing(8)
            dot = QLabel('●')
            color = colors[i % len(colors)]
            dot.setStyleSheet(f'color: {color}; font-size: 12px; background-color: transparent;')
            dot.setFixedSize(14, 14)
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            text = QLabel(f'{domain}: {percentage}%')
            text.setStyleSheet('color: #f9fafb; font-size: 12px; font-weight: 500; background-color: transparent;')
            item_layout.addWidget(dot)
            item_layout.addWidget(text)
            item_layout.addStretch()
            domain_list_layout.addLayout(item_layout)
        pie_chart = self.create_huge_pie_chart_up_left(domain_data)
        content_layout.addWidget(domain_list_widget, 35)
        content_layout.addWidget(pie_chart, 65)
        container.body_layout.addLayout(content_layout)
        return container

    def create_huge_pie_chart_up_left(self, domain_data):
        chart = QChart()
        chart.setBackgroundBrush(QColor('transparent'))
        chart.setMargins(QMargins(0, 0, 0, 0))
        colors = ['#22c55e', '#32B8C6', '#E68161', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#9ca3af']
        series = QPieSeries()
        for i, (domain, percentage) in enumerate(domain_data.items()):
            slice_obj = series.append(f'{domain[:6]}', percentage)
            color = colors[i % len(colors)]
            slice_obj.setBrush(QColor(color))
            slice_obj.setBorderColor(QColor('#1a1f2e'))
            slice_obj.setBorderWidth(3)
            slice_obj.setLabelVisible(False)
        chart.addSeries(series)
        chart.setTitle('')
        chart.legend().setVisible(False)
        chart_view = QChartView(chart)
        chart_view.setFixedSize(480, 480)
        chart_view.setStyleSheet('background-color: transparent; border: none;')
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_container = QWidget()
        chart_container.setStyleSheet('background-color: transparent;')
        chart_layout = QHBoxLayout(chart_container)
        chart_layout.setContentsMargins(-20, 0, 40, 20)
        chart_layout.addWidget(chart_view)
        chart_layout.addStretch()
        return chart_container

    def create_horizontal_performance_metrics(self):
        container = QFrame()
        container.setObjectName('performance-metrics-horizontal')
        container.setStyleSheet(f'''
            QFrame[objectName="performance-metrics-horizontal"] {{
                background-color: #1a1f2e;
                border: 1px solid {CARD_BORDER_COLOR};
                border-radius: 12px;
                padding: 16px;
            }}
        ''')
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(0, 0, 0, 0)
        header = SectionHeader('📈 Performance Metrics')
        main_layout.addWidget(header)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(16)
        grid_layout.setContentsMargins(0, 4, 0, 0)
        metrics = [
            ('Avg Speed', '45.2 MB/s', '#32B8C6', 0, 0),
            ('Success Rate', '94.2%', '#22c55e', 0, 1),
            ('Docs Today', '2,847', '#8b5cf6', 0, 2),
            ('Queue Length', '12', '#E68161', 1, 0),
            ('Uptime', '2h 14m', '#f59e0b', 1, 1),
            ('Storage Growth', '+1.2GB', '#06b6d4', 1, 2)
        ]
        for label, value, color, row, col in metrics:
            metric_container = QWidget()
            metric_container.setStyleSheet('background-color: transparent;')
            metric_layout = QVBoxLayout(metric_container)
            metric_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            metric_layout.setSpacing(2)
            value_label = QLabel(value)
            value_label.setStyleSheet(f'color: {color}; font-size: 16px; font-weight: 700; text-align: center; background-color: transparent;')
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label_widget = QLabel(label)
            label_widget.setStyleSheet('color: #C5C7C7; font-size: 10px; text-align: center; background-color: transparent;')
            label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            metric_layout.addWidget(value_label)
            metric_layout.addWidget(label_widget)
            grid_layout.addWidget(metric_container, row, col)
        main_layout.addLayout(grid_layout)
        return container

    def create_refined_task_queue(self):
        container = QFrame()
        container.setObjectName('task-queue-refined')
        container.setStyleSheet(f'''
            QFrame[objectName="task-queue-refined"] {{
                background-color: #1a1f2e;
                border: 1px solid {CARD_BORDER_COLOR};
                border-radius: 12px;
                padding: 16px;
            }}
        ''')
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(0, 0, 0, 0)
        header = SectionHeader('📋 Task Queue')
        main_layout.addWidget(header)
        
        # Top section with running tasks
        top_section = QWidget()
        top_section.setStyleSheet('background-color: transparent;')
        top_layout = QVBoxLayout(top_section)
        top_layout.setSpacing(4)
        top_layout.setContentsMargins(0, 4, 0, 0)
        
        running_label = QLabel('Running Tasks:')
        running_label.setStyleSheet('color: #C5C7C7; font-size: 11px; font-weight: 600; background-color: transparent;')
        top_layout.addWidget(running_label)
        
        tasks = [
            (tid, info)
            for tid, info in self.task_queue_manager.tasks.items()
            if info.get("status") == "running"
        ]
        colors = ['#22c55e', '#32B8C6', '#E68161', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#9ca3af']
        for idx, (task_id, info) in enumerate(tasks):
            task_name = info.get('name', task_id)
            progress = info.get('progress', 0)
            color = colors[idx % len(colors)]
            task_container = QWidget()
            task_container.setStyleSheet('background-color: transparent;')
            task_layout = QVBoxLayout(task_container)
            task_layout.setSpacing(2)
            name_label = QLabel(task_name)
            name_label.setStyleSheet('color: #f9fafb; font-size: 10px; background-color: transparent;')
            progress_bar = create_styled_progress_bar(progress, color, height=4)
            self._task_bars[task_id] = progress_bar
            task_layout.addWidget(name_label)
            task_layout.addWidget(progress_bar)
            top_layout.addWidget(task_container)
        
        main_layout.addWidget(top_section)
        main_layout.addStretch()
        
        # Bottom right section with stats
        bottom_section = QWidget()
        bottom_section.setStyleSheet('background-color: transparent;')
        bottom_layout = QHBoxLayout(bottom_section)
        bottom_layout.addStretch()
        
        stats_container = QWidget()
        stats_container.setStyleSheet('background-color: transparent;')
        stats_layout = QVBoxLayout(stats_container)
        stats_layout.setSpacing(2)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        
        stats_info = [
            ('⏳', 'Pending', 'pending_label', '#32B8C6'),
            ('🔄', 'Retry', 'retry_label', '#E68161'),
            ('❌', 'Failed', 'failed_label', '#ef4444'),
        ]

        for icon, word, attr, color in stats_info:
            stat_item = QWidget()
            stat_item.setStyleSheet('background-color: transparent;')
            stat_layout_item = QHBoxLayout(stat_item)
            stat_layout_item.setSpacing(4)
            stat_layout_item.setContentsMargins(0, 0, 0, 0)
            
            icon_label = QLabel(icon)
            icon_label.setFixedSize(14, 14)
            icon_label.setStyleSheet('background-color: transparent; font-size: 10px;')
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            word_label = QLabel(word + ':')
            word_label.setStyleSheet('color: #C5C7C7; font-size: 10px; font-weight: 500; background-color: transparent;')
            
            number_label = QLabel('0')
            number_label.setStyleSheet(f'color: {color}; font-size: 10px; font-weight: 700; background-color: transparent;')
            
            stat_layout_item.addWidget(icon_label)
            stat_layout_item.addWidget(word_label)
            stat_layout_item.addWidget(number_label)
            setattr(self, attr, number_label)
            stats_layout.addWidget(stat_item)
        
        bottom_layout.addWidget(stats_container)
        main_layout.addWidget(bottom_section)
        return container

    def create_simple_metrics_no_containers(self):
        metrics_container = QWidget()
        metrics_container.setStyleSheet('background-color: transparent;')
        metrics_layout = QHBoxLayout(metrics_container)
        metrics_layout.setSpacing(40)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics = [('Total Docs', '2570'), ('Total Size', '0.08 GB'), ('Active Domains', '4'), ('Storage Usage', '2.5%'), ('Running Ops', '3')]
        for title, value in metrics:
            metric_widget = QWidget()
            metric_widget.setObjectName('metric-simple')
            metric_widget.setStyleSheet('background-color: transparent; border: none;')
            metric_layout = QVBoxLayout(metric_widget)
            metric_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            metric_layout.setSpacing(4)
            metric_layout.setContentsMargins(20, 20, 20, 20)
            value_label = QLabel(value)
            value_label.setStyleSheet(
                f'font-size: 28px; color: {BUTTON_COLOR_PRIMARY}; font-weight: 700; background-color: transparent; text-align: center;'
            )
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label = QLabel(title)
            title_label.setStyleSheet('font-size: 14px; color: #C5C7C7; font-weight: 600; background-color: transparent; text-align: center;')
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            metric_layout.addWidget(value_label)
            metric_layout.addWidget(title_label)
            metrics_layout.addWidget(metric_widget)
        return metrics_container

    def create_environment_info(self):
        container = QFrame()
        container.setObjectName('environment-info')
        container.setStyleSheet(f'''
            QFrame[objectName="environment-info"] {{
                background-color: #1a1f2e;
                border: 1px solid {CARD_BORDER_COLOR};
                border-radius: 12px;
                padding: 16px;
            }}
        ''')
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)
        header = SectionHeader('🌍 Environment')
        layout.addWidget(header)
        info = [
            ('Python', '3.12.0'),
            ('OS', 'Windows 10'),
            ('Memory', '16GB'),
            ('Storage', '1TB SSD')
        ]
        for label, value in info:
            info_container = QWidget()
            info_container.setStyleSheet('background-color: transparent;')
            info_layout = QHBoxLayout(info_container)
            info_layout.setContentsMargins(0, 2, 0, 2)
            info_layout.setSpacing(8)
            label_widget = QLabel(label)
            label_widget.setStyleSheet('color: #f9fafb; font-size: 12px; background-color: transparent;')
            value_widget = QLabel(value)
            value_widget.setStyleSheet('color: #C5C7C7; font-size: 12px; background-color: transparent;')
            info_layout.addWidget(label_widget)
            info_layout.addWidget(value_widget)
            info_layout.addStretch()
            layout.addWidget(info_container)
        return container

    def force_system_status_transparency(self):
        container = QFrame()
        container.setObjectName('system-status-narrow')
        container.setStyleSheet(f'''
            QFrame[objectName="system-status-narrow"] {{
                background-color: #1a1f2e;
                border: 1px solid {CARD_BORDER_COLOR};
                border-radius: 12px;
                padding: 16px;
            }}
            QFrame[objectName="system-status-narrow"] QLabel {{
                background-color: transparent;
            }}
        ''')
        layout = QVBoxLayout(container)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)
        header = SectionHeader('🖥️ System Status')
        layout.addWidget(header)
        resources = [('CPU', 45, '#32B8C6'), ('RAM', 67, '#E68161'), ('Disk', 23, '#22c55e')]
        for label, value, color in resources:
            resource_container = QWidget()
            resource_container.setStyleSheet('background-color: transparent;')
            resource_layout = QHBoxLayout(resource_container)
            resource_layout.setContentsMargins(0, 2, 0, 2)
            resource_layout.setSpacing(8)
            label_widget = QLabel(label)
            label_widget.setFixedWidth(35)
            label_widget.setStyleSheet('color: #f9fafb; font-size: 12px; background-color: transparent;')
            progress_bar = create_styled_progress_bar(value, color, height=6)
            progress_bar.setFixedWidth(80)
            percent_label = QLabel(f'{value}%')
            percent_label.setStyleSheet('color: #f9fafb; font-size: 12px; font-weight: 600; background-color: transparent;')
            percent_label.setFixedWidth(30)
            resource_layout.addWidget(label_widget)
            resource_layout.addWidget(progress_bar)
            resource_layout.addWidget(percent_label)
            layout.addWidget(resource_container)
        uptime_label = QLabel('Uptime: 2h 14m')
        uptime_label.setStyleSheet('color: #9ca3af; font-size: 10px; background-color: transparent; margin-top: 4px;')
        layout.addWidget(uptime_label)
        return container

    def force_alerts_transparency(self):
        container = QFrame()
        container.setObjectName('alerts-narrow')
        container.setMinimumWidth(140)
        container.setStyleSheet(f'''
            QFrame[objectName="alerts-narrow"] {{
                background-color: #1a1f2e;
                border: 1px solid {CARD_BORDER_COLOR};
                border-radius: 12px;
                padding: 16px;
            }}
            QFrame[objectName="alerts-narrow"] QLabel {{
                background-color: transparent;
            }}
        ''')
        layout = QVBoxLayout(container)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)
        header = SectionHeader('🔔 Alerts')
        layout.addWidget(header)
        alerts = [('⚠️', 'Storage > 90%', '#E68161'), ('ℹ️', 'Update available', '#32B8C6'), ('✅', 'Backup current', '#22c55e')]
        for icon, text, color in alerts:
            alert_container = QWidget()
            alert_container.setStyleSheet('background-color: transparent;')
            alert_layout = QHBoxLayout(alert_container)
            alert_layout.setContentsMargins(0, 2, 0, 2)
            alert_layout.setSpacing(6)
            icon_label = QLabel(icon)
            icon_label.setFixedSize(12, 12)
            icon_label.setStyleSheet('background-color: transparent;')
            text_label = QLabel(text)
            text_label.setStyleSheet(f'color: {color}; font-size: 11px; background-color: transparent;')
            text_label.setWordWrap(True)
            alert_layout.addWidget(icon_label)
            alert_layout.addWidget(text_label)
            layout.addWidget(alert_container)
        return container

    def force_system_alerts_transparency(self):
        system_widgets = self.findChildren(QFrame, 'system-status-narrow')
        for widget in system_widgets:
            widget.setStyleSheet(widget.styleSheet() + '''
                QFrame[objectName="system-status-narrow"] QLabel {
                    background-color: transparent;
                }
            ''')
            for label in widget.findChildren(QLabel):
                label.setStyleSheet(label.styleSheet() + 'background-color: transparent;')
        
        alert_widgets = self.findChildren(QFrame, 'alerts-narrow')
        for widget in alert_widgets:
            widget.setStyleSheet(widget.styleSheet() + '''
                QFrame[objectName="alerts-narrow"] QLabel {
                    background-color: transparent;
                }
            ''')
            for label in widget.findChildren(QLabel):
                label.setStyleSheet(label.styleSheet() + 'background-color: transparent;')

    def setup_ui(self):
        # ... existing code ...
        self.force_system_alerts_transparency()  # Force transparency on all text labels