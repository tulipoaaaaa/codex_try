"""
Main window for CryptoFinance Corpus Builder
"""

from PySide6.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, QWidget, 
                             QStatusBar, QMenuBar, QToolBar, QProgressBar, 
                             QLabel, QSplitter, QMessageBox, QHBoxLayout, QPushButton, QMenu, QDialog, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, QTimer, Signal as pyqtSignal, QThread, QSize
from PySide6.QtGui import QAction, QIcon, QPixmap
import logging
from pathlib import Path

# Import all tab widgets
from ui.tabs.dashboard_tab import DashboardTab
from ui.tabs.collectors_tab import CollectorsTab
from ui.tabs.processors_tab import ProcessorsTab
from ui.tabs.corpus_manager_tab import CorpusManagerTab
from ui.tabs.balancer_tab import BalancerTab
from ui.tabs.analytics_tab import AnalyticsTab
from ui.tabs.configuration_tab import ConfigurationTab
from ui.tabs.logs_tab import LogsTab
from ui.tabs.maintenance_tab import MaintenanceTab
from ui.tabs.full_activity_tab import FullActivityTab

class CryptoCorpusMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, config):
        super().__init__()
        print(f"DEBUG: MainWindow received config type: {type(config)}")
        print(f"DEBUG: MainWindow received config value: {config}")
        print(f"DEBUG: Config has 'get' method: {hasattr(config, 'get')}")
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize tab attributes to None
        self.dashboard_tab = None
        self.collectors_tab = None
        self.processors_tab = None
        self.corpus_manager_tab = None
        self.balancer_tab = None
        self.analytics_tab = None
        self.configuration_tab = None
        self.logs_tab = None
        self.maintenance_tab = None
        self.full_activity_tab = None
        
        # Initialize UI
        self.init_ui()
        self.init_status_bar()
        self.init_menu_bar()
        self.init_toolbar()
        
        # Connect signals
        self.connect_signals()
        
        # Setup update timer
        self.setup_update_timer()
        
        self.logger.info("Main window initialized")
    
    def init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle("CryptoFinance Corpus Builder v3")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(False)
        layout.addWidget(self.tab_widget)
        
        # Initialize all tabs
        self.init_tabs()
    
    def init_tabs(self):
        """Initialize all application tabs"""
        try:
            print(f"DEBUG: About to initialize tabs with config type: {type(self.config)}")
            print(f"DEBUG: About to initialize tabs with config value: {self.config}")
            # Dashboard tab
            print("DEBUG: Initializing DashboardTab...")
            self.dashboard_tab = DashboardTab(self.config)
            print("DEBUG: DashboardTab initialized successfully")
            self.tab_widget.addTab(self.dashboard_tab, "📊 Dashboard")
            # Collectors tab
            print("DEBUG: Initializing CollectorsTab...")
            self.collectors_tab = CollectorsTab(self.config)
            print("DEBUG: CollectorsTab initialized successfully")
            self.tab_widget.addTab(self.collectors_tab, "🔍 Collectors")
            # Processors tab
            print("DEBUG: Initializing ProcessorsTab...")
            self.processors_tab = ProcessorsTab(self.config)
            print("DEBUG: ProcessorsTab initialized successfully")
            self.tab_widget.addTab(self.processors_tab, "⚙️ Processors")
            # Corpus Manager tab
            print("DEBUG: Initializing CorpusManagerTab...")
            self.corpus_manager_tab = CorpusManagerTab(self.config)
            print("DEBUG: CorpusManagerTab initialized successfully")
            self.tab_widget.addTab(self.corpus_manager_tab, "📁 Corpus Manager")
            # Balancer tab
            print("DEBUG: Initializing BalancerTab...")
            self.balancer_tab = BalancerTab(self.config)
            print("DEBUG: BalancerTab initialized successfully")
            self.tab_widget.addTab(self.balancer_tab, "⚖️ Balancer")
            # Analytics tab
            print("DEBUG: Initializing AnalyticsTab...")
            self.analytics_tab = AnalyticsTab(self.config)
            print("DEBUG: AnalyticsTab initialized successfully")
            self.tab_widget.addTab(self.analytics_tab, "📈 Analytics")
            # Configuration tab
            print("DEBUG: Initializing ConfigurationTab...")
            self.configuration_tab = ConfigurationTab(self.config)
            print("DEBUG: ConfigurationTab initialized successfully")
            self.tab_widget.addTab(self.configuration_tab, "⚙️ Configuration")
            # Logs tab
            print("DEBUG: Initializing LogsTab...")
            self.logs_tab = LogsTab(self.config)
            print("DEBUG: LogsTab initialized successfully")
            self.tab_widget.addTab(self.logs_tab, "📝 Logs")
            # Add Maintenance tab
            print("DEBUG: Initializing MaintenanceTab...")
            self.maintenance_tab = MaintenanceTab(parent=self)
            print("DEBUG: MaintenanceTab initialized successfully")
            self.tab_widget.addTab(self.maintenance_tab, "🛠️ Maintenance")
            self.logger.info("All tabs initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize tabs: {e}")
            self.show_error("Initialization Error", f"Failed to initialize application tabs: {e}")
    
    def init_status_bar(self):
        """Initialize the status bar"""
        self.status_bar = self.statusBar()
        
        # System status label
        self.system_status_label = QLabel("System Ready")
        self.status_bar.addWidget(self.system_status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Environment label
        env_label = QLabel(f"Environment: {self.config.environment}")
        self.status_bar.addPermanentWidget(env_label)
    
    def init_menu_bar(self):
        """Initialize the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # Exit action
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('&Tools')
        
        # Export action
        export_action = QAction('&Export Corpus', self)
        export_action.setStatusTip('Export corpus data')
        export_action.triggered.connect(self.export_corpus)
        tools_menu.addAction(export_action)
        
        # Import action
        import_action = QAction('&Import Corpus', self)
        import_action.setStatusTip('Import corpus data')
        import_action.triggered.connect(self.import_corpus)
        tools_menu.addAction(import_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        # About action
        about_action = QAction('&About', self)
        about_action.setStatusTip('About CryptoFinance Corpus Builder')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def init_toolbar(self):
        """Initialize the toolbar"""
        toolbar = self.addToolBar('Main')
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        
        # Quick actions
        start_collection_action = QAction('Start Collection', self)
        start_collection_action.setStatusTip('Start data collection')
        start_collection_action.triggered.connect(self.quick_start_collection)
        toolbar.addAction(start_collection_action)
        
        toolbar.addSeparator()
        
        start_processing_action = QAction('Start Processing', self)
        start_processing_action.setStatusTip('Start data processing')
        start_processing_action.triggered.connect(self.quick_start_processing)
        toolbar.addAction(start_processing_action)
    
    def connect_signals(self):
        """Connect signals between components"""
        # Tab change signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Connect tab signals to status updates
        if getattr(self, "collectors_tab", None) and hasattr(self.collectors_tab, 'collection_started'):
            self.collectors_tab.collection_started.connect(self.on_collection_started)
            self.collectors_tab.collection_finished.connect(self.on_collection_finished)
        
        if getattr(self, "processors_tab", None) and hasattr(self.processors_tab, 'processing_started'):
            self.processors_tab.processing_started.connect(self.on_processing_started)
            self.processors_tab.processing_finished.connect(self.on_processing_finished)
        
        # Connect dashboard View All signal to show full activity tab
        if getattr(self, "dashboard_tab", None) and hasattr(self.dashboard_tab, 'view_all_activity_requested'):
            self.dashboard_tab.view_all_activity_requested.connect(self.show_full_activity_tab)
    
    def setup_update_timer(self):
        """Setup timer for periodic updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    def on_tab_changed(self, index):
        """Handle tab change"""
        tab_names = ["Dashboard", "Collectors", "Processors", "Corpus Manager", 
                     "Balancer", "Analytics", "Configuration", "Logs"]
        if 0 <= index < len(tab_names):
            self.system_status_label.setText(f"Viewing: {tab_names[index]}")
    
    def on_collection_started(self, collector_name):
        """Handle collection start"""
        self.system_status_label.setText(f"Collecting: {collector_name}")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
    
    def on_collection_finished(self, collector_name, success):
        """Handle collection finish"""
        status = "completed" if success else "failed"
        self.system_status_label.setText(f"Collection {status}: {collector_name}")
        self.progress_bar.setVisible(False)
    
    def on_processing_started(self, processor_name):
        """Handle processing start"""
        self.system_status_label.setText(f"Processing: {processor_name}")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
    
    def on_processing_finished(self, processor_name, success):
        """Handle processing finish"""
        status = "completed" if success else "failed"
        self.system_status_label.setText(f"Processing {status}: {processor_name}")
        self.progress_bar.setVisible(False)
    
    def update_status(self):
        """Update status periodically"""
        # Update system status if no operations running
        if not self.progress_bar.isVisible():
            self.system_status_label.setText("System Ready")
    
    def quick_start_collection(self):
        """Quick start collection from toolbar"""
        self.tab_widget.setCurrentIndex(1)  # Switch to collectors tab
        # Trigger quick collection if available
        if getattr(self, "collectors_tab", None) and hasattr(self.collectors_tab, 'quick_start'):
            self.collectors_tab.quick_start()
    
    def quick_start_processing(self):
        """Quick start processing from toolbar"""
        self.tab_widget.setCurrentIndex(2)  # Switch to processors tab
        # Trigger quick processing if available
        if getattr(self, "processors_tab", None) and hasattr(self.processors_tab, 'quick_start'):
            self.processors_tab.quick_start()
    
    def export_corpus(self):
        """Export corpus data"""
        # TODO: Implement corpus export
        QMessageBox.information(self, "Export", "Corpus export functionality coming soon!")
    
    def import_corpus(self):
        """Import corpus data"""
        # TODO: Implement corpus import
        QMessageBox.information(self, "Import", "Corpus import functionality coming soon!")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>CryptoFinance Corpus Builder v3</h2>
        <p>A comprehensive tool for building and managing cryptocurrency research corpora.</p>
        <p><b>Features:</b></p>
        <ul>
        <li>Multi-source data collection</li>
        <li>Advanced text processing</li>
        <li>Corpus balancing and analytics</li>
        <li>Real-time monitoring</li>
        </ul>
        <p><b>© 2025 CryptoFinance Research</b></p>
        """
        QMessageBox.about(self, "About", about_text)
    
    def show_error(self, title, message):
        """Show error dialog"""
        QMessageBox.critical(self, title, message)
    
    def show_full_activity_tab(self):
        """Show the full activity tab when View All is clicked"""
        try:
            # Check if Full Activity tab already exists
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == "📊 Full Activity":
                    # Tab exists, switch to it
                    self.tab_widget.setCurrentIndex(i)
                    return
            
            # Create new Full Activity tab
            if not self.full_activity_tab:
                self.full_activity_tab = FullActivityTab(self.config)
            
            # Add the tab and switch to it
            tab_index = self.tab_widget.addTab(self.full_activity_tab, "📊 Full Activity")
            self.tab_widget.setCurrentIndex(tab_index)
            
            self.logger.info("Full Activity tab opened successfully")
            
        except Exception as e:
            self.logger.error(f"Error opening Full Activity tab: {e}")
            self.show_error("Tab Error", f"Failed to open Full Activity tab: {e}")
    
    def center_on_screen(self):
        """Center the window on the screen"""
        screen = self.screen().availableGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop any running operations
        try:
            if getattr(self, "collectors_tab", None) and hasattr(self.collectors_tab, 'stop_all'):
                self.collectors_tab.stop_all()
            if getattr(self, "processors_tab", None) and hasattr(self.processors_tab, 'stop_all'):
                self.processors_tab.stop_all()
        except Exception as e:
            self.logger.error(f"Error stopping operations: {e}")
        
        # Accept the close event
        event.accept()
        self.logger.info("Main window closed")
