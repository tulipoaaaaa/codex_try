from __future__ import annotations

import logging
import subprocess
from typing import Optional

from PySide6.QtCore import QObject, QThread, Signal as pyqtSignal

from upgrade_dependencies import upgrade_package, UPGRADES


class DependencyUpdateThread(QThread):
    """Worker thread to run dependency upgrades."""

    progress = pyqtSignal(int, str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, dry_run: bool = False, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.dry_run = dry_run
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self) -> None:  # pragma: no cover - runtime thread
        total = len(UPGRADES)
        try:
            for i, (pkg, ver) in enumerate(UPGRADES, start=1):
                if self.isInterruptionRequested():
                    return
                if self.dry_run:
                    msg = f"Would upgrade {pkg} to {ver}"
                else:
                    upgrade_package(pkg, ver)
                    msg = f"Upgraded {pkg} to {ver}"
                self.progress.emit(int(i / total * 100), msg)
            if not self.dry_run:
                with open("CorpusBuilderApp/requirements.txt", "w", encoding="utf-8") as fh:
                    subprocess.run(["pip", "freeze"], stdout=fh, check=True)
            self.finished.emit()
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Dependency update failed: %s", exc)
            self.error.emit(str(exc))


class DependencyUpdateService(QObject):
    """Service interface for running dependency updates."""

    dependency_update_started = pyqtSignal()
    dependency_update_progress = pyqtSignal(int, str)
    dependency_update_completed = pyqtSignal()
    dependency_update_failed = pyqtSignal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._thread: DependencyUpdateThread | None = None

    # ------------------------------------------------------------------
    def start_update(self, dry_run: bool = False) -> bool:
        """Begin the dependency update in a background thread."""
        if self._thread and self._thread.isRunning():
            return False
        self._thread = DependencyUpdateThread(dry_run, self)
        self._thread.progress.connect(self.dependency_update_progress.emit)
        self._thread.finished.connect(self._on_finished)
        self._thread.error.connect(self._on_error)
        self.dependency_update_started.emit()
        self._thread.start()
        return True

    # ------------------------------------------------------------------
    def _on_finished(self) -> None:
        self.dependency_update_completed.emit()
        self._thread = None

    # ------------------------------------------------------------------
    def _on_error(self, msg: str) -> None:
        self.dependency_update_failed.emit(msg)
        self._thread = None
