from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QTabWidget,
    QFileDialog,
    QCheckBox,
    QFormLayout,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QInputDialog,
)
from PySide6.QtCore import Qt, Slot as pyqtSlot, QMimeData, Signal as pyqtSignal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv, set_key
from pydantic import ValidationError
from app.helpers.crypto_utils import encrypt_value, decrypt_value
from app.ui.widgets.card_wrapper import CardWrapper
from app.ui.widgets.section_header import SectionHeader
from app.ui.theme.theme_constants import PAGE_MARGIN
from app.ui.utils.ui_helpers import set_line_edit_text


class ConfigurationTab(QWidget):
    """Tab for viewing and editing project configuration."""

    configuration_saved = pyqtSignal(dict)

    def __init__(self, project_config, parent=None):
        super().__init__(parent)
        self.project_config = project_config
        self.env_path = Path(project_config.config_path).parent / ".env"
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
        self.default_btn.setObjectName("danger")
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
        env_card = CardWrapper(title="Environment")
        env_layout = env_card.body_layout

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
        env_vars_card = CardWrapper(title="Environment Variables")
        env_vars_layout = env_vars_card.body_layout

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
        self.venv_path.setPlaceholderText("venv/")
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
        layout.addWidget(env_card)
        layout.addWidget(env_vars_card)
        layout.addStretch()

        return tab

    def create_api_keys_tab(self):
        """Create the API keys configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # API Keys form
        keys_card = CardWrapper(title="API Credentials")
        keys_layout = QFormLayout()
        keys_card.body_layout.addLayout(keys_layout)

        # GitHub
        self.github_token = QLineEdit()
        self.github_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.github_token.setPlaceholderText("Enter GitHub API token")
        self.github_token.setToolTip(
            "Enter your GitHub API token. This will be stored securely in .env or encrypted config. Never stored in plaintext."
        )
        keys_layout.addRow("GitHub Token:", self.github_token)

        # FRED
        self.fred_token = QLineEdit()
        self.fred_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.fred_token.setPlaceholderText("Enter FRED API token")
        keys_layout.addRow("FRED Token:", self.fred_token)

        # BitMEX
        self.bitmex_token = QLineEdit()
        self.bitmex_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.bitmex_token.setPlaceholderText("Enter BitMEX API token")
        keys_layout.addRow("BitMEX Token:", self.bitmex_token)

        # Quantopian
        self.quantopian_token = QLineEdit()
        self.quantopian_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.quantopian_token.setPlaceholderText("Enter Quantopian API token")
        keys_layout.addRow("Quantopian Token:", self.quantopian_token)

        # SciDB
        self.scidb_token = QLineEdit()
        self.scidb_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.scidb_token.setPlaceholderText("Enter SciDB API token")
        keys_layout.addRow("SciDB Token:", self.scidb_token)

        # Web
        self.web_token = QLineEdit()
        self.web_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.web_token.setPlaceholderText("Enter Web API token")
        keys_layout.addRow("Web Token:", self.web_token)

        layout.addWidget(keys_card)
        layout.addStretch()

        return tab

    def create_directories_tab(self):
        """Create the directories configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Directories form
        dirs_card = CardWrapper(title="Directory Settings")
        dirs_layout = QFormLayout()
        dirs_card.body_layout.addLayout(dirs_layout)

        # Corpus root
        corpus_layout = QHBoxLayout()
        self.corpus_root = QLineEdit()
        corpus_layout.addWidget(self.corpus_root)
        corpus_browse = QPushButton("Browse...")
        corpus_browse.clicked.connect(lambda: self.browse_directory(self.corpus_root, "Select Corpus Root"))
        corpus_layout.addWidget(corpus_browse)
        dirs_layout.addRow("Corpus Root:", corpus_layout)

        # Raw data directory
        raw_layout = QHBoxLayout()
        self.raw_data_dir = QLineEdit()
        raw_layout.addWidget(self.raw_data_dir)
        raw_browse = QPushButton("Browse...")
        raw_browse.clicked.connect(lambda: self.browse_directory(self.raw_data_dir, "Select Raw Data Directory"))
        raw_layout.addWidget(raw_browse)
        dirs_layout.addRow("Raw Data Directory:", raw_layout)

        # Processed directory
        processed_layout = QHBoxLayout()
        self.processed_dir = QLineEdit()
        processed_layout.addWidget(self.processed_dir)
        processed_browse = QPushButton("Browse...")
        processed_browse.clicked.connect(lambda: self.browse_directory(self.processed_dir, "Select Processed Directory"))
        processed_layout.addWidget(processed_browse)
        dirs_layout.addRow("Processed Directory:", processed_layout)

        # Metadata directory
        metadata_layout = QHBoxLayout()
        self.metadata_dir = QLineEdit()
        metadata_layout.addWidget(self.metadata_dir)
        metadata_browse = QPushButton("Browse...")
        metadata_browse.clicked.connect(lambda: self.browse_directory(self.metadata_dir, "Select Metadata Directory"))
        metadata_layout.addWidget(metadata_browse)
        dirs_layout.addRow("Metadata Directory:", metadata_layout)

        # Logs directory
        logs_layout = QHBoxLayout()
        self.logs_dir = QLineEdit()
        logs_layout.addWidget(self.logs_dir)
        logs_browse = QPushButton("Browse...")
        logs_browse.clicked.connect(lambda: self.browse_directory(self.logs_dir, "Select Logs Directory"))
        logs_layout.addWidget(logs_browse)
        dirs_layout.addRow("Logs Directory:", logs_layout)

        layout.addWidget(dirs_card)
        layout.addStretch()

        return tab

    def create_domains_tab(self):
        """Create the domains configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Domains form
        domains_card = CardWrapper(title="Domain Settings")
        domains_layout = QFormLayout()
        domains_card.body_layout.addLayout(domains_layout)

        # Domain table
        self.domain_table = QTableWidget()
        self.domain_table.setColumnCount(3)
        self.domain_table.setHorizontalHeaderLabels(["Domain", "Enabled", "Priority"])
        self.domain_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.domain_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.domain_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        domains_layout.addRow(self.domain_table)

        # Add domain button
        add_domain_btn = QPushButton("Add Domain")
        add_domain_btn.clicked.connect(self.add_domain)
        domains_layout.addRow(add_domain_btn)

        layout.addWidget(domains_card)
        layout.addStretch()

        return tab

    def create_processing_tab(self):
        """Create the processing configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Processing form
        processing_card = CardWrapper(title="Processing Settings")
        processing_layout = QFormLayout()
        processing_card.body_layout.addLayout(processing_layout)

        # Max workers
        self.max_workers = QSpinBox()
        self.max_workers.setRange(1, 32)
        self.max_workers.setValue(4)
        processing_layout.addRow("Max Workers:", self.max_workers)

        # Batch size
        self.batch_size = QSpinBox()
        self.batch_size.setRange(1, 1000)
        self.batch_size.setValue(100)
        processing_layout.addRow("Batch Size:", self.batch_size)

        # Timeout
        self.timeout = QSpinBox()
        self.timeout.setRange(1, 3600)
        self.timeout.setValue(300)
        processing_layout.addRow("Timeout (seconds):", self.timeout)

        layout.addWidget(processing_card)
        layout.addStretch()

        return tab

    def browse_config_file(self):
        """Browse for a configuration file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Config File", "", "YAML Files (*.yaml *.yml)"
        )
        if file_path:
            set_line_edit_text(self.config_path, file_path)

    def browse_python_executable(self):
        """Browse for a Python executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Python Executable", "", "Executable Files (*.exe);;All Files (*.*)"
        )
        if file_path:
            set_line_edit_text(self.python_path, file_path)

    def browse_venv_path(self):
        """Browse for a virtual environment directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Virtual Environment Directory"
        )
        if dir_path:
            set_line_edit_text(self.venv_path, dir_path)

    def browse_temp_dir(self):
        """Browse for a temporary directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Temporary Directory"
        )
        if dir_path:
            set_line_edit_text(self.temp_dir, dir_path)

    def browse_directory(self, line_edit, title):
        """Browse for a directory and update the line edit"""
        dir_path = QFileDialog.getExistingDirectory(self, title)
        if dir_path:
            set_line_edit_text(line_edit, dir_path)

    def on_environment_changed(self):
        """Handle environment selection change"""
        env = self.env_selector.currentText()
        # Persist the selected environment using ProjectConfig
        self.project_config.set('environment.active', env)
        self.project_config.save()

    def validate_domain_config(self):
        """Validate domain configuration"""
        domains = {}
        for row in range(self.domain_table.rowCount()):
            domain = self.domain_table.item(row, 0).text()
            enabled = self.domain_table.item(row, 1).checkState() == Qt.CheckState.Checked
            priority = int(self.domain_table.item(row, 2).text())
            domains[domain] = {"enabled": enabled, "priority": priority}
        return domains

    def load_current_config(self):
        """Load the current configuration into the UI."""
        # Environment
        env = self.project_config.get("environment", {})
        set_line_edit_text(self.corpus_root, env.get("corpus_root", ""))
        set_line_edit_text(self.raw_data_dir, env.get("raw_data_dir", ""))
        set_line_edit_text(self.processed_dir, env.get("processed_dir", ""))
        set_line_edit_text(self.metadata_dir, env.get("metadata_dir", ""))
        set_line_edit_text(self.logs_dir, env.get("logs_dir", ""))

        # API Keys
        api_keys = self.project_config.get("api_keys", {})
        set_line_edit_text(self.github_token, api_keys.get("github", ""))
        set_line_edit_text(self.fred_token, api_keys.get("fred", ""))
        set_line_edit_text(self.bitmex_token, api_keys.get("bitmex", ""))
        set_line_edit_text(self.quantopian_token, api_keys.get("quantopian", ""))
        set_line_edit_text(self.scidb_token, api_keys.get("scidb", ""))
        set_line_edit_text(self.web_token, api_keys.get("web", ""))

        # Environment paths
        env = self.project_config.get("environment", {})
        set_line_edit_text(self.python_path, env.get("python_path", ""))
        set_line_edit_text(self.venv_path, env.get("venv_path", ""))
        set_line_edit_text(self.temp_dir, env.get("temp_dir", ""))
        set_line_edit_text(self.config_path, str(self.project_config.config_path))

        # Load domains
        domains = self.project_config.get("domains", {})
        self.domain_table.setRowCount(0)
        for domain_key, domain_data in domains.items():
            row = self.domain_table.rowCount()
            self.domain_table.insertRow(row)
            self.domain_table.setItem(row, 0, QTableWidgetItem(domain_key))
            chk_item = QTableWidgetItem()
            chk_item.setCheckState(Qt.Checked if domain_data.get("enabled", True) else Qt.Unchecked)
            self.domain_table.setItem(row, 1, chk_item)
            self.domain_table.setItem(row, 2, QTableWidgetItem(str(domain_data.get("priority", 0))))

        # Load processing settings
        self.max_workers.setValue(self.project_config.get("processing.max_workers", 4))
        self.batch_size.setValue(self.project_config.get("processing.batch_size", 100))
        self.timeout.setValue(self.project_config.get("processing.timeout", 300))

        # Load environment variables
        self.auto_save.setChecked(self.project_config.get("environment.auto_save", True))

    def load_default_config(self):
        """Reset all fields to empty."""
        set_line_edit_text(self.config_path, "")
        set_line_edit_text(self.python_path, "")
        set_line_edit_text(self.venv_path, "")
        set_line_edit_text(self.temp_dir, "")
        set_line_edit_text(self.github_token, "")
        set_line_edit_text(self.fred_token, "")
        set_line_edit_text(self.bitmex_token, "")
        set_line_edit_text(self.quantopian_token, "")
        set_line_edit_text(self.scidb_token, "")
        set_line_edit_text(self.web_token, "")
        set_line_edit_text(self.corpus_root, "")
        set_line_edit_text(self.raw_data_dir, "")
        set_line_edit_text(self.processed_dir, "")
        set_line_edit_text(self.metadata_dir, "")
        set_line_edit_text(self.logs_dir, "")

        # Reset domains
        self.domain_table.setRowCount(0)

        # Reset processing settings
        self.max_workers.setValue(4)
        self.batch_size.setValue(100)
        self.timeout.setValue(300)

    def save_configuration(self):
        """Save the current configuration."""
        env = self.env_selector.currentText()
        self.project_config.set("environment.active", env)

        # Save directories using the new schema
        self.project_config.set(f"environments.{env}.corpus_root", self.corpus_root.text())
        self.project_config.set(f"environments.{env}.raw_data_dir", self.raw_data_dir.text())
        self.project_config.set(f"environments.{env}.processed_dir", self.processed_dir.text())
        self.project_config.set(f"environments.{env}.metadata_dir", self.metadata_dir.text())
        self.project_config.set(f"environments.{env}.log_dir", self.logs_dir.text())

        # Save API keys
        self.project_config.set("api_keys.github", self.github_token.text())
        self.project_config.set("api_keys.fred", self.fred_token.text())
        self.project_config.set("api_keys.bitmex", self.bitmex_token.text())
        self.project_config.set("api_keys.quantopian", self.quantopian_token.text())
        self.project_config.set("api_keys.scidb", self.scidb_token.text())
        self.project_config.set("api_keys.web", self.web_token.text())

        # Save domains
        domains = {}
        for row in range(self.domain_table.rowCount()):
            domain_key = self.domain_table.item(row, 0).text()
            enabled = self.domain_table.item(row, 1).checkState() == Qt.Checked
            priority = int(self.domain_table.item(row, 2).text())
            domains[domain_key] = {"enabled": enabled, "priority": priority}
        self.project_config.set("domains", domains)

        # Save processing settings
        self.project_config.set("processing.max_workers", self.max_workers.value())
        self.project_config.set("processing.batch_size", self.batch_size.value())
        self.project_config.set("processing.timeout", self.timeout.value())

        # Save environment variables
        self.project_config.set("environment.python_path", self.python_path.text())
        self.project_config.set("environment.venv_path", self.venv_path.text())
        self.project_config.set("environment.temp_dir", self.temp_dir.text())
        self.project_config.set("environment.auto_save", self.auto_save.isChecked())

        # Save config file path
        self.project_config.config_path = self.config_path.text()

        # Save the configuration
        self.project_config.save()

        # Emit saved signal
        self.configuration_saved.emit(self.project_config.config)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            self.import_config_file(file_path)

    def import_config_file(self, file_path: str):
        """Import configuration from a file"""
        try:
            with open(file_path, "r") as f:
                config = yaml.safe_load(f)
            self.project_config.config.update(config)
            self.load_current_config()
            QMessageBox.information(self, "Success", "Configuration imported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import configuration: {str(e)}")

    def add_domain(self):
        """
        Prompt the user for a domain key and optional allocation,
        then store it in ProjectConfig and refresh the domain table.
        """
        # Prompt for domain
        domain_key, ok = QInputDialog.getText(
            self, "Add Domain", "Enter new domain identifier (e.g., crypto_derivatives):"
        )
        if not ok or not domain_key.strip():
            return
        domain_key = domain_key.strip()

        # Prompt for allocation
        alloc_str, ok2 = QInputDialog.getText(
            self, "Allocation (0–1)", "Optional allocation percentage (blank = 0):"
        )
        if not ok2:
            return
        try:
            allocation = float(alloc_str) if alloc_str else 0.0
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Allocation must be a number.")
            return
        if not (0.0 <= allocation <= 1.0):
            QMessageBox.warning(self, "Invalid Input", "Allocation must be 0–1.")
            return

        # Update config
        domains = self.project_config.get("domains", {})
        if domain_key in domains:
            QMessageBox.information(self, "Duplicate", f"Domain '{domain_key}' already exists.")
            return
        domains[domain_key] = {"enabled": True, "priority": 0, "allocation": allocation, "keywords": []}
        self.project_config.set("domains", domains)
        self.project_config.save()

        # Add to table
        row = self.domain_table.rowCount()
        self.domain_table.insertRow(row)
        self.domain_table.setItem(row, 0, QTableWidgetItem(domain_key))
        chk_item = QTableWidgetItem()
        chk_item.setCheckState(Qt.Checked)
        self.domain_table.setItem(row, 1, chk_item)
        self.domain_table.setItem(row, 2, QTableWidgetItem("0"))

        # Emit saved signal
        self.configuration_saved.emit(self.project_config.config)
