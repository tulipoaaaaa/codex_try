from PySide6.QtWidgets import QProgressBar


def create_styled_progress_bar(value: int, color: str, height: int = 8) -> QProgressBar:
    """Return a QProgressBar with common styling applied."""
    bar = QProgressBar()
    bar.setValue(value)
    bar.setFixedHeight(height)
    bar.setTextVisible(False)
    radius = max(1, height // 2)
    bar.setStyleSheet(
        f"""
        QProgressBar {{ background-color: #2d3748; border-radius: {radius}px; }}
        QProgressBar::chunk {{ background-color: {color}; border-radius: {radius}px; }}
        """
    )
    return bar
