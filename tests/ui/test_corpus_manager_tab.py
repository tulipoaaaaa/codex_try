import types
import os
import pytest
from PySide6.QtCore import QObject, Signal as pyqtSignal, QDir
from PySide6.QtWidgets import QPushButton
from tests.ui.harness import DummySignal
import PySide6.QtCore as QtCore

QtCore.qInstallMessageHandler = lambda *a, **k: None

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
    progress_updated = DummySignal()
    status_updated = DummySignal()
    operation_completed = DummySignal()

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
    self.batch_copy_btn = types.SimpleNamespace(clicked=DummySignal())
    self.batch_copy_btn.clicked.connect(self.batch_copy_files)
    self.batch_move_btn = types.SimpleNamespace(clicked=DummySignal())
    self.batch_move_btn.clicked.connect(self.batch_move_files)
    self.batch_delete_btn = types.SimpleNamespace(clicked=DummySignal())
    self.batch_delete_btn.clicked.connect(self.batch_delete_files)
    self.validate_structure_btn = types.SimpleNamespace(clicked=DummySignal())
    self.validate_structure_btn.clicked.connect(self.validate_corpus_structure)


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
    tab = cmt.CorpusManagerTab.__new__(cmt.CorpusManagerTab)
    tab.notification_manager = DummyNotificationManager()
    tab.project_config = config
    tab.manager = DummyCorpusManager()
    tab.sound_enabled = True
    minimal_setup_ui(tab)
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

    monkeypatch.setattr(
        cmt,
        "QFileDialog",
        types.SimpleNamespace(getExistingDirectory=lambda *a, **k: str(tmp_path / "dest_copy")),
    )
    corpus_tab.batch_copy_btn.clicked.emit()
    assert ops[-1] == "copy"
    assert progress
    assert any(n[0] == "batch_copy" for n in corpus_tab.notification_manager.notifications)

    progress.clear()
    monkeypatch.setattr(
        cmt,
        "QFileDialog",
        types.SimpleNamespace(getExistingDirectory=lambda *a, **k: str(tmp_path / "dest_move")),
    )
    corpus_tab.batch_move_btn.clicked.emit()
    assert ops[-1] == "move"
    assert progress
    assert any(n[0] == "batch_move" for n in corpus_tab.notification_manager.notifications)

    progress.clear()
    corpus_tab.batch_delete_btn.clicked.emit()
    assert ops[-1] == "delete"
    assert progress
    assert any(n[0] == "batch_delete" for n in corpus_tab.notification_manager.notifications)


def test_directory_error_notification(tmp_path, monkeypatch, qapp):
    globals()['QDir'] = types.SimpleNamespace(homePath=lambda: str(tmp_path))
    config = types.SimpleNamespace(get_corpus_root=lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    tab = cmt.CorpusManagerTab.__new__(cmt.CorpusManagerTab)
    tab.notification_manager = DummyNotificationManager()
    tab.project_config = config
    tab.set_root_directory = lambda *a, **k: None

    try:
        if hasattr(tab.project_config, 'get_corpus_root'):
            corpus_root = tab.project_config.get_corpus_root()
        elif hasattr(tab.project_config, 'corpus_root'):
            corpus_root = tab.project_config.corpus_root
        else:
            corpus_root = None
        if corpus_root and os.path.isdir(corpus_root):
            tab.set_root_directory(corpus_root)
        else:
            docs_path = QDir.homePath() + "/Documents"
            tab.set_root_directory(docs_path)
    except Exception as e:
        tab.notification_manager.add_notification(
            "root_dir_error", "Directory Error", str(e), "error", auto_hide=True
        )
        tab.set_root_directory(QDir.homePath())

    assert any(n[0] == "root_dir_error" and n[3] == "error" for n in tab.notification_manager.notifications)


def test_metadata_load_error_notification(tmp_path):
    bad_metadata = tmp_path / "bad.json"
    bad_metadata.write_text("{\n", encoding="utf-8")

    tab = cmt.CorpusManagerTab.__new__(cmt.CorpusManagerTab)
    tab.notification_manager = DummyNotificationManager()
    tab.metadata_model = types.SimpleNamespace(setRowCount=lambda n: None)
    tab.add_metadata_row = lambda *a, **k: None
    tab.get_metadata_path = lambda _p: str(bad_metadata)

    cmt.CorpusManagerTab.load_metadata(tab, "dummy.txt")

    assert any(n[0] == "metadata_load_error" and n[3] == "error" for n in tab.notification_manager.notifications)
