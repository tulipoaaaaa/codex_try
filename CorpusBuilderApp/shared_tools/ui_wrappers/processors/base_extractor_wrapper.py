"""
Base Extractor Wrapper for UI Integration
Provides configuration interface for base extraction functionality
"""

import os
from typing import Dict, List, Optional, Any
from PySide6.QtCore import QObject, Signal as pyqtSignal, Slot as pyqtSlot
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QTextEdit, QFileDialog, QCheckBox, 
                           QSpinBox, QGroupBox, QGridLayout, QComboBox,
                           QLineEdit, QTabWidget, QSlider)
from shared_tools.ui_wrappers.base_wrapper import BaseWrapper
from shared_tools.processors.base_extractor import BaseExtractor


class BaseExtractorWrapper(BaseWrapper):
    """UI Wrapper for Base Extractor Configuration"""
    
    configuration_changed = pyqtSignal(dict)  # Emitted when configuration changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.extractor = BaseExtractor()
        self.current_config = {}
        self.setup_ui()
        self.setup_connections()
        self.load_default_configuration()
        
    def setup_ui(self):
        """Initialize the user interface components"""
        layout = QVBoxLayout(self)
        
        # Create tab widget for different configuration categories
        self.tab_widget = QTabWidget()
        
        # General Configuration Tab
        general_tab = self._create_general_configuration_tab()
        self.tab_widget.addTab(general_tab, "General")
        
        # Processing Configuration Tab
        processing_tab = self._create_processing_configuration_tab()
        self.tab_widget.addTab(processing_tab, "Processing")
        
        # Quality Configuration Tab
        quality_tab = self._create_quality_configuration_tab()
        self.tab_widget.addTab(quality_tab, "Quality Control")
        
        layout.addWidget(self.tab_widget)
        
        # Control Buttons
        control_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Apply Configuration")
        self.reset_btn = QPushButton("Reset to Defaults")
        self.export_btn = QPushButton("Export Config")
        self.import_btn = QPushButton("Import Config")
        
        control_layout.addWidget(self.apply_btn)
        control_layout.addWidget(self.reset_btn)
        control_layout.addWidget(self.export_btn)
        control_layout.addWidget(self.import_btn)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
    def _create_general_configuration_tab(self) -> QWidget:
        """Create the general configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Input/Output Settings
        io_group = QGroupBox("Input/Output Settings")
        io_layout = QGridLayout(io_group)
        
        self.input_encoding_label = QLabel("Default Input Encoding:")
        self.input_encoding_combo = QComboBox()
        self.input_encoding_combo.addItems(["utf-8", "utf-16", "ascii", "iso-8859-1", "cp1252"])
        self.input_encoding_combo.setCurrentText("utf-8")
        
        self.output_encoding_label = QLabel("Default Output Encoding:")
        self.output_encoding_combo = QComboBox()
        self.output_encoding_combo.addItems(["utf-8", "utf-16", "ascii", "iso-8859-1", "cp1252"])
        self.output_encoding_combo.setCurrentText("utf-8")
        
        self.temp_directory_label = QLabel("Temporary Directory:")
        self.temp_directory_edit = QLineEdit()
        self.temp_directory_edit.setPlaceholderText("System default")
        self.temp_browse_btn = QPushButton("Browse...")
        
        io_layout.addWidget(self.input_encoding_label, 0, 0)
        io_layout.addWidget(self.input_encoding_combo, 0, 1)
        io_layout.addWidget(self.output_encoding_label, 1, 0)
        io_layout.addWidget(self.output_encoding_combo, 1, 1)
        io_layout.addWidget(self.temp_directory_label, 2, 0)
        io_layout.addWidget(self.temp_directory_edit, 2, 1)
        io_layout.addWidget(self.temp_browse_btn, 2, 2)
        
        # File Handling Settings
        file_group = QGroupBox("File Handling")
        file_layout = QGridLayout(file_group)
        
        self.max_file_size_label = QLabel("Maximum File Size (MB):")
        self.max_file_size_spin = QSpinBox()
        self.max_file_size_spin.setRange(1, 10000)
        self.max_file_size_spin.setValue(100)
        
        self.backup_originals_cb = QCheckBox("Backup Original Files")
        self.backup_originals_cb.setChecked(False)
        
        self.overwrite_existing_cb = QCheckBox("Overwrite Existing Output")
        self.overwrite_existing_cb.setChecked(False)
        
        self.preserve_metadata_cb = QCheckBox("Preserve File Metadata")
        self.preserve_metadata_cb.setChecked(True)
        
        file_layout.addWidget(self.max_file_size_label, 0, 0)
        file_layout.addWidget(self.max_file_size_spin, 0, 1)
        file_layout.addWidget(self.backup_originals_cb, 1, 0, 1, 2)
        file_layout.addWidget(self.overwrite_existing_cb, 2, 0, 1, 2)
        file_layout.addWidget(self.preserve_metadata_cb, 3, 0, 1, 2)
        
        layout.addWidget(io_group)
        layout.addWidget(file_group)
        layout.addStretch()
        
        return tab
        
    def _create_processing_configuration_tab(self) -> QWidget:
        """Create the processing configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Threading Settings
        threading_group = QGroupBox("Threading Configuration")
        threading_layout = QGridLayout(threading_group)
        
        self.max_workers_label = QLabel("Maximum Worker Threads:")
        self.max_workers_spin = QSpinBox()
        self.max_workers_spin.setRange(1, 16)
        self.max_workers_spin.setValue(4)
        
        self.enable_parallel_cb = QCheckBox("Enable Parallel Processing")
        self.enable_parallel_cb.setChecked(True)
        
        self.thread_timeout_label = QLabel("Thread Timeout (seconds):")
        self.thread_timeout_spin = QSpinBox()
        self.thread_timeout_spin.setRange(30, 3600)
        self.thread_timeout_spin.setValue(300)
        
        threading_layout.addWidget(self.max_workers_label, 0, 0)
        threading_layout.addWidget(self.max_workers_spin, 0, 1)
        threading_layout.addWidget(self.enable_parallel_cb, 1, 0, 1, 2)
        threading_layout.addWidget(self.thread_timeout_label, 2, 0)
        threading_layout.addWidget(self.thread_timeout_spin, 2, 1)
        
        # Memory Management
        memory_group = QGroupBox("Memory Management")
        memory_layout = QGridLayout(memory_group)
        
        self.memory_limit_label = QLabel("Memory Limit (MB):")
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(256, 8192)
        self.memory_limit_spin.setValue(1024)
        
        self.enable_gc_cb = QCheckBox("Enable Aggressive Garbage Collection")
        self.enable_gc_cb.setChecked(False)
        
        self.chunk_size_label = QLabel("Processing Chunk Size:")
        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setRange(1, 1000)
        self.chunk_size_spin.setValue(50)
        
        memory_layout.addWidget(self.memory_limit_label, 0, 0)
        memory_layout.addWidget(self.memory_limit_spin, 0, 1)
        memory_layout.addWidget(self.enable_gc_cb, 1, 0, 1, 2)
        memory_layout.addWidget(self.chunk_size_label, 2, 0)
        memory_layout.addWidget(self.chunk_size_spin, 2, 1)
        
        # Error Handling
        error_group = QGroupBox("Error Handling")
        error_layout = QGridLayout(error_group)
        
        self.retry_count_label = QLabel("Max Retry Attempts:")
        self.retry_count_spin = QSpinBox()
        self.retry_count_spin.setRange(0, 10)
        self.retry_count_spin.setValue(3)
        
        self.continue_on_error_cb = QCheckBox("Continue Processing on Errors")
        self.continue_on_error_cb.setChecked(True)
        
        self.log_errors_cb = QCheckBox("Log Detailed Error Information")
        self.log_errors_cb.setChecked(True)
        
        error_layout.addWidget(self.retry_count_label, 0, 0)
        error_layout.addWidget(self.retry_count_spin, 0, 1)
        error_layout.addWidget(self.continue_on_error_cb, 1, 0, 1, 2)
        error_layout.addWidget(self.log_errors_cb, 2, 0, 1, 2)
        
        layout.addWidget(threading_group)
        layout.addWidget(memory_group)
        layout.addWidget(error_group)
        layout.addStretch()
        
        return tab
        
    def _create_quality_configuration_tab(self) -> QWidget:
        """Create the quality configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Quality Thresholds
        quality_group = QGroupBox("Quality Thresholds")
        quality_layout = QGridLayout(quality_group)
        
        self.min_quality_label = QLabel("Minimum Quality Score:")
        self.min_quality_slider = QSlider()
        self.min_quality_slider.setRange(0, 100)
        self.min_quality_slider.setValue(70)
        self.min_quality_value_label = QLabel("70%")
        self.min_quality_slider.valueChanged.connect(
            lambda v: self.min_quality_value_label.setText(f"{v}%")
        )
        
        self.confidence_threshold_label = QLabel("Confidence Threshold:")
        self.confidence_threshold_slider = QSlider()
        self.confidence_threshold_slider.setRange(0, 100)
        self.confidence_threshold_slider.setValue(80)
        self.confidence_value_label = QLabel("80%")
        self.confidence_threshold_slider.valueChanged.connect(
            lambda v: self.confidence_value_label.setText(f"{v}%")
        )
        
        quality_layout.addWidget(self.min_quality_label, 0, 0)
        quality_layout.addWidget(self.min_quality_slider, 0, 1)
        quality_layout.addWidget(self.min_quality_value_label, 0, 2)
        quality_layout.addWidget(self.confidence_threshold_label, 1, 0)
        quality_layout.addWidget(self.confidence_threshold_slider, 1, 1)
        quality_layout.addWidget(self.confidence_value_label, 1, 2)
        
        # Quality Checks
        checks_group = QGroupBox("Quality Checks")
        checks_layout = QGridLayout(checks_group)
        
        self.enable_spell_check_cb = QCheckBox("Enable Spell Checking")
        self.enable_spell_check_cb.setChecked(False)
        
        self.enable_grammar_check_cb = QCheckBox("Enable Grammar Checking")
        self.enable_grammar_check_cb.setChecked(False)
        
        self.check_encoding_cb = QCheckBox("Validate Text Encoding")
        self.check_encoding_cb.setChecked(True)
        
        self.detect_language_cb = QCheckBox("Detect Document Language")
        self.detect_language_cb.setChecked(True)
        
        self.validate_structure_cb = QCheckBox("Validate Document Structure")
        self.validate_structure_cb.setChecked(True)
        
        checks_layout.addWidget(self.enable_spell_check_cb, 0, 0)
        checks_layout.addWidget(self.enable_grammar_check_cb, 0, 1)
        checks_layout.addWidget(self.check_encoding_cb, 1, 0)
        checks_layout.addWidget(self.detect_language_cb, 1, 1)
        checks_layout.addWidget(self.validate_structure_cb, 2, 0)
        
        layout.addWidget(quality_group)
        layout.addWidget(checks_group)
        layout.addStretch()
        
        return tab
        
    def setup_connections(self):
        """Setup signal-slot connections"""
        self.temp_browse_btn.clicked.connect(self.browse_temp_directory)
        self.apply_btn.clicked.connect(self.apply_configuration)
        self.reset_btn.clicked.connect(self.reset_configuration)
        self.export_btn.clicked.connect(self.export_configuration)
        self.import_btn.clicked.connect(self.import_configuration)
        
        # Connect all controls to configuration change detection
        self._connect_all_controls()
        
    def _connect_all_controls(self):
        """Connect all UI controls to detect configuration changes"""
        # Connect combo boxes
        self.input_encoding_combo.currentTextChanged.connect(self._on_configuration_changed)
        self.output_encoding_combo.currentTextChanged.connect(self._on_configuration_changed)
        
        # Connect checkboxes
        checkboxes = [
            self.backup_originals_cb, self.overwrite_existing_cb, self.preserve_metadata_cb,
            self.enable_parallel_cb, self.enable_gc_cb, self.continue_on_error_cb, 
            self.log_errors_cb, self.enable_spell_check_cb, self.enable_grammar_check_cb,
            self.check_encoding_cb, self.detect_language_cb, self.validate_structure_cb
        ]
        for checkbox in checkboxes:
            checkbox.toggled.connect(self._on_configuration_changed)
            
        # Connect spin boxes
        spinboxes = [
            self.max_file_size_spin, self.max_workers_spin, self.thread_timeout_spin,
            self.memory_limit_spin, self.chunk_size_spin, self.retry_count_spin
        ]
        for spinbox in spinboxes:
            spinbox.valueChanged.connect(self._on_configuration_changed)
            
        # Connect sliders
        self.min_quality_slider.valueChanged.connect(self._on_configuration_changed)
        self.confidence_threshold_slider.valueChanged.connect(self._on_configuration_changed)
        
        # Connect line edits
        self.temp_directory_edit.textChanged.connect(self._on_configuration_changed)
        
    @pyqtSlot()
    def _on_configuration_changed(self):
        """Handle configuration changes"""
        self.current_config = self.get_current_configuration()
        self.configuration_changed.emit(self.current_config)
        
    @pyqtSlot()
    def browse_temp_directory(self):
        """Browse for temporary directory"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Temporary Directory",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.temp_directory_edit.setText(directory)
            
    def get_current_configuration(self) -> Dict[str, Any]:
        """Get current configuration from UI controls"""
        config = {
            # General settings
            'input_encoding': self.input_encoding_combo.currentText(),
            'output_encoding': self.output_encoding_combo.currentText(),
            'temp_directory': self.temp_directory_edit.text() or None,
            'max_file_size_mb': self.max_file_size_spin.value(),
            'backup_originals': self.backup_originals_cb.isChecked(),
            'overwrite_existing': self.overwrite_existing_cb.isChecked(),
            'preserve_metadata': self.preserve_metadata_cb.isChecked(),
            
            # Processing settings
            'max_workers': self.max_workers_spin.value(),
            'enable_parallel': self.enable_parallel_cb.isChecked(),
            'thread_timeout': self.thread_timeout_spin.value(),
            'memory_limit_mb': self.memory_limit_spin.value(),
            'enable_gc': self.enable_gc_cb.isChecked(),
            'chunk_size': self.chunk_size_spin.value(),
            
            # Error handling
            'max_retries': self.retry_count_spin.value(),
            'continue_on_error': self.continue_on_error_cb.isChecked(),
            'log_errors': self.log_errors_cb.isChecked(),
            
            # Quality settings
            'min_quality_score': self.min_quality_slider.value(),
            'confidence_threshold': self.confidence_threshold_slider.value(),
            'enable_spell_check': self.enable_spell_check_cb.isChecked(),
            'enable_grammar_check': self.enable_grammar_check_cb.isChecked(),
            'check_encoding': self.check_encoding_cb.isChecked(),
            'detect_language': self.detect_language_cb.isChecked(),
            'validate_structure': self.validate_structure_cb.isChecked()
        }
        
        return config
        
    def set_configuration(self, config: Dict[str, Any]):
        """Set configuration in UI controls"""
        # Block signals to prevent cascading updates
        self.blockSignals(True)
        
        try:
            # General settings
            self.input_encoding_combo.setCurrentText(config.get('input_encoding', 'utf-8'))
            self.output_encoding_combo.setCurrentText(config.get('output_encoding', 'utf-8'))
            self.temp_directory_edit.setText(config.get('temp_directory', ''))
            self.max_file_size_spin.setValue(config.get('max_file_size_mb', 100))
            self.backup_originals_cb.setChecked(config.get('backup_originals', False))
            self.overwrite_existing_cb.setChecked(config.get('overwrite_existing', False))
            self.preserve_metadata_cb.setChecked(config.get('preserve_metadata', True))
            
            # Processing settings
            self.max_workers_spin.setValue(config.get('max_workers', 4))
            self.enable_parallel_cb.setChecked(config.get('enable_parallel', True))
            self.thread_timeout_spin.setValue(config.get('thread_timeout', 300))
            self.memory_limit_spin.setValue(config.get('memory_limit_mb', 1024))
            self.enable_gc_cb.setChecked(config.get('enable_gc', False))
            self.chunk_size_spin.setValue(config.get('chunk_size', 50))
            
            # Error handling
            self.retry_count_spin.setValue(config.get('max_retries', 3))
            self.continue_on_error_cb.setChecked(config.get('continue_on_error', True))
            self.log_errors_cb.setChecked(config.get('log_errors', True))
            
            # Quality settings
            self.min_quality_slider.setValue(config.get('min_quality_score', 70))
            self.confidence_threshold_slider.setValue(config.get('confidence_threshold', 80))
            self.enable_spell_check_cb.setChecked(config.get('enable_spell_check', False))
            self.enable_grammar_check_cb.setChecked(config.get('enable_grammar_check', False))
            self.check_encoding_cb.setChecked(config.get('check_encoding', True))
            self.detect_language_cb.setChecked(config.get('detect_language', True))
            self.validate_structure_cb.setChecked(config.get('validate_structure', True))
            
        finally:
            self.blockSignals(False)
            
        # Update current config
        self.current_config = config.copy()
        
    def load_default_configuration(self):
        """Load default configuration"""
        default_config = {
            'input_encoding': 'utf-8',
            'output_encoding': 'utf-8',
            'temp_directory': '',
            'max_file_size_mb': 100,
            'backup_originals': False,
            'overwrite_existing': False,
            'preserve_metadata': True,
            'max_workers': 4,
            'enable_parallel': True,
            'thread_timeout': 300,
            'memory_limit_mb': 1024,
            'enable_gc': False,
            'chunk_size': 50,
            'max_retries': 3,
            'continue_on_error': True,
            'log_errors': True,
            'min_quality_score': 70,
            'confidence_threshold': 80,
            'enable_spell_check': False,
            'enable_grammar_check': False,
            'check_encoding': True,
            'detect_language': True,
            'validate_structure': True
        }
        
        self.set_configuration(default_config)
        
    @pyqtSlot()
    def apply_configuration(self):
        """Apply current configuration to the base extractor"""
        config = self.get_current_configuration()
        
        try:
            # Apply configuration to the base extractor
            self.extractor.configure(**config)
            self.show_info("Configuration Applied", "Base extractor configuration has been updated successfully")
            
            # Emit configuration change signal
            self.configuration_changed.emit(config)
            
        except Exception as e:
            self.show_error("Configuration Error", f"Failed to apply configuration: {str(e)}")
            
    @pyqtSlot()
    def reset_configuration(self):
        """Reset to default configuration"""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Reset Configuration",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.load_default_configuration()
            
    @pyqtSlot()
    def export_configuration(self):
        """Export configuration to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Configuration",
            "base_extractor_config.json",
            "JSON Files (*.json);;YAML Files (*.yaml)"
        )
        
        if filename:
            try:
                import json
                config = self.get_current_configuration()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    if filename.endswith('.yaml'):
                        import yaml
                        yaml.dump(config, f, default_flow_style=False)
                    else:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                        
                self.show_info("Export Successful", f"Configuration exported to {filename}")
                
            except Exception as e:
                self.show_error("Export Error", f"Failed to export configuration: {str(e)}")
                
    @pyqtSlot()
    def import_configuration(self):
        """Import configuration from file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import Configuration",
            "",
            "JSON Files (*.json);;YAML Files (*.yaml);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    if filename.endswith('.yaml'):
                        import yaml
                        config = yaml.safe_load(f)
                    else:
                        import json
                        config = json.load(f)
                        
                self.set_configuration(config)
                self.show_info("Import Successful", f"Configuration imported from {filename}")
                
            except Exception as e:
                self.show_error("Import Error", f"Failed to import configuration: {str(e)}")
                
    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.current_config.copy()
        
    def is_configuration_valid(self) -> bool:
        """Check if current configuration is valid"""
        config = self.get_current_configuration()
        
        # Basic validation
        if config['max_file_size_mb'] <= 0:
            return False
        if config['max_workers'] <= 0:
            return False
        if config['memory_limit_mb'] <= 0:
            return False
            
        return True
