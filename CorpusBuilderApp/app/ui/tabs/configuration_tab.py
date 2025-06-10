from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QLabel, QPushButton, QLineEdit, QComboBox,
                             QTabWidget, QFileDialog, QCheckBox, QFormLayout,
                             QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox)
from PySide6.QtCore import Qt, Slot as pyqtSlot, QMimeData, Signal as pyqtSignal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv, set_key
from pydantic import ValidationError
from app.helpers.crypto_utils import encrypt_value, decrypt_value
from app.ui.widgets.section_header import SectionHeader
from app.ui.theme.theme_constants import PAGE_MARGIN


class ConfigurationTab(QWidget):
    """Tab for viewing and editing project configuration."""

    configuration_saved = pyqtSignal(dict)
    def __init__(self, project_config, parent=None):
        super().__init__(parent)
        self.project_config = project_config
        self.env_path = Path(project_config.config_path).parent / '.env'
        self.setup_ui()
        self.load_current_config()
        # Enable drop events
        self.setAcceptDrops(True)
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
        main_layout.setSpacing(PAGE_MARGIN)
        
        # Create tabs for different configuration sections
        self.config_tabs = QTabWidget()
        
        # Environment tab
        env_tab = self.create_environment_tab()
        self.config_tabs.addTab(env_tab, "Environment")
        
        # API Keys tab
        api_tab = self.create_api_keys_tab()
        self.config_tabs.addTab(api_tab, "API Keys")
        
        # Directories tab
        dir_tab = self.create_directories_tab()
        self.config_tabs.addTab(dir_tab, "Directories")
        
        # Domains tab
        domains_tab = self.create_domains_tab()
        self.config_tabs.addTab(domains_tab, "Domains")
        
        # Processing tab
        processing_tab = self.create_processing_tab()
        self.config_tabs.addTab(processing_tab, "Processing")
        
        main_layout.addWidget(self.config_tabs)
        
        # Control buttons at the bottom
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.clicked.connect(self.save_configuration)
        buttons_layout.addWidget(self.save_btn)
        
        self.reset_btn = QPushButton("Reset to Current")
        self.reset_btn.clicked.connect(self.load_current_config)
        buttons_layout.addWidget(self.reset_btn)
        
        self.default_btn = QPushButton("Reset to Defaults")
        self.default_btn.clicked.connect(self.load_default_config)
        buttons_layout.addWidget(self.default_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # Add drag-and-drop area for importing config files
        self.drop_area = QLabel("Drop config file here to import")
        self.drop_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_area.setObjectName("config-drop-area")
        main_layout.addWidget(self.drop_area)
    
    def create_environment_tab(self):
        """Create the environment configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Environment selection
        env_group = QGroupBox("Environment")
        env_layout = QVBoxLayout(env_group)
        
        # Environment selector
        form_layout = QFormLayout()
        self.env_selector = QComboBox()
        self.env_selector.addItems(["test", "master", "production"])
        self.env_selector.currentIndexChanged.connect(self.on_environment_changed)
        form_layout.addRow("Active Environment:", self.env_selector)
        
        # Config file path
        self.config_path = QLineEdit()
        self.config_path.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_config_file)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.config_path)
        path_layout.addWidget(browse_btn)
        form_layout.addRow("Config File:", path_layout)
        
        env_layout.addLayout(form_layout)
        
        # Environment variables
        env_vars_group = QGroupBox("Environment Variables")
        env_vars_layout = QVBoxLayout(env_vars_group)
        
        # Python executable
        python_layout = QHBoxLayout()
        python_layout.addWidget(QLabel("Python Executable:"))
        self.python_path = QLineEdit()
        python_layout.addWidget(self.python_path)
        python_browse = QPushButton("Browse...")
        python_browse.clicked.connect(self.browse_python_executable)
        python_layout.addWidget(python_browse)
        env_vars_layout.addLayout(python_layout)
        
        # Virtual environment
        venv_layout = QHBoxLayout()
        venv_layout.addWidget(QLabel("Virtual Environment:"))
        self.venv_path = QLineEdit()
        self.venv_path.setPlaceholderText('venv/')
        venv_browse = QPushButton("Browse...")
        venv_browse.clicked.connect(self.browse_venv_path)
        venv_layout.addWidget(self.venv_path)
        venv_layout.addWidget(venv_browse)
        env_vars_layout.addLayout(venv_layout)
        
        # Temp directory
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Temp Directory:"))
        self.temp_dir = QLineEdit()
        temp_layout.addWidget(self.temp_dir)
        temp_browse = QPushButton("Browse...")
        temp_browse.clicked.connect(self.browse_temp_dir)
        temp_layout.addWidget(temp_browse)
        env_vars_layout.addLayout(temp_layout)
        
        # Auto-save option
        self.auto_save = QCheckBox("Auto-save environment when changed")
        self.auto_save.setChecked(True)
        env_vars_layout.addWidget(self.auto_save)
        
        # Add the groups to the tab
        layout.addWidget(env_group)
        layout.addWidget(env_vars_group)
        layout.addStretch()
        
        return tab
    
    def create_api_keys_tab(self):
        """Create the API keys configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # API Keys form
        keys_group = QGroupBox("API Credentials")
        keys_layout = QFormLayout(keys_group)
        
        # GitHub
        self.github_token = QLineEdit()
        self.github_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.github_token.setPlaceholderText("Enter GitHub API token")
        self.github_token.setToolTip("Enter your GitHub API token. This will be stored securely in .env or encrypted config. Never stored in plaintext.")
        keys_layout.addRow("GitHub Token:", self.github_token)
        
        # Anna's Archive
        self.aa_cookie = QLineEdit()
        self.aa_cookie.setEchoMode(QLineEdit.EchoMode.Password)
        self.aa_cookie.setPlaceholderText("Enter Anna's Archive cookie")
        self.aa_cookie.setToolTip("Enter your Anna's Archive cookie. This will be stored securely in .env or encrypted config. Never stored in plaintext.")
        keys_layout.addRow("Anna's Archive Cookie:", self.aa_cookie)
        
        # FRED API
        self.fred_key = QLineEdit()
        self.fred_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.fred_key.setPlaceholderText("Enter FRED API key")
        self.fred_key.setToolTip("Enter your FRED API key. This will be stored securely in .env or encrypted config. Never stored in plaintext.")
        keys_layout.addRow("FRED API Key:", self.fred_key)
        
        # BitMEX API
        self.bitmex_key = QLineEdit()
        self.bitmex_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.bitmex_key.setPlaceholderText("Enter BitMEX API key")
        self.bitmex_key.setToolTip("Enter your BitMEX API key. This will be stored securely in .env or encrypted config. Never stored in plaintext.")
        keys_layout.addRow("BitMEX API Key:", self.bitmex_key)
        
        self.bitmex_secret = QLineEdit()
        self.bitmex_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self.bitmex_secret.setPlaceholderText("Enter BitMEX API secret")
        self.bitmex_secret.setToolTip("Enter your BitMEX API secret. This will be stored securely in .env or encrypted config. Never stored in plaintext.")
        keys_layout.addRow("BitMEX API Secret:", self.bitmex_secret)
        
        # arXiv
        self.arxiv_email = QLineEdit()
        self.arxiv_email.setPlaceholderText("Enter contact email for arXiv API")
        self.arxiv_email.setToolTip("Enter your contact email for arXiv API. This will be stored securely in .env or encrypted config. Never stored in plaintext.")
        keys_layout.addRow("arXiv Contact Email:", self.arxiv_email)
        
        layout.addWidget(keys_group)
        
        # Secure storage options
        storage_group = QGroupBox("Credential Storage")
        storage_layout = QVBoxLayout(storage_group)
        
        self.encrypt_keys = QCheckBox("Encrypt API keys in configuration")
        self.encrypt_keys.setChecked(True)
        storage_layout.addWidget(self.encrypt_keys)
        
        self.use_env_file = QCheckBox("Store credentials in .env file (not in main config)")
        self.use_env_file.setChecked(True)
        storage_layout.addWidget(self.use_env_file)
        
        layout.addWidget(storage_group)
        layout.addStretch()
        
        return tab
    
    def create_directories_tab(self):
        """Create the directories configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Directory paths
        paths_group = QGroupBox("Directory Paths")
        paths_layout = QFormLayout(paths_group)
        
        # Corpus root
        self.corpus_root = QLineEdit()
        corpus_browse = QPushButton("Browse...")
        corpus_browse.clicked.connect(lambda: self.browse_directory(self.corpus_root, "Select Corpus Root Directory"))
        corpus_layout = QHBoxLayout()
        corpus_layout.addWidget(self.corpus_root)
        corpus_layout.addWidget(corpus_browse)
        paths_layout.addRow("Corpus Root:", corpus_layout)
        
        # Raw data
        self.raw_data_dir = QLineEdit()
        raw_browse = QPushButton("Browse...")
        raw_browse.clicked.connect(lambda: self.browse_directory(self.raw_data_dir, "Select Raw Data Directory"))
        raw_layout = QHBoxLayout()
        raw_layout.addWidget(self.raw_data_dir)
        raw_layout.addWidget(raw_browse)
        paths_layout.addRow("Raw Data:", raw_layout)
        
        # Processed data
        self.processed_dir = QLineEdit()
        processed_browse = QPushButton("Browse...")
        processed_browse.clicked.connect(lambda: self.browse_directory(self.processed_dir, "Select Processed Data Directory"))
        processed_layout = QHBoxLayout()
        processed_layout.addWidget(self.processed_dir)
        processed_layout.addWidget(processed_browse)
        paths_layout.addRow("Processed Data:", processed_layout)
        
        # Metadata
        self.metadata_dir = QLineEdit()
        metadata_browse = QPushButton("Browse...")
        metadata_browse.clicked.connect(lambda: self.browse_directory(self.metadata_dir, "Select Metadata Directory"))
        metadata_layout = QHBoxLayout()
        metadata_layout.addWidget(self.metadata_dir)
        metadata_layout.addWidget(metadata_browse)
        paths_layout.addRow("Metadata:", metadata_layout)
        
        # Logs
        self.logs_dir = QLineEdit()
        logs_browse = QPushButton("Browse...")
        logs_browse.clicked.connect(lambda: self.browse_directory(self.logs_dir, "Select Logs Directory"))
        logs_layout = QHBoxLayout()
        logs_layout.addWidget(self.logs_dir)
        logs_layout.addWidget(logs_browse)
        paths_layout.addRow("Logs:", logs_layout)
        
        layout.addWidget(paths_group)
        
        # Directory options
        options_group = QGroupBox("Directory Options")
        options_layout = QVBoxLayout(options_group)
        
        self.create_missing = QCheckBox("Create missing directories automatically")
        self.create_missing.setChecked(True)
        options_layout.addWidget(self.create_missing)
        
        self.relative_paths = QCheckBox("Use relative paths (relative to corpus root)")
        self.relative_paths.setChecked(False)
        options_layout.addWidget(self.relative_paths)
        
        self.validate_paths = QCheckBox("Validate directory paths on startup")
        self.validate_paths.setChecked(True)
        options_layout.addWidget(self.validate_paths)
        
        layout.addWidget(options_group)
        layout.addStretch()
        
        return tab
    
    def create_domains_tab(self):
        """Create the domains configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Domains table
        self.domains_table = QTableWidget(8, 3)  # 8 domains, 3 columns
        self.domains_table.setHorizontalHeaderLabels([
            "Domain", "Target %", "Description"
        ])
        
        # Set up table properties
        self.domains_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.domains_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.domains_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.domains_table.setAlternatingRowColors(True)
        
        # Initialize with domains
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
        
        # Default targets (as percentages)
        targets = [20, 15, 15, 15, 12, 10, 8, 5]
        
        # Descriptions
        descriptions = [
            "Futures, options, perpetual swaps",
            "Algorithmic trading, market making",
            "Portfolio risk, volatility models",
            "Order book dynamics, liquidity",
            "Decentralized finance protocols",
            "Asset allocation, optimization",
            "Token valuation, fundamental analysis",
            "Legal frameworks, compliance"
        ]
        
        for i, (domain, target, desc) in enumerate(zip(domains, targets, descriptions)):
            self.domains_table.setItem(i, 0, QTableWidgetItem(domain))
            self.domains_table.setItem(i, 1, QTableWidgetItem(str(target)))
            self.domains_table.setItem(i, 2, QTableWidgetItem(desc))
        
        layout.addWidget(SectionHeader("Domain Configuration"))
        layout.addWidget(self.domains_table)
        
        # Domain options
        options_group = QGroupBox("Domain Options")
        options_layout = QVBoxLayout(options_group)
        
        self.normalize_percentages = QCheckBox("Normalize percentages to 100%")
        self.normalize_percentages.setChecked(True)
        options_layout.addWidget(self.normalize_percentages)
        
        self.validate_domains = QPushButton("Validate Domain Configuration")
        self.validate_domains.clicked.connect(self.validate_domain_config)
        options_layout.addWidget(self.validate_domains)
        
        layout.addWidget(options_group)
        
        return tab
    
    def create_processing_tab(self):
        """Create the processing configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # PDF Processing options
        pdf_group = QGroupBox("PDF Processing")
        pdf_layout = QFormLayout(pdf_group)
        
        self.enable_ocr = QCheckBox("Enable OCR for scanned PDFs")
        self.enable_ocr.setChecked(True)
        pdf_layout.addRow("OCR:", self.enable_ocr)
        
        self.pdf_threads = QSpinBox()
        self.pdf_threads.setRange(1, 16)
        self.pdf_threads.setValue(4)
        pdf_layout.addRow("Worker Threads:", self.pdf_threads)
        
        self.enable_formula = QCheckBox("Extract mathematical formulas")
        self.enable_formula.setChecked(True)
        pdf_layout.addRow("Formula Extraction:", self.enable_formula)
        
        self.enable_tables = QCheckBox("Extract tables")
        self.enable_tables.setChecked(True)
        pdf_layout.addRow("Table Extraction:", self.enable_tables)
        
        layout.addWidget(pdf_group)
        
        # Text Processing options
        text_group = QGroupBox("Text Processing")
        text_layout = QFormLayout(text_group)
        
        self.text_threads = QSpinBox()
        self.text_threads.setRange(1, 16)
        self.text_threads.setValue(4)
        text_layout.addRow("Worker Threads:", self.text_threads)
        
        self.enable_language = QCheckBox("Enable language detection")
        self.enable_language.setChecked(True)
        text_layout.addRow("Language Detection:", self.enable_language)
        
        self.min_quality = QSpinBox()
        self.min_quality.setRange(0, 100)
        self.min_quality.setValue(70)
        text_layout.addRow("Minimum Quality:", self.min_quality)
        
        self.enable_deduplication = QCheckBox("Enable deduplication")
        self.enable_deduplication.setChecked(True)
        text_layout.addRow("Deduplication:", self.enable_deduplication)
        
        layout.addWidget(text_group)
        
        # Advanced options
        advanced_group = QGroupBox("Advanced Processing")
        advanced_layout = QFormLayout(advanced_group)
        
        self.batch_size = QSpinBox()
        self.batch_size.setRange(1, 1000)
        self.batch_size.setValue(50)
        advanced_layout.addRow("Batch Size:", self.batch_size)
        
        self.max_retries = QSpinBox()
        self.max_retries.setRange(0, 10)
        self.max_retries.setValue(3)
        advanced_layout.addRow("Max Retries:", self.max_retries)
        
        self.timeout = QSpinBox()
        self.timeout.setRange(10, 3600)
        self.timeout.setValue(300)
        self.timeout.setSuffix(" seconds")
        advanced_layout.addRow("Timeout:", self.timeout)
        
        layout.addWidget(advanced_group)
        layout.addStretch()
        
        return tab
    
    def browse_config_file(self):
        """Browse for a configuration file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Configuration File", "", "YAML Files (*.yaml *.yml)"
        )
        if file_path:
            self.config_path.setText(file_path)
    
    def browse_python_executable(self):
        """Browse for Python executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Python Executable", "", "Executables (*.exe);;All Files (*)"
        )
        if file_path:
            self.python_path.setText(file_path)
    
    def browse_venv_path(self):
        """Browse for virtual environment directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Virtual Environment Directory"
        )
        if directory:
            self.venv_path.setText(directory)
    
    def browse_temp_dir(self):
        """Browse for temp directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Temp Directory"
        )
        if directory:
            self.temp_dir.setText(directory)
    
    def browse_directory(self, line_edit, title):
        """Browse for a directory and update a line edit"""
        directory = QFileDialog.getExistingDirectory(self, title)
        if directory:
            line_edit.setText(directory)
    
    def on_environment_changed(self):
        """Handle environment selection change"""
        env = self.env_selector.currentText()
        
        # In a real implementation, this would load the correct environment config
        # For now, just update the config path to show the correct file
        self.config_path.setText(f"config/{env}.yaml")
        
        # If auto-save is enabled, save the current environment
        if self.auto_save.isChecked():
            # Persist the selected environment using ProjectConfig
            self.project_config.set('environment.active', env)
            self.project_config.save()
    
    def validate_domain_config(self):
        """Validate the domain configuration"""
        # Check that percentages add up to 100%
        total = 0
        for i in range(self.domains_table.rowCount()):
            try:
                percentage = float(self.domains_table.item(i, 1).text())
                total += percentage
            except (ValueError, AttributeError):
                QMessageBox.warning(
                    self, "Validation Error", 
                    f"Invalid percentage in row {i+1}. Please enter numeric values."
                )
                return
        
        # Check if total is close to 100%
        if abs(total - 100) > 0.1:
            if self.normalize_percentages.isChecked():
                # Normalize the percentages
                for i in range(self.domains_table.rowCount()):
                    try:
                        percentage = float(self.domains_table.item(i, 1).text())
                        normalized = (percentage / total) * 100
                        self.domains_table.setItem(i, 1, QTableWidgetItem(f"{normalized:.1f}"))
                    except (ValueError, AttributeError):
                        pass
                
                QMessageBox.information(
                    self, "Normalization Complete",
                    f"Percentages have been normalized from {total:.1f}% to 100%."
                )
            else:
                QMessageBox.warning(
                    self, "Validation Warning",
                    f"Domain percentages add up to {total:.1f}%, not 100%.\n"
                    "Enable normalization or adjust manually."
                )
        else:
            QMessageBox.information(
                self, "Validation Successful",
                "Domain configuration is valid."
            )
    
    def load_current_config(self):
        """Load the current configuration into UI"""
        # Load from .env file if it exists
        if self.env_path.exists():
            load_dotenv(self.env_path)
        
        # Environment tab
        self.env_selector.setCurrentText(os.getenv('ENVIRONMENT', 'test'))
        self.config_path.setText(str(self.project_config.config_path))
        self.python_path.setText(os.getenv('PYTHON_PATH', ''))
        self.venv_path.setText('venv/')
        self.temp_dir.setText(os.getenv('TEMP_DIR', ''))
        
        # API Keys tab
        self.github_token.setText(os.getenv('GITHUB_TOKEN', ''))
        self.aa_cookie.setText(os.getenv('AA_COOKIE', ''))
        self.fred_key.setText(os.getenv('FRED_API_KEY', ''))
        self.bitmex_key.setText(os.getenv('BITMEX_API_KEY', ''))
        self.bitmex_secret.setText(os.getenv('BITMEX_API_SECRET', ''))
        self.arxiv_email.setText(os.getenv('ARXIV_EMAIL', ''))
        
        # Directories tab
        self.corpus_root.setText(os.getenv('CORPUS_ROOT', '~/crypto_corpus'))
        self.raw_data_dir.setText(os.getenv('RAW_DATA_DIR', '~/crypto_corpus/raw'))
        self.processed_dir.setText(os.getenv('PROCESSED_DIR', '~/crypto_corpus/processed'))
        self.metadata_dir.setText(os.getenv('METADATA_DIR', '~/crypto_corpus/metadata'))
        self.logs_dir.setText(os.getenv('LOGS_DIR', '~/crypto_corpus/logs'))
        
        # Processing tab
        self.pdf_threads.setValue(int(os.getenv('PDF_THREADS', '4')))
        self.text_threads.setValue(int(os.getenv('TEXT_THREADS', '4')))
        self.batch_size.setValue(int(os.getenv('BATCH_SIZE', '50')))
        self.max_retries.setValue(int(os.getenv('MAX_RETRIES', '3')))
        self.timeout.setValue(int(os.getenv('TIMEOUT', '300')))
    
    def load_default_config(self):
        """Reset to default configuration.
        
        Note: This method sets up a default configuration with non-functional placeholder values.
        All credential fields are cleared and must be populated with real values before use.
        """
        # Confirm with user
        confirm = QMessageBox.question(
            self, "Confirm Reset",
            "Are you sure you want to reset to default configuration?\n\n"
            "Note: This will clear all API credentials and other sensitive information.\n"
            "You will need to re-enter these values before using the application.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            # Reset all fields to defaults
            # Environment tab
            self.env_selector.setCurrentText("test")
            self.config_path.setText("config/test.yaml")
            self.python_path.setText("")
            self.venv_path.setText("venv/")
            self.temp_dir.setText("")
            
            # API Keys tab - Clear all credential fields
            self.github_token.clear()
            self.aa_cookie.clear()
            self.fred_key.clear()
            self.bitmex_key.clear()
            self.bitmex_secret.clear()
            self.arxiv_email.clear()
            
            # Directories tab
            base_dir = os.path.expanduser("~/crypto_corpus")
            self.corpus_root.setText(base_dir)
            self.raw_data_dir.setText(f"{base_dir}/raw")
            self.processed_dir.setText(f"{base_dir}/processed")
            self.metadata_dir.setText(f"{base_dir}/metadata")
            self.logs_dir.setText(f"{base_dir}/logs")
            
            # Domains tab - reset to default values
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
            
            # Default targets (as percentages)
            targets = [20, 15, 15, 15, 12, 10, 8, 5]
            
            # Descriptions
            descriptions = [
                "Futures, options, perpetual swaps",
                "Algorithmic trading, market making",
                "Portfolio risk, volatility models",
                "Order book dynamics, liquidity",
                "Decentralized finance protocols",
                "Asset allocation, optimization",
                "Token valuation, fundamental analysis",
                "Legal frameworks, compliance"
            ]
            
            for i, (domain, target, desc) in enumerate(zip(domains, targets, descriptions)):
                self.domains_table.setItem(i, 0, QTableWidgetItem(domain))
                self.domains_table.setItem(i, 1, QTableWidgetItem(str(target)))
                self.domains_table.setItem(i, 2, QTableWidgetItem(desc))
            
            # Processing tab
            self.enable_ocr.setChecked(True)
            self.pdf_threads.setValue(4)
            self.enable_formula.setChecked(True)
            self.enable_tables.setChecked(True)
            self.text_threads.setValue(4)
            self.enable_language.setChecked(True)
            self.min_quality.setValue(70)
            self.enable_deduplication.setChecked(True)
            self.batch_size.setValue(50)
            self.max_retries.setValue(3)
            self.timeout.setValue(300)
            
            QMessageBox.information(
                self, "Reset Complete", 
                "Configuration has been reset to defaults.\n\n"
                "Note: All API credentials have been cleared and must be re-entered before use."
            )
    
    def save_configuration(self):
        """Save the current configuration"""
        try:
            # Create .env file if it doesn't exist
            if not self.env_path.exists():
                self.env_path.touch()
            
            # Save API keys to .env file
            if self.use_env_file.isChecked():
                env_vars = {
                    'ENVIRONMENT': self.env_selector.currentText(),
                    'PYTHON_PATH': self.python_path.text(),
                    'VENV_PATH': self.venv_path.text(),
                    'TEMP_DIR': self.temp_dir.text(),
                    'GITHUB_TOKEN': self.github_token.text(),
                    'AA_COOKIE': self.aa_cookie.text(),
                    'FRED_API_KEY': self.fred_key.text(),
                    'BITMEX_API_KEY': self.bitmex_key.text(),
                    'BITMEX_API_SECRET': self.bitmex_secret.text(),
                    'ARXIV_EMAIL': self.arxiv_email.text(),
                    'CORPUS_ROOT': self.corpus_root.text(),
                    'RAW_DATA_DIR': self.raw_data_dir.text(),
                    'PROCESSED_DIR': self.processed_dir.text(),
                    'METADATA_DIR': self.metadata_dir.text(),
                    'LOGS_DIR': self.logs_dir.text(),
                    'PDF_THREADS': str(self.pdf_threads.value()),
                    'TEXT_THREADS': str(self.text_threads.value()),
                    'BATCH_SIZE': str(self.batch_size.value()),
                    'MAX_RETRIES': str(self.max_retries.value()),
                    'TIMEOUT': str(self.timeout.value())
                }
                
                # Update .env file
                for key, value in env_vars.items():
                    set_key(self.env_path, key, value)
            
            # Save non-sensitive configuration to YAML
            config = {
                'environment': {
                    'active': self.env_selector.currentText(),
                    'config_path': str(self.project_config.config_path),
                    'auto_save': self.auto_save.isChecked()
                },
                'processing': {
                    'pdf': {
                        'enable_ocr': self.enable_ocr.isChecked(),
                        'enable_formula': self.enable_formula.isChecked(),
                        'enable_tables': self.enable_tables.isChecked()
                    },
                    'text': {
                        'enable_language': self.enable_language.isChecked(),
                        'min_quality': self.min_quality.value(),
                        'enable_deduplication': self.enable_deduplication.isChecked()
                    }
                },
                'directories': {
                    'create_missing': self.create_missing.isChecked(),
                    'relative_paths': self.relative_paths.isChecked(),
                    'validate_paths': self.validate_paths.isChecked()
                }
            }
            
            # Save to YAML
            with open(self.project_config.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)

            # Persist changes in ProjectConfig
            self.project_config.set('environment.active', self.env_selector.currentText())
            self.project_config.set('environment.config_path', str(self.project_config.config_path))
            self.project_config.set('environment.auto_save', self.auto_save.isChecked())
            self.project_config.set('processing.pdf.enable_ocr', self.enable_ocr.isChecked())
            self.project_config.set('processing.pdf.enable_formula', self.enable_formula.isChecked())
            self.project_config.set('processing.pdf.enable_tables', self.enable_tables.isChecked())
            self.project_config.set('processing.text.enable_language', self.enable_language.isChecked())
            self.project_config.set('processing.text.min_quality', self.min_quality.value())
            self.project_config.set('processing.text.enable_deduplication', self.enable_deduplication.isChecked())
            self.project_config.set('directories.create_missing', self.create_missing.isChecked())
            self.project_config.set('directories.relative_paths', self.relative_paths.isChecked())
            self.project_config.set('directories.validate_paths', self.validate_paths.isChecked())
            self.project_config.save()

            # Emit signal so other components can refresh
            self.configuration_saved.emit(config)
            
            QMessageBox.information(
                self, "Configuration Saved",
                "Configuration has been saved successfully."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Save Error",
                f"Failed to save configuration: {str(e)}"
            )

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        if files:
            self.import_config_file(files[0])
            
    def import_config_file(self, file_path: str):
        try:
            with open(file_path, "r") as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                raise ValueError("Config file did not contain a dictionary")

            # Environment
            env_cfg = config.get("environment", {})
            if isinstance(env_cfg, dict):
                self.env_selector.setCurrentText(env_cfg.get("active", "test"))
                self.config_path.setText(env_cfg.get("config_path", self.config_path.text()))
                self.python_path.setText(env_cfg.get("python_path", self.python_path.text()))
                self.venv_path.setText(env_cfg.get("venv_path", self.venv_path.text()))
                self.temp_dir.setText(env_cfg.get("temp_dir", self.temp_dir.text()))
                if "auto_save" in env_cfg:
                    self.auto_save.setChecked(bool(env_cfg.get("auto_save")))
            elif isinstance(env_cfg, str):
                self.env_selector.setCurrentText(env_cfg)

            # API keys
            api_cfg = config.get("api_keys", {})
            if isinstance(api_cfg, dict):
                self.github_token.setText(api_cfg.get("github_token", ""))
                self.aa_cookie.setText(api_cfg.get("aa_cookie", ""))
                self.fred_key.setText(api_cfg.get("fred_key", ""))
                self.bitmex_key.setText(api_cfg.get("bitmex_key", ""))
                self.bitmex_secret.setText(api_cfg.get("bitmex_secret", ""))
                self.arxiv_email.setText(api_cfg.get("arxiv_email", ""))

            # Directories
            dir_cfg = config.get("directories", {})
            if isinstance(dir_cfg, dict):
                self.corpus_root.setText(dir_cfg.get("corpus_root", self.corpus_root.text()))
                self.raw_data_dir.setText(dir_cfg.get("raw_data_dir", self.raw_data_dir.text()))
                self.processed_dir.setText(dir_cfg.get("processed_dir", self.processed_dir.text()))
                self.metadata_dir.setText(dir_cfg.get("metadata_dir", self.metadata_dir.text()))
                self.logs_dir.setText(dir_cfg.get("logs_dir", self.logs_dir.text()))
                if "create_missing" in dir_cfg:
                    self.create_missing.setChecked(bool(dir_cfg.get("create_missing")))
                if "relative_paths" in dir_cfg:
                    self.relative_paths.setChecked(bool(dir_cfg.get("relative_paths")))
                if "validate_paths" in dir_cfg:
                    self.validate_paths.setChecked(bool(dir_cfg.get("validate_paths")))

            # Processing
            proc_cfg = config.get("processing", {})
            pdf_cfg = proc_cfg.get("pdf", {}) if isinstance(proc_cfg, dict) else {}
            if isinstance(pdf_cfg, dict):
                if "enable_ocr" in pdf_cfg:
                    self.enable_ocr.setChecked(bool(pdf_cfg.get("enable_ocr")))
                if "threads" in pdf_cfg:
                    self.pdf_threads.setValue(int(pdf_cfg.get("threads")))
                if "enable_formula" in pdf_cfg:
                    self.enable_formula.setChecked(bool(pdf_cfg.get("enable_formula")))
                if "enable_tables" in pdf_cfg:
                    self.enable_tables.setChecked(bool(pdf_cfg.get("enable_tables")))

            text_cfg = proc_cfg.get("text", {}) if isinstance(proc_cfg, dict) else {}
            if isinstance(text_cfg, dict):
                if "threads" in text_cfg:
                    self.text_threads.setValue(int(text_cfg.get("threads")))
                if "enable_language" in text_cfg:
                    self.enable_language.setChecked(bool(text_cfg.get("enable_language")))
                if "min_quality" in text_cfg:
                    self.min_quality.setValue(int(text_cfg.get("min_quality")))
                if "enable_deduplication" in text_cfg:
                    self.enable_deduplication.setChecked(bool(text_cfg.get("enable_deduplication")))

            adv_cfg = proc_cfg.get("advanced", {}) if isinstance(proc_cfg, dict) else {}
            if isinstance(adv_cfg, dict):
                if "batch_size" in adv_cfg:
                    self.batch_size.setValue(int(adv_cfg.get("batch_size")))
                if "max_retries" in adv_cfg:
                    self.max_retries.setValue(int(adv_cfg.get("max_retries")))
                if "timeout" in adv_cfg:
                    self.timeout.setValue(int(adv_cfg.get("timeout")))

            # Update ProjectConfig and revalidate
            self.project_config.config = config
            try:
                self.project_config.revalidate()
            except ValidationError as exc:
                QMessageBox.warning(self, "Validation Error", str(exc))

            # Notify others of imported configuration
            self.configuration_saved.emit(config)

        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import config: {str(e)}")
