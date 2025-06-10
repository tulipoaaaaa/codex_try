"""
Chart Manager for Crypto Corpus Builder
Centralizes chart styling, colors, and creation for consistency across the application.
"""

from PySide6.QtGui import QColor, QPainter
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PySide6.QtCore import Qt
from typing import List, Dict, Any


class ChartManager:
    """Centralized chart manager for consistent styling and colors"""
    
    # Brand color palette - consistent across all charts
    BRAND_COLORS = {
        'primary': '#32B8C6',      # Main brand color (teal/cyan)
        'secondary': '#2DA6B2',    # Darker variant
        'accent': '#E68161',       # Orange for warnings/attention
        'error': '#FF5459',        # Red for errors/critical
        'success': '#50C878',      # Green for success/optimal
        'info': '#A7A9A9',         # Gray for info/neutral
        'background_dark': '#0f1419',    # Deep blue dark background (Claude style)
        'background_light': '#FFFFFD',
        'text_dark': '#f9fafb',          # White text for dark theme
        'text_light': '#13343B'
    }
    
    # Analytics bar chart specific colors - harmonious variety
    ANALYTICS_BAR_COLORS = {
        'quality_metrics': '#E68161',    # Orange (top right as suggested)
        'collection_trends': '#4ECDC4',  # Light teal 
        'language_analysis': '#B45BCF'   # Purple (bottom right as suggested)
    }
    
    # Domain-specific color mapping for consistency
    DOMAIN_COLORS = {
        'Crypto Derivatives': '#32B8C6',      # Primary brand
        'High Frequency Trading': '#2DA6B2',  # Secondary brand  
        'Risk Management': '#E68161',         # Orange
        'Market Microstructure': '#FF5459',   # Red
        'DeFi': '#50C878',                    # Green
        'Portfolio Construction': '#54a0ff',  # Blue/teal
        'Valuation Models': '#B45BCF',        # Purple
        'Regulation & Compliance': '#F39C12'  # Gold
    }
    
    # Status color mapping
    STATUS_COLORS = {
        'optimal': '#32B8C6',      # On target
        'good': '#E68161',         # Acceptable
        'warning': '#E68161',      # Needs attention
        'error': '#FF5459',        # Critical/below target
        'success': '#50C878',      # Success operations
        'info': '#6b7280'          # Neutral/info
    }
    
    def __init__(self, theme: str = 'dark'):
        """Initialize chart manager with theme"""
        self.theme = theme
        self.background_color = self.BRAND_COLORS['background_dark'] if theme == 'dark' else self.BRAND_COLORS['background_light']
        self.text_color = self.BRAND_COLORS['text_dark'] if theme == 'dark' else self.BRAND_COLORS['text_light']
        self.title_color = self.BRAND_COLORS['primary']
    
    def set_theme(self, theme: str):
        """Update theme for all charts"""
        self.theme = theme
        self.background_color = self.BRAND_COLORS['background_dark'] if theme == 'dark' else self.BRAND_COLORS['background_light']
        self.text_color = self.BRAND_COLORS['text_dark'] if theme == 'dark' else self.BRAND_COLORS['text_light']
    
    def create_chart_view(self, title: str, object_name: str = "chart-view") -> QChartView:
        """Create a standardized chart view with consistent styling"""
        chart = QChart()
        chart.setTitle(title)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        # Apply theme-consistent styling
        chart.setBackgroundBrush(QColor(self.background_color))
        chart.setTitleBrush(QColor(self.title_color))
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setObjectName(object_name)
        chart_view.setMinimumSize(400, 300)
        
        return chart_view
    
    def create_pie_chart(self, title: str, data: Dict[str, float], 
                        use_domain_colors: bool = True, show_legend: bool = True) -> QChartView:
        """Create a pie chart with consistent brand colors"""
        chart_view = self.create_chart_view(title)
        chart = chart_view.chart()
        
        # Create pie series
        series = QPieSeries()
        
        for i, (label, value) in enumerate(data.items()):
            slice_obj = series.append(label, value)
            slice_obj.setLabelVisible(True)
            
            # Apply consistent colors
            if use_domain_colors and label in self.DOMAIN_COLORS:
                slice_obj.setColor(QColor(self.DOMAIN_COLORS[label]))
            else:
                # Use rotating brand colors
                colors = list(self.BRAND_COLORS.values())[:6]  # Use first 6 brand colors
                slice_obj.setColor(QColor(colors[i % len(colors)]))
            
            # Ultra-refined white borders (minimal but visible)
            slice_obj.setBorderColor(QColor(255, 255, 255))
            slice_obj.setBorderWidth(1)  # Minimal border thickness (cannot go below 1)
            
            # Maximum contrast label text for perfect readability
            if self.theme == 'dark':
                slice_obj.setLabelColor(QColor(255, 255, 255))  # Pure white for dark theme
            else:
                slice_obj.setLabelColor(QColor(0, 0, 0))        # Pure black for light theme

            # Attach count and percentage details to label and tooltip
            domain_count = slice_obj.property("domain_count")
            pct = round(slice_obj.percentage() * 100, 1)
            slice_label = slice_obj.label()
            slice_obj.setLabel(f"{slice_label} ({pct}%)")
            slice_obj.setToolTip(
                f"{slice_obj.label()}: {domain_count if domain_count is not None else 0} files ({slice_obj.percentage() * 100:.1f}%)"
            )
        
        chart.addSeries(series)
        
        # Configure legend based on parameter
        legend = chart.legend()
        if show_legend:
            legend.setVisible(True)
            legend.setAlignment(Qt.AlignmentFlag.AlignBottom)
            # Maximum contrast legend text
            if self.theme == 'dark':
                legend.setLabelColor(QColor(255, 255, 255))  # Pure white for maximum contrast
            else:
                legend.setLabelColor(QColor(0, 0, 0))        # Pure black for maximum contrast
        else:
            legend.setVisible(False)  # Remove legends to allow bigger pie circle
        
        return chart_view
    
    def create_bar_chart(self, title: str, categories: List[str], 
                        datasets: List[Dict[str, Any]], 
                        y_axis_title: str = "Value") -> QChartView:
        """Create a bar chart with consistent styling"""
        chart_view = self.create_chart_view(title)
        chart = chart_view.chart()
        
        # Create bar series
        series = QBarSeries()
        
        for dataset in datasets:
            bar_set = QBarSet(dataset['label'])
            
            # Add data
            for value in dataset['data']:
                bar_set.append(value)
            
            # Apply colors
            if 'color' in dataset:
                bar_set.setColor(QColor(dataset['color']))
            elif dataset['label'] in self.DOMAIN_COLORS:
                bar_set.setColor(QColor(self.DOMAIN_COLORS[dataset['label']]))
            else:
                bar_set.setColor(QColor(self.BRAND_COLORS['primary']))
            
            series.append(bar_set)
        
        chart.addSeries(series)
        
        # Setup axes
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        if datasets and datasets[0]['data']:
            max_val = max(max(dataset['data']) for dataset in datasets)
            axis_y.setRange(0, max_val * 1.1)  # Add 10% padding
        axis_y.setTitleText(y_axis_title)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        
        return chart_view
    
    def create_status_bar_chart(self, title: str, categories: List[str], 
                               values: List[float], statuses: List[str]) -> QChartView:
        """Create a bar chart with status-based colors"""
        chart_view = self.create_chart_view(title)
        chart = chart_view.chart()
        
        # Create individual bar sets for each status to get different colors
        status_groups: Dict[str, Dict[str, List]] = {}
        for i, status in enumerate(statuses):
            if status not in status_groups:
                status_groups[status] = {'categories': [], 'values': []}
            status_groups[status]['categories'].append(categories[i])
            status_groups[status]['values'].append(values[i])
        
        series = QBarSeries()
        
        for status, data in status_groups.items():
            bar_set = QBarSet(status.title())
            
            # Create full array with zeros, then fill in values for this status
            full_values = [0] * len(categories)
            for cat, val in zip(data['categories'], data['values']):
                if cat in categories:
                    full_values[categories.index(cat)] = val
            
            for val in full_values:
                bar_set.append(val)
            
            # Apply status color
            color = self.STATUS_COLORS.get(status.lower(), self.BRAND_COLORS['primary'])
            bar_set.setColor(QColor(color))
            
            series.append(bar_set)
        
        chart.addSeries(series)
        
        # Setup axes
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        if values:
            axis_y.setRange(0, max(values) * 1.1)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        
        return chart_view
    
    def get_domain_color(self, domain: str) -> str:
        """Get consistent color for a domain"""
        return self.DOMAIN_COLORS.get(domain, self.BRAND_COLORS['primary'])
    
    def get_status_color(self, status: str) -> str:
        """Get consistent color for a status"""
        return self.STATUS_COLORS.get(status.lower(), self.BRAND_COLORS['primary'])
    
    def apply_chart_theme(self, chart: QChart) -> None:
        """Apply the current theme to a chart instance."""
        chart.setBackgroundBrush(QColor(self.background_color))
        chart.setTitleBrush(QColor(self.title_color))

        legend = chart.legend()
        if legend:
            legend.setLabelColor(QColor(255, 255, 255))  # White text for better contrast
            legend.setBackgroundVisible(True)
            legend.setColor(QColor(self.background_color))

    def update_chart_theme(self, chart_view: QChartView) -> None:
        """Update an existing chart view's theme"""
        self.apply_chart_theme(chart_view.chart())
    
