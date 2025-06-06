from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QWidget,
)
from PySide6.QtCore import Qt, Signal as pyqtSignal

from app.ui.widgets.status_dot import StatusDot


class CollectorCard(QFrame):
    """Card widget representing a single collector."""

    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    configure_requested = pyqtSignal()
    logs_requested = pyqtSignal()

    def __init__(self, name: str, description: str = "", tags: list[str] | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("collector-card")
        self._name = name
        self.tags = tags or []
        self._setup_ui(name, description)

    def _setup_ui(self, name: str, description: str) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header with name and status indicator
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)
        title = QLabel(name)
        title.setObjectName("card__header")
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.status_dot = StatusDot("Stopped", "info")
        header_layout.addWidget(self.status_dot)
        layout.addLayout(header_layout)

        # Description
        if description:
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color:#C5C7C7;font-size:12px;")
            layout.addWidget(desc_label)

        # Tags
        if self.tags:
            tags_layout = QHBoxLayout()
            tags_layout.setSpacing(4)
            for tag in self.tags:
                tag_label = QLabel(tag)
                tag_label.setStyleSheet(
                    "background:#374151;color:#d1d5db;font-size:11px;padding:2px 6px;border-radius:12px;"
                )
                tags_layout.addWidget(tag_label)
            tags_layout.addStretch()
            layout.addLayout(tags_layout)


        # Metrics placeholder
        self.metrics_label = QLabel("Files collected: 0")
        layout.addWidget(self.metrics_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Controls
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.configure_btn = QPushButton("Configure")
        self.logs_btn = QPushButton("Logs")

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.configure_btn)
        btn_layout.addWidget(self.logs_btn)
        layout.addLayout(btn_layout)

        # Connect signals
        self.start_btn.clicked.connect(self.start_requested)
        self.stop_btn.clicked.connect(self.stop_requested)
        self.configure_btn.clicked.connect(self.configure_requested)
        self.logs_btn.clicked.connect(self.logs_requested)

    def update_status(self, status: str) -> None:
        """Update the card's status indicator and button states."""
        status = status.lower()
        running = "running" in status
        level = "error" if "error" in status else ("success" if running else "info")
        self.setProperty("status", level)
        self.status_dot.label.setText(status.title())
        self.status_dot.dot.setStyleSheet(
            f"border-radius:4px;background:{StatusDot.COLOR_MAP.get(level, StatusDot.COLOR_MAP['info'])};"
        )
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)

    def update_progress(self, value: int) -> None:
        self.progress_bar.setValue(value)

    def update_metrics(self, **kwargs) -> None:
        """Update metrics display using provided keyword arguments."""
        if not kwargs:
            return
        parts = [f"{k.replace('_', ' ').title()}: {v}" for k, v in kwargs.items()]
        self.metrics_label.setText(" • ".join(parts))

