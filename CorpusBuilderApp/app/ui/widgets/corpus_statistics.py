# File: app/ui/widgets/corpus_statistics.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QProgressBar, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, Signal as pyqtSignal, QTimer
from PySide6.QtGui import QFont, QColor, QPalette
from app.helpers.icon_manager import IconManager

class CorpusStatistics(QWidget):
    """Widget for displaying corpus statistics."""
    
    refresh_requested = pyqtSignal()
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setObjectName("card")
        self.setup_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_requested)
        self.timer.start(30000)  # Refresh every 30 seconds
        
    def setup_ui(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add header with consistent styling
        header_label = QLabel("Corpus Statistics")
        header_label.setObjectName("dashboard-section-header")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)
        
        # Create stats grid
        stats_layout = QHBoxLayout()
        
        # Total documents
        self.total_docs_widget, self.total_docs_value_label = self._create_stat_widget(
            "Total Documents", 
            "0", 
            "documents in corpus"
        )
        stats_layout.addWidget(self.total_docs_widget)
        
        # Total size
        self.total_size_widget, self.total_size_value_label = self._create_stat_widget(
            "Total Size", 
            "0 MB", 
            "of data"
        )
        stats_layout.addWidget(self.total_size_widget)
        
        # Domains
        self.domains_widget, self.domains_value_label = self._create_stat_widget(
            "Domains", 
            "0/8", 
            "domains filled"
        )
        stats_layout.addWidget(self.domains_widget)
        
        main_layout.addLayout(stats_layout)
        
        # Add separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator2)
        
        # Storage usage with proper spacing and alignment
        storage_outer_container = QFrame()
        storage_outer_layout = QHBoxLayout(storage_outer_container)
        storage_outer_layout.setContentsMargins(10, 5, 25, 5)  # Add right margin for spacing from pie chart
        
        # Gray background container for storage usage (no black background)
        storage_container = QFrame()
        storage_container.setObjectName("storage-usage-container")
        storage_container.setStyleSheet("""
            QFrame#storage-usage-container {
                background: transparent;
                border: none;
                border-radius: 0px;
                padding: 0px;
                margin: 0px;
            }
        """)
        
        storage_layout = QVBoxLayout(storage_container)
        storage_layout.setContentsMargins(8, 6, 8, 6)
        storage_layout.setSpacing(4)
        
        # Header with aligned text and orange percentage
        storage_header = QHBoxLayout()
        storage_header.setContentsMargins(0, 0, 0, 0)
        
        storage_label = QLabel("Storage Usage:")
        storage_label.setStyleSheet("color: #C5C7C7; font-weight: 500;")
        storage_header.addWidget(storage_label)
        
        self.storage_percentage = QLabel("0%")
        self.storage_percentage.setStyleSheet("color: #E68161; font-weight: 600; background: transparent;")
        storage_header.addWidget(self.storage_percentage, alignment=Qt.AlignmentFlag.AlignRight)
        
        storage_layout.addLayout(storage_header)
        
        # Progress bar aligned with the header
        self.storage_bar = QProgressBar()
        self.storage_bar.setRange(0, 100)
        self.storage_bar.setValue(0)
        self.storage_bar.setTextVisible(False)
        self.storage_bar.setFixedHeight(8)
        self.storage_bar.setStyleSheet("""
            QProgressBar {
                background: transparent;
                border: none;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #E68161;
                border-radius: 4px;
            }
        """)
        storage_layout.addWidget(self.storage_bar)
        
        # Add storage container to outer container with left alignment
        storage_outer_layout.addWidget(storage_container)
        storage_outer_layout.addStretch()  # Push everything to the left
        
        main_layout.addWidget(storage_outer_container)
        
        # Domain distribution header
        main_layout.addWidget(QLabel("Domain Distribution:"))
        
        # Domain progress bars (placeholder for actual domains)
        self.domain_bars = {}
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
        
        for domain in domains:
            domain_layout = QHBoxLayout()
            domain_layout.setContentsMargins(10, 0, 10, 0)
            
            domain_label = QLabel(domain)
            domain_label.setMinimumWidth(150)
            domain_layout.addWidget(domain_label)
            
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(0)
            domain_layout.addWidget(progress, stretch=1)
            
            count_label = QLabel("0")
            count_label.setMinimumWidth(50)
            count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            domain_layout.addWidget(count_label)
            
            main_layout.addLayout(domain_layout)
            self.domain_bars[domain] = (progress, count_label)
        
        # Add spacer at the bottom
        main_layout.addStretch()
    
    def _create_stat_widget(self, title, value, subtitle):
        """Create a statistic widget with title, value, and subtitle. Returns (widget, value_label)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        # Subtitle
        subtitle_label = QLabel(subtitle)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        return widget, value_label
        
    def update_statistics(self, stats_data):
        """Update the statistics with the provided data."""
        # Update total documents
        total_docs = stats_data.get('total_documents', 0)
        self.total_docs_value_label.setText(str(total_docs))
        
        # Update total size
        total_size = stats_data.get('total_size', 0)
        size_str = self._format_size(total_size)
        self.total_size_value_label.setText(size_str)
        
        # Update domains
        filled_domains = stats_data.get('filled_domains', 0)
        total_domains = stats_data.get('total_domains', 8)
        self.domains_value_label.setText(f"{filled_domains}/{total_domains}")
        
        # Update storage usage
        storage_used = stats_data.get('storage_used', 0)
        storage_total = stats_data.get('storage_total', 1)
        storage_percentage = min(100, int((storage_used / storage_total) * 100)) if storage_total > 0 else 0
        self.storage_percentage.setText(f"{storage_percentage}%")
        self.storage_bar.setValue(storage_percentage)
        
        # Update domain distribution
        domain_distribution = stats_data.get('domain_distribution', {})
        for domain, (progress_bar, count_label) in self.domain_bars.items():
            count = domain_distribution.get(domain, {}).get('count', 0)
            percentage = domain_distribution.get(domain, {}).get('percentage', 0)
            progress_bar.setValue(int(percentage))
            count_label.setText(str(count))

            # Color code based on target vs actual
            target = domain_distribution.get(domain, {}).get('target', 0)
            if abs(percentage - target) <= 2:
                # On target (±2%)
                progress_bar.setObjectName("progress-on-target")
            elif percentage < target:
                # Below target
                progress_bar.setObjectName("progress-below-target")
            else:
                # Above target
                progress_bar.setObjectName("progress-above-target")
    
    def _format_size(self, size_bytes):
        """Format file size in a human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
