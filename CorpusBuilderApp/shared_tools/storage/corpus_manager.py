from __future__ import annotations
import os
import shutil
from typing import List
from PySide6.QtCore import QObject, Signal

class CorpusManager(QObject):
    """Simple corpus manager handling batch file operations."""

    progress_updated = Signal(int, str)
    status_updated = Signal(str, str)
    operation_completed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    # ----------------------------- helpers ---------------------------------
    def _emit_progress(self, index: int, total: int, op: str) -> None:
        percent = int((index / total) * 100)
        self.progress_updated.emit(percent, op)

    def batch_copy_files(self, files: List[str], target_dir: str) -> None:
        os.makedirs(target_dir, exist_ok=True)
        total = len(files)
        for i, src in enumerate(files, 1):
            try:
                shutil.copy2(src, target_dir)
                self.status_updated.emit(src, "success")
            except Exception:
                self.status_updated.emit(src, "error")
            self._emit_progress(i, total, "copy")
        self.operation_completed.emit("copy")

    def batch_move_files(self, files: List[str], target_dir: str) -> None:
        os.makedirs(target_dir, exist_ok=True)
        total = len(files)
        for i, src in enumerate(files, 1):
            try:
                shutil.move(src, target_dir)
                self.status_updated.emit(src, "success")
            except Exception:
                self.status_updated.emit(src, "error")
            self._emit_progress(i, total, "move")
        self.operation_completed.emit("move")

    def batch_delete_files(self, files: List[str]) -> None:
        total = len(files)
        for i, path in enumerate(files, 1):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.status_updated.emit(path, "success")
            except Exception:
                self.status_updated.emit(path, "error")
            self._emit_progress(i, total, "delete")
        self.operation_completed.emit("delete")
