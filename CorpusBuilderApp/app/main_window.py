"""
Main window for Crypto Corpus Builder
"""

from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QStatusBar,
    QMenuBar,
    QToolBar,
    QProgressBar,
    QLabel,
    QSplitter,
    QMessageBox,
    QMenu,
    QFileDialog,
)
from PySide6.QtCore import Qt, QTimer, Signal as pyqtSignal, QThread
from PySide6.QtGui import QAction, QIcon
import logging
from pathlib import Path
import shutil
import zipfile

# Import all tab widgets
from ui.tabs.dashboard_tab import DashboardTab
from ui.tabs.collectors_tab import CollectorsTab
from ui.tabs.processors_tab import ProcessorsTab
from ui.tabs.corpus_manager_tab import CorpusManagerTab
from ui.tabs.balancer_tab import BalancerTab
from ui.tabs.analytics_tab import AnalyticsTab
from ui.tabs.configuration_tab import ConfigurationTab
from ui.tabs.logs_tab import LogsTab
from ui.tabs.full_activity_tab import FullActivityTab
from ui.tabs.monitoring_tab import MonitoringTab
from ui.dialogs.settings_dialog import SettingsDialog
from shared_tools.ui_wrappers.processors.corpus_balancer_wrapper import CorpusBalancerWrapper
from shared_tools.services.activity_log_service import ActivityLogService
from shared_tools.services.task_history_service import TaskHistoryService
from shared_tools.services.tab_audit_service import TabAuditService
from shared_tools.services.task_queue_manager import TaskQueueManager

class CryptoCorpusMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, config):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(
            "MainWindow received config type: %s", type(config)
        )
        self.logger.debug("MainWindow received config value: %s", config)
        self.logger.debug(
            "Config has 'get' method: %s", hasattr(config, "get")
        )
        self.config = config

        # Services and wrappers
        self.activity_log_service = ActivityLogService()
        self.task_history_service = TaskHistoryService()
        self.task_queue_manager = TaskQueueManager()
        self.balancer_wrapper = CorpusBalancerWrapper(self.config)
        self.balancer_wrapper.balance_completed.connect(self.on_balance_completed)
        
        # Initialize tab attributes to None
        self.dashboard_tab = None
        self.collectors_tab = None
        self.processors_tab = None
        self.corpus_manager_tab = None
        self.balancer_tab = None
        self.analytics_tab = None
        self.configuration_tab = None
        self.logs_tab = None
        self.full_activity_tab = None
        self.monitoring_tab = None

        # Settings dialog for application preferences
        self.settings_dialog = SettingsDialog(current_settings=getattr(self.config, 'config', {}), parent=self)
        self.settings_dialog.settings_saved.connect(self.on_settings_saved)
        
        # Initialize UI
        self.init_ui()
        self.init_status_bar()
        self.init_menu_bar()
        self.init_toolbar()
        
        # Connect signals
        self.connect_signals()
        
        # Setup update timer
        self.setup_update_timer()

        # Run a startup audit of tab connections
        try:
            self.tab_audit_service = TabAuditService(self)
            self.tab_audit_service.audit()
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Tab audit failed: %s", exc)

        self.logger.info("Main window initialized")
    
    def init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle("Crypto Corpus Builder v3")
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
            self.logger.debug(
                "About to initialize tabs with config type: %s", type(self.config)
            )
            self.logger.debug(
                "About to initialize tabs with config value: %s", self.config
            )
            # Dashboard tab
            self.logger.debug("Initializing DashboardTab...")
            self.dashboard_tab = DashboardTab(
                self.config,
                self.activity_log_service,
                task_queue_manager=self.task_queue_manager,
            )
            self.dashboard_tab.view_all_activity_requested.connect(
                lambda: self.switch_to_tab("full_activity_tab")
            )
            self.logger.debug("DashboardTab initialized successfully")
            self.tab_widget.addTab(self.dashboard_tab, "📊 Dashboard")
            # Collectors tab
            self.logger.debug("Initializing CollectorsTab...")
            self.collectors_tab = CollectorsTab(self.config, task_history_service=self.task_history_service)
            self.logger.debug("CollectorsTab initialized successfully")
            self.tab_widget.addTab(self.collectors_tab, "🔍 Collectors")
            # Processors tab
            self.logger.debug("Initializing ProcessorsTab...")
            self.processors_tab = ProcessorsTab(self.config, task_history_service=self.task_history_service)
            self.logger.debug("ProcessorsTab initialized successfully")
            self.tab_widget.addTab(self.processors_tab, "⚙️ Processors")
            # Corpus Manager tab
            self.logger.debug("Initializing CorpusManagerTab...")
            self.corpus_manager_tab = CorpusManagerTab(
                self.config, activity_log_service=self.activity_log_service
            )
            self.logger.debug("CorpusManagerTab initialized successfully")
            self.tab_widget.addTab(self.corpus_manager_tab, "📁 Corpus Manager")
            # Balancer tab
            self.logger.debug("Initializing BalancerTab...")
            self.balancer_tab = BalancerTab(self.config)
            self.logger.debug("BalancerTab initialized successfully")
            self.tab_widget.addTab(self.balancer_tab, "⚖️ Balancer")
            # Analytics tab
            self.logger.debug("Initializing AnalyticsTab...")
            self.analytics_tab = AnalyticsTab(self.config)
            self.logger.debug("AnalyticsTab initialized successfully")
            self.tab_widget.addTab(self.analytics_tab, "📈 Analytics")
            # Configuration tab
            self.logger.debug("Initializing ConfigurationTab...")
            self.configuration_tab = ConfigurationTab(self.config)
            self.logger.debug("ConfigurationTab initialized successfully")
            self.tab_widget.addTab(self.configuration_tab, "⚙️ Configuration")
            # Logs tab
            self.logger.debug("Initializing LogsTab...")
            self.logs_tab = LogsTab(self.config)
            self.logger.debug("LogsTab initialized successfully")
            self.tab_widget.addTab(self.logs_tab, "📝 Logs")
            self.logger.info("All tabs initialized successfully")

            # Registry for runtime tab audits
            self.tab_registry = {
                "dashboard_tab": self.dashboard_tab,
                "collectors_tab": self.collectors_tab,
                "processors_tab": self.processors_tab,
                "balancer_tab": self.balancer_tab,
                "corpus_manager_tab": self.corpus_manager_tab,
                "configuration_tab": self.configuration_tab,
                "logs_tab": self.logs_tab,
                "analytics_tab": self.analytics_tab,
                "full_activity_tab": self.full_activity_tab,
                "monitoring_tab": self.monitoring_tab,
            }

            # Full Activity tab
            self.logger.debug("Initializing FullActivityTab...")
            self.full_activity_tab = FullActivityTab(
                self.config,
                activity_log_service=self.activity_log_service,
                task_history_service=self.task_history_service,
            )
            self.logger.debug("FullActivityTab initialized successfully")
            self.tab_widget.addTab(self.full_activity_tab, "📊 Full Activity")
            self.tab_registry.update({
                "full_activity_tab": self.full_activity_tab,
            })

            # Monitoring tab
            self.logger.debug("Initializing MonitoringTab...")
            self.monitoring_tab = MonitoringTab(self.config, parent=self)
            self.logger.debug("MonitoringTab initialized successfully")
            self.tab_widget.addTab(self.monitoring_tab, "Monitoring")
            self.tab_registry.update({
                'monitoring_tab': self.monitoring_tab,
            })
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
        about_action.setStatusTip('About Crypto Corpus Builder')
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

        if getattr(self, "configuration_tab", None) and hasattr(self.configuration_tab, 'configuration_saved'):
            self.configuration_tab.configuration_saved.connect(lambda _: self.config.save())
            if getattr(self, "dashboard_tab", None):
                self.configuration_tab.configuration_saved.connect(lambda _: self.dashboard_tab.update_environment_info())
            if self.activity_log_service:
                self.configuration_tab.configuration_saved.connect(
                    lambda _: self.activity_log_service.log("Configuration", "Settings saved")
                )

        # Connect dashboard signals
        if getattr(self, "dashboard_tab", None):
            if hasattr(self.dashboard_tab, 'view_all_activity_requested'):
                self.dashboard_tab.view_all_activity_requested.connect(self.show_full_activity_tab)
            if hasattr(self.dashboard_tab, 'rebalance_requested'):
                self.dashboard_tab.rebalance_requested.connect(self.on_rebalance_requested)

        # Refresh collectors when balancing completes
        if getattr(self, "balancer_tab", None) and hasattr(self.balancer_tab, "balancer"):
            balancer = self.balancer_tab.balancer
            if hasattr(balancer, "balance_completed"):
                balancer.balance_completed.connect(self.on_balance_completed)
    
    def setup_update_timer(self):
        """Setup timer for periodic updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    def on_tab_changed(self, index):
        """Handle tab change"""
        tab_names = ["Dashboard", "Collectors", "Processors", "Corpus Manager", 
                     "Balancer", "Analytics", "Configuration", "Logs", "Full Activity", "Monitoring"]
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

    def on_settings_saved(self, settings):
        """Persist settings from the settings dialog."""
        for key, value in settings.items():
            try:
                self.config.set(key, value)
            except Exception as exc:
                self.logger.error("Failed to set config %s: %s", key, exc)
        self.config.save()
    
    def export_corpus(self):
        """Export corpus data"""
        corpus_dir = None
        if hasattr(self.config, "get_corpus_dir"):
            try:
                corpus_dir = Path(self.config.get_corpus_dir())
            except Exception:  # pragma: no cover - defensive
                corpus_dir = None

        if not corpus_dir or not corpus_dir.exists():
            QMessageBox.critical(self, "Export Error", "Corpus directory not found")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Corpus",
            "corpus_export.zip",
            "ZIP Files (*.zip);;All Files (*)",
        )

        if not file_path:
            return

        if not file_path.endswith(".zip"):
            file_path += ".zip"

        archive_base = str(Path(file_path).with_suffix(""))

        try:
            shutil.make_archive(archive_base, "zip", corpus_dir)
            QMessageBox.information(
                self,
                "Export Complete",
                f"Corpus exported to {file_path}",
            )
            if self.activity_log_service:
                self.activity_log_service.log("Corpus", f"Exported corpus to {file_path}")
        except Exception as exc:  # pragma: no cover - runtime guard
            self.logger.error("Corpus export failed: %s", exc)
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export corpus: {exc}",
            )

    def import_corpus(self):
        """Import corpus data"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Corpus",
            "",
            "ZIP Files (*.zip);;All Files (*)",
        )

        if not file_path:
            return

        corpus_dir = None
        if hasattr(self.config, "get_corpus_dir"):
            try:
                corpus_dir = Path(self.config.get_corpus_dir())
            except Exception:  # pragma: no cover - defensive
                corpus_dir = None

        if not corpus_dir:
            QMessageBox.critical(self, "Import Error", "Corpus directory not configured")
            return

        corpus_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(corpus_dir)

            QMessageBox.information(
                self,
                "Import Complete",
                f"Corpus imported from {file_path}",
            )
            if self.activity_log_service:
                self.activity_log_service.log("Corpus", f"Imported corpus from {file_path}")
            if getattr(self, "corpus_manager_tab", None) and hasattr(
                self.corpus_manager_tab, "refresh_file_view"
            ):
                try:
                    self.corpus_manager_tab.refresh_file_view()
                except Exception:  # pragma: no cover - defensive
                    pass
        except Exception as exc:  # pragma: no cover - runtime guard
            self.logger.error("Corpus import failed: %s", exc)
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import corpus: {exc}",
            )
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>Crypto Corpus Builder v3</h2>
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

    def on_rebalance_requested(self):
        """Handle manual rebalance requests from the dashboard."""
        if self.activity_log_service:
            self.activity_log_service.log("Balancer", "Manual rebalancing initiated from Dashboard")
        self.balancer_wrapper.balance_corpus()
    
    def show_full_activity_tab(self):
        """Show the full activity tab when View All is clicked"""
        try:
            print("[DEBUG] show_full_activity_tab called")
            # Check if Full Activity tab already exists
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == "📊 Full Activity":
                    # Tab exists, switch to it
                    self.tab_widget.setCurrentIndex(i)
                    return
            
            # Create new Full Activity tab
            if not self.full_activity_tab:
                self.full_activity_tab = FullActivityTab(
                    self.config,
                    activity_log_service=self.activity_log_service,
                    task_history_service=self.task_history_service,
                )
                self.full_activity_tab.retry_requested.connect(self.on_retry_requested)
                self.full_activity_tab.stop_requested.connect(self.on_stop_requested)
            
            # Add the tab and switch to it
            tab_index = self.tab_widget.addTab(self.full_activity_tab, "📊 Full Activity")
            self.tab_widget.setCurrentIndex(tab_index)
            
            self.logger.info("Full Activity tab opened successfully")
            
        except Exception as e:
            self.logger.error(f"Error opening Full Activity tab: {e}")
            self.show_error("Tab Error", f"Failed to open Full Activity tab: {e}")

    def on_retry_requested(self, task_id: str) -> None:
        """Handle retry requests from the Full Activity tab."""
        self.logger.info("Retry requested for task %s", task_id)

    def on_stop_requested(self, task_id: str) -> None:
        """Handle stop requests from the Full Activity tab."""
        self.logger.info("Stop requested for task %s", task_id)
    
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

    def on_balance_completed(self):
        """Refresh collectors and log completion of corpus rebalancing."""
        if getattr(self, "collectors_tab", None):
            wrappers = getattr(self.collectors_tab, "collector_wrappers", {})
            for wrapper in wrappers.values():
                if hasattr(wrapper, "refresh_config"):
                    try:
                        wrapper.refresh_config()
                    except Exception as e:  # pragma: no cover
                        self.logger.error(
                            f"Failed to refresh config for collector {getattr(wrapper, 'name', 'unknown')}: {e}"
                        )
        else:
            message = "Corpus balancing completed (no collectors tab found)."

        try:
            if self.activity_log_service:
                self.activity_log_service.log("Balancer", message)
            else:
                self.logger.info(message)
        except Exception as e:
            self.logger.error(f"Failed to log activity: {e}")

    def switch_to_tab(self, tab_key: str):
        tab = self.tab_registry.get(tab_key)
        if tab:
            index = self.tab_widget.indexOf(tab)
            if index >= 0:
                self.tab_widget.setCurrentIndex(index) 
     