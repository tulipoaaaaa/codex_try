from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QProgressBar,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QListWidget,
    QGroupBox,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, Slot as pyqtSlot, Signal as pyqtSignal
import logging
from PySide6.QtGui import QIcon
import os
import shutil
import time

from shared_tools.ui_wrappers.processors.batch_nonpdf_extractor_enhanced_wrapper import BatchNonPDFExtractorEnhancedWrapper
from shared_tools.ui_wrappers.processors.pdf_extractor_wrapper import PDFExtractorWrapper
from shared_tools.ui_wrappers.processors.base_extractor_wrapper import BaseExtractorWrapper
from shared_tools.ui_wrappers.processors.text_extractor_wrapper import TextExtractorWrapper
from shared_tools.ui_wrappers.processors.batch_text_extractor_enhanced_prerefactor_wrapper import BatchTextExtractorEnhancedPrerefactorWrapper
from shared_tools.ui_wrappers.processors.deduplicate_nonpdf_outputs_wrapper import DeduplicateNonPDFOutputsWrapper
from shared_tools.ui_wrappers.processors.deduplicator_wrapper import DeduplicatorWrapper
from shared_tools.ui_wrappers.processors.quality_control_wrapper import QualityControlWrapper
from shared_tools.ui_wrappers.processors.corruption_detector_wrapper import CorruptionDetectorWrapper
from shared_tools.ui_wrappers.processors.domain_classifier_wrapper import DomainClassifierWrapper
from shared_tools.ui_wrappers.processors.domainsmanager_wrapper import DomainsManagerWrapper
from shared_tools.ui_wrappers.processors.monitor_progress_wrapper import MonitorProgressWrapper
from shared_tools.ui_wrappers.processors.machine_translation_detector_wrapper import MachineTranslationDetectorWrapper
from shared_tools.ui_wrappers.processors.language_confidence_detector_wrapper import LanguageConfidenceDetectorWrapper
from shared_tools.ui_wrappers.processors.financial_symbol_processor_wrapper import FinancialSymbolProcessorWrapper
from shared_tools.ui_wrappers.processors.chart_image_extractor_wrapper import ChartImageExtractorWrapper
from shared_tools.ui_wrappers.processors.formula_extractor_wrapper import FormulaExtractorWrapper
from shared_tools.ui_wrappers.processors.corpus_balancer_wrapper import CorpusBalancerWrapper
from .corpus_manager_tab import NotificationManager
from app.helpers.icon_manager import IconManager
from app.helpers.notifier import Notifier
from app.ui.widgets.section_header import SectionHeader
from app.ui.theme.theme_constants import PAGE_MARGIN

logger = logging.getLogger(__name__)


class ProcessorsTab(QWidget):
    processing_started = pyqtSignal(str)
    processing_finished = pyqtSignal(str, bool)
    def __init__(
        self,
        project_config,
        task_history_service=None,
        task_queue_manager=None,
        parent=None,
    ):
        super().__init__(parent)
        self.project_config = project_config
        self.task_history_service = task_history_service
        self.task_queue_manager = task_queue_manager
        self._task_ids = {}
        self.processor_wrappers = {}
        self.file_queue = []
        self.notification_manager = NotificationManager(self)
        self.sound_enabled = True  # Will be set from user settings
        self.setup_ui()
        self.init_processors()
        self.connect_signals()
        self.processing_started.connect(self.on_processing_started)
        self.processing_finished.connect(self.on_processing_finished)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
        main_layout.setSpacing(PAGE_MARGIN)
        icon_manager = IconManager()

        header = SectionHeader("Processors")
        main_layout.addWidget(header)

        # Create tabs for different processor types with icons
        pdf_icon = icon_manager.get_icon_path('PDF document', by='Description') or icon_manager.get_icon_path('Main dashboard and analytics view', by='Function')
        text_icon = icon_manager.get_icon_path('Text Files', by='Description') or icon_manager.get_icon_path('File management and organization', by='Function')
        advanced_icon = icon_manager.get_icon_path('Analytics line chart icon with dark blue styling', by='Description') or icon_manager.get_icon_path('Data analytics and visualization', by='Function')
        batch_icon = icon_manager.get_icon_path('Data collection and processing', by='Function')
        self.processor_tabs = QTabWidget()
        self.processor_tabs.addTab(self.create_pdf_tab(), QIcon(pdf_icon) if pdf_icon else QIcon(), "PDF Processing")
        self.processor_tabs.addTab(self.create_text_tab(), QIcon(text_icon) if text_icon else QIcon(), "Text Processing")
        self.processor_tabs.addTab(self.create_advanced_tab(), QIcon(advanced_icon) if advanced_icon else QIcon(), "Advanced Processing")
        self.processor_tabs.addTab(self.create_batch_tab(), QIcon(batch_icon) if batch_icon else QIcon(), "Batch Operations")
        
        main_layout.addWidget(self.processor_tabs)
        
        # Add a status/summary area at the bottom
        status_group = QGroupBox("Processing Status")
        status_layout = QVBoxLayout(status_group)
        
        self.processing_status_label = QLabel("Ready to process files")
        status_layout.addWidget(self.processing_status_label)
        
        # Overall progress bar
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        status_layout.addWidget(self.overall_progress)
        
        # Button for stopping all processors
        stop_all_btn = QPushButton("Stop All Processors")
        stop_all_btn.setObjectName("danger")
        stop_all_btn.clicked.connect(self.stop_all_processors)
        status_layout.addWidget(stop_all_btn)
        
        main_layout.addWidget(status_group)
        # Add notification area at the bottom
        main_layout.addWidget(self.notification_manager)

    def create_pdf_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        icon_manager = IconManager()
        
        # Configuration group
        config_group = QGroupBox("PDF Processor Configuration")
        config_layout = QVBoxLayout(config_group)
        
        # OCR options
        self.ocr_enabled = QCheckBox("Enable OCR for scanned documents")
        self.ocr_enabled.setChecked(True)
        config_layout.addWidget(self.ocr_enabled)
        
        # Table extraction
        self.table_extraction = QCheckBox("Extract tables")
        self.table_extraction.setChecked(True)
        config_layout.addWidget(self.table_extraction)
        
        # Formula extraction
        self.formula_extraction = QCheckBox("Extract mathematical formulas")
        self.formula_extraction.setChecked(True)
        config_layout.addWidget(self.formula_extraction)
        
        # Thread count
        thread_layout = QHBoxLayout()
        thread_layout.addWidget(QLabel("Worker Threads:"))
        self.pdf_threads = QSpinBox()
        self.pdf_threads.setRange(1, 16)
        self.pdf_threads.setValue(4)
        thread_layout.addWidget(self.pdf_threads)
        config_layout.addLayout(thread_layout)
        
        layout.addWidget(config_group)
        
        # File selection
        files_group = QGroupBox("PDF Files")
        files_layout = QVBoxLayout(files_group)
        
        file_buttons_layout = QHBoxLayout()
        self.add_pdf_btn = QPushButton("Add PDF Files")
        self.add_pdf_btn.clicked.connect(self.add_pdf_files)
        self.clear_pdf_btn = QPushButton("Clear List")
        self.clear_pdf_btn.clicked.connect(self.clear_pdf_files)
        file_buttons_layout.addWidget(self.add_pdf_btn)
        file_buttons_layout.addWidget(self.clear_pdf_btn)
        
        files_layout.addLayout(file_buttons_layout)
        
        self.pdf_file_list = QListWidget()
        files_layout.addWidget(self.pdf_file_list)
        
        layout.addWidget(files_group)
        
        # Controls
        controls_group = QGroupBox("Controls")
        controls_group.setObjectName("card")
        controls_layout = QHBoxLayout(controls_group)
        
        self.pdf_start_btn = QPushButton("Start Processing")
        start_icon = icon_manager.get_icon_path('Start/play operation control', by='Function')
        if start_icon:
            self.pdf_start_btn.setIcon(QIcon(start_icon))
        self.pdf_stop_btn = QPushButton("Stop")
        self.pdf_stop_btn.setObjectName("danger")
        stop_icon = icon_manager.get_icon_path('Stop operation control', by='Function')
        if stop_icon:
            self.pdf_stop_btn.setIcon(QIcon(stop_icon))
        self.pdf_stop_btn.setEnabled(False)
        
        controls_layout.addWidget(self.pdf_start_btn)
        controls_layout.addWidget(self.pdf_stop_btn)
        
        layout.addWidget(controls_group)
        
        # Progress
        progress_group = QGroupBox("Progress")
        progress_group.setObjectName("card")
        progress_layout = QVBoxLayout(progress_group)
        
        self.pdf_status = QLabel("Ready")
        self.pdf_status.setObjectName("status-info")
        progress_layout.addWidget(self.pdf_status)
        
        self.pdf_progress_bar = QProgressBar()
        self.pdf_progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.pdf_progress_bar)
        
        layout.addWidget(progress_group)
        
        return tab

    def create_text_tab(self):
        # Similar to PDF tab but for text files
        tab = QWidget()
        layout = QVBoxLayout(tab)
        icon_manager = IconManager()
        
        # Configuration group
        config_group = QGroupBox("Text Processor Configuration")
        config_layout = QVBoxLayout(config_group)
        
        # Language detection
        self.language_detection = QCheckBox("Enable language detection")
        self.language_detection.setChecked(True)
        config_layout.addWidget(self.language_detection)
        
        # Quality threshold
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality Threshold:"))
        self.quality_threshold = QSpinBox()
        self.quality_threshold.setRange(0, 100)
        self.quality_threshold.setValue(80)
        quality_layout.addWidget(self.quality_threshold)
        config_layout.addLayout(quality_layout)
        
        # Thread count
        thread_layout = QHBoxLayout()
        thread_layout.addWidget(QLabel("Worker Threads:"))
        self.text_threads = QSpinBox()
        self.text_threads.setRange(1, 16)
        self.text_threads.setValue(4)
        thread_layout.addWidget(self.text_threads)
        config_layout.addLayout(thread_layout)
        
        layout.addWidget(config_group)
        
        # File selection
        files_group = QGroupBox("Text Files")
        files_layout = QVBoxLayout(files_group)
        
        file_buttons_layout = QHBoxLayout()
        self.add_text_btn = QPushButton("Add Text Files")
        self.add_text_btn.clicked.connect(self.add_text_files)
        self.clear_text_btn = QPushButton("Clear List")
        self.clear_text_btn.clicked.connect(self.clear_text_files)
        file_buttons_layout.addWidget(self.add_text_btn)
        file_buttons_layout.addWidget(self.clear_text_btn)
        
        files_layout.addLayout(file_buttons_layout)
        
        self.text_file_list = QListWidget()
        files_layout.addWidget(self.text_file_list)
        
        layout.addWidget(files_group)
        
        # Controls and progress similar to PDF tab
        controls_group = QGroupBox("Controls")
        controls_group.setObjectName("card")
        controls_layout = QHBoxLayout(controls_group)
        
        self.text_start_btn = QPushButton("Start Processing")
        start_icon = icon_manager.get_icon_path('Start/play operation control', by='Function')
        if start_icon:
            self.text_start_btn.setIcon(QIcon(start_icon))
        self.text_stop_btn = QPushButton("Stop")
        self.text_stop_btn.setObjectName("danger")
        stop_icon = icon_manager.get_icon_path('Stop operation control', by='Function')
        if stop_icon:
            self.text_stop_btn.setIcon(QIcon(stop_icon))
        self.text_stop_btn.setEnabled(False)
        
        controls_layout.addWidget(self.text_start_btn)
        controls_layout.addWidget(self.text_stop_btn)
        
        layout.addWidget(controls_group)
        
        progress_group = QGroupBox("Progress")
        progress_group.setObjectName("card")
        progress_layout = QVBoxLayout(progress_group)
        
        self.text_status = QLabel("Ready")
        self.text_status.setObjectName("status-info")
        progress_layout.addWidget(self.text_status)
        
        self.text_progress_bar = QProgressBar()
        self.text_progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.text_progress_bar)
        
        layout.addWidget(progress_group)
        
        return tab

    def create_advanced_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        icon_manager = IconManager()
        
        # Advanced processing options
        advanced_group = QGroupBox("Advanced Processing Options")
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Deduplication
        self.enable_deduplication = QCheckBox("Enable deduplication")
        self.enable_deduplication.setChecked(True)
        advanced_layout.addWidget(self.enable_deduplication)
        
        # Domain classification
        self.enable_domain_classification = QCheckBox("Enable domain classification")
        self.enable_domain_classification.setChecked(True)
        advanced_layout.addWidget(self.enable_domain_classification)
        
        # Financial symbol processing
        self.enable_financial_symbols = QCheckBox("Extract financial symbols")
        self.enable_financial_symbols.setChecked(True)
        advanced_layout.addWidget(self.enable_financial_symbols)
        
        # Language confidence
        self.enable_language_confidence = QCheckBox("Detect language confidence")
        self.enable_language_confidence.setChecked(True)
        advanced_layout.addWidget(self.enable_language_confidence)
        
        # Machine translation detection
        self.enable_mt_detection = QCheckBox("Detect machine translation")
        self.enable_mt_detection.setChecked(True)
        advanced_layout.addWidget(self.enable_mt_detection)
        
        layout.addWidget(advanced_group)
        
        # Batch operations group
        batch_group = QGroupBox("Apply to Corpus")
        batch_layout = QVBoxLayout(batch_group)
        
        self.apply_to_all_btn = QPushButton("Apply to Entire Corpus")
        self.apply_to_all_btn.clicked.connect(self.apply_advanced_processing)
        batch_layout.addWidget(self.apply_to_all_btn)
        
        self.apply_to_selected_btn = QPushButton("Apply to Selected Domain")
        self.apply_to_selected_btn.clicked.connect(self.apply_selected_domain)
        batch_layout.addWidget(self.apply_to_selected_btn)
        
        layout.addWidget(batch_group)
        
        # Progress for batch operations
        progress_group = QGroupBox("Batch Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.advanced_status = QLabel("Ready")
        self.advanced_status.setObjectName("status-info")
        progress_layout.addWidget(self.advanced_status)
        
        self.advanced_progress_bar = QProgressBar()
        self.advanced_progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.advanced_progress_bar)
        
        layout.addWidget(progress_group)
        
        return tab

    def create_batch_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        icon_manager = IconManager()
        
        # Batch processing options
        batch_config_group = QGroupBox("Batch Configuration")
        batch_config_layout = QVBoxLayout(batch_config_group)
        
        # Directory selection
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Input Directory:"))
        self.input_dir_path = QLabel("Not selected")
        dir_layout.addWidget(self.input_dir_path)
        self.select_input_dir_btn = QPushButton("Select...")
        self.select_input_dir_btn.clicked.connect(self.select_input_directory)
        dir_layout.addWidget(self.select_input_dir_btn)
        batch_config_layout.addLayout(dir_layout)
        
        # Recursive option
        self.recursive_processing = QCheckBox("Process subdirectories recursively")
        self.recursive_processing.setChecked(True)
        batch_config_layout.addWidget(self.recursive_processing)
        
        # File type selection
        file_type_layout = QHBoxLayout()
        file_type_layout.addWidget(QLabel("File Types:"))
        self.process_pdf = QCheckBox("PDF")
        self.process_pdf.setChecked(True)
        self.process_text = QCheckBox("Text")
        self.process_text.setChecked(True)
        self.process_docx = QCheckBox("DOCX")
        self.process_docx.setChecked(True)
        self.process_html = QCheckBox("HTML")
        self.process_html.setChecked(True)
        file_type_layout.addWidget(self.process_pdf)
        file_type_layout.addWidget(self.process_text)
        file_type_layout.addWidget(self.process_docx)
        file_type_layout.addWidget(self.process_html)
        batch_config_layout.addLayout(file_type_layout)
        
        # Thread count
        thread_layout = QHBoxLayout()
        thread_layout.addWidget(QLabel("Batch Threads:"))
        self.batch_threads = QSpinBox()
        self.batch_threads.setRange(1, 16)
        self.batch_threads.setValue(4)
        thread_layout.addWidget(self.batch_threads)
        batch_config_layout.addLayout(thread_layout)
        
        layout.addWidget(batch_config_group)
        
        # Controls
        controls_group = QGroupBox("Batch Controls")
        controls_group.setObjectName("card")
        controls_layout = QHBoxLayout(controls_group)
        
        self.batch_start_btn = QPushButton("Start Batch Processing")
        start_icon = icon_manager.get_icon_path('Start/play operation control', by='Function')
        if start_icon:
            self.batch_start_btn.setIcon(QIcon(start_icon))
        self.batch_stop_btn = QPushButton("Stop")
        self.batch_stop_btn.setObjectName("danger")
        stop_icon = icon_manager.get_icon_path('Stop operation control', by='Function')
        if stop_icon:
            self.batch_stop_btn.setIcon(QIcon(stop_icon))
        self.batch_stop_btn.setEnabled(False)
        
        controls_layout.addWidget(self.batch_start_btn)
        controls_layout.addWidget(self.batch_stop_btn)
        
        layout.addWidget(controls_group)
        
        # Progress
        progress_group = QGroupBox("Batch Progress")
        progress_group.setObjectName("card")
        progress_layout = QVBoxLayout(progress_group)
        
        self.batch_status = QLabel("Ready")
        self.batch_status.setObjectName("status-info")
        progress_layout.addWidget(self.batch_status)
        
        self.batch_progress_bar = QProgressBar()
        self.batch_progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.batch_progress_bar)
        
        # Stats
        self.batch_stats = QLabel("No files processed yet")
        progress_layout.addWidget(self.batch_stats)
        
        layout.addWidget(progress_group)
        
        return tab

    def init_processors(self):
        """Initialize all processor wrappers with correct parameter types"""
        try:
            logger.debug("Starting processor wrapper initialization...")
            logger.debug("project_config type: %s", type(self.project_config))
            
            # Get both config object and config path
            config_object = self.project_config
            config_path = getattr(
                self.project_config, "config_path", str(self.project_config)
            )
            logger.debug("Using config_path: %s", config_path)
            
            # Wrappers that expect config_path (string)

            path_wrappers = [
            ]

            # Wrappers that expect config object
            object_wrappers = [
                ('pdf', PDFExtractorWrapper),
                ('text', TextExtractorWrapper),
                ('domain', DomainClassifierWrapper),
                ('formula', FormulaExtractorWrapper),
                ('chart', ChartImageExtractorWrapper),
                ('quality', QualityControlWrapper),
                ('language', LanguageConfidenceDetectorWrapper),
                ('mt_detector', MachineTranslationDetectorWrapper),
                ('financial', FinancialSymbolProcessorWrapper),
                ('deduplicator', DeduplicatorWrapper),
                ('balancer', CorpusBalancerWrapper)
            ]
            
            # Initialize path-based wrappers
            for name, wrapper_class in path_wrappers:
                try:
                    logger.debug(
                        "Initializing %s with config_path...",
                        wrapper_class.__name__,
                    )
                    self.processor_wrappers[name] = wrapper_class(config_path)
                    logger.debug("%s initialized successfully", wrapper_class.__name__)
                except Exception as e:
                    logger.error(
                        "Failed to initialize %s: %s", wrapper_class.__name__, e
                    )
                    self.processor_wrappers[name] = None
            
            # Initialize object-based wrappers
            for name, wrapper_class in object_wrappers:
                try:
                    if wrapper_class.__name__ in (
                        "QualityControlWrapper",
                        "MonitorProgressWrapper",
                    ):
                        self.processor_wrappers[name] = wrapper_class(
                            self.project_config,
                            parent=self,
                        )
                    else:
                        self.processor_wrappers[name] = wrapper_class(
                            self.project_config
                        )
                    logger.debug("%s initialized successfully", wrapper_class.__name__)
                except Exception as e:
                    logger.error(
                        "Failed to initialize %s: %s", wrapper_class.__name__, e
                    )
                    self.processor_wrappers[name] = None

            if self.task_queue_manager:
                for wrapper in self.processor_wrappers.values():
                    if wrapper:
                        wrapper.task_queue_manager = self.task_queue_manager

            logger.debug("Processor wrapper initialization completed")
            
        except Exception as e:
            logger.error("Failed to initialize processor wrappers: %s", e)
            # Fallback: create empty wrappers dict
            self.processor_wrappers = {
                name: None
                for name in [
                'pdf', 'text', 'balancer', 'quality', 'deduplicator',
                'domain', 'formula', 'chart', 'language', 'mt_detector', 'financial'
                ]
            }
            logger.debug("Using empty processor wrappers as fallback")

    def connect_signals(self):
        """Connect signals with defensive checks"""
        logger.debug("Setting up processor signal connections...")
        # Connect PDF processor signals if they exist
        pdf_wrapper = self.processor_wrappers.get('pdf')
        if pdf_wrapper:
            if hasattr(pdf_wrapper, 'progress_updated'):
                pdf_wrapper.progress_updated.connect(self.pdf_progress_bar.setValue)
            if hasattr(pdf_wrapper, 'status_updated'):
                pdf_wrapper.status_updated.connect(self.pdf_status.setText)
            if hasattr(pdf_wrapper, 'batch_completed'):
                pdf_wrapper.batch_completed.connect(self.on_pdf_batch_completed)
            else:
                logger.debug("PDFExtractorWrapper has no 'batch_completed' signal")
        # Connect Text processor signals if they exist
        text_wrapper = self.processor_wrappers.get('text')
        if text_wrapper:
            if hasattr(text_wrapper, 'progress_updated'):
                text_wrapper.progress_updated.connect(self.text_progress_bar.setValue)
            if hasattr(text_wrapper, 'status_updated'):
                text_wrapper.status_updated.connect(self.text_status.setText)
            if hasattr(text_wrapper, 'batch_completed'):
                text_wrapper.batch_completed.connect(self.on_text_batch_completed)
            else:
                logger.debug("TextExtractorWrapper has no 'batch_completed' signal")
        # Connect button signals
        if hasattr(self, 'pdf_start_btn'):
            self.pdf_start_btn.clicked.connect(self.start_pdf_processing)
        if hasattr(self, 'pdf_stop_btn'):
            self.pdf_stop_btn.clicked.connect(self.stop_pdf_processing)
        if hasattr(self, 'text_start_btn'):
            self.text_start_btn.clicked.connect(self.start_text_processing)
        if hasattr(self, 'text_stop_btn'):
            self.text_stop_btn.clicked.connect(self.stop_text_processing)
        logger.debug("Processor signal connections completed")

    def add_pdf_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files", "", "PDF Files (*.pdf)"
        )
        if files:
            for file in files:
                self.pdf_file_list.addItem(file)

    def clear_pdf_files(self):
        self.pdf_file_list.clear()

    def add_text_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Text Files", "", 
            "Text Files (*.txt *.html *.htm *.docx *.doc *.md *.csv *.json *.xml)"
        )
        if files:
            for file in files:
                self.text_file_list.addItem(file)

    def clear_text_files(self):
        self.text_file_list.clear()

    def select_input_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Input Directory", ""
        )
        if directory:
            self.input_dir_path.setText(str(directory))

    def start_pdf_processing(self):
        """Start PDF processing with safety checks"""
        if not hasattr(self, 'pdf_file_list'):
            logger.debug("PDF UI not fully initialized")
            self.processing_status_label.setText("PDF UI not fully initialized")
            return
        pdf_wrapper = self.processor_wrappers.get('pdf')
        if not pdf_wrapper:
            logger.debug("PDF wrapper not available")
            self.processing_status_label.setText("PDF wrapper not available")
            return
        logger.debug("PDF processing start requested")
        # Get files from list
        files_to_process = []
        for i in range(self.pdf_file_list.count()):
            files_to_process.append(self.pdf_file_list.item(i).text())
        if not files_to_process:
            self.pdf_status.setText("Error: No files to process")
            return
        # Configure processor
        pdf_wrapper.set_ocr_enabled(self.ocr_enabled.isChecked())
        pdf_wrapper.set_table_extraction(self.table_extraction.isChecked())
        pdf_wrapper.set_formula_extraction(self.formula_extraction.isChecked())
        pdf_wrapper.set_worker_threads(self.pdf_threads.value())
        # Update UI
        self.pdf_start_btn.setEnabled(False)
        self.pdf_stop_btn.setEnabled(True)
        if self.task_history_service:
            tid = f"processor_pdf_{int(time.time()*1000)}"
            self._task_ids['pdf'] = tid
            self.task_history_service.start_task(tid, 'PDF Processing', {'type': 'processing'})
        self.processing_started.emit('pdf')
        # Start processing
        pdf_wrapper.start_batch_processing(files_to_process)

    def stop_pdf_processing(self):
        self.processor_wrappers['pdf'].stop()
        if self.task_history_service and 'pdf' in self._task_ids:
            self.task_history_service.fail_task(self._task_ids.pop('pdf'), 'stopped')
        self.pdf_start_btn.setEnabled(True)
        self.pdf_stop_btn.setEnabled(False)
        self.processing_finished.emit('pdf', False)

    def start_text_processing(self):
        """Start Text processing with safety checks"""
        if not hasattr(self, 'text_file_list'):
            logger.debug("Text UI not fully initialized")
            self.processing_status_label.setText("Text UI not fully initialized")
            return
        text_wrapper = self.processor_wrappers.get('text')
        if not text_wrapper:
            logger.debug("Text wrapper not available")
            self.processing_status_label.setText("Text wrapper not available")
            return
        logger.debug("Text processing start requested")
        # Get files from list
        files_to_process = []
        for i in range(self.text_file_list.count()):
            files_to_process.append(self.text_file_list.item(i).text())
        if not files_to_process:
            self.text_status.setText("Error: No files to process")
            return
        # Configure processor
        text_wrapper.set_language_detection(self.language_detection.isChecked())
        text_wrapper.set_quality_threshold(self.quality_threshold.value())
        text_wrapper.set_worker_threads(self.text_threads.value())
        # Update UI
        self.text_start_btn.setEnabled(False)
        self.text_stop_btn.setEnabled(True)
        if self.task_history_service:
            tid = f"processor_text_{int(time.time()*1000)}"
            self._task_ids['text'] = tid
            self.task_history_service.start_task(tid, 'Text Processing', {'type': 'processing'})
        self.processing_started.emit('text')
        # Start processing
        text_wrapper.start_batch_processing(files_to_process)

    def stop_text_processing(self):
        self.processor_wrappers['text'].stop()
        if self.task_history_service and 'text' in self._task_ids:
            self.task_history_service.fail_task(self._task_ids.pop('text'), 'stopped')
        self.text_start_btn.setEnabled(True)
        self.text_stop_btn.setEnabled(False)
        self.processing_finished.emit('text', False)
    
    def apply_advanced_processing(self):
        # Enable/disable processors based on UI selections
        
        wrappers_to_run = []
        mapping = [
            ("deduplicator", self.enable_deduplication),
            ("domain", self.enable_domain_classification),
            ("financial", self.enable_financial_symbols),
            ("language", self.enable_language_confidence),
            ("mt_detector", self.enable_mt_detection),
        ]

        # Enable/disable wrappers if supported and collect the ones to run
        for name, checkbox in mapping:
            wrapper = self.processor_wrappers.get(name)
            if not wrapper:
                continue
            if hasattr(wrapper, "set_enabled"):
                wrapper.set_enabled(checkbox.isChecked())
            if checkbox.isChecked():
                wrappers_to_run.append(wrapper)

        if not wrappers_to_run:
            self.advanced_status.setText("No advanced processors enabled")
            self.advanced_progress_bar.setValue(0)
            return

        self._advanced_wrappers = wrappers_to_run
        self._current_advanced_index = 0

        self.advanced_progress_bar.setValue(0)
        self.advanced_status.setText("Starting advanced processing...")
        self._start_next_advanced_processor()

    @pyqtSlot()
    def apply_selected_domain(self):
        """Apply advanced processing to a user-selected domain."""
        from PySide6.QtWidgets import QInputDialog
        from shared_tools.utils.domain_utils import get_valid_domains

        domains = get_valid_domains()
        if not domains:
            self.advanced_status.setText("No domains available")
            return

        domain, ok = QInputDialog.getItem(
            self,
            "Select Domain",
            "Domain:",
            domains,
            0,
            False,
        )

        if not ok or not domain:
            return

        wrappers_to_run = []
        mapping = [
            ("deduplicator", self.enable_deduplication),
            ("domain", self.enable_domain_classification),
            ("financial", self.enable_financial_symbols),
            ("language", self.enable_language_confidence),
            ("mt_detector", self.enable_mt_detection),
        ]

        for name, checkbox in mapping:
            wrapper = self.processor_wrappers.get(name)
            if not wrapper:
                continue
            if hasattr(wrapper, "set_enabled"):
                wrapper.set_enabled(checkbox.isChecked())
            if checkbox.isChecked():
                wrappers_to_run.append(wrapper)

        if not wrappers_to_run:
            self.advanced_status.setText("No advanced processors enabled")
            self.advanced_progress_bar.setValue(0)
            return

        self._advanced_wrappers = wrappers_to_run
        self._current_advanced_index = 0
        self._advanced_domain = domain

        if self.task_queue_manager:
            tid = f"adv_domain_{domain}_{int(time.time()*1000)}"
            self._task_ids["selected_domain"] = tid
            self.task_queue_manager.add_task(
                tid,
                {"name": "AdvancedDomain", "domain": domain},
            )

        self.advanced_progress_bar.setValue(0)
        self.advanced_status.setText(f"Starting processing for domain '{domain}'...")
        self._start_next_advanced_processor(domain=domain)

    def start_batch_processing(self):
        input_dir = self.input_dir_path.text()
        if input_dir == "Not selected" or not os.path.isdir(input_dir):
            self.batch_status.setText("Error: Invalid input directory")
            return
        
        # Configure batch processing
        recursive = self.recursive_processing.isChecked()
        thread_count = self.batch_threads.value()
        
        # Determine file types to process
        file_types = []
        if self.process_pdf.isChecked():
            file_types.append(".pdf")
        if self.process_text.isChecked():
            file_types.append(".txt")
        if self.process_docx.isChecked():
            file_types.append(".docx")
        if self.process_html.isChecked():
            file_types.extend([".html", ".htm"])
        
        if not file_types:
            self.batch_status.setText("Error: No file types selected")
            return
        
        # Collect files to process
        files_to_process = []
        for root, dirs, files in os.walk(input_dir):
            if not recursive and root != input_dir:
                continue
                
            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in file_types:
                    files_to_process.append(os.path.join(root, file))
        
        if not files_to_process:
            self.batch_status.setText("Error: No matching files found")
            return
        
        # Update UI
        self.batch_start_btn.setEnabled(False)
        self.batch_stop_btn.setEnabled(True)
        self.batch_status.setText(f"Processing {len(files_to_process)} files...")
        
        # Start batch processing
        # In a real implementation, you'd determine the appropriate processor for each file
        # For now, just simulate a batch process
        
        # Categorize files by type
        pdf_files = [f for f in files_to_process if f.lower().endswith('.pdf')]
        text_files = [f for f in files_to_process if not f.lower().endswith('.pdf')]
        
        # Process PDFs with PDF processor
        if pdf_files:
            pdf_wrapper = self.processor_wrappers['pdf']
            pdf_wrapper.set_worker_threads(thread_count)
            pdf_wrapper.start_batch_processing(pdf_files)
        
        # Process text files with text processor
        if text_files:
            text_wrapper = self.processor_wrappers['text']
            text_wrapper.set_worker_threads(thread_count)
            text_wrapper.start_batch_processing(text_files)
            
        # Real implementation would coordinate these processes better

    def stop_batch_processing(self):
        # Stop all active processors
        for wrapper in self.processor_wrappers.values():
            wrapper.stop()
        
        # Update UI
        self.batch_start_btn.setEnabled(True)
        self.batch_stop_btn.setEnabled(False)
        self.batch_status.setText("Batch processing stopped")

    @pyqtSlot(dict)
    def on_pdf_batch_completed(self, results):
        self.pdf_start_btn.setEnabled(True)
        self.pdf_stop_btn.setEnabled(False)
        if self.task_history_service and 'pdf' in self._task_ids:
            self.task_history_service.complete_task(self._task_ids.pop('pdf'))
        
        # Update status
        success_count = results.get('success_count', 0)
        fail_count = results.get('fail_count', 0)
        
        message = f"PDF processing completed: {success_count} successes, {fail_count} failures"
        self.pdf_status.setText(message)
        self.processing_status_label.setText(message)
        self.processing_finished.emit('pdf', True)

    @pyqtSlot(dict)
    def on_text_batch_completed(self, results):
        self.text_start_btn.setEnabled(True)
        self.text_stop_btn.setEnabled(False)
        if self.task_history_service and 'text' in self._task_ids:
            self.task_history_service.complete_task(self._task_ids.pop('text'))
        
        # Update status
        success_count = results.get('success_count', 0)
        fail_count = results.get('fail_count', 0)
        
        message = f"Text processing completed: {success_count} successes, {fail_count} failures"
        self.text_status.setText(message)
        self.processing_status_label.setText(message)
        self.processing_finished.emit('text', True)

    def stop_all_processors(self):
        for wrapper in self.processor_wrappers.values():
            wrapper.stop()

        self._advanced_wrappers = []
        self._current_advanced_index = 0
        self.advanced_progress_bar.setValue(0)
        self.advanced_status.setText("Advanced processing stopped")
            
        # Reset UI elements
        self.pdf_start_btn.setEnabled(True)
        self.pdf_stop_btn.setEnabled(False)
        self.text_start_btn.setEnabled(True)
        self.text_stop_btn.setEnabled(False)
        self.batch_start_btn.setEnabled(True)
        self.batch_stop_btn.setEnabled(False)
        
        self.processing_status_label.setText("All processors stopped")

    def on_processing_started(self, name: str) -> None:
        """Update UI when a processing task begins."""
        self.processing_status_label.setText(f"Processing: {name}")
        self.overall_progress.setRange(0, 0)

    def on_processing_finished(self, name: str, success: bool) -> None:
        """Reset progress when processing ends."""
        status = "completed" if success else "stopped"
        self.processing_status_label.setText(f"Processing {status}: {name}")
        self.overall_progress.setRange(0, 100)

    def _start_next_advanced_processor(self, domain=None):
        if domain is not None:
            self._advanced_domain = domain
        domain = getattr(self, "_advanced_domain", None)

        if self._current_advanced_index >= len(getattr(self, "_advanced_wrappers", [])):
            self.advanced_progress_bar.setValue(100)
            if domain:
                self.advanced_status.setText(f"Processing for domain '{domain}' completed")
            else:
                self.advanced_status.setText("Advanced processing completed")
            if self.task_queue_manager and "selected_domain" in self._task_ids:
                self.task_queue_manager.update_task(self._task_ids.pop("selected_domain"), "completed", 100)
            self._advanced_wrappers = []
            return

        wrapper = self._advanced_wrappers[self._current_advanced_index]

        if hasattr(wrapper, "progress_updated"):
            wrapper.progress_updated.connect(self._update_advanced_progress)
        if hasattr(wrapper, "status_updated"):
            wrapper.status_updated.connect(self.advanced_status.setText)
        if hasattr(wrapper, "batch_completed"):
            wrapper.batch_completed.connect(self._on_advanced_wrapper_completed)
        elif hasattr(wrapper, "completed"):
            wrapper.completed.connect(self._on_advanced_wrapper_completed)

        if domain:
            wrapper.start(domain=domain)
        else:
            wrapper.start()

    def _update_advanced_progress(self, value):
        total = len(self._advanced_wrappers)
        base = (self._current_advanced_index / total) * 100
        step = value / total
        progress = int(base + step)
        self.advanced_progress_bar.setValue(progress)
        if self.task_queue_manager and "selected_domain" in self._task_ids:
            self.task_queue_manager.update_task(
                self._task_ids["selected_domain"], "running", progress
            )

    def _on_advanced_wrapper_completed(self, _results):
        wrapper = self._advanced_wrappers[self._current_advanced_index]
        try:
            if hasattr(wrapper, "progress_updated"):
                wrapper.progress_updated.disconnect(self._update_advanced_progress)
            if hasattr(wrapper, "status_updated"):
                wrapper.status_updated.disconnect(self.advanced_status.setText)
            if hasattr(wrapper, "batch_completed"):
                wrapper.batch_completed.disconnect(self._on_advanced_wrapper_completed)
            elif hasattr(wrapper, "completed"):
                wrapper.completed.disconnect(self._on_advanced_wrapper_completed)
        except Exception as exc:
            logger.warning("Failed to disconnect advanced wrapper signals: %s", exc)

        self._current_advanced_index += 1
        self._start_next_advanced_processor()

    def run_batch_operation(self, operation_type):
        selected_files = self.get_selected_files()
        if not selected_files:
            QMessageBox.warning(self, f"No files selected", f"Please select files to {operation_type}.")
            return
        try:
            if operation_type == "copy":
                target_dir = QFileDialog.getExistingDirectory(self, "Select Target Directory")
                if not target_dir:
                    return
                for file_path in selected_files:
                    try:
                        shutil.copy2(file_path, target_dir)
                    except Exception as e:
                        self.notification_manager.add_notification(f"copy_{file_path}", "Copy Error", str(e), "error", auto_hide=True)
                        if self.sound_enabled:
                            Notifier.notify("Copy Error", str(e), level="error")
                self.notification_manager.add_notification("batch_copy", "Batch Copy", f"Copied {len(selected_files)} files.", "success", auto_hide=True)
                if self.sound_enabled:
                    Notifier.notify("Batch Copy", f"Copied {len(selected_files)} files.", level="success")
            elif operation_type == "move":
                target_dir = QFileDialog.getExistingDirectory(self, "Select Target Directory")
                if not target_dir:
                    return
                for file_path in selected_files:
                    try:
                        shutil.move(file_path, target_dir)
                    except Exception as e:
                        self.notification_manager.add_notification(f"move_{file_path}", "Move Error", str(e), "error", auto_hide=True)
                self.notification_manager.add_notification("batch_move", "Batch Move", f"Moved {len(selected_files)} files.", "success", auto_hide=True)
            elif operation_type == "delete":
                confirm = QMessageBox.question(self, "Confirm Delete", f"Delete {len(selected_files)} files?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if confirm == QMessageBox.StandardButton.Yes:
                    for file_path in selected_files:
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            self.notification_manager.add_notification(f"delete_{file_path}", "Delete Error", str(e), "error", auto_hide=True)
                    self.notification_manager.add_notification("batch_delete", "Batch Delete", f"Deleted {len(selected_files)} files.", "success", auto_hide=True)
            # Add more operations as needed
            self.refresh_file_view()
        except Exception as e:
            QMessageBox.critical(self, f"Batch {operation_type.capitalize()} Error", str(e))
            if self.sound_enabled:
                Notifier.notify(f"Batch {operation_type.capitalize()} Error", str(e), level="error")

    def get_selected_files(self):
        """Return the list of selected files from the active tab's file list."""
        current_tab = self.processor_tabs.currentIndex()
        if current_tab == 0:  # PDF tab
            return [self.pdf_file_list.item(i).text() for i in range(self.pdf_file_list.count()) if self.pdf_file_list.item(i).isSelected()]
        elif current_tab == 1:  # Text tab
            return [self.text_file_list.item(i).text() for i in range(self.text_file_list.count()) if self.text_file_list.item(i).isSelected()]
        elif current_tab == 3:  # Batch tab
            # In batch tab, select all files found in the last batch operation (if any)
            # For now, return empty list (could be extended to support selection)
            return []
        else:
            return []

    def refresh_file_view(self):
        """Refresh the file lists in the UI after batch operations."""
        # For PDF and Text tabs, just clear and reload the lists
        self.pdf_file_list.clear()
        self.text_file_list.clear()
        # Optionally, could reload from disk or keep a cache of last directory
        # For now, just clear the lists
