"""Simple dashboard tab showing live metrics and corpus stats."""


from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
)
from PySide6.QtCore import Qt, Signal
from app.ui.widgets.card_wrapper import CardWrapper
from app.ui.widgets.section_header import SectionHeader
from app.ui.widgets.status_dot import StatusDot
class DashboardTab(QWidget):
    """Dashboard displaying high level metrics for the corpus."""

    view_all_activity_requested = Signal()

    def __init__(self, project_config, parent=None):
        super().__init__(parent)
        self.config = project_config

        # Metric attributes
        self.active_collectors = 0
        self.active_processors = 0
        self.error_count = 0
        self.total_documents = 0
        self.domain_distribution = {"Crypto": 40, "Finance": 30, "Other": 30}

        self._init_ui()

    # ------------------------------------------------------------------ UI ----
    def _init_ui(self) -> None:
        """Build the dashboard layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Top statistics row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.collectors_card = self._create_stat_card(
            "Active Collectors", str(self.active_collectors)
        )
        stats_layout.addWidget(self.collectors_card)

        self.processors_card = self._create_stat_card(
            "Active Processors", str(self.active_processors)
        )
        stats_layout.addWidget(self.processors_card)

        self.errors_card = self._create_stat_card("Errors", str(self.error_count))
        stats_layout.addWidget(self.errors_card)
        stats_layout.addStretch()

        main_layout.addLayout(stats_layout)

        # Corpus metrics section
        corpus_card = CardWrapper()
        corpus_layout = corpus_card.body_layout
        corpus_layout.setSpacing(16)

        self.total_docs_label = SectionHeader(f"Total Documents: {self.total_documents}")
        corpus_layout.addWidget(self.total_docs_label)

        distribution_header = SectionHeader("Domain Distribution")
        corpus_layout.addWidget(distribution_header)

        self.domain_layout = QVBoxLayout()
        corpus_layout.addLayout(self.domain_layout)
        self.domain_widgets = {}
        for domain, perc in self.domain_distribution.items():
            row = QHBoxLayout()
            status = StatusDot(f"{domain}: {perc}%", "info")
            row.addWidget(status)
            row.addStretch()
            self.domain_layout.addLayout(row)
            self.domain_widgets[domain] = status

        main_layout.addWidget(corpus_card)

        # View all activity link
        self.view_all_btn = QPushButton("View All Activity")
        self.view_all_btn.setObjectName("btn--link")
        self.view_all_btn.clicked.connect(self.view_all_activity_requested)
        main_layout.addWidget(self.view_all_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        main_layout.addStretch()

    # ---------------------------------------------------------- helpers ----
    def _create_stat_card(self, label: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("stat-card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(4)

        value_label = QLabel(value)
        value_label.setObjectName("stat-value")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        text_label = QLabel(label)
        text_label.setObjectName("stat-label")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)

        return card

    def _update_metrics(self) -> None:  # pragma: no cover - integration pending
        """Refresh dashboard metrics using live application data."""
        try:
            # Determine active collectors from CollectorsTab if available
            active = 0
            main_win = self.window()
            collectors_tab = getattr(main_win, "collectors_tab", None)
            if collectors_tab and hasattr(collectors_tab, "cards"):
                for card in collectors_tab.cards.values():
                    if not card.start_btn.isEnabled():
                        active += 1
            else:
                collectors_cfg = self.config.get("collectors", {})
                if isinstance(collectors_cfg, dict):
                    active = sum(
                        1
                        for c in collectors_cfg.values()
                        if isinstance(c, dict) and c.get("running")
                    )
            self.active_collectors = active
            value_label = self.collectors_card.findChild(QLabel, "stat-value")
            if value_label:
                value_label.setText(str(active))
        except Exception:
            pass

        try:
            from CryptoFinanceCorpusBuilder.shared_tools.storage.corpus_manager import (
                CorpusManager,
            )

            cm = CorpusManager(self.config)
            stats = cm.get_corpus_stats()
            self.total_documents = stats.get("total_documents", 0)
            self.total_docs_label.setText(
                f"Total Documents: {self.total_documents}"
            )

            distribution = (
                stats.get("domain_metrics", {}).get("domain_distribution")
            )
            if not distribution:
                domain_cfg = self.config.get("domains", {})
                distribution = {
                    d: cfg.get("allocation", 0) * 100
                    for d, cfg in domain_cfg.items()
                    if isinstance(cfg, dict)
                }
            else:
                total = sum(distribution.values()) or 1
                distribution = {
                    d: (v / total) * 100 for d, v in distribution.items()
                }

            self.domain_distribution = distribution

            # Update UI widgets, creating new ones if needed
            for domain, percent in distribution.items():
                widget = self.domain_widgets.get(domain)
                if widget is None:
                    row = QHBoxLayout()
                    widget = StatusDot(f"{domain}: {int(percent)}%", "info")
                    row.addWidget(widget)
                    row.addStretch()
                    self.domain_layout.addLayout(row)
                    self.domain_widgets[domain] = widget
                else:
                    widget.setText(f"{domain}: {int(percent)}%")
        except Exception:
            pass
