from __future__ import annotations

from datetime import datetime
from PySide6.QtCore import QObject, Signal as pyqtSignal


class ActivityLogService(QObject):
    """Lightweight service for tracking application activity."""

    activity_added = pyqtSignal(dict)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._entries: list[dict] = []

    def log(self, source: str, message: str, details: object | None = None) -> None:
        """Record a log entry and emit an update signal."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "source": source,
            "message": message,
            "details": details,
        }
        self._entries.append(entry)
        self.activity_added.emit(entry)

    def load_recent(self, n: int = 20) -> list[dict]:
        """Return the most recent ``n`` log entries."""
        return self._entries[-n:]
