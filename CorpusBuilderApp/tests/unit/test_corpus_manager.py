import sys
import types
import os
from pathlib import Path

# Provide minimal PySide6 stub so corpus_manager imports succeed
class _DummySignal:
    def __init__(self):
        self._slots = []
    def connect(self, slot):
        self._slots.append(slot)
    def emit(self, *args, **kwargs):
        for s in list(self._slots):
            s(*args, **kwargs)

qtcore = types.SimpleNamespace(QObject=object, Signal=lambda *a, **k: _DummySignal())
sys.modules.setdefault("PySide6", types.SimpleNamespace(QtCore=qtcore))
sys.modules.setdefault("PySide6.QtCore", qtcore)

from shared_tools.storage.corpus_manager import CorpusManager

class TestableCorpusManager(CorpusManager):
    """Extend CorpusManager to emit an operation_completed signal."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.operation_completed = _DummySignal()

    def _emit_complete(self, op: str):
        self.operation_completed.emit(op)

    def copy_files(self, *args, **kwargs):
        res = super().copy_files(*args, **kwargs)
        self._emit_complete("copy")
        return res

    def move_files(self, *args, **kwargs):
        res = super().move_files(*args, **kwargs)
        self._emit_complete("move")
        return res

    def rename_files(self, *args, **kwargs):
        res = super().rename_files(*args, **kwargs)
        self._emit_complete("rename")
        return res

    def delete_files(self, *args, **kwargs):
        res = super().delete_files(*args, **kwargs)
        self._emit_complete("delete")
        return res

    def organize_files(self, *args, **kwargs):
        res = super().organize_files(*args, **kwargs)
        self._emit_complete("organize")
        return res


def _capture_signals(manager):
    progress = []
    status = []
    completed = []
    manager.progress_updated.connect(lambda *args: progress.append(args))
    manager.status_updated.connect(lambda msg: status.append(msg))
    manager.operation_completed.connect(lambda op: completed.append(op))
    return progress, status, completed


def test_copy_files(tmp_path):
    src = tmp_path / "src.txt"
    src.write_text("demo")
    dest_dir = tmp_path / "dest"

    mgr = TestableCorpusManager()
    progress, status, completed = _capture_signals(mgr)

    results = mgr.copy_files([src], dest_dir)

    dest_file = dest_dir / "src.txt"
    assert dest_file.exists()
    assert results == [dest_file]
    assert progress
    assert status[-1] == "Copy completed"
    assert completed == ["copy"]


def test_move_files(tmp_path):
    src = tmp_path / "mv.txt"
    src.write_text("demo")
    dest_dir = tmp_path / "moved"

    mgr = TestableCorpusManager()
    progress, status, completed = _capture_signals(mgr)

    results = mgr.move_files([src], dest_dir)

    dest_file = dest_dir / "mv.txt"
    assert dest_file.exists()
    assert not src.exists()
    assert results == [dest_file]
    assert progress
    assert status[-1] == "Move completed"
    assert completed == ["move"]


def test_delete_files(tmp_path):
    f1 = tmp_path / "del.txt"
    f1.write_text("bye")

    mgr = TestableCorpusManager()
    progress, status, completed = _capture_signals(mgr)

    count = mgr.delete_files([f1])

    assert count == 1
    assert not f1.exists()
    assert status[-1] == "Delete completed"
    assert completed == ["delete"]


def test_rename_files(tmp_path):
    f1 = tmp_path / "a.txt"
    f1.write_text("x")

    mgr = TestableCorpusManager()
    progress, status, completed = _capture_signals(mgr)

    results = mgr.rename_files([f1], "renamed_{index}.{extension}")

    dest = tmp_path / "renamed_1.txt"
    assert dest.exists()
    assert results == [dest]
    assert progress
    assert status[-1] == "Rename completed"
    assert completed == ["rename"]


def test_organize_files(tmp_path):
    f1 = tmp_path / "file.txt"
    f1.write_text("x")

    mgr = TestableCorpusManager()
    progress, status, completed = _capture_signals(mgr)

    results = mgr.organize_files([f1], criteria="extension")

    dest = tmp_path / "TXT" / "file.txt"
    assert dest.exists()
    assert results == [dest]
    assert progress
    assert status[-1] == "Organize completed"
    assert completed == ["organize"]
