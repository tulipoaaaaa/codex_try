from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QLabel, QProgressBar, QPushButton, QComboBox,
                             QSpinBox, QLineEdit, QGroupBox, QScrollArea)
from PySide6.QtCore import Qt, Slot as pyqtSlot

from shared_tools.ui_wrappers.collectors.isda_wrapper import ISDAWrapper
from shared_tools.ui_wrappers.collectors.github_wrapper import GitHubWrapper
from shared_tools.ui_wrappers.collectors.annas_archive_wrapper import AnnasArchiveWrapper
from shared_tools.ui_wrappers.collectors.arxiv_wrapper import ArxivWrapper
from shared_tools.ui_wrappers.collectors.fred_wrapper import FREDWrapper
from shared_tools.ui_wrappers.collectors.bitmex_wrapper import BitMEXWrapper
from shared_tools.ui_wrappers.collectors.quantopian_wrapper import QuantopianWrapper
from shared_tools.ui_wrappers.collectors.scidb_wrapper import SciDBWrapper
from shared_tools.ui_wrappers.collectors.web_wrapper import WebWrapper
from app.helpers.notifier import Notifier


class CollectorsTab(QWidget):
    def __init__(self, project_config, parent=None):
        super().__init__(parent)
        self.project_config = project_config
        self.collector_wrappers = {}
        self.init_collectors()
        self.setup_ui()
        self.connect_signals()
        self.sound_enabled = True  # Will be set from user settings

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Collector tabs widget
        self.collector_tabs = QTabWidget()
        
        # Create tabs for each collector using initialized wrappers
        for name, label in [
            ('isda', "ISDA"),
            ('github', "GitHub"),
            ('anna', "Anna's Archive"),
            ('arxiv', "arXiv"),
            ('fred', "FRED"),
            ('bitmex', "BitMEX"),
            ('quantopian', "Quantopian"),
            ('scidb', "SciDB"),
            ('web', "Web")
        ]:
            print(f"Adding tab: {name}, type: {type(self.collector_wrappers[name])}")
            
            # Create a QWidget container for each wrapper
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            
            # Add the wrapper to the container widget
            wrapper = self.collector_wrappers[name]
            
            # If wrapper is not a QWidget, create a placeholder
            if not isinstance(wrapper, QWidget):
                placeholder_label = QLabel(f"{label} collector interface not yet implemented")
                placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                tab_layout.addWidget(placeholder_label)
                
                # Add basic controls for testing
                start_btn = QPushButton(f"Start {label} Collection")
                stop_btn = QPushButton(f"Stop {label} Collection") 
                progress_bar = QProgressBar()
                status_label = QLabel("Ready")
                
                controls_layout = QHBoxLayout()
                controls_layout.addWidget(start_btn)
                controls_layout.addWidget(stop_btn)
                
                tab_layout.addLayout(controls_layout)
                tab_layout.addWidget(progress_bar)
                tab_layout.addWidget(status_label)
                tab_layout.addStretch()
                
                # Store references to UI elements for signal connections
                setattr(self, f"{name}_start_btn", start_btn)
                setattr(self, f"{name}_stop_btn", stop_btn)
                setattr(self, f"{name}_progress_bar", progress_bar)
                setattr(self, f"{name}_status", status_label)
            else:
                tab_layout.addWidget(wrapper)
            
            self.collector_tabs.addTab(tab_widget, label)
        
        main_layout.addWidget(self.collector_tabs)
        
        # Add a status/summary area at the bottom
        status_group = QGroupBox("Collection Status")
        status_layout = QVBoxLayout(status_group)
        
        self.collection_status_label = QLabel("")
        self.collection_status_label.setObjectName("status-info")
        status_layout.addWidget(self.collection_status_label)
        
        # Overall progress bar
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        status_layout.addWidget(self.overall_progress)
        
        # Button for stopping all collectors
        stop_all_btn = QPushButton("Stop All Collectors")
        stop_all_btn.clicked.connect(self.stop_all_collectors)
        status_layout.addWidget(stop_all_btn)
        
        main_layout.addWidget(status_group)

    def init_collectors(self):
        # Initialize all collector wrappers
        self.collector_wrappers['isda'] = ISDAWrapper(self.project_config)
        self.collector_wrappers['github'] = GitHubWrapper(self.project_config)
        self.collector_wrappers['anna'] = AnnasArchiveWrapper(self.project_config)
        self.collector_wrappers['arxiv'] = ArxivWrapper(self.project_config)
        self.collector_wrappers['fred'] = FREDWrapper(self.project_config)
        self.collector_wrappers['bitmex'] = BitMEXWrapper(self.project_config)
        self.collector_wrappers['quantopian'] = QuantopianWrapper(self.project_config)
        self.collector_wrappers['scidb'] = SciDBWrapper(self.project_config)
        self.collector_wrappers['web'] = WebWrapper(self.project_config)

    def connect_signals(self):
        """Connect signals with defensive checks."""
        # Connect signals for ISDA collector if they exist
        isda_wrapper = self.collector_wrappers.get('isda')
        if isda_wrapper:
            # Connect signals only if they exist
            if hasattr(isda_wrapper, 'progress_updated'):
                isda_wrapper.progress_updated.connect(self.update_progress)
            if hasattr(isda_wrapper, 'status_updated'):
                isda_wrapper.status_updated.connect(self.update_status)
            if hasattr(isda_wrapper, 'collection_completed'):
                isda_wrapper.collection_completed.connect(self.on_isda_collection_completed)
        
        # Connect signals for GitHub collector if they exist
        github_wrapper = self.collector_wrappers.get('github')
        if github_wrapper:
            if hasattr(github_wrapper, 'progress_updated'):
                github_wrapper.progress_updated.connect(self.update_progress)
            if hasattr(github_wrapper, 'status_updated'):
                github_wrapper.status_updated.connect(self.update_status)
            if hasattr(github_wrapper, 'collection_completed'):
                github_wrapper.collection_completed.connect(self.on_github_collection_completed)
        
        # Add similar defensive connections for other collectors
        for name in ['anna', 'arxiv', 'fred', 'bitmex', 'quantopian', 'scidb', 'web']:
            wrapper = self.collector_wrappers.get(name)
            if wrapper:
                if hasattr(wrapper, 'progress_updated'):
                    wrapper.progress_updated.connect(self.update_progress)
                if hasattr(wrapper, 'status_updated'):
                    wrapper.status_updated.connect(self.update_status)
                if hasattr(wrapper, 'collection_completed'):
                    wrapper.collection_completed.connect(
                        lambda results, n=name: self.on_collection_completed(n, results)
                    )
        
        print("DEBUG: Signal connections set up with defensive checks")
    
    def update_progress(self, value):
        """Update overall progress"""
        if hasattr(self, 'overall_progress'):
            self.overall_progress.setValue(value)
    
    def update_status(self, message):
        """Update status message"""
        if hasattr(self, 'collection_status_label'):
            self.collection_status_label.setText(message)
    
    def on_isda_collection_completed(self, results):
        """Handle ISDA collection completion"""
        print(f"DEBUG: ISDA collection completed with results: {results}")
        self.update_status("ISDA collection completed")
        if hasattr(self, 'isda_start_btn'):
            self.isda_start_btn.setEnabled(True)
        if hasattr(self, 'isda_stop_btn'):
            self.isda_stop_btn.setEnabled(False)
    
    def on_github_collection_completed(self, results):
        """Handle GitHub collection completion"""
        print(f"DEBUG: GitHub collection completed with results: {results}")
        self.update_status("GitHub collection completed")
        if hasattr(self, 'github_start_btn'):
            self.github_start_btn.setEnabled(True)
        if hasattr(self, 'github_stop_btn'):
            self.github_stop_btn.setEnabled(False)
    
    def on_collection_completed(self, collector_name, results):
        """Generic handler for collection completion"""
        print(f"DEBUG: {collector_name} collection completed with results: {results}")
        self.update_status(f"{collector_name} collection completed")
        if hasattr(self, f'{collector_name}_start_btn'):
            getattr(self, f'{collector_name}_start_btn').setEnabled(True)
        if hasattr(self, f'{collector_name}_stop_btn'):
            getattr(self, f'{collector_name}_stop_btn').setEnabled(False)
    
    def start_isda_collection(self):
        """Start ISDA collection"""
        print("DEBUG: ISDA collection start requested")
        if hasattr(self, 'isda_start_btn'):
            self.isda_start_btn.setEnabled(False)
        if hasattr(self, 'isda_stop_btn'):
            self.isda_stop_btn.setEnabled(True)
    
    def stop_isda_collection(self):
        """Stop ISDA collection"""
        print("DEBUG: ISDA collection stop requested")
        if hasattr(self, 'isda_start_btn'):
            self.isda_start_btn.setEnabled(True)
        if hasattr(self, 'isda_stop_btn'):
            self.isda_stop_btn.setEnabled(False)
    
    def start_github_collection(self):
        """Start GitHub collection"""
        print("DEBUG: GitHub collection start requested")
        if hasattr(self, 'github_start_btn'):
            self.github_start_btn.setEnabled(False)
        if hasattr(self, 'github_stop_btn'):
            self.github_stop_btn.setEnabled(True)
    
    def stop_github_collection(self):
        """Stop GitHub collection"""
        print("DEBUG: GitHub collection stop requested")
        if hasattr(self, 'github_start_btn'):
            self.github_start_btn.setEnabled(True)
        if hasattr(self, 'github_stop_btn'):
            self.github_stop_btn.setEnabled(False)
    
    def stop_all_collectors(self):
        for collector_name, wrapper in self.collector_wrappers.items():
            wrapper.stop()
        
        # Reset UI elements
        self.isda_start_btn.setEnabled(True)
        self.isda_stop_btn.setEnabled(False)
        self.github_start_btn.setEnabled(True)
        self.github_stop_btn.setEnabled(False)
        # Reset other collector buttons similarly
        
        self.collection_status_label.setText("All collectors stopped")
