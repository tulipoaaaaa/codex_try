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
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis, QLineSeries, QSplineSeries
from PySide6.QtGui import QPainter, QColor, QIcon, QLinearGradient, QPen
from app.helpers.chart_manager import ChartManager
from app.ui.widgets.card_wrapper import CardWrapper
from app.ui.widgets.section_header import SectionHeader

import random
import datetime


class AnalyticsTab(QWidget):
    def __init__(self, project_config, parent=None):
        super().__init__(parent)
        self.project_config = project_config
        self.chart_manager = ChartManager('dark')  # Will be updated based on actual theme
        self.setup_ui()
        
    def setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer_layout.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)

        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(32)
        main_layout.setContentsMargins(32, 32, 32, 32)
        
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
        domains = [
            "Crypto Derivatives", "High Frequency Trading", "Risk Management",
            "Market Microstructure", "DeFi", "Portfolio Construction",
            "Valuation Models", "Regulation & Compliance"
        ]
        self.domain_filter.addItems(domains)
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
        self.quality_chart_container = self.create_chart_card(
            "Document Quality by Domain", "Average quality scores across domains", self.create_quality_metrics_chart()
        )
        self.time_chart_container = self.create_chart_card(
            "Document Collection Over Time", "Collection trends and document count", self.create_time_trends_chart()
        )
        self.lang_chart_container = self.create_chart_card(
            "Language Distribution", "Document count by language", self.create_language_chart()
        )
        
        charts_grid.addWidget(self.domain_chart_container, 0, 0)
        charts_grid.addWidget(self.quality_chart_container, 0, 1)
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
    
    def create_quality_metrics_chart(self):
        # Create a bar chart for quality metrics using ChartManager
        chart_view = self.chart_manager.create_chart_view("Document Quality by Domain")
        self.quality_chart = chart_view  # Store reference for updates
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
        
        # In a real implementation, this would fetch and analyze actual corpus data
        # For demonstration, we'll use simulated data
        
        self.update_domain_distribution_chart(domain, min_quality)
        self.update_quality_metrics_chart(domain, min_quality)
        self.update_time_trends_chart(from_date, to_date, domain)
        self.update_language_chart(domain, min_quality)
    
    def update_domain_distribution_chart(self, domain_filter, min_quality):
        chart_view = self.domain_chart
        chart = chart_view.chart()
        chart.removeAllSeries()
        # Custom vibrant palette (Claude style)
        palette = [
            QColor("#06b6d4"), QColor("#10b981"), QColor("#f59e0b"), QColor("#ef4444"),
            QColor("#8b5cf6"), QColor("#ec4899"), QColor("#f97316"), QColor("#22d3ee")
        ]
        domains = [
            "Crypto Derivatives", "High Frequency Trading", "Risk Management",
            "Market Microstructure", "DeFi", "Portfolio Construction",
            "Valuation Models", "Regulation & Compliance"
        ]
        if domain_filter != "All Domains":
            domains = [domain_filter]
        counts = [320, 180, 175, 160, 200, 100, 75, 40]
        series = QPieSeries()
        # Remove the donut hole - make it a filled pie chart
        for i, (domain, count) in enumerate(zip(domains, counts)):
            if domain_filter == "All Domains" or domain == domain_filter:
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
    
    def update_quality_metrics_chart(self, domain_filter, min_quality):
        """Update the quality metrics bar chart with multicolored bars"""
        chart_view = self.quality_chart
        chart = chart_view.chart()
        chart.removeAllSeries()
        chart.removeAxis(chart.axisX())
        chart.removeAxis(chart.axisY())
        
        domains = [
            "Crypto Derivatives", 
            "High Frequency Trading",
            "Risk Management",
            "Market Microstructure",
            "DeFi",
            "Portfolio Construction",
            "Valuation Models",
            "Regulation & Compliance"
        ]
        if domain_filter != "All Domains":
            domains = [domain_filter]
        quality_scores = [85, 78, 82, 75, 88, 90, 83, 79]
        
        # Create colorful gradient bars for each domain
        gradient_colors = [
            "#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", 
            "#ffeaa7", "#dda0dd", "#ff9ff3", "#54a0ff"
        ]
        
        # Create multiple bar sets in a single series for proper distribution
        series = QBarSeries()
        filtered_domains = []
        
        # First pass: collect filtered domains
        for i, (domain, score) in enumerate(zip(domains, quality_scores)):
            if domain_filter == "All Domains" or domain == domain_filter:
                filtered_domains.append(domain)
        
        # Create individual bar sets for each domain with different colors
        for i, (domain, score) in enumerate(zip(domains, quality_scores)):
            if domain_filter == "All Domains" or domain == domain_filter:
                quality_set = QBarSet(domain)
                # Add values: score for this domain, 0 for others
                for j, filtered_domain in enumerate(filtered_domains):
                    if filtered_domain == domain:
                        if score >= min_quality:
                            quality_set.append(score)
                        else:
                            quality_set.append(min_quality)
                    else:
                        quality_set.append(0)
                # Set individual color (borders not supported in PySide6 QBarSet)
                quality_set.setColor(QColor(gradient_colors[i % len(gradient_colors)]))
                series.append(quality_set)
        
        chart.addSeries(series)
        
        # Set up axes with proper domain labels
        axis_x = QBarCategoryAxis()
        axis_x.append(filtered_domains)
        axis_x.setLabelsColor(QColor("#f9fafb"))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(min_quality, 100)
        axis_y.setTitleText("Quality Score")
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
        """Update the time trends chart as a smooth line chart"""
        chart_view = self.time_chart
        chart = chart_view.chart()
        chart.removeAllSeries()
        chart.removeAxis(chart.axisX())
        chart.removeAxis(chart.axisY())
        
        # Create smooth line series
        series = QSplineSeries()
        series.setName("Document Count")
        pen = QPen(QColor("#26A69A"))
        pen.setWidth(3)
        series.setPen(pen)
        
        # Generate time series data
        months = []
        current_date = datetime.date.today()
        for i in range(5, -1, -1):
            month_date = current_date - datetime.timedelta(days=i*30)
            months.append(month_date.strftime("%b %Y"))
        document_counts = []
        base_count = 100
        for i in range(6):
            count = base_count + i*20 + random.randint(-10, 10)
            document_counts.append(count)
        
        # Add data points to line series
        for i, count in enumerate(document_counts):
            series.append(i, count)
        
        chart.addSeries(series)
        chart.createDefaultAxes()
        
        # Customize axes
        axis_x = chart.axisX()
        axis_y = chart.axisY()
        axis_x.setLabelsColor(QColor("#f9fafb"))
        axis_y.setLabelsColor(QColor("#f9fafb"))
        axis_y.setTitleText("Document Count")
        
        # Set proper range
        axis_y.setRange(0, max(document_counts) + 20)
        
        # Hide legend for cleaner look
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
        
        languages = ["English", "Chinese", "Spanish", "French", "German", "Japanese", "Russian"]
        language_counts = [850, 150, 100, 50, 40, 30, 30]
        
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
                    filtered_count = count
                    if domain_filter != "All Domains":
                        filtered_count = int(count * 0.3)
                    lang_set.append(filtered_count)
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
        max_count = max(language_counts) + 50
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
