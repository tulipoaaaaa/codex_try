from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QDateEdit,
    QGridLayout,
    QSlider,
    QFrame,
    QScrollArea,
)
from PySide6.QtCore import Qt, QDate, Slot as pyqtSlot, QMargins
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis, QLineSeries
from PySide6.QtGui import QPainter, QColor, QIcon, QLinearGradient, QPen
from app.helpers.chart_manager import ChartManager
from app.ui.widgets.card_wrapper import CardWrapper
from app.ui.widgets.section_header import SectionHeader
from shared_tools.services.corpus_stats_service import CorpusStatsService
from app.ui.theme.theme_constants import PAGE_MARGIN

import datetime


class AnalyticsTab(QWidget):
    def __init__(self, project_config, parent=None):
        super().__init__(parent)
        self.project_config = project_config
        self.chart_manager = ChartManager('dark')  # Will be updated based on actual theme
        self.stats_service = CorpusStatsService(project_config)
        self.stats_service.stats_updated.connect(self.on_stats_updated)
        self.setup_ui()
        self.stats_service.refresh_stats()

    def showEvent(self, event):
        super().showEvent(event)
        self.stats_service.refresh_stats()

    def setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer_layout.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)

        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(PAGE_MARGIN)
        main_layout.setContentsMargins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
        
        # Page header
        header = SectionHeader("Analytics")
        main_layout.addWidget(header)
        
        # Filter section
        filter_section = CardWrapper(title="Filters")
        filter_vbox = filter_section.body_layout
        filter_vbox.setSpacing(20)
        
        # Filter header with icon
        filter_header = QHBoxLayout()
        filter_header.addWidget(QLabel("Data Filters"), 0)
        filter_header.addStretch(1)
        filter_vbox.addLayout(filter_header)
        
        # Filter grid
        filter_grid = QGridLayout()
        filter_grid.setHorizontalSpacing(24)
        filter_grid.setVerticalSpacing(0)
        
        def make_label(text):
            return QLabel(text)
        
        # From Date
        filter_grid.addWidget(make_label("From Date"), 0, 0)
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-3))
        filter_grid.addWidget(self.date_from, 1, 0)
        self.date_from.dateChanged.connect(self.update_charts)
        
        # To Date
        filter_grid.addWidget(make_label("To Date"), 0, 1)
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        filter_grid.addWidget(self.date_to, 1, 1)
        self.date_to.dateChanged.connect(self.update_charts)
        
        # Domain
        filter_grid.addWidget(make_label("Domain"), 0, 2)
        self.domain_filter = QComboBox()
        self.domain_filter.addItem("All Domains")
        filter_grid.addWidget(self.domain_filter, 1, 2)
        self.domain_filter.currentIndexChanged.connect(self.update_charts)
        
        # Quality Score
        filter_grid.addWidget(make_label("Quality Score"), 0, 3)
        self.quality_filter = QComboBox()
        self.quality_filter.addItem("All Quality Levels")
        for i in range(0, 101, 10):
            self.quality_filter.addItem(f"{i}+")
        filter_grid.addWidget(self.quality_filter, 1, 3)
        self.quality_filter.currentIndexChanged.connect(self.update_charts)
        
        # Apply Filters Button
        self.apply_filters_btn = QPushButton("Apply Filters")
        self.apply_filters_btn.clicked.connect(self.update_charts)
        filter_grid.addWidget(self.apply_filters_btn, 1, 4)
        
        filter_vbox.addLayout(filter_grid)
        main_layout.addWidget(filter_section)
        
        # Charts grid
        charts_grid = QGridLayout()
        charts_grid.setSpacing(24)
        charts_grid.setContentsMargins(0, 0, 0, 0)
        
        # Chart cards (no icons)
        self.domain_chart_container = self.create_chart_card(
            "Corpus Domain Distribution", "Distribution across different domains", self.create_domain_distribution_chart()
        )
        self.size_chart_container = self.create_chart_card(
            "Size by Domain", "Total document size in MB per domain", self.create_size_metrics_chart()
        )
        self.time_chart_container = self.create_chart_card(
            "Document Collection Over Time", "Collection trends and document count", self.create_time_trends_chart()
        )
        self.lang_chart_container = self.create_chart_card(
            "Language Distribution", "Document count by language", self.create_language_chart()
        )
        
        charts_grid.addWidget(self.domain_chart_container, 0, 0)
        charts_grid.addWidget(self.size_chart_container, 0, 1)
        charts_grid.addWidget(self.time_chart_container, 1, 0)
        charts_grid.addWidget(self.lang_chart_container, 1, 1)
        charts_grid.setColumnStretch(0, 1)
        charts_grid.setColumnStretch(1, 1)
        charts_grid.setRowStretch(0, 1)
        charts_grid.setRowStretch(1, 1)
        
        charts_container = QWidget()
        charts_container.setLayout(charts_grid)
        main_layout.addWidget(charts_container)

        self.update_charts()
        
    def update_theme(self, theme_name):
        """Update the chart manager theme and refresh charts"""
        self.chart_manager.set_theme(theme_name)
        self.update_charts()

    def on_stats_updated(self, stats: dict):
        """Handle updated corpus statistics."""
        domains = list(self.stats_service.get_domain_summary().keys())
        self.domain_filter.blockSignals(True)
        current = self.domain_filter.currentText()
        self.domain_filter.clear()
        self.domain_filter.addItem("All Domains")
        self.domain_filter.addItems(domains)
        if current in domains:
            self.domain_filter.setCurrentText(current)
        self.domain_filter.blockSignals(False)
        self.update_charts()
    
    def create_chart_card(self, title, subtitle, chart_view):
        card = CardWrapper(title=title)
        layout = card.body_layout
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Chart area
        chart_area = QFrame()
        chart_layout = QVBoxLayout(chart_area)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        chart_layout.addWidget(chart_view)
        layout.addWidget(chart_area)
        return card
    
    def create_domain_distribution_chart(self):
        # Create a pie chart for domain distribution using ChartManager with Claude-style formatting
        chart_view = self.chart_manager.create_chart_view("Corpus Domain Distribution")
        chart = chart_view.chart()
        chart.setBackgroundBrush(QColor("#0f1419"))
        chart.setTitle("")
        chart.setMargins(QMargins(20, 20, 20, 20))
        chart.legend().setVisible(False)
        self.domain_chart = chart_view  # Store reference for updates
        return chart_view
    
    def create_size_metrics_chart(self):
        """Create bar chart for document size by domain."""
        chart_view = self.chart_manager.create_chart_view("Size by Domain")
        self.size_chart = chart_view  # Store reference for updates
        return chart_view
    
    def create_time_trends_chart(self):
        # Create a line chart for time trends using ChartManager
        chart_view = self.chart_manager.create_chart_view("Document Collection Over Time")
        self.time_chart = chart_view  # Store reference for updates
        return chart_view
    
    def create_language_chart(self):
        # Create a bar chart for language distribution using ChartManager
        chart_view = self.chart_manager.create_chart_view("Language Distribution")
        self.lang_chart = chart_view  # Store reference for updates
        return chart_view
    
    def get_min_quality(self):
        quality_text = self.quality_filter.currentText()
        if quality_text == "All Quality Levels":
            return 0
        else:
            return int(quality_text.rstrip('+'))
    
    def update_charts(self):
        """Update all analytics charts with current data"""
        # Get filter values
        from_date = self.date_from.date().toPython()
        to_date = self.date_to.date().toPython()
        domain = self.domain_filter.currentText()
        min_quality = self.get_min_quality()

        counts = self.stats_service.get_domain_summary()
        sizes = self.stats_service.get_domain_size_summary()

        self.update_domain_distribution_chart(domain, counts)
        self.update_size_chart(domain, sizes)
        self.update_time_trends_chart(from_date, to_date, domain)
        self.update_language_chart(domain, min_quality)
    
    def update_domain_distribution_chart(self, domain_filter, counts):
        chart_view = self.domain_chart
        chart = chart_view.chart()
        chart.removeAllSeries()
        palette = [
            QColor("#06b6d4"), QColor("#10b981"), QColor("#f59e0b"), QColor("#ef4444"),
            QColor("#8b5cf6"), QColor("#ec4899"), QColor("#f97316"), QColor("#22d3ee")
        ]

        domains = list(counts.keys())
        if domain_filter != "All Domains":
            domains = [d for d in domains if d == domain_filter]

        series = QPieSeries()
        for i, domain in enumerate(domains):
            count = counts.get(domain, 0)
            slice_obj = series.append(f"{domain}", count)
            slice_obj.setColor(palette[i % len(palette)])
            slice_obj.setLabelVisible(False)
            slice_obj.setBorderColor(QColor("#0f1419"))
            slice_obj.setBorderWidth(2)
        chart.addSeries(series)
        # Custom legend (horizontal, no background)
        legend = chart.legend()
        legend.setVisible(True)
        legend.setAlignment(Qt.AlignBottom)
        legend.setLabelColor(QColor("#f9fafb"))
        legend.setBackgroundVisible(False)
        legend.setBorderColor(QColor("#1a1f2e"))
        legend.setFont(chart_view.font())
        # Remove legend background
        legend.setBrush(QColor(0,0,0,0))
        # Style legend markers
        for marker in legend.markers(series):
            marker.setLabelBrush(QColor("#f9fafb"))
            marker.setBrush(marker.brush())
            marker.setPen(QColor("#1a1f2e"))
        # Remove chart drop shadow if present
        chart.setDropShadowEnabled(False)
        # Remove chart background border
        chart.setBackgroundRoundness(0)
        chart.setBackgroundPen(QColor("#1a1f2e"))
        # Remove chart title
        chart.setTitle("")
        # Center the chart
        chart_view.setAlignment(Qt.AlignCenter)
    
    def update_size_chart(self, domain_filter, sizes):
        """Display document size distribution per domain."""
        chart_view = self.size_chart
        chart = chart_view.chart()
        chart.removeAllSeries()
        chart.removeAxis(chart.axisX())
        chart.removeAxis(chart.axisY())

        domains = list(sizes.keys())
        if domain_filter != "All Domains":
            domains = [d for d in domains if d == domain_filter]

        bar_set = QBarSet("Size MB")
        for domain in domains:
            bar_set.append(sizes.get(domain, 0))

        series = QBarSeries()
        series.append(bar_set)

        chart.addSeries(series)

        # Set up axes with proper domain labels
        axis_x = QBarCategoryAxis()
        axis_x.append(domains)
        axis_x.setLabelsColor(QColor("#f9fafb"))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        max_val = max(sizes.values()) if sizes else 0
        axis_y.setRange(0, max_val * 1.1 if max_val else 1)
        axis_y.setTitleText("Size (MB)")
        axis_y.setLabelsColor(QColor("#f9fafb"))
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        
        # Hide legend for cleaner look
        legend = chart.legend()
        if legend:
            legend.setVisible(False)
            
        chart.setBackgroundBrush(QColor("#0f1419"))
        chart.setBackgroundPen(QColor("#1a1f2e"))
        chart.setBackgroundRoundness(0)
        chart.setDropShadowEnabled(False)
        chart.setTitle("")
    
    def update_time_trends_chart(self, from_date, to_date, domain_filter):
        """Update the time trends chart from metadata timestamps."""
        chart_view = self.time_chart
        chart = chart_view.chart()
        chart.removeAllSeries()
        chart.removeAxis(chart.axisX())
        chart.removeAxis(chart.axisY())

        meta_dir = self.project_config.get_metadata_dir()
        counts = self.stats_service.get_daily_document_counts(meta_dir)
        filtered = {
            d: c
            for d, c in counts.items()
            if from_date <= datetime.date.fromisoformat(d) <= to_date
        }
        if not filtered:
            return

        dates = sorted(filtered.keys())
        series = QLineSeries()
        pen = QPen(QColor("#26A69A"))
        pen.setWidth(3)
        series.setPen(pen)
        for idx, d in enumerate(dates):
            series.append(idx, filtered[d])

        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(dates)
        axis_x.setLabelsColor(QColor("#f9fafb"))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, max(filtered.values()))
        axis_y.setLabelsColor(QColor("#f9fafb"))
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        legend = chart.legend()
        if legend:
            legend.setVisible(False)

        chart.setBackgroundBrush(QColor("#0f1419"))
        chart.setBackgroundPen(QColor("#1a1f2e"))
        chart.setBackgroundRoundness(0)
        chart.setDropShadowEnabled(False)
        chart.setTitle("")
    
    def update_language_chart(self, domain_filter, min_quality):
        """Update the language distribution chart with multicolored bars"""
        chart_view = self.lang_chart
        chart = chart_view.chart()
        chart.removeAllSeries()
        chart.removeAxis(chart.axisX())
        chart.removeAxis(chart.axisY())
        
        meta_dir = self.project_config.get_metadata_dir()
        lang_counts = self.stats_service.get_language_distribution(meta_dir)
        languages = sorted(lang_counts.keys())
        language_counts = [lang_counts[l] for l in languages]
        
        # Use purple gradient colors for language chart
        purple_colors = [
            "#9c88ff", "#8c7ae6", "#6c5ce7", "#a29bfe", 
            "#fd79a8", "#e84393", "#74b9ff"
        ]
        
        # Create multiple bar sets in a single series for proper distribution
        series = QBarSeries()
        
        # Create individual bar sets for each language with different colors
        for i, (lang, count) in enumerate(zip(languages, language_counts)):
            lang_set = QBarSet(lang)
            
            # Add values: count for this language, 0 for others
            for j, language in enumerate(languages):
                if language == lang:
                    lang_set.append(count)
                else:
                    lang_set.append(0)
        
            # Set individual color (borders not supported in PySide6 QBarSet)
            lang_set.setColor(QColor(purple_colors[i % len(purple_colors)]))
            series.append(lang_set)
            
        chart.addSeries(series)
        
        # Set up axes with proper language labels  
        axis_x = QBarCategoryAxis()
        axis_x.append(languages)
        axis_x.setLabelsColor(QColor("#f9fafb"))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        max_count = max(language_counts) + 1 if language_counts else 1
        axis_y.setRange(0, max_count)
        axis_y.setTitleText("Document Count")
        axis_y.setLabelsColor(QColor("#f9fafb"))
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        
        # Hide legend for cleaner look
        legend = chart.legend()
        if legend:
            legend.setVisible(False)
            
        chart.setBackgroundBrush(QColor("#0f1419"))
        chart.setBackgroundPen(QColor("#1a1f2e"))
        chart.setBackgroundRoundness(0)
        chart.setDropShadowEnabled(False)
        chart.setTitle("")
