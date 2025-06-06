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
        corpus_card = QFrame()
        corpus_card.setObjectName("card")
        corpus_layout = QVBoxLayout(corpus_card)
        corpus_layout.setSpacing(16)

        self.total_docs_label = QLabel(f"Total Documents: {self.total_documents}")
        self.total_docs_label.setObjectName("card__header")
        corpus_layout.addWidget(self.total_docs_label)

        distribution_header = QLabel("Domain Distribution")
        distribution_header.setObjectName("card__header")
        corpus_layout.addWidget(distribution_header)

        for domain, perc in self.domain_distribution.items():
            row = QHBoxLayout()
            dot = QLabel()
            dot.setObjectName("status-dot-active")
            row.addWidget(dot)
            label = QLabel(f"{domain}: {perc}%")
            row.addWidget(label)
            row.addStretch()
            corpus_layout.addLayout(row)

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

    # Placeholder for future metrics update logic
    def _update_metrics(self) -> None:  # pragma: no cover - stub
        pass
