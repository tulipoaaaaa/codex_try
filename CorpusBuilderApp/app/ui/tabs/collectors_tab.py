from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QGroupBox,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal as pyqtSignal
from PySide6.QtGui import QFont
import time
import logging

from shared_tools.ui_wrappers.collectors.isda_wrapper import ISDAWrapper
from shared_tools.ui_wrappers.collectors.github_wrapper import GitHubWrapper
from shared_tools.ui_wrappers.collectors.annas_archive_wrapper import AnnasArchiveWrapper
from shared_tools.ui_wrappers.collectors.arxiv_wrapper import ArxivWrapper
from shared_tools.ui_wrappers.collectors.fred_wrapper import FREDWrapper
from shared_tools.ui_wrappers.collectors.bitmex_wrapper import BitMEXWrapper
from shared_tools.ui_wrappers.collectors.quantopian_wrapper import QuantopianWrapper
from shared_tools.ui_wrappers.collectors.scidb_wrapper import SciDBWrapper
from shared_tools.ui_wrappers.collectors.web_wrapper import WebWrapper

from app.ui.widgets.collector_card import CollectorCard
from app.ui.widgets.card_wrapper import CardWrapper
from app.ui.widgets.section_header import SectionHeader
from app.helpers.notifier import Notifier
from app.ui.dialogs.collector_config_dialog import CollectorConfigDialog
from app.ui.theme.theme_constants import (
    DEFAULT_FONT_SIZE,
    CARD_MARGIN,
    BUTTON_COLOR_DANGER,
    PAGE_MARGIN,
)


class CollectorsTab(QWidget):
    """Manage all data collectors in a scrollable card view."""

    collection_started = pyqtSignal(str)
    collection_finished = pyqtSignal(str, bool)
    collector_error = pyqtSignal(str, str)

    def __init__(
        self,
        project_config,
        task_history_service=None,
        task_queue_manager=None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.project_config = project_config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.task_history_service = task_history_service
        self.task_queue_manager = task_queue_manager
        self._task_ids: dict[str, str] = {}
        self.cards: dict[str, CollectorCard] = {}

        # Initialize collector wrappers
        self.collector_wrappers = {
            "isda": ISDAWrapper(self.project_config),
            "github": GitHubWrapper(self.project_config),
            "annas_archive": AnnasArchiveWrapper(self.project_config),
            "arxiv": ArxivWrapper(self.project_config),
            "fred": FREDWrapper(self.project_config),
            "bitmex": BitMEXWrapper(self.project_config),
            "quantopian": QuantopianWrapper(self.project_config),
            "scidb": SciDBWrapper(self.project_config),
            "web": WebWrapper(self.project_config),
        }

        if self.task_queue_manager:
            for wrapper in self.collector_wrappers.values():
                wrapper.task_queue_manager = self.task_queue_manager

        # Configure wrappers from project config
        for name, wrapper in self.collector_wrappers.items():
            params = self.project_config.get(f"collectors.{name}", {})
            if isinstance(params, dict):
                for key, value in params.items():
                    method = f"set_{key}"
                    if hasattr(wrapper, method):
                        try:
                            getattr(wrapper, method)(value)
                        except Exception as exc:
                            self.logger.info("Failed to apply %s on %s: %s", method, name, exc)

        # Setup UI
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
        layout.setSpacing(PAGE_MARGIN)

        header = SectionHeader("Collectors")
        layout.addWidget(header)

        # Status section
        status_group = QGroupBox("Collection Status")
        status_layout = QVBoxLayout(status_group)
        
        self.collection_status_label = QLabel("Ready")
        self.collection_status_label.setFont(QFont("Arial", DEFAULT_FONT_SIZE))
        status_layout.addWidget(self.collection_status_label)
        
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        status_layout.addWidget(self.overall_progress)
        
        layout.addWidget(status_group)
        
        # Collectors section
        collectors_group = QGroupBox("Collectors")
        collectors_layout = QVBoxLayout(collectors_group)
        
        # Create scroll area for collector cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Container widget for cards
        cards_container = QWidget()
        cards_layout = QVBoxLayout(cards_container)
        cards_layout.setSpacing(CARD_MARGIN)
        
        # Create cards for each collector
        for name, wrapper in self.collector_wrappers.items():
            description = getattr(wrapper, 'description', f'Collect data from {name.replace("_", " ").title()}')
            card = CollectorCard(
                name=name,
                description=description
            )
            card.start_requested.connect(lambda n=name: self.start_collection(n))
            card.stop_requested.connect(lambda n=name: self.stop_collection(n))
            card.configure_requested.connect(lambda n=name: self.configure_collector(n))
            card.logs_requested.connect(lambda n=name: self.show_logs(n))
            self.cards[name] = card
            cards_layout.addWidget(card)
        
        scroll_area.setWidget(cards_container)
        collectors_layout.addWidget(scroll_area)
        layout.addWidget(collectors_group)
        
        # Control buttons
        control_layout = QHBoxLayout()

        stop_all_btn = QPushButton("Stop All Collectors")
        stop_all_btn.setObjectName("danger")
        stop_all_btn.clicked.connect(self.stop_all_collectors)
        control_layout.addWidget(stop_all_btn)
        
        layout.addLayout(control_layout)

        self.connect_signals()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setSpacing(32)
        layout.setContentsMargins(32, 32, 32, 32)

        header = SectionHeader("Collectors")
        layout.addWidget(header)

    def connect_signals(self) -> None:
        """Connect signals for collector cards."""
        for name, card in self.cards.items():
            card.start_requested.connect(lambda n=name: self.start_collection(n))
            card.stop_requested.connect(lambda n=name: self.stop_collection(n))
            card.configure_requested.connect(lambda n=name: self.configure_collector(n))
            card.logs_requested.connect(lambda n=name: self.show_logs(n))

    def _handle_progress(self, name: str, value: int) -> None:
        """Handle progress updates from collectors."""
        if name in self.cards:
            self.cards[name].update_progress(value)

    def _handle_status(self, name: str, message: str) -> None:
        """Handle status updates from collectors."""
        if name in self.cards:
            self.cards[name].update_status(message)

    def start_collection(self, name: str) -> None:
        """Start data collection for the specified collector."""
        if name in self.collector_wrappers:
            wrapper = self.collector_wrappers[name]
            wrapper.start_collection()
            self.collection_started.emit(name)

    def stop_collection(self, name: str) -> None:
        """Stop data collection for the specified collector."""
        if name in self.collector_wrappers:
            wrapper = self.collector_wrappers[name]
            wrapper.stop_collection()
            self.collection_finished.emit(name, False)

    def configure_collector(self, name: str) -> None:
        """Configure the specified collector."""
        if name in self.collector_wrappers:
            wrapper = self.collector_wrappers[name]
            self.show_config_dialog(wrapper)

    def show_config_dialog(self, wrapper) -> None:
        """Show configuration dialog for the collector."""
        dialog = CollectorConfigDialog(wrapper, self)
        if dialog.exec_():
            # Configuration was accepted
            pass

    def show_logs(self, name: str) -> None:
        """Show logs for the specified collector."""
        if name in self.collector_wrappers:
            wrapper = self.collector_wrappers[name]
            # Implement log viewing logic here

    def stop_all_collectors(self) -> None:
        """Stop all active collectors."""
        for name in self.collector_wrappers:
            self.stop_collection(name)

    def update_progress(self, value: int) -> None:
        """Update overall progress bar."""
        self.overall_progress.setValue(value)

    def update_status(self, message: str) -> None:
        """Update status label."""
        self.collection_status_label.setText(message)

    def on_collection_completed(self, collector_name: str, results: dict) -> None:
        """Handle collection completion."""
        if collector_name in self.cards:
            self.cards[collector_name].update_status("Collection completed")
            self.collection_finished.emit(collector_name, True)

    def on_wrapper_error(self, collector_name: str, message: str) -> None:
        """Handle errors from collector wrappers."""
        if collector_name in self.cards:
            self.cards[collector_name].update_status(f"Error: {message}")
            self.collector_error.emit(collector_name, message)

