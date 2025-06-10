from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


def create_metric_card(title: str, value: str, color: str):
    """Return a standardized metric card widget.

    Parameters
    ----------
    title: str
        Title displayed below the value.
    value: str
        Value shown in large font.
    color: str
        Hex color string for the value text.

    Returns
    -------
    tuple[QFrame, QLabel]
        The card widget and the value label so callers can update it later.
    """
    card = QFrame()
    card.setObjectName("card")
    card.setMinimumSize(200, 100)
    card.setStyleSheet(
        "background-color: #1a1f2e; border-radius: 12px; border: 1px solid #2d3748;"
    )

    layout = QVBoxLayout(card)
    layout.setSpacing(8)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    title_label = QLabel(title)
    title_label.setStyleSheet(
        "font-size: 14px; color: #C5C7C7; font-weight: 600;"
    )
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(title_label)

    value_label = QLabel(str(value))
    value_label.setStyleSheet(
        f"font-size: 28px; color: {color}; font-weight: 700;"
    )
    value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(value_label)

    return card, value_label
