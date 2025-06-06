from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QLabel,
    QPushButton,
    QProgressBar,
    QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

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
from app.helpers.notifier import Notifier


class CollectorsTab(QWidget):
    """Manage all data collectors in a scrollable card view."""

    collection_started = pyqtSignal(str)
    collection_finished = pyqtSignal(str, bool)
    collector_error = pyqtSignal(str, str)

    def __init__(self, project_config, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project_config = project_config
        self.collector_wrappers: dict[str, object] = {}
        self.cards: dict[str, CollectorCard] = {}
        self.init_collectors()
        self.setup_ui()
        self.connect_signals()

    # ------------------------------------------------------------------ UI ----
    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.cards_layout = QVBoxLayout(container)
        self.cards_layout.setSpacing(16)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        collectors_info = [
            (
                "isda",
                "ISDA Collector",
                "Collects derivatives documentation from ISDA sources.",
                ["Docs", "ISDA"],
            ),
            (
                "github",
                "GitHub Collector",
                "Scrapes financial trading repositories and documentation from GitHub organizations",
                ["Code", "Trading", "API"],
            ),
            (
                "anna",
                "Anna's Archive Collector",
                "Searches and downloads textbooks and research materials from Anna's Archive",
                ["Books", "Archive"],
            ),
            (
                "arxiv",
                "arXiv Collector",
                "Downloads quantitative finance papers from arXiv",
                ["Academic", "PDF"],
            ),
            (
                "fred",
                "FRED Collector",
                "Fetches economic data from Federal Reserve Economic Data",
                ["Economic", "API"],
            ),
            (
                "bitmex",
                "BitMEX Collector",
                "Retrieves crypto trading documents from BitMEX",
                ["Exchange", "Trading"],
            ),
            (
                "quantopian",
                "Quantopian Collector",
                "Downloads trading algorithms from Quantopian",
                ["Algorithms"],
            ),
            (
                "scidb",
                "SciDB Collector",
                "Collects research data from SciDB",
                ["Database"],
            ),
            (
                "web",
                "Web Collector",
                "General purpose web scraping",
                ["Web"],
            ),
        ]

        for key, title, desc, tags in collectors_info:
            wrapper = self.collector_wrappers.get(key)
            card = CollectorCard(title, desc, tags)
            self.cards[key] = card
            self.cards_layout.addWidget(card)

            card.start_requested.connect(lambda _, n=key: self.start_collection(n))
            card.stop_requested.connect(lambda _, n=key: self.stop_collection(n))
            card.configure_requested.connect(lambda _, n=key: self.configure_collector(n))
            card.logs_requested.connect(lambda _, n=key: self.show_logs(n))

        self.cards_layout.addStretch()

        # Status/summary section
        status_group = QGroupBox("Collection Status")
        status_layout = QVBoxLayout(status_group)

        self.collection_status_label = QLabel()
        self.collection_status_label.setObjectName("status-info")
        status_layout.addWidget(self.collection_status_label)

        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        status_layout.addWidget(self.overall_progress)

        stop_all = QPushButton("Stop All Collectors")
        stop_all.clicked.connect(self.stop_all_collectors)
        status_layout.addWidget(stop_all)

        layout.addWidget(status_group)

    # -------------------------------------------------------------- Wrappers ----
    def init_collectors(self) -> None:
        self.collector_wrappers["isda"] = ISDAWrapper(self.project_config)
        self.collector_wrappers["github"] = GitHubWrapper(self.project_config)
        self.collector_wrappers["anna"] = AnnasArchiveWrapper(self.project_config)
        self.collector_wrappers["arxiv"] = ArxivWrapper(self.project_config)
        self.collector_wrappers["fred"] = FREDWrapper(self.project_config)
        self.collector_wrappers["bitmex"] = BitMEXWrapper(self.project_config)
        self.collector_wrappers["quantopian"] = QuantopianWrapper(self.project_config)
        self.collector_wrappers["scidb"] = SciDBWrapper(self.project_config)
        self.collector_wrappers["web"] = WebWrapper(self.project_config)

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
            self.cards[name].set_progress(value)
        self.update_progress(value)

    def _handle_status(self, name: str, message: str) -> None:
        if name in self.cards:
            running = "running" in message.lower()
            self.cards[name].set_running(running)
        self.update_status(message)

    def start_collection(self, name: str) -> None:
        wrapper = self.collector_wrappers.get(name)
        if not wrapper:
            return
        wrapper.start()
        self.cards[name].set_running(True)
        self.project_config.set(f"collectors.{name}.running", True)
        self.project_config.save()
        self.collection_started.emit(name)

    def stop_collection(self, name: str) -> None:
        wrapper = self.collector_wrappers.get(name)
        if not wrapper:
            return
        wrapper.stop()
        self.cards[name].set_running(False)
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
                self.cards[name].set_running(False)
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
        self.cards[collector_name].set_running(False)
        self.project_config.set(f"collectors.{collector_name}.running", False)
        self.project_config.save()
        self.collection_finished.emit(collector_name, True)
        self.collection_status_label.setText(f"{collector_name} collection completed")

    def on_wrapper_error(self, collector_name: str, message: str) -> None:
        self.cards[collector_name].set_running(False)
        self.project_config.set(f"collectors.{collector_name}.running", False)
        self.project_config.save()
        self.collector_error.emit(collector_name, message)
        self.collection_status_label.setText(f"{collector_name} error: {message}")

