# File: app/ui/dialogs/settings_dialog.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QDialogButtonBox,
                             QCheckBox, QComboBox, QTabWidget, QWidget, QSpinBox,
                             QFileDialog, QGroupBox)
from PySide6.QtCore import Qt, Signal as pyqtSignal, Slot as pyqtSlot
from app.helpers.theme_manager import ThemeManager
import json
import os

class SettingsDialog(QDialog):
    """Dialog for application settings."""
    
    settings_updated = pyqtSignal(dict)
    
    def __init__(self, current_settings=None, parent=None):
        super().__init__(parent)
        self.current_settings = current_settings or {}
        self.setup_ui()
        self.load_current_settings()
        
    def setup_ui(self):
        """Set up the UI components."""
        self.setWindowTitle("Application Settings")
        self.setMinimumWidth(600)
        
        main_layout = QVBoxLayout(self)
        
        # Tabs for different settings categories
        self.tabs = QTabWidget()
        
        # General tab
        general_tab = QWidget()
        self.tabs.addTab(general_tab, "General")
        general_layout = QVBoxLayout(general_tab)
        
        # Environment settings
        env_group = QGroupBox("Environment")
        env_layout = QFormLayout(env_group)
        
        self.env_selector = QComboBox()
        self.env_selector.addItems(["test", "master", "production"])
        env_layout.addRow("Active Environment:", self.env_selector)
        
        self.python_path = QLineEdit()
        python_browse = QPushButton("Browse...")
        python_browse.clicked.connect(self.browse_python_path)
        python_layout = QHBoxLayout()
        python_layout.addWidget(self.python_path)
        python_layout.addWidget(python_browse)
        env_layout.addRow("Python Executable:", python_layout)
        
        self.venv_path = QLineEdit()
        self.venv_path.setPlaceholderText('venv/')
        venv_browse = QPushButton("Browse...")
        venv_browse.clicked.connect(self.browse_venv_path)
        venv_layout = QHBoxLayout()
        venv_layout.addWidget(self.venv_path)
        venv_layout.addWidget(venv_browse)
        env_layout.addRow("Virtual Environment:", venv_layout)
        
        general_layout.addWidget(env_group)
        
        # User interface settings
        ui_group = QGroupBox("User Interface")
        ui_layout = QFormLayout(ui_group)
        
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["System", "Light", "Dark"])
        ui_layout.addRow("Theme:", self.theme_selector)
        self.theme_selector.currentIndexChanged.connect(self.on_theme_changed)
        
        self.show_tooltips = QCheckBox()
        self.show_tooltips.setChecked(True)
        ui_layout.addRow("Show Tooltips:", self.show_tooltips)
        
        self.auto_refresh = QCheckBox()
        self.auto_refresh.setChecked(True)
        ui_layout.addRow("Auto-refresh Dashboard:", self.auto_refresh)
        
        self.sound_checkbox = QCheckBox("Enable sound notifications")
        ui_layout.addRow("Sound Notifications:", self.sound_checkbox)
        
        general_layout.addWidget(ui_group)
        
        # Directories tab
        directories_tab = QWidget()
        self.tabs.addTab(directories_tab, "Directories")
        directories_layout = QFormLayout(directories_tab)
        
        # Corpus root
        self.corpus_root = QLineEdit()
        corpus_browse = QPushButton("Browse...")
        corpus_browse.clicked.connect(lambda: self.browse_directory(self.corpus_root))
        corpus_layout = QHBoxLayout()
        corpus_layout.addWidget(self.corpus_root)
        corpus_layout.addWidget(corpus_browse)
        directories_layout.addRow("Corpus Root:", corpus_layout)
        
        # Raw data
        self.raw_dir = QLineEdit()
        raw_browse = QPushButton("Browse...")
        raw_browse.clicked.connect(lambda: self.browse_directory(self.raw_dir))
        raw_layout = QHBoxLayout()
        raw_layout.addWidget(self.raw_dir)
        raw_layout.addWidget(raw_browse)
        directories_layout.addRow("Raw Data:", raw_layout)
        
        # Processed data
        self.processed_dir = QLineEdit()
        processed_browse = QPushButton("Browse...")
        processed_browse.clicked.connect(lambda: self.browse_directory(self.processed_dir))
        processed_layout = QHBoxLayout()
        processed_layout.addWidget(self.processed_dir)
        processed_layout.addWidget(processed_browse)
        directories_layout.addRow("Processed Data:", processed_layout)
        
        # Metadata
        self.metadata_dir = QLineEdit()
        metadata_browse = QPushButton("Browse...")
        metadata_browse.clicked.connect(lambda: self.browse_directory(self.metadata_dir))
        metadata_layout = QHBoxLayout()
        metadata_layout.addWidget(self.metadata_dir)
        metadata_layout.addWidget(metadata_browse)
        directories_layout.addRow("Metadata:", metadata_layout)
        
        # Logs
        self.logs_dir = QLineEdit()
        logs_browse = QPushButton("Browse...")
        logs_browse.clicked.connect(lambda: self.browse_directory(self.logs_dir))
        logs_layout = QHBoxLayout()
        logs_layout.addWidget(self.logs_dir)
        logs_layout.addWidget(logs_browse)
        directories_layout.addRow("Logs:", logs_layout)
        
        # Create missing dirs
        self.create_missing = QCheckBox()
        self.create_missing.setChecked(True)
        directories_layout.addRow("Create Missing Directories:", self.create_missing)
        
        # Processing tab
        processing_tab = QWidget()
        self.tabs.addTab(processing_tab, "Processing")
        processing_layout = QVBoxLayout(processing_tab)
        
        # PDF Processing
        pdf_group = QGroupBox("PDF Processing")
        pdf_layout = QFormLayout(pdf_group)
        
        self.enable_ocr = QCheckBox()
        self.enable_ocr.setChecked(True)
        pdf_layout.addRow("Enable OCR:", self.enable_ocr)
        
        self.pdf_threads = QSpinBox()
        self.pdf_threads.setRange(1, 16)
        self.pdf_threads.setValue(4)
        pdf_layout.addRow("Worker Threads:", self.pdf_threads)
        
        self.extract_formulas = QCheckBox()
        self.extract_formulas.setChecked(True)
        pdf_layout.addRow("Extract Formulas:", self.extract_formulas)
        
        self.extract_tables = QCheckBox()
        self.extract_tables.setChecked(True)
        pdf_layout.addRow("Extract Tables:", self.extract_tables)
        
        processing_layout.addWidget(pdf_group)
        
        # Text Processing
        text_group = QGroupBox("Text Processing")
        text_layout = QFormLayout(text_group)
        
        self.text_threads = QSpinBox()
        self.text_threads.setRange(1, 16)
        self.text_threads.setValue(4)
        text_layout.addRow("Worker Threads:", self.text_threads)
        
        self.detect_language = QCheckBox()
        self.detect_language.setChecked(True)
        text_layout.addRow("Detect Language:", self.detect_language)
        
        self.min_quality = QSpinBox()
        self.min_quality.setRange(0, 100)
        self.min_quality.setValue(70)
        text_layout.addRow("Minimum Quality:", self.min_quality)
        
        processing_layout.addWidget(text_group)
        
        # Advanced options
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QFormLayout(advanced_group)
        
        self.batch_size = QSpinBox()
        self.batch_size.setRange(1, 1000)
        self.batch_size.setValue(50)
        advanced_layout.addRow("Batch Size:", self.batch_size)
        
        self.timeout = QSpinBox()
        self.timeout.setRange(10, 3600)
        self.timeout.setValue(300)
        self.timeout.setSuffix(" seconds")
        advanced_layout.addRow("Timeout:", self.timeout)
        
        processing_layout.addWidget(advanced_group)
        
        # Load sound setting from config
        config_path = os.path.join(os.path.dirname(__file__), '../../theme_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.sound_checkbox.setChecked(data.get('sound_enabled', True))
            except Exception:
                self.sound_checkbox.setChecked(True)
        else:
            self.sound_checkbox.setChecked(True)
        self.sound_checkbox.stateChanged.connect(self.on_sound_setting_changed)
        
        # Add tabs to main layout
        main_layout.addWidget(self.tabs)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_box.addButton(reset_btn, QDialogButtonBox.ButtonRole.ResetRole)
        
        main_layout.addWidget(button_box)
    
    def load_current_settings(self):
        """Load current settings into the dialog."""
        # General tab
        self.env_selector.setCurrentText(self.current_settings.get('environment', 'test'))
        self.python_path.setText(self.current_settings.get('python_path', ''))
        self.venv_path.setText('venv/')
        self.theme_selector.setCurrentText(self.current_settings.get('theme', 'System'))
        self.show_tooltips.setChecked(self.current_settings.get('show_tooltips', True))
        self.auto_refresh.setChecked(self.current_settings.get('auto_refresh', True))
        
        # Directories tab
        self.corpus_root.setText(self.current_settings.get('corpus_root', ''))
        self.raw_dir.setText(self.current_settings.get('raw_dir', ''))
        self.processed_dir.setText(self.current_settings.get('processed_dir', ''))
        self.metadata_dir.setText(self.current_settings.get('metadata_dir', ''))
        self.logs_dir.setText(self.current_settings.get('logs_dir', ''))
        self.create_missing.setChecked(self.current_settings.get('create_missing_dirs', True))
        
        # Processing tab
        self.enable_ocr.setChecked(self.current_settings.get('enable_ocr', True))
        self.pdf_threads.setValue(self.current_settings.get('pdf_threads', 4))
        self.extract_formulas.setChecked(self.current_settings.get('extract_formulas', True))
        self.extract_tables.setChecked(self.current_settings.get('extract_tables', True))
        self.text_threads.setValue(self.current_settings.get('text_threads', 4))
        self.detect_language.setChecked(self.current_settings.get('detect_language', True))
        self.min_quality.setValue(self.current_settings.get('min_quality', 70))
        self.batch_size.setValue(self.current_settings.get('batch_size', 50))
        self.timeout.setValue(self.current_settings.get('timeout', 300))
    
    def get_settings(self):
        """Get the settings from the dialog."""
        return {
            # General
            'environment': self.env_selector.currentText(),
            'python_path': self.python_path.text(),
            'venv_path': self.venv_path.text(),
            'theme': self.theme_selector.currentText(),
            'show_tooltips': self.show_tooltips.isChecked(),
            'auto_refresh': self.auto_refresh.isChecked(),
            
            # Directories
            'corpus_root': self.corpus_root.text(),
            'raw_dir': self.raw_dir.text(),
            'processed_dir': self.processed_dir.text(),
            'metadata_dir': self.metadata_dir.text(),
            'logs_dir': self.logs_dir.text(),
            'create_missing_dirs': self.create_missing.isChecked(),
            
            # Processing
            'enable_ocr': self.enable_ocr.isChecked(),
            'pdf_threads': self.pdf_threads.value(),
            'extract_formulas': self.extract_formulas.isChecked(),
            'extract_tables': self.extract_tables.isChecked(),
            'text_threads': self.text_threads.value(),
            'detect_language': self.detect_language.isChecked(),
            'min_quality': self.min_quality.value(),
            'batch_size': self.batch_size.value(),
            'timeout': self.timeout.value(),
            'sound_enabled': self.sound_checkbox.isChecked()
        }
    
    def accept(self):
        """Handle dialog acceptance."""
        settings = self.get_settings()
        # Save the selected theme to current_settings
        self.current_settings['theme'] = self.theme_selector.currentText()
        self.settings_updated.emit(settings)
        super().accept()
    
    def reset_to_defaults(self):
        """Reset settings to defaults."""
        # General
        self.env_selector.setCurrentText('test')
        self.python_path.setText('')
        self.venv_path.setText('venv/')
        self.theme_selector.setCurrentText('System')
        self.show_tooltips.setChecked(True)
        self.auto_refresh.setChecked(True)
        
        # Directories
        import os
        base_dir = os.path.expanduser("~/crypto_corpus")
        self.corpus_root.setText(base_dir)
        self.raw_dir.setText(f"{base_dir}/raw")
        self.processed_dir.setText(f"{base_dir}/processed")
        self.metadata_dir.setText(f"{base_dir}/metadata")
        self.logs_dir.setText(f"{base_dir}/logs")
        self.create_missing.setChecked(True)
        
        # Processing
        self.enable_ocr.setChecked(True)
        self.pdf_threads.setValue(4)
        self.extract_formulas.setChecked(True)
        self.extract_tables.setChecked(True)
        self.text_threads.setValue(4)
        self.detect_language.setChecked(True)
        self.min_quality.setValue(70)
        self.batch_size.setValue(50)
        self.timeout.setValue(300)
    
    def browse_python_path(self):
        """Browse for Python executable."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Python Executable", "", "Executables (*.exe);;All Files (*)"
        )
        if file_path:
            self.python_path.setText(file_path)
    
    def browse_venv_path(self):
        """Browse for virtual environment directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Virtual Environment Directory"
        )
        if directory:
            self.venv_path.setText(directory)
    
    def browse_directory(self, line_edit):
        """Browse for a directory and update a line edit."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory"
        )
        if directory:
            line_edit.setText(directory)

    def on_theme_changed(self):
        theme = self.theme_selector.currentText().lower()
        if theme == "system":
            theme = "light"  # Default to light for now
        ThemeManager.apply_theme(theme)
        self.current_settings['theme'] = self.theme_selector.currentText()

    def on_sound_setting_changed(self):
        # Save sound setting to config
        config_path = os.path.join(os.path.dirname(__file__), '../../theme_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {}
        data['sound_enabled'] = self.sound_checkbox.isChecked()
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception:
            pass
        # Emit a signal or call a method to update sound_enabled in all tabs if needed
