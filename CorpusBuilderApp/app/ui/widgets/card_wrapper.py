from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget

class CardWrapper(QFrame):
    """Generic card container with optional header."""

    def __init__(self, title: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)
        if title is not None:
            header = QLabel(title)
            header.setObjectName("card__header")
            outer.addWidget(header)
        self.body_layout = QVBoxLayout()
        self.body_layout.setSpacing(8)
        outer.addLayout(self.body_layout)
