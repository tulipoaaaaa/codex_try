from __future__ import annotations

import psutil
from PySide6.QtCore import QObject, QTimer, Signal as pyqtSignal


class SystemMonitor(QObject):
    """Emit periodic system metrics for dashboard consumption."""

    system_metrics = pyqtSignal(float, float, float)  # cpu, ram, disk

    def __init__(self, interval_ms: int = 5000, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._emit_metrics)
        self.timer.start(interval_ms)

    # ------------------------------------------------------------------
    def _emit_metrics(self) -> None:
        """Gather current CPU, RAM and disk usage and emit the values."""
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        self.system_metrics.emit(cpu, ram, disk)

    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start the periodic monitoring timer."""
        if not self.timer.isActive():
            self.timer.start(self.timer.interval())

    # ------------------------------------------------------------------
    def stop(self) -> None:
        """Stop emitting system metrics."""
        if self.timer.isActive():
            self.timer.stop()
