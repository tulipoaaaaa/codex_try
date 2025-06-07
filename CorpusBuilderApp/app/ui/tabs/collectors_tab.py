from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QProgressBar,
    QPushButton,
    QComboBox,
    QSpinBox,
    QLineEdit,
    QGroupBox,
    QScrollArea,
)
from PySide6.QtCore import Qt, Slot as pyqtSlot, Signal as pyqtSignal
from PySide6.QtGui import QFont

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
from app.ui.theme.theme_constants import (
    DEFAULT_FONT_SIZE,
    CARD_MARGIN,
    BUTTON_COLOR_PRIMARY,
    BUTTON_COLOR_DANGER,
    BUTTON_COLOR_GRAY,
)


class CollectorsTab(QWidget):
    """Manage all data collectors in a scrollable card view."""

    collection_started = pyqtSignal(str)
    collection_finished = pyqtSignal(str, bool)
    collector_error = pyqtSignal(str, str)

    def __init__(self, project_config, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project_config = project_config

        # Initialize collector wrappers
        self.collector_wrappers = {
            "isda": ISDAWrapper(),
            "github": GitHubWrapper(),
            "anna": AnnasArchiveWrapper(),
            "arxiv": ArxivWrapper(),
            "fred": FREDWrapper(),
            "bitmex": BitMEXWrapper(),
            "quantopian": QuantopianWrapper(),
            "scidb": SciDBWrapper(),
            "web": WebWrapper(),
        }

        self.cards: dict[str, CollectorCard] = {}

        self._init_ui()

        for name, wrapper in self.collector_wrappers.items():
            params = self.project_config.get(f"collectors.{name}", {})
            if isinstance(params, dict):
                for key, value in params.items():
                    method = f"set_{key}"
                    if hasattr(wrapper, method):
                        try:
                            getattr(wrapper, method)(value)
                        except Exception:
                            pass

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

        for name, wrapper in self.collector_wrappers.items():
            card_wrap = CardWrapper()
            card_layout = card_wrap.body_layout
            card = CollectorCard(name.title())
            running = bool(self.project_config.get(f"collectors.{name}.running", False))
            card.update_status("running" if running else "stopped")
            card.start_requested.connect(lambda n=name: self.start_collection(n))
            card.stop_requested.connect(lambda n=name: self.stop_collection(n))
            card.configure_requested.connect(lambda n=name: self.configure_collector(n))
            card.logs_requested.connect(lambda n=name: self.show_logs(n))
            self.cards[name] = card
            card_layout.addWidget(card)
            layout.addWidget(card_wrap)

        status_card = CardWrapper()
        status_layout = status_card.body_layout
        self.collection_status_label = QLabel("Ready")
        status_layout.addWidget(self.collection_status_label)
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        status_layout.addWidget(self.overall_progress)
        stop_all_btn = QPushButton("Stop All Collectors")
        stop_all_btn.clicked.connect(self.stop_all_collectors)
        status_layout.addWidget(stop_all_btn)
        layout.addWidget(status_card)

    def connect_signals(self) -> None:
        for name, wrapper in self.collector_wrappers.items():
            if hasattr(wrapper, "progress_updated"):
                wrapper.progress_updated.connect(lambda v, n=name: self._handle_progress(n, v))
            if hasattr(wrapper, "status_updated"):
                wrapper.status_updated.connect(lambda m, n=name: self._handle_status(n, m))
            if hasattr(wrapper, "completed"):
                wrapper.completed.connect(lambda r, n=name: self.on_collection_completed(n, r))
            if hasattr(wrapper, "error_occurred"):
                wrapper.error_occurred.connect(lambda m, n=name: self.on_wrapper_error(n, m))

    # --------------------------------------------------------------- Slots ----
    def _handle_progress(self, name: str, value: int) -> None:
        if name in self.cards:
            self.cards[name].update_progress(value)
        self.update_progress(value)

    def _handle_status(self, name: str, message: str) -> None:
        if name in self.cards:
            self.cards[name].update_status(message)
        self.update_status(message)

    def start_collection(self, name: str) -> None:
        wrapper = self.collector_wrappers.get(name)
        if not wrapper:
            return
        wrapper.start()
        self.cards[name].update_status("running")
        self.project_config.set(f"collectors.{name}.running", True)
        self.project_config.save()
        self.collection_started.emit(name)

    def stop_collection(self, name: str) -> None:
        wrapper = self.collector_wrappers.get(name)
        if not wrapper:
            return
        wrapper.stop()
        self.cards[name].update_status("stopped")
        self.project_config.set(f"collectors.{name}.running", False)
        self.project_config.save()

    def configure_collector(self, name: str) -> None:
        Notifier.notify("Configure", f"Configuration for {name} not implemented")

    def show_logs(self, name: str) -> None:
        Notifier.notify("Logs", f"Logs for {name} not implemented")

    def stop_all_collectors(self) -> None:
        for name, wrapper in self.collector_wrappers.items():
            wrapper.stop()
            if name in self.cards:
                self.cards[name].update_status("stopped")
            self.project_config.set(f"collectors.{name}.running", False)
            self.collection_finished.emit(name, False)
        self.collection_status_label.setText("All collectors stopped")
        self.project_config.save()

    # ------------------------------------------------------------- Handlers ----
    def update_progress(self, value: int) -> None:
        self.overall_progress.setValue(value)

    def update_status(self, message: str) -> None:
        self.collection_status_label.setText(message)

    def on_collection_completed(self, collector_name: str, results: dict) -> None:
        self.cards[collector_name].update_status("stopped")
        self.project_config.set(f"collectors.{collector_name}.running", False)
        self.project_config.save()
        self.collection_finished.emit(collector_name, True)
        self.collection_status_label.setText(f"{collector_name} collection completed")

    def on_wrapper_error(self, collector_name: str, message: str) -> None:
        self.cards[collector_name].update_status("error")
        self.project_config.set(f"collectors.{collector_name}.running", False)
        self.project_config.save()
        self.collector_error.emit(collector_name, message)
        self.collection_status_label.setText(f"{collector_name} error: {message}")

