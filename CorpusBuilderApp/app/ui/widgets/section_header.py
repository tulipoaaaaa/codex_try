from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

class SectionHeader(QLabel):
    """Styled section header label."""

    def __init__(self, text: str, underlined: bool = False, parent=None) -> None:
        super().__init__(text, parent)
        self.setObjectName("dashboard-section-header")
        if underlined:
            self.setStyleSheet("text-decoration: underline;")
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
