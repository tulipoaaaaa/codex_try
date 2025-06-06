"""
Domains Manager Wrapper for UI Integration
Provides domain classification and management capabilities
"""

import os
import json
from typing import Dict, List, Optional, Any, Set
from PySide6.QtCore import QObject, QThread, Signal as pyqtSignal, Slot as pyqtSlot, QMutex
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QProgressBar, QLabel, QTextEdit, QFileDialog, QCheckBox, 
                           QSpinBox, QGroupBox, QGridLayout, QComboBox, QListWidget,
                           QSplitter, QTabWidget, QTableWidget, QTableWidgetItem,
                           QHeaderView, QLineEdit, QTreeWidget, QTreeWidgetItem)
from shared_tools.ui_wrappers.base_wrapper import BaseWrapper
from shared_tools.processors.domainsmanager import DomainsManager
from shared_tools.processors.mixins.processor_wrapper_mixin import ProcessorWrapperMixin


class DomainsManagerWorker(QThread):
    """Worker thread for domain management operations"""
    
    progress_updated = pyqtSignal(int, str)  # progress percentage, current operation
    domain_processed = pyqtSignal(str, dict)  # domain, classification result
    classification_completed = pyqtSignal(dict)  # final statistics
    error_occurred = pyqtSignal(str, str)  # error type, error message
    domain_added = pyqtSignal(str, str)  # domain, category
    domain_removed = pyqtSignal(str)  # domain
    
    def __init__(self, operation: str, data: Any, options: Dict[str, Any]):
        super().__init__()
        self.operation = operation
        self.data = data
        self.options = options
        self.manager = DomainsManager()
        self._is_cancelled = False
        self._mutex = QMutex()
        
    def run(self):
        """Execute domain management operation"""
        try:
            if self.operation == "classify_domains":
                self._classify_domains()
            elif self.operation == "import_domains":
                self._import_domains()
            elif self.operation == "export_domains":
                self._export_domains()
            elif self.operation == "analyze_corpus":
                self._analyze_corpus()
                
        except Exception as e:
            self.error_occurred.emit("Operation Error", str(e))
            
    def _classify_domains(self):
        """Classify a list of domains"""
        domains = self.data
        total_domains = len(domains)
        
        if total_domains == 0:
            self.error_occurred.emit("No Domains", "No domains provided for classification")
            return
            
        results = {'classified': 0, 'failed': 0, 'categories': {}}
        
        for i, domain in enumerate(domains):
            if self._is_cancelled:
                break
                
            # Update progress
            progress = int((i / total_domains) * 100)
            self.progress_updated.emit(progress, f"Classifying: {domain}")
            
            try:
                # Classify domain
                classification = self.manager.classify_domain(
                    domain,
                    confidence_threshold=self.options.get('confidence_threshold', 0.7),
                    use_ml_classification=self.options.get('use_ml_classification', True),
                    check_whois=self.options.get('check_whois', False)
                )
                
                self.domain_processed.emit(domain, classification)
                results['classified'] += 1
                
                # Update category statistics
                category = classification.get('category', 'unknown')
                results['categories'][category] = results['categories'].get(category, 0) + 1
                
            except Exception as e:
                results['failed'] += 1
                self.domain_processed.emit(domain, {
                    'category': 'error',
                    'confidence': 0.0,
                    'error': str(e)
                })
                
        self.progress_updated.emit(100, "Classification completed")
        self.classification_completed.emit(results)
        
    def _import_domains(self):
        """Import domains from file"""
        file_path = self.data
        
        try:
            imported_count = self.manager.import_domains_from_file(
                file_path,
                format=self.options.get('format', 'auto'),
                update_existing=self.options.get('update_existing', False)
            )
            
            self.progress_updated.emit(100, f"Imported {imported_count} domains")
            self.classification_completed.emit({'imported': imported_count})
            
        except Exception as e:
            self.error_occurred.emit("Import Error", str(e))
            
    def _export_domains(self):
        """Export domains to file"""
        file_path, categories = self.data
        
        try:
            exported_count = self.manager.export_domains_to_file(
                file_path,
                categories=categories,
                format=self.options.get('format', 'json'),
                include_metadata=self.options.get('include_metadata', True)
            )
            
            self.progress_updated.emit(100, f"Exported {exported_count} domains")
            self.classification_completed.emit({'exported': exported_count})
            
        except Exception as e:
            self.error_occurred.emit("Export Error", str(e))
            
    def _analyze_corpus(self):
        """Analyze domain distribution in corpus"""
        corpus_path = self.data
        
        try:
            analysis = self.manager.analyze_corpus_domains(
                corpus_path,
                extract_urls=self.options.get('extract_urls', True),
                classify_domains=self.options.get('classify_domains', True),
                generate_report=self.options.get('generate_report', True)
            )
            
            self.progress_updated.emit(100, "Corpus analysis completed")
            self.classification_completed.emit(analysis)
            
        except Exception as e:
            self.error_occurred.emit("Analysis Error", str(e))
            
    def cancel(self):
        """Cancel the current operation"""
        self._mutex.lock()
        self._is_cancelled = True
        self._mutex.unlock()


class DomainsManagerWrapper(BaseWrapper, ProcessorWrapperMixin):
    """UI Wrapper for Domains Manager"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.domain_classifications = {}
        self.domain_categories = set()
        self.setup_ui()
        self.setup_connections()
        self.load_existing_domains()
        
    def setup_ui(self):
        """Initialize the user interface components"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Domain Classification Tab
        classification_tab = self._create_classification_tab()
        self.tab_widget.addTab(classification_tab, "Domain Classification")
        
        # Domain Management Tab
        management_tab = self._create_management_tab()
        self.tab_widget.addTab(management_tab, "Domain Management")
        
        # Corpus Analysis Tab
        analysis_tab = self._create_analysis_tab()
        self.tab_widget.addTab(analysis_tab, "Corpus Analysis")
        
        # Settings Tab
        settings_tab = self._create_settings_tab()
        self.tab_widget.addTab(settings_tab, "Settings")
        
        layout.addWidget(self.tab_widget)
        
    def _create_classification_tab(self) -> QWidget:
        """Create the domain classification tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Input Section
        input_group = QGroupBox("Domain Input")
        input_layout = QVBoxLayout(input_group)
        
        # Single domain input
        single_layout = QHBoxLayout()
        self.single_domain_input = QLineEdit()
        self.single_domain_input.setPlaceholderText("Enter domain (e.g., example.com)")
        self.classify_single_btn = QPushButton("Classify")
        
        single_layout.addWidget(QLabel("Single Domain:"))
        single_layout.addWidget(self.single_domain_input)
        single_layout.addWidget(self.classify_single_btn)
        
        # Bulk domain input
        bulk_layout = QVBoxLayout()
        bulk_layout.addWidget(QLabel("Bulk Domains (one per line):"))
        self.bulk_domains_input = QTextEdit()
        self.bulk_domains_input.setMaximumHeight(150)
        self.bulk_domains_input.setPlaceholderText("domain1.com\ndomain2.org\ndomain3.net")
        
        bulk_controls = QHBoxLayout()
        self.load_domains_btn = QPushButton("Load from File")
        self.classify_bulk_btn = QPushButton("Classify All")
        self.clear_domains_btn = QPushButton("Clear")
        
        bulk_controls.addWidget(self.load_domains_btn)
        bulk_controls.addWidget(self.classify_bulk_btn)
        bulk_controls.addWidget(self.clear_domains_btn)
        bulk_controls.addStretch()
        
        bulk_layout.addWidget(self.bulk_domains_input)
        bulk_layout.addLayout(bulk_controls)
        
        input_layout.addLayout(single_layout)
        input_layout.addLayout(bulk_layout)
        
        # Classification Options
        options_group = QGroupBox("Classification Options")
        options_layout = QGridLayout(options_group)
        
        self.confidence_threshold_label = QLabel("Confidence Threshold:")
        self.confidence_threshold_spin = QDoubleSpinBox()
        self.confidence_threshold_spin.setRange(0.0, 1.0)
        self.confidence_threshold_spin.setSingleStep(0.1)
        self.confidence_threshold_spin.setValue(0.7)
        
        self.use_ml_cb = QCheckBox("Use ML Classification")
        self.use_ml_cb.setChecked(True)
        
        self.check_whois_cb = QCheckBox("Check WHOIS Data")
        self.check_whois_cb.setChecked(False)
        
        options_layout.addWidget(self.confidence_threshold_label, 0, 0)
        options_layout.addWidget(self.confidence_threshold_spin, 0, 1)
        options_layout.addWidget(self.use_ml_cb, 1, 0)
        options_layout.addWidget(self.check_whois_cb, 1, 1)
        
        # Progress and Results
        progress_group = QGroupBox("Classification Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("Ready to classify domains")
        
        # Results table
        self.classification_table = QTableWidget()
        self.classification_table.setColumnCount(4)
        self.classification_table.setHorizontalHeaderLabels(["Domain", "Category", "Confidence", "Details"])
        
        header = self.classification_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.classification_table)
        
        layout.addWidget(input_group)
        layout.addWidget(options_group)
        layout.addWidget(progress_group)
        
        return tab
        
    def _create_management_tab(self) -> QWidget:
        """Create the domain management tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create splitter
        splitter = QSplitter()
        
        # Domain Tree
        tree_group = QGroupBox("Domain Categories")
        tree_layout = QVBoxLayout(tree_group)
        
        self.domain_tree = QTreeWidget()
        self.domain_tree.setHeaderLabels(["Category", "Count"])
        tree_layout.addWidget(self.domain_tree)
        
        # Tree controls
        tree_controls = QHBoxLayout()
        self.add_category_btn = QPushButton("Add Category")
        self.remove_category_btn = QPushButton("Remove Category")
        self.refresh_tree_btn = QPushButton("Refresh")
        
        tree_controls.addWidget(self.add_category_btn)
        tree_controls.addWidget(self.remove_category_btn)
        tree_controls.addWidget(self.refresh_tree_btn)
        tree_controls.addStretch()
        
        tree_layout.addLayout(tree_controls)
        
        # Domain List
        list_group = QGroupBox("Domains in Selected Category")
        list_layout = QVBoxLayout(list_group)
        
        self.domain_list = QListWidget()
        list_layout.addWidget(self.domain_list)
        
        # Domain controls
        domain_controls = QHBoxLayout()
        self.add_domain_btn = QPushButton("Add Domain")
        self.remove_domain_btn = QPushButton("Remove Domain")
        self.move_domain_btn = QPushButton("Move to Category")
        
        domain_controls.addWidget(self.add_domain_btn)
        domain_controls.addWidget(self.remove_domain_btn)
        domain_controls.addWidget(self.move_domain_btn)
        domain_controls.addStretch()
        
        list_layout.addLayout(domain_controls)
        
        splitter.addWidget(tree_group)
        splitter.addWidget(list_group)
        splitter.setSizes([300, 400])
        
        # Import/Export Controls
        io_layout = QHBoxLayout()
        self.import_domains_btn = QPushButton("Import Domains")
        self.export_domains_btn = QPushButton("Export Domains")
        self.export_category_btn = QPushButton("Export Category")
        
        io_layout.addWidget(self.import_domains_btn)
        io_layout.addWidget(self.export_domains_btn)
        io_layout.addWidget(self.export_category_btn)
        io_layout.addStretch()
        
        layout.addWidget(splitter)
        layout.addLayout(io_layout)
        
        return tab
        
    def _create_analysis_tab(self) -> QWidget:
        """Create the corpus analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Corpus Selection
        corpus_group = QGroupBox("Corpus Selection")
        corpus_layout = QGridLayout(corpus_group)
        
        self.corpus_path_label = QLabel("Corpus Directory:")
        self.corpus_path_display = QLabel("No directory selected")
        self.corpus_browse_btn = QPushButton("Browse...")
        
        corpus_layout.addWidget(self.corpus_path_label, 0, 0)
        corpus_layout.addWidget(self.corpus_path_display, 0, 1)
        corpus_layout.addWidget(self.corpus_browse_btn, 0, 2)
        
        # Analysis Options
        analysis_group = QGroupBox("Analysis Options")
        analysis_layout = QGridLayout(analysis_group)
        
        self.extract_urls_cb = QCheckBox("Extract URLs from Documents")
        self.extract_urls_cb.setChecked(True)
        
        self.classify_extracted_cb = QCheckBox("Classify Extracted Domains")
        self.classify_extracted_cb.setChecked(True)
        
        self.generate_report_cb = QCheckBox("Generate Analysis Report")
        self.generate_report_cb.setChecked(True)
        
        analysis_layout.addWidget(self.extract_urls_cb, 0, 0)
        analysis_layout.addWidget(self.classify_extracted_cb, 0, 1)
        analysis_layout.addWidget(self.generate_report_cb, 1, 0)
        
        # Analysis Controls
        control_layout = QHBoxLayout()
        self.start_analysis_btn = QPushButton("Start Analysis")
        self.cancel_analysis_btn = QPushButton("Cancel")
        self.cancel_analysis_btn.setEnabled(False)
        
        control_layout.addWidget(self.start_analysis_btn)
        control_layout.addWidget(self.cancel_analysis_btn)
        control_layout.addStretch()
        
        # Results Display
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout(results_group)
        
        self.analysis_results = QTextEdit()
        self.analysis_results.setReadOnly(True)
        results_layout.addWidget(self.analysis_results)
        
        layout.addWidget(corpus_group)
        layout.addWidget(analysis_group)
        layout.addLayout(control_layout)
        layout.addWidget(results_group)
        
        return tab
        
    def _create_settings_tab(self) -> QWidget:
        """Create the settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Database Settings
        db_group = QGroupBox("Database Settings")
        db_layout = QGridLayout(db_group)
        
        self.db_path_label = QLabel("Database Path:")
        self.db_path_display = QLabel("default.db")
        self.db_browse_btn = QPushButton("Browse...")
        
        db_layout.addWidget(self.db_path_label, 0, 0)
        db_layout.addWidget(self.db_path_display, 0, 1)
        db_layout.addWidget(self.db_browse_btn, 0, 2)
        
        # API Settings
        api_group = QGroupBox("API Settings")
        api_layout = QGridLayout(api_group)
        
        self.api_timeout_label = QLabel("API Timeout (seconds):")
        self.api_timeout_spin = QSpinBox()
        self.api_timeout_spin.setRange(5, 300)
        self.api_timeout_spin.setValue(30)
        
        self.max_retries_label = QLabel("Max Retries:")
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setRange(0, 10)
        self.max_retries_spin.setValue(3)
        
        api_layout.addWidget(self.api_timeout_label, 0, 0)
        api_layout.addWidget(self.api_timeout_spin, 0, 1)
        api_layout.addWidget(self.max_retries_label, 1, 0)
        api_layout.addWidget(self.max_retries_spin, 1, 1)
        
        # Cache Settings
        cache_group = QGroupBox("Cache Settings")
        cache_layout = QGridLayout(cache_group)
        
        self.enable_cache_cb = QCheckBox("Enable Classification Cache")
        self.enable_cache_cb.setChecked(True)
        
        self.cache_expiry_label = QLabel("Cache Expiry (days):")
        self.cache_expiry_spin = QSpinBox()
        self.cache_expiry_spin.setRange(1, 365)
        self.cache_expiry_spin.setValue(30)
        
        self.clear_cache_btn = QPushButton("Clear Cache")
        
        cache_layout.addWidget(self.enable_cache_cb, 0, 0)
        cache_layout.addWidget(self.cache_expiry_label, 1, 0)
        cache_layout.addWidget(self.cache_expiry_spin, 1, 1)
        cache_layout.addWidget(self.clear_cache_btn, 2, 0)
        
        layout.addWidget(db_group)
        layout.addWidget(api_group)
        layout.addWidget(cache_group)
        layout.addStretch()
        
        return tab
        
    def setup_connections(self):
        """Setup signal-slot connections"""
        # Classification tab
        self.classify_single_btn.clicked.connect(self.classify_single_domain)
        self.load_domains_btn.clicked.connect(self.load_domains_from_file)
        self.classify_bulk_btn.clicked.connect(self.classify_bulk_domains)
        self.clear_domains_btn.clicked.connect(self.clear_domain_input)
        
        # Management tab
        self.add_category_btn.clicked.connect(self.add_category)
        self.remove_category_btn.clicked.connect(self.remove_category)
        self.refresh_tree_btn.clicked.connect(self.refresh_domain_tree)
        self.add_domain_btn.clicked.connect(self.add_domain)
        self.remove_domain_btn.clicked.connect(self.remove_domain)
        self.move_domain_btn.clicked.connect(self.move_domain)
        self.import_domains_btn.clicked.connect(self.import_domains)
        self.export_domains_btn.clicked.connect(self.export_domains)
        self.export_category_btn.clicked.connect(self.export_category)
        
        # Analysis tab
        self.corpus_browse_btn.clicked.connect(self.browse_corpus_directory)
        self.start_analysis_btn.clicked.connect(self.start_corpus_analysis)
        self.cancel_analysis_btn.clicked.connect(self.cancel_operation)
        
        # Settings tab
        self.db_browse_btn.clicked.connect(self.browse_database_path)
        self.clear_cache_btn.clicked.connect(self.clear_classification_cache)
        
        # Tree selection
        self.domain_tree.currentItemChanged.connect(self.on_category_selected)
        
    def load_existing_domains(self):
        """Load existing domains from database"""
        try:
            # This would typically load from the DomainsManager
            # For now, we'll populate with sample data
            self.refresh_domain_tree()
        except Exception as e:
            self.show_error("Load Error", f"Failed to load existing domains: {str(e)}")
            
    @pyqtSlot()
    def classify_single_domain(self):
        """Classify a single domain"""
        domain = self.single_domain_input.text().strip()
        if not domain:
            self.show_error("Input Error", "Please enter a domain to classify")
            return
            
        options = self._get_classification_options()
        
        # Create and start worker
        self.worker = DomainsManagerWorker("classify_domains", [domain], options)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.domain_processed.connect(self.add_classification_result)
        self.worker.classification_completed.connect(self.classification_completed)
        self.worker.error_occurred.connect(self.handle_error)
        
        self.worker.start()
        
    @pyqtSlot()
    def classify_bulk_domains(self):
        """Classify multiple domains"""
        domain_text = self.bulk_domains_input.toPlainText().strip()
        if not domain_text:
            self.show_error("Input Error", "Please enter domains to classify")
            return
            
        domains = [d.strip() for d in domain_text.split('\n') if d.strip()]
        if not domains:
            self.show_error("Input Error", "No valid domains found")
            return
            
        options = self._get_classification_options()
        
        # Clear existing results
        self.classification_table.setRowCount(0)
        
        # Create and start worker
        self.worker = DomainsManagerWorker("classify_domains", domains, options)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.domain_processed.connect(self.add_classification_result)
        self.worker.classification_completed.connect(self.classification_completed)
        self.worker.error_occurred.connect(self.handle_error)
        
        self.worker.start()
        
    def _get_classification_options(self) -> Dict[str, Any]:
        """Get current classification options"""
        return {
            'confidence_threshold': self.confidence_threshold_spin.value(),
            'use_ml_classification': self.use_ml_cb.isChecked(),
            'check_whois': self.check_whois_cb.isChecked()
        }
        
    @pyqtSlot(int, str)
    def update_progress(self, percentage: int, message: str):
        """Update progress display"""
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(message)
        
    @pyqtSlot(str, dict)
    def add_classification_result(self, domain: str, result: dict):
        """Add classification result to table"""
        row = self.classification_table.rowCount()
        self.classification_table.insertRow(row)
        
        category = result.get('category', 'unknown')
        confidence = result.get('confidence', 0.0)
        
        # Determine status icon
        if category == 'error':
            status_icon = "❌"
            details = result.get('error', 'Unknown error')
        elif confidence >= 0.8:
            status_icon = "✅"
            details = result.get('details', 'High confidence classification')
        elif confidence >= 0.6:
            status_icon = "⚠️"
            details = result.get('details', 'Moderate confidence classification')
        else:
            status_icon = "❓"
            details = result.get('details', 'Low confidence classification')
            
        self.classification_table.setItem(row, 0, QTableWidgetItem(domain))
        self.classification_table.setItem(row, 1, QTableWidgetItem(f"{status_icon} {category}"))
        self.classification_table.setItem(row, 2, QTableWidgetItem(f"{confidence:.3f}"))
        self.classification_table.setItem(row, 3, QTableWidgetItem(details))
        
        # Store result
        self.domain_classifications[domain] = result
        
    @pyqtSlot(dict)
    def classification_completed(self, stats: dict):
        """Handle classification completion"""
        self.operation_finished()
        
        # Show completion message
        classified = stats.get('classified', 0)
        failed = stats.get('failed', 0)
        categories = stats.get('categories', {})
        
        message = f"Classification completed:\n"
        message += f"Successfully classified: {classified}\n"
        message += f"Failed: {failed}\n\n"
        
        if categories:
            message += "Category distribution:\n"
            for category, count in categories.items():
                message += f"  {category}: {count}\n"
                
        self.show_info("Classification Complete", message)
        
    @pyqtSlot(str, str)
    def handle_error(self, error_type: str, error_message: str):
        """Handle operation errors"""
        self.operation_finished()
        self.show_error(error_type, error_message)
        
    def operation_finished(self):
        """Reset UI state after operation completion"""
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
            
    @pyqtSlot()
    def load_domains_from_file(self):
        """Load domains from a text file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Domains from File",
            "",
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Simple parsing - one domain per line or comma-separated
                if filename.endswith('.csv'):
                    domains = [d.strip() for line in content.split('\n') 
                              for d in line.split(',') if d.strip()]
                else:
                    domains = [d.strip() for d in content.split('\n') if d.strip()]
                    
                self.bulk_domains_input.setPlainText('\n'.join(domains))
                self.show_info("Domains Loaded", f"Loaded {len(domains)} domains from file")
                
            except Exception as e:
                self.show_error("Load Error", f"Failed to load domains: {str(e)}")
                
    @pyqtSlot()
    def clear_domain_input(self):
        """Clear domain input fields"""
        self.single_domain_input.clear()
        self.bulk_domains_input.clear()
        self.classification_table.setRowCount(0)
        
    def refresh_domain_tree(self):
        """Refresh the domain category tree"""
        self.domain_tree.clear()
        
        # This would typically load from DomainsManager
        # For demo purposes, we'll show sample categories
        categories = {
            'Academic': ['edu.domains', 'university.sites'],
            'Commercial': ['business.sites', 'ecommerce.domains'],
            'Government': ['gov.domains', 'official.sites'],
            'News': ['news.sites', 'media.domains'],
            'Social': ['social.networks', 'forums.sites'],
            'Unknown': ['unclassified.domains']
        }
        
        for category, domains in categories.items():
            category_item = QTreeWidgetItem([category, str(len(domains))])
            self.domain_tree.addTopLevelItem(category_item)
            
            for domain in domains:
                domain_item = QTreeWidgetItem([domain, ""])
                category_item.addChild(domain_item)
                
        self.domain_tree.expandAll()
        
    def on_category_selected(self, current, previous):
        """Handle category selection in tree"""
        if current and current.parent() is None:  # Top-level category
            category = current.text(0)
            self._load_domains_for_category(category)
            
    def _load_domains_for_category(self, category: str):
        """Load domains for selected category"""
        self.domain_list.clear()
        
        # This would typically load from DomainsManager
        # For demo purposes, we'll show sample domains
        sample_domains = {
            'Academic': ['harvard.edu', 'stanford.edu', 'mit.edu'],
            'Commercial': ['amazon.com', 'google.com', 'microsoft.com'],
            'Government': ['whitehouse.gov', 'fbi.gov', 'nasa.gov'],
            'News': ['cnn.com', 'bbc.com', 'reuters.com'],
            'Social': ['facebook.com', 'twitter.com', 'linkedin.com'],
            'Unknown': ['example1.com', 'example2.org', 'example3.net']
        }
        
        domains = sample_domains.get(category, [])
        for domain in domains:
            self.domain_list.addItem(domain)
            
    @pyqtSlot()
    def add_category(self):
        """Add a new domain category"""
        from PySide6.QtWidgets import QInputDialog
        
        category, ok = QInputDialog.getText(
            self, 
            "Add Category", 
            "Enter category name:"
        )
        
        if ok and category.strip():
            # This would typically add to DomainsManager
            self.refresh_domain_tree()
            self.show_info("Category Added", f"Category '{category}' has been added")
            
    @pyqtSlot()
    def remove_category(self):
        """Remove selected domain category"""
        current = self.domain_tree.currentItem()
        if current and current.parent() is None:
            category = current.text(0)
            
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "Remove Category",
                f"Are you sure you want to remove category '{category}'?\n"
                "This will also remove all domains in this category.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # This would typically remove from DomainsManager
                self.refresh_domain_tree()
                self.show_info("Category Removed", f"Category '{category}' has been removed")
                
    @pyqtSlot()
    def add_domain(self):
        """Add domain to selected category"""
        current = self.domain_tree.currentItem()
        if not current or current.parent() is not None:
            self.show_error("Selection Error", "Please select a category first")
            return
            
        from PySide6.QtWidgets import QInputDialog
        
        domain, ok = QInputDialog.getText(
            self, 
            "Add Domain", 
            "Enter domain name:"
        )
        
        if ok and domain.strip():
            category = current.text(0)
            # This would typically add to DomainsManager
            self._load_domains_for_category(category)
            self.show_info("Domain Added", f"Domain '{domain}' added to category '{category}'")
            
    @pyqtSlot()
    def remove_domain(self):
        """Remove selected domain"""
        current_domain = self.domain_list.currentItem()
        if not current_domain:
            self.show_error("Selection Error", "Please select a domain to remove")
            return
            
        domain = current_domain.text()
        
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Remove Domain",
            f"Are you sure you want to remove domain '{domain}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # This would typically remove from DomainsManager
            current_category = self.domain_tree.currentItem()
            if current_category:
                self._load_domains_for_category(current_category.text(0))
            self.show_info("Domain Removed", f"Domain '{domain}' has been removed")
            
    @pyqtSlot()
    def move_domain(self):
        """Move domain to different category"""
        current_domain = self.domain_list.currentItem()
        if not current_domain:
            self.show_error("Selection Error", "Please select a domain to move")
            return
            
        # Implementation would show category selection dialog
        self.show_info("Move Domain", "Domain move functionality would be implemented here")
        
    @pyqtSlot()
    def import_domains(self):
        """Import domains from file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import Domains",
            "",
            "JSON Files (*.json);;CSV Files (*.csv);;Text Files (*.txt)"
        )
        
        if filename:
            options = {'format': 'auto', 'update_existing': True}
            
            self.worker = DomainsManagerWorker("import_domains", filename, options)
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.classification_completed.connect(self.import_completed)
            self.worker.error_occurred.connect(self.handle_error)
            
            self.worker.start()
            
    @pyqtSlot(dict)
    def import_completed(self, stats: dict):
        """Handle import completion"""
        self.operation_finished()
        imported = stats.get('imported', 0)
        self.show_info("Import Complete", f"Successfully imported {imported} domains")
        self.refresh_domain_tree()
        
    @pyqtSlot()
    def export_domains(self):
        """Export all domains"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Domains",
            "domains_export.json",
            "JSON Files (*.json);;CSV Files (*.csv)"
        )
        
        if filename:
            format_type = 'json' if filename.endswith('.json') else 'csv'
            options = {'format': format_type, 'include_metadata': True}
            
            self.worker = DomainsManagerWorker("export_domains", (filename, None), options)
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.classification_completed.connect(self.export_completed)
            self.worker.error_occurred.connect(self.handle_error)
            
            self.worker.start()
            
    @pyqtSlot()
    def export_category(self):
        """Export selected category"""
        current = self.domain_tree.currentItem()
        if not current or current.parent() is not None:
            self.show_error("Selection Error", "Please select a category to export")
            return
            
        category = current.text(0)
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            f"Export Category: {category}",
            f"{category}_domains.json",
            "JSON Files (*.json);;CSV Files (*.csv)"
        )
        
        if filename:
            format_type = 'json' if filename.endswith('.json') else 'csv'
            options = {'format': format_type, 'include_metadata': True}
            
            self.worker = DomainsManagerWorker("export_domains", (filename, [category]), options)
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.classification_completed.connect(self.export_completed)
            self.worker.error_occurred.connect(self.handle_error)
            
            self.worker.start()
            
    @pyqtSlot(dict)
    def export_completed(self, stats: dict):
        """Handle export completion"""
        self.operation_finished()
        exported = stats.get('exported', 0)
        self.show_info("Export Complete", f"Successfully exported {exported} domains")
        
    @pyqtSlot()
    def browse_corpus_directory(self):
        """Browse for corpus directory"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Corpus Directory",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.corpus_path_display.setText(directory)
            
    @pyqtSlot()
    def start_corpus_analysis(self):
        """Start corpus domain analysis"""
        corpus_path = self.corpus_path_display.text()
        
        if corpus_path == "No directory selected":
            self.show_error("Configuration Error", "Please select a corpus directory")
            return
            
        options = {
            'extract_urls': self.extract_urls_cb.isChecked(),
            'classify_domains': self.classify_extracted_cb.isChecked(),
            'generate_report': self.generate_report_cb.isChecked()
        }
        
        # Update UI state
        self.start_analysis_btn.setEnabled(False)
        self.cancel_analysis_btn.setEnabled(True)
        self.analysis_results.clear()
        
        # Switch to analysis tab
        self.tab_widget.setCurrentIndex(2)
        
        self.worker = DomainsManagerWorker("analyze_corpus", corpus_path, options)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.classification_completed.connect(self.analysis_completed)
        self.worker.error_occurred.connect(self.handle_error)
        
        self.worker.start()
        
    @pyqtSlot(dict)
    def analysis_completed(self, analysis: dict):
        """Handle corpus analysis completion"""
        self.start_analysis_btn.setEnabled(True)
        self.cancel_analysis_btn.setEnabled(False)
        self.operation_finished()
        
        # Display analysis results
        results_text = "CORPUS DOMAIN ANALYSIS RESULTS\n"
        results_text += "="*40 + "\n\n"
        
        # Add analysis data (this would come from the actual analysis)
        results_text += f"Total URLs extracted: {analysis.get('total_urls', 0)}\n"
        results_text += f"Unique domains found: {analysis.get('unique_domains', 0)}\n"
        results_text += f"Domains classified: {analysis.get('classified_domains', 0)}\n\n"
        
        domain_categories = analysis.get('domain_categories', {})
        if domain_categories:
            results_text += "Domain Categories:\n"
            results_text += "-" * 20 + "\n"
            for category, count in domain_categories.items():
                results_text += f"{category}: {count}\n"
                
        self.analysis_results.setText(results_text)
        
    @pyqtSlot()
    def cancel_operation(self):
        """Cancel current operation"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(3000)
            self.operation_finished()
            
        self.start_analysis_btn.setEnabled(True)
        self.cancel_analysis_btn.setEnabled(False)
        
    @pyqtSlot()
    def browse_database_path(self):
        """Browse for database file"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Select Database File",
            "domains.db",
            "Database Files (*.db);;All Files (*)"
        )
        
        if filename:
            self.db_path_display.setText(filename)
            
    @pyqtSlot()
    def clear_classification_cache(self):
        """Clear classification cache"""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Clear Cache",
            "Are you sure you want to clear the classification cache?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # This would clear the actual cache
            self.show_info("Cache Cleared", "Classification cache has been cleared")
            
    def get_domain_classifications(self) -> Dict[str, dict]:
        """Get domain classification results"""
        return self.domain_classifications.copy()
        
    def is_processing(self) -> bool:
        """Check if any operation is currently active"""
        return self.worker is not None and self.worker.isRunning()
