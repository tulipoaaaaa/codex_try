from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal as pyqtSignal


class TaskHistoryService(QObject):
    """Track task execution history for collectors and processors."""

    history_changed = pyqtSignal()
    task_updated = pyqtSignal(str, dict)

    def __init__(self, history_file: str | Path | None = None, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.history_file = Path(history_file) if history_file else None
        self.tasks: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if self.history_file and self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as fh:
                    self.tasks = json.load(fh)
            except Exception:
                self.tasks = {}

    def _save(self) -> None:
        if self.history_file:
            try:
                with open(self.history_file, "w", encoding="utf-8") as fh:
                    json.dump(self.tasks, fh)
            except Exception:
                pass

    def start_task(self, task_id: str, description: str = "", metadata: Optional[dict] = None) -> None:
        info = {
            "description": description,
            "start_time": datetime.utcnow().isoformat(),
            "status": "running",
            "progress": 0,
        }
        if isinstance(metadata, dict):
            info.update(metadata)
        self.tasks[task_id] = info
        self._save()
        self.task_updated.emit(task_id, info)
        self.history_changed.emit()

    def update_progress(self, task_id: str, progress: int) -> None:
        task = self.tasks.get(task_id)
        if not task:
            return
        task["progress"] = progress
        self._save()
        self.task_updated.emit(task_id, task)

    def complete_task(self, task_id: str) -> None:
        task = self.tasks.get(task_id)
        if not task:
            return
        task["status"] = "completed"
        task["progress"] = 100
        task["end_time"] = datetime.utcnow().isoformat()
        self._save()
        self.task_updated.emit(task_id, task)
        self.history_changed.emit()

    def fail_task(self, task_id: str, error: str = "") -> None:
        task = self.tasks.get(task_id)
        if not task:
            return
        task["status"] = "failed"
        task["error"] = error
        task["end_time"] = datetime.utcnow().isoformat()
        self._save()
        self.task_updated.emit(task_id, task)
        self.history_changed.emit()

    def get_history(self) -> list[dict]:
        history: list[dict] = []
        for tid, info in self.tasks.items():
            start = info.get("start_time")
            end = info.get("end_time")
            try:
                start_dt = datetime.fromisoformat(start) if start else None
            except Exception:
                start_dt = None
            try:
                end_dt = datetime.fromisoformat(end) if end else None
            except Exception:
                end_dt = None
            if start_dt:
                finish = end_dt or datetime.utcnow()
                duration = int((finish - start_dt).total_seconds())
            else:
                duration = 0
            entry = dict(info)
            entry["task_id"] = tid
            entry["duration_seconds"] = duration
            history.append(entry)
        return history
