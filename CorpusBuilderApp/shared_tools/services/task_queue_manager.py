from __future__ import annotations

from PySide6.QtCore import QObject, Signal as pyqtSignal


class TaskQueueManager(QObject):
    """Service for tracking background tasks in the UI."""

    queue_counts_changed = pyqtSignal(int, int, int, int)  # pending, retry, failed, completed
    task_progress = pyqtSignal(str, int)  # task_id, progress

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.tasks: dict[str, dict] = {}

    # ------------------------------------------------------------------
    def add_task(self, task_id: str, task_info: dict) -> None:
        """Add a new task to the internal registry."""
        info = {"status": "pending", "progress": 0}
        info.update(task_info)
        self.tasks[task_id] = info
        self._emit_counts()

    # ------------------------------------------------------------------
    def update_task(self, task_id: str, status: str, progress: int = 0) -> None:
        """Update status and progress for a task."""
        task = self.tasks.setdefault(task_id, {"status": status, "progress": progress})
        task["status"] = status
        task["progress"] = progress
        self.task_progress.emit(task_id, progress)
        self._emit_counts()

    # ------------------------------------------------------------------
    def pause_task(self, task_id: str) -> None:
        """Mark a task as paused."""
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "paused"
            self._emit_counts()

    # ------------------------------------------------------------------
    def stop_task(self, task_id: str) -> None:
        """Mark a task as stopped."""
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "stopped"
            self._emit_counts()

    # ------------------------------------------------------------------
    def get_task_summary(self) -> dict:
        """Return counts of tasks by status."""
        summary = {"pending": 0, "retry": 0, "failed": 0, "completed": 0}
        for info in self.tasks.values():
            status = info.get("status")
            if status in summary:
                summary[status] += 1
        return summary

    # ------------------------------------------------------------------
    def _emit_counts(self) -> None:
        summary = self.get_task_summary()
        self.queue_counts_changed.emit(
            summary.get("pending", 0),
            summary.get("retry", 0),
            summary.get("failed", 0),
            summary.get("completed", 0),
        )
