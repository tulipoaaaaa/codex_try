import types
import sys

import pytest

from shared_tools.services import dependency_update_service as dservice

class DummySignal:
    def __init__(self):
        self._slots = []

    def connect(self, slot):
        self._slots.append(slot)

    def emit(self, *args):
        for s in list(self._slots):
            s(*args)

class DummyThread:
    def __init__(self, dry_run=False, parent=None):
        self.progress = DummySignal()
        self.finished = DummySignal()
        self.error = DummySignal()
        self.dry_run = dry_run

    def isRunning(self):
        return False

    def start(self):  # simulate immediate run
        total = len(dservice.UPGRADES)
        for i, (pkg, ver) in enumerate(dservice.UPGRADES, start=1):
            msg = f"Would upgrade {pkg} to {ver}" if self.dry_run else f"Upgraded {pkg} to {ver}"
            self.progress.emit(int(i / total * 100), msg)
        self.finished.emit()

def test_service_dry_run(monkeypatch):
    monkeypatch.setattr(dservice, "DependencyUpdateThread", DummyThread)
    service = dservice.DependencyUpdateService()
    # replace Qt signals with dummy versions
    service.dependency_update_progress = DummySignal()
    service.dependency_update_completed = DummySignal()
    progress = []
    completed = []
    service.dependency_update_progress.connect(lambda p, m: progress.append((p, m)))
    service.dependency_update_completed.connect(lambda: completed.append(True))
    assert service.start_update(dry_run=True)
    assert completed
    assert progress
