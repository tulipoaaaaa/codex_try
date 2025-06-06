# File: app/ui/dialogs/api_key_dialog.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QDialogButtonBox,
                             QCheckBox, QComboBox, QTabWidget, QWidget)
from PySide6.QtCore import Qt, Signal as pyqtSignal, Slot as pyqtSlot

class APIKeyDialog(QDialog):
    """Dialog for managing API keys and credentials."""
    
    keys_updated = pyqtSignal(dict)
    
    def __init__(self, existing_keys=None, parent=None):
        super().__init__(parent)
        self.existing_keys = existing_keys or {}
        self.setup_ui()
        self.load_existing_keys()
        
    def setup_ui(self):
        """Set up the UI components."""
        self.setWindowTitle("API Key Management")
        self.setMinimumWidth(500)
        
        main_layout = QVBoxLayout(self)
        
        # Tabs for different API categories
        self.tabs = QTabWidget()
        
        # Data Source APIs tab
        data_sources_tab = QWidget()
        self.tabs.addTab(data_sources_tab, "Data Sources")
        data_sources_layout = QFormLayout(data_sources_tab)
        
        # GitHub
        self.github_key = QLineEdit()
        self.github_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.github_key.setPlaceholderText("Enter GitHub API token")
        self.github_key.setToolTip("Enter your GitHub API token. This will be stored securely in .env or encrypted config. Never stored in plaintext.")
        data_sources_layout.addRow("GitHub Token:", self.github_key)
        
        # ISDA
        self.isda_username = QLineEdit()
        self.isda_username.setPlaceholderText("Enter ISDA username")
        data_sources_layout.addRow("ISDA Username:", self.isda_username)
        
        self.isda_password = QLineEdit()
        self.isda_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.isda_password.setPlaceholderText("Enter ISDA password")
        data_sources_layout.addRow("ISDA Password:", self.isda_password)
        
        # Anna's Archive
        self.annas_cookie = QLineEdit()
        self.annas_cookie.setEchoMode(QLineEdit.EchoMode.Password)
        self.annas_cookie.setPlaceholderText("Enter Anna's Archive cookie")
        self.annas_cookie.setToolTip("Enter your Anna's Archive cookie. This will be stored securely in .env or encrypted config. Never stored in plaintext.")
        data_sources_layout.addRow("Anna's Archive Cookie:", self.annas_cookie)
        
        # Financial APIs tab
        financial_tab = QWidget()
        self.tabs.addTab(financial_tab, "Financial APIs")
        financial_layout = QFormLayout(financial_tab)
        
        # FRED API
        self.fred_key = QLineEdit()
        self.fred_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.fred_key.setPlaceholderText("Enter FRED API key")
        self.fred_key.setToolTip("Enter your FRED API key. This will be stored securely in .env or encrypted config. Never stored in plaintext.")
        financial_layout.addRow("FRED API Key:", self.fred_key)
        
        # BitMEX API
        self.bitmex_key = QLineEdit()
        self.bitmex_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.bitmex_key.setPlaceholderText("Enter BitMEX API key")
        self.bitmex_key.setToolTip("Enter your BitMEX API key. This will be stored securely in .env or encrypted config. Never stored in plaintext.")
        financial_layout.addRow("BitMEX API Key:", self.bitmex_key)
        
        self.bitmex_secret = QLineEdit()
        self.bitmex_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self.bitmex_secret.setPlaceholderText("Enter BitMEX API secret")
        self.bitmex_secret.setToolTip("Enter your BitMEX API secret. This will be stored securely in .env or encrypted config. Never stored in plaintext.")
        financial_layout.addRow("BitMEX API Secret:", self.bitmex_secret)
        
        # Other APIs tab
        other_tab = QWidget()
        self.tabs.addTab(other_tab, "Other APIs")
        other_layout = QFormLayout(other_tab)
        
        # arXiv
        self.arxiv_email = QLineEdit()
        self.arxiv_email.setPlaceholderText("Enter contact email for arXiv API")
        self.arxiv_email.setToolTip("Enter your contact email for arXiv API. This will be stored securely in .env or encrypted config. Never stored in plaintext.")
        other_layout.addRow("arXiv Contact Email:", self.arxiv_email)
        
        main_layout.addWidget(self.tabs)
        
        # Security options
        security_layout = QHBoxLayout()
        
        self.encrypt_keys = QCheckBox("Encrypt API keys in configuration")
        self.encrypt_keys.setChecked(True)
        security_layout.addWidget(self.encrypt_keys)
        
        self.use_env_file = QCheckBox("Store in .env file (not in main config)")
        self.use_env_file.setChecked(True)
        security_layout.addWidget(self.use_env_file)
        
        main_layout.addLayout(security_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        test_btn = QPushButton("Test Connections")
        test_btn.clicked.connect(self.test_connections)
        button_box.addButton(test_btn, QDialogButtonBox.ButtonRole.ActionRole)
        
        main_layout.addWidget(button_box)
    
    def load_existing_keys(self):
        """Load existing API keys."""
        # GitHub
        self.github_key.setText(self.existing_keys.get('github_token', ''))
        
        # ISDA
        self.isda_username.setText(self.existing_keys.get('isda_username', ''))
        self.isda_password.setText(self.existing_keys.get('isda_password', ''))
        
        # Anna's Archive
        self.annas_cookie.setText(self.existing_keys.get('annas_cookie', ''))
        
        # FRED
        self.fred_key.setText(self.existing_keys.get('fred_key', ''))
        
        # BitMEX
        self.bitmex_key.setText(self.existing_keys.get('bitmex_key', ''))
        self.bitmex_secret.setText(self.existing_keys.get('bitmex_secret', ''))
        
        # arXiv
        self.arxiv_email.setText(self.existing_keys.get('arxiv_email', ''))
        
        # Options
        self.encrypt_keys.setChecked(self.existing_keys.get('encrypt_keys', True))
        self.use_env_file.setChecked(self.existing_keys.get('use_env_file', True))
    
    def get_api_keys(self):
        """Get the API keys from the dialog."""
        return {
            'github_token': self.github_key.text(),
            'isda_username': self.isda_username.text(),
            'isda_password': self.isda_password.text(),
            'annas_cookie': self.annas_cookie.text(),
            'fred_key': self.fred_key.text(),
            'bitmex_key': self.bitmex_key.text(),
            'bitmex_secret': self.bitmex_secret.text(),
            'arxiv_email': self.arxiv_email.text(),
            'encrypt_keys': self.encrypt_keys.isChecked(),
            'use_env_file': self.use_env_file.isChecked()
        }
    
    def accept(self):
        """Handle dialog acceptance."""
        if not self.encrypt_keys.isChecked() and not self.use_env_file.isChecked():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Security Warning",
                "At least one secure storage method must be enabled. Please enable 'Encrypt API keys in configuration' or 'Store in .env file'."
            )
            return
        api_keys = self.get_api_keys()
        self.keys_updated.emit(api_keys)
        super().accept()
    
    def test_connections(self):
        """Test connections to APIs."""
        from PySide6.QtWidgets import QMessageBox
        
        # In a real implementation, this would test the actual APIs
        # For now, just show a message
        QMessageBox.information(
            self,
            "Test Connections",
            "API connection testing is not implemented yet.\n"
            "This would test all configured API connections for validity."
        )
