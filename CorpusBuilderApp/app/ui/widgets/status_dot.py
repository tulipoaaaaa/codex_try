from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from app.ui.theme.theme_constants import (
    STATUS_DOT_GREEN,
    STATUS_DOT_RED,
    STATUS_DOT_GRAY,
    BUTTON_COLOR_PRIMARY,
)

class StatusDot(QWidget):
    """Label with colored status dot."""

    COLOR_MAP = {
        "success": STATUS_DOT_GREEN,
        "error": STATUS_DOT_RED,
        "warning": "#E68161",
        "info": BUTTON_COLOR_PRIMARY,
    }

    def __init__(self, text: str, status: str, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.dot = QFrame()
        self.dot.setFixedSize(8, 8)
        self.dot.setStyleSheet(
            f"border-radius:4px;background:{self.COLOR_MAP.get(status, STATUS_DOT_GRAY)};"
        )
        layout.addWidget(self.dot, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.label = QLabel(text)
        self.label.setObjectName(f"status--{status}")
        layout.addWidget(self.label)
        layout.addStretch()
