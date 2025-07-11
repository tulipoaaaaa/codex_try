from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, Dict
from PySide6.QtCore import QObject, Signal as pyqtSignal


class TaskHistoryService(QObject):
    """Simple service to record background task history."""

    task_added = pyqtSignal(dict)
    task_updated = pyqtSignal(dict)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._tasks: Dict[str, dict] = {}

    # ------------------------------------------------------------------
    def add_task(self, task_id: str, info: dict) -> None:
        """Register a new task and emit ``task_added``."""
        entry = {
            "id": task_id,
            "name": info.get("name", task_id),
            "status": info.get("status", "pending"),
            "progress": info.get("progress", 0),
            "start_time": info.get("start_time", datetime.utcnow().isoformat()),
        }
        entry.update(info)
        self._tasks[task_id] = entry
        self.task_added.emit(entry)

    # ------------------------------------------------------------------
    def update_task(self, task_id: str, **updates: object) -> None:
        """Update an existing task and emit ``task_updated``."""
        task = self._tasks.setdefault(
            task_id,
            {"id": task_id, "name": task_id, "status": "pending", "progress": 0, "start_time": datetime.utcnow().isoformat()},
        )
        task.update(updates)
        if "end_time" not in task and task.get("status") in {"success", "error", "stopped"}:
            task["end_time"] = datetime.utcnow().isoformat()
        self.task_updated.emit(task)

    # ------------------------------------------------------------------
    def load_recent_tasks(self, n: int = 20) -> list[dict]:
        """Return a list of the most recently added tasks."""
        tasks = list(self._tasks.values())
        tasks.sort(key=lambda t: t.get("start_time", ""))
        return tasks[-n:]

    # ------------------------------------------------------------------
    def get_recent_tasks(self, limit: int = 5) -> list[dict]:
        """Return simplified info for the most recent tasks."""
        tasks = self.load_recent_tasks(limit)
        result = []
        for t in reversed(tasks):
            result.append(
                {
                    "action": t.get("name", ""),
                    "time": t.get("start_time", ""),
                    "status": t.get("status", ""),
                    "details": t.get("details", ""),
                }
            )
        return result

    # ------------------------------------------------------------------
    def get_recent_task_counts(self, days: int = 7) -> Dict[str, int]:
        """Return a mapping of date string to number of tasks started on that day."""
        end = datetime.utcnow().date()
        start = end - timedelta(days=days - 1)
        counts: Dict[str, int] = {}
        for t in self._tasks.values():
            ts = t.get("start_time")
            try:
                dt = datetime.fromisoformat(str(ts))
            except Exception:
                continue
            d = dt.date()
            if start <= d <= end:
                key = d.isoformat()
                counts[key] = counts.get(key, 0) + 1
        return counts
