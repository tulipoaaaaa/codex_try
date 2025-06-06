from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal


class CollectorCard(QFrame):
    """Card widget representing a single collector."""

    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    configure_requested = pyqtSignal()
    logs_requested = pyqtSignal()

    def __init__(self, name: str, description: str = "", tags: list[str] | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("card")
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
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(10, 10)
        self.status_indicator.setStyleSheet("border-radius:5px;background:#6b7280;")
        header_layout.addWidget(self.status_indicator)
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

    def set_status_color(self, color: str) -> None:
        self.status_indicator.setStyleSheet(f"border-radius:5px;background:{color};")

    def set_running(self, running: bool) -> None:
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        color = "#10b981" if running else "#6b7280"
        self.set_status_color(color)

    def set_progress(self, value: int) -> None:
        self.progress_bar.setValue(value)

