import types
import pytest
from PySide6.QtCore import QObject, Signal as pyqtSignal
from PySide6.QtWidgets import QPushButton

pytestmark = pytest.mark.optional_dependency

from app.ui.tabs import corpus_manager_tab as cmt


class DummyNotificationManager:
    def __init__(self, *a, **k):
        self.notifications = []

    def add_notification(self, nid, title, msg, level="info", auto_hide=False):
        self.notifications.append((nid, title, msg, level))


class DummyNotifier:
    calls = []

    @staticmethod
    def notify(title, message, level="info"):
        DummyNotifier.calls.append((title, message, level))


class DummyCorpusManager(QObject):
    progress_updated = pyqtSignal(int, str, dict)
    status_updated = pyqtSignal(str)
    operation_completed = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def copy_files(self, files, target_dir, overwrite=False, rename_conflicts=True):
        self.progress_updated.emit(50, "copying", {})
        self.status_updated.emit("done")
        self.operation_completed.emit("copy")

    def move_files(self, files, target_dir, overwrite=False, rename_conflicts=True):
        self.progress_updated.emit(50, "moving", {})
        self.status_updated.emit("done")
        self.operation_completed.emit("move")

    def delete_files(self, files):
        self.progress_updated.emit(50, "deleting", {})
        self.status_updated.emit("done")
        self.operation_completed.emit("delete")
        return len(files)


def minimal_setup_ui(self):
    self.batch_copy_btn = QPushButton()
    self.batch_copy_btn.clicked.connect(self.batch_copy_files)
    self.batch_move_btn = QPushButton()
    self.batch_move_btn.clicked.connect(self.batch_move_files)
    self.batch_delete_btn = QPushButton()
    self.batch_delete_btn.clicked.connect(self.batch_delete_files)


class DummyMessageBox:
    class StandardButton:
        Yes = 1
        No = 0

    @staticmethod
    def question(*a, **k):
        return DummyMessageBox.StandardButton.Yes

    @staticmethod
    def critical(*a, **k):
        pass

    @staticmethod
    def warning(*a, **k):
        pass

    @staticmethod
    def information(*a, **k):
        pass


@pytest.fixture
def corpus_tab(tmp_path, monkeypatch):
    monkeypatch.setattr(cmt, "NotificationManager", DummyNotificationManager)
    monkeypatch.setattr(cmt, "CorpusManager", DummyCorpusManager)
    monkeypatch.setattr(cmt, "Notifier", DummyNotifier)
    monkeypatch.setattr(cmt.CorpusManagerTab, "setup_ui", minimal_setup_ui)
    monkeypatch.setattr(cmt, "QMessageBox", DummyMessageBox)

    config = types.SimpleNamespace(get_corpus_root=lambda: str(tmp_path))
    tab = cmt.CorpusManagerTab(config)
    tab.refresh_file_view = lambda: None
    return tab


def test_batch_operations_emit_signals(tmp_path, corpus_tab, monkeypatch):
    file1 = tmp_path / "a.txt"
    file2 = tmp_path / "b.txt"
    file1.write_text("a")
    file2.write_text("b")
    corpus_tab.get_selected_files = lambda: [str(file1), str(file2)]

    progress = []
    ops = []
    corpus_tab.manager.progress_updated.connect(lambda *args: progress.append(args))
    corpus_tab.manager.operation_completed.connect(lambda op: ops.append(op))

    monkeypatch.setattr(cmt.QFileDialog, "getExistingDirectory", lambda *a, **k: str(tmp_path / "dest_copy"))
    corpus_tab.batch_copy_btn.clicked.emit()
    assert ops[-1] == "copy"
    assert progress
    assert any(n[0] == "batch_copy" for n in corpus_tab.notification_manager.notifications)

    progress.clear()
    monkeypatch.setattr(cmt.QFileDialog, "getExistingDirectory", lambda *a, **k: str(tmp_path / "dest_move"))
    corpus_tab.batch_move_btn.clicked.emit()
    assert ops[-1] == "move"
    assert progress
    assert any(n[0] == "batch_move" for n in corpus_tab.notification_manager.notifications)

    progress.clear()
    corpus_tab.batch_delete_btn.clicked.emit()
    assert ops[-1] == "delete"
    assert progress
    assert any(n[0] == "batch_delete" for n in corpus_tab.notification_manager.notifications)
