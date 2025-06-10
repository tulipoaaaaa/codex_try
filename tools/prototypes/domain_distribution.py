# ⚠️ Prototype Widget: DomainDistribution is not currently used in the UI
# Kept for potential future integration into dashboard chart views
# File: app/ui/widgets/domain_distribution.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QCheckBox)
from PySide6.QtCore import Qt, Signal as pyqtSignal
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PySide6.QtGui import QColor, QPainter
from app.helpers.chart_manager import ChartManager

class DomainDistribution(QWidget):
    """Widget for displaying corpus domain distribution."""
    
    refresh_requested = pyqtSignal()
    balance_requested = pyqtSignal()
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.chart_manager = ChartManager('dark')  # Will be updated based on actual theme
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)
        
        # Set widget object name for styling
        self.setObjectName("card")
        self.setStyleSheet("background-color: #1a1f2e; border-radius: 12px; border: 1px solid #2d3748;")
        
        # Header with consistent styling
        header = QLabel("Domain Distribution")
        header.setObjectName("dashboard-section-header")
        header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setStyleSheet("color: #06b6d4; font-size: 18px; font-weight: 600; margin-bottom: 8px;")
        main_layout.addWidget(header)
        
        # Controls layout with better alignment
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(10, 0, 10, 0)
        controls_layout.setSpacing(8)
        
        # Left side controls
        left_controls = QHBoxLayout()
        left_controls.setSpacing(8)
        left_controls.addWidget(QLabel("Chart Type:"))
        self.chart_type = QComboBox()
        self.chart_type.addItems(["Pie Chart", "Bar Chart"])
        self.chart_type.currentTextChanged.connect(self.update_chart_type)
        left_controls.addWidget(self.chart_type)
        
        # Compare with target option
        self.show_target = QCheckBox("Compare with Target")
        self.show_target.setChecked(True)
        self.show_target.stateChanged.connect(self.update_chart)
        left_controls.addWidget(self.show_target)
        
        controls_layout.addLayout(left_controls)
        controls_layout.addStretch()
        
        # Right side buttons with better spacing
        right_controls = QHBoxLayout()
        right_controls.setSpacing(8)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_requested)
        right_controls.addWidget(refresh_btn)
        
        # Balance button
        balance_btn = QPushButton("Balance Corpus")
        balance_btn.clicked.connect(self.balance_requested)
        right_controls.addWidget(balance_btn)
        
        controls_layout.addLayout(right_controls)
        main_layout.addLayout(controls_layout)
        
        # Chart and summary area in a horizontal layout
        chart_summary_layout = QHBoxLayout()
        chart_summary_layout.setSpacing(24)
        chart_summary_layout.setContentsMargins(0, 0, 0, 0)
        
        # Chart view using ChartManager for consistent styling
        self.chart_view = self.chart_manager.create_chart_view("Corpus Domain Distribution", "chart-view")
        self.chart = self.chart_view.chart()
        self.chart_view.setMinimumSize(320, 320)
        self.chart_view.setMaximumSize(340, 340)
        self.chart_view.setStyleSheet("background: #0f1419; border-radius: 8px; border: 1px solid #374151;")
        chart_summary_layout.addWidget(self.chart_view, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # Summary area (placeholder for now)
        self.summary_widget = QWidget()
        self.summary_widget.setStyleSheet("background: #1a1f2e; border-radius: 8px;")
        summary_layout = QVBoxLayout(self.summary_widget)
        summary_layout.setContentsMargins(16, 16, 16, 16)
        summary_layout.setSpacing(12)
        # Example summary labels (replace with real data as needed)
        self.top_domain_label = QLabel("Top Domain: 45%")
        self.top_domain_label.setStyleSheet("color: #06b6d4; font-size: 18px; font-weight: 700;")
        summary_layout.addWidget(self.top_domain_label)
        self.total_domains_label = QLabel("Total Domains: 678")
        self.total_domains_label.setStyleSheet("color: #d1d5db; font-size: 14px;")
        summary_layout.addWidget(self.total_domains_label)
        self.completion_label = QLabel("Completion: 89%")
        self.completion_label.setStyleSheet("color: #d1d5db; font-size: 14px;")
        summary_layout.addWidget(self.completion_label)
        summary_layout.addStretch()
        chart_summary_layout.addWidget(self.summary_widget, 1)
        
        main_layout.addLayout(chart_summary_layout)
        main_layout.addStretch()
        
        # Initial data (placeholder)
        self.domains = [
            "Crypto Derivatives", 
            "High Frequency Trading",
            "Risk Management",
            "Market Microstructure",
            "DeFi",
            "Portfolio Construction",
            "Valuation Models",
            "Regulation & Compliance"
        ]
        
        self.current_distribution = {
            "Crypto Derivatives": 25,
            "High Frequency Trading": 15,
            "Risk Management": 15,
            "Market Microstructure": 12,
            "DeFi": 15,
            "Portfolio Construction": 8,
            "Valuation Models": 5,
            "Regulation & Compliance": 5
        }
        
        self.target_distribution = {
            "Crypto Derivatives": {"allocation": 0.20},
            "High Frequency Trading": {"allocation": 0.15},
            "Risk Management": {"allocation": 0.15},
            "Market Microstructure": {"allocation": 0.15},
            "DeFi": {"allocation": 0.12},
            "Portfolio Construction": {"allocation": 0.10},
            "Valuation Models": {"allocation": 0.08},
            "Regulation & Compliance": {"allocation": 0.05},
        }
        
        # Initial chart
        self.update_chart()
    
    def update_theme(self, theme_name):
        """Update chart colors based on current theme"""
        self.chart_manager.set_theme(theme_name)
        self.chart_manager.update_chart_theme(self.chart_view)
        self.update_chart()  # Refresh chart with new colors
    
    def update_distribution_data(self, current_distribution, target_distribution=None):
        """Update the distribution data and refresh the chart."""
        self.current_distribution = current_distribution
        if target_distribution:
            self.target_distribution = target_distribution
        
        self.update_chart()
    
    def update_chart_type(self):
        """Update the chart type based on selection."""
        self.update_chart()
    
    def update_chart(self):
        """Update the chart with current data."""
        # Clear existing series
        self.chart.removeAllSeries()
        if self.chart.axisX():
            self.chart.removeAxis(self.chart.axisX())
        if self.chart.axisY():
            self.chart.removeAxis(self.chart.axisY())
        
        if self.chart_type.currentText() == "Pie Chart":
            self._create_pie_chart()
        else:
            self._create_bar_chart()
    
    def _create_pie_chart(self):
        """Create and display a pie chart with white borders and better text contrast."""
        # Create pie series for current distribution
        series = QPieSeries()
        
        # Set chart title
        self.chart.setTitle("Current Corpus Domain Distribution")
        
        # Add slices with improved styling
        for domain, data in self.current_distribution.items():
            # Handle both integer values and dictionary values
            if isinstance(data, dict):
                value = data.get("current", 0) * 100  # Convert to percentage
            else:
                # data is just an integer percentage
                value = data
                
            slice = series.append(f"{domain} ({value:.1f}%)", value)
            slice.setLabelVisible(True)
            
            # Apply consistent brand colors using ChartManager
            slice.setColor(QColor(self.chart_manager.get_domain_color(domain)))
            
            # Add white borders to all slices for better definition
            slice.setBorderColor(QColor(255, 255, 255))  # White border
            slice.setBorderWidth(2)  # 2px border width for visibility
            
            # Set label color to white for better contrast
            slice.setLabelColor(QColor(255, 255, 255))
            # Note: Label position will use default positioning for compatibility
            
            # Optional: Add status indication based on target comparison
            if self.show_target.isChecked():
                target_data = self.target_distribution.get(domain, {})
                if isinstance(target_data, dict):
                    target = target_data.get("allocation", 0) * 100
                else:
                    target = target_data if target_data else 0
                # Status indication via border thickness, keeping white color
                deviation = abs(value - target)
                if deviation <= 2:
                    slice.setBorderWidth(3)  # Thicker border for optimal
                elif deviation <= 5:
                    slice.setBorderWidth(2)  # Normal border for good
                else:
                    slice.setBorderWidth(4)  # Thickest border for warning
        
        # Improve overall series presentation
        series.setLabelsVisible(True)
        series.setUseOpenGL(True)  # Better rendering performance
        
        self.chart.addSeries(series)
    
    def _create_bar_chart(self):
        """Create and display a bar chart."""
        # Create bar series for current distribution
        current_set = QBarSet("Current")
        
        # Add target set if requested
        if self.show_target.isChecked():
            target_set = QBarSet("Target")
            self.chart.setTitle("Current vs Target Domain Distribution")
        else:
            self.chart.setTitle("Current Domain Distribution")
        
        # Add data
        for domain in self.domains:
            current_data = self.current_distribution.get(domain, {})
            # Handle both integer values and dictionary values
            if isinstance(current_data, dict):
                current_value = current_data.get("current", 0) * 100
            else:
                # current_data is just an integer percentage
                current_value = current_data if current_data else 0
                
            current_set.append(current_value)
            
            if self.show_target.isChecked():
                target_data = self.target_distribution.get(domain, {})
                if isinstance(target_data, dict):
                    target_value = target_data.get("allocation", 0) * 100
                else:
                    target_value = target_data if target_data else 0
                target_set.append(target_value)
        
        # Create and configure bar series
        series = QBarSeries()
        series.append(current_set)
        if self.show_target.isChecked():
            series.append(target_set)
        
        self.chart.addSeries(series)
        
        # Add axes
        axis_x = QBarCategoryAxis()
        axis_x.append(self.domains)
        self.chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, 100)  # Adjust range as needed for percentage
        axis_y.setTitleText("Percentage (%)")
        self.chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
