import sys
import types
import pytest

pytestmark = pytest.mark.optional_dependency

class DummySignal:
    def __init__(self):
        self._slots = []
    def connect(self, slot):
        self._slots.append(slot)
    def emit(self, *args):
        for s in self._slots:
            s(*args)

qtcore = types.SimpleNamespace(
    QObject=type("QObject", (), {"__init__": lambda self, *a, **k: None}),
    Signal=lambda *a, **k: DummySignal(),
    QThread=object,
    QTimer=object,
    qInstallMessageHandler=lambda *a, **k: None,
)
sys.modules["PySide6"] = types.SimpleNamespace(QtCore=qtcore)
sys.modules["PySide6.QtCore"] = qtcore

from shared_tools.services.task_queue_manager import TaskQueueManager
from shared_tools.ui_wrappers import base_wrapper as bw

class DummyThread:
    def __init__(self, *a, **k):
        self.progress = bw.DummySignal()
        self.error = bw.DummySignal()
        self.finished = bw.DummySignal()
    def start(self):
        self.progress.emit(1, 1, "done")
        self.finished.emit({})
    def isRunning(self):
        return False
    def stop(self):
        pass
    def wait(self):
        pass

class SimpleWrapper(bw.BaseWrapper):
    def _create_target_object(self):
        return object()
    def _get_operation_type(self):
        return "collect"


def test_queue_counts_update_on_start(monkeypatch):
    monkeypatch.setattr(bw, "BaseWorkerThread", DummyThread)
    manager = TaskQueueManager(test_mode=True)
    wrapper = SimpleWrapper({}, task_queue_manager=manager, test_mode=True)
    counts = []
    manager.queue_counts_changed.connect(lambda p, r, f, c: counts.append((p, r, f, c)))

    wrapper.start()

    assert counts[0] == (1, 0, 0, 0)
    assert counts[-1] == (0, 0, 0, 1)
