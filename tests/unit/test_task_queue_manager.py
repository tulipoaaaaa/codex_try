import sys
import types
import pytest

pytestmark = pytest.mark.optional_dependency

class DummySignal:
    def __init__(self, *a, **k):
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
)
sys.modules["PySide6"] = types.SimpleNamespace(QtCore=qtcore)
sys.modules["PySide6.QtCore"] = qtcore

from shared_tools.services.task_queue_manager import TaskQueueManager


def test_queue_counts_change_on_add_and_remove():
    manager = TaskQueueManager()
    emitted = []
    manager.queue_counts_changed.connect(lambda p, r, f, c: emitted.append((p, r, f, c)))

    manager.add_task("t1", {})
    assert emitted[-1] == (1, 0, 0, 0)

    manager.add_task("t2", {})
    assert emitted[-1] == (2, 0, 0, 0)

    manager.stop_task("t1")
    assert emitted[-1] == (1, 0, 0, 0)

    manager.update_task("t2", "failed")
    assert emitted[-1] == (0, 0, 1, 0)

    manager.stop_task("t2")
    assert emitted[-1] == (0, 0, 0, 0)
