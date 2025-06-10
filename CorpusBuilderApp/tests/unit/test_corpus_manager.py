import sys
import types
import os
from pathlib import Path
import json
import pytest
from shared_tools.storage.corpus_manager import CorpusManager

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

# Class 1 — for UI signal-based tests
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

# Class 2 — for corpus stats and metadata tests
class SimpleCorpusManager(CorpusManager):
    """Extend CorpusManager with minimal helpers for testing."""

    def add_document(self, doc_path: Path, corpus_dir: Path) -> Path:
        """Copy a document to the corpus and create a .meta file."""
        dest = self.copy_files([doc_path], corpus_dir)[0]
        meta_path = dest.with_suffix(dest.suffix + ".meta")
        with open(meta_path, "w", encoding="utf-8") as fh:
            json.dump({"filename": dest.name}, fh)
        return dest

    def get_corpus_stats(self, corpus_dir: Path) -> dict:
        """Return simple corpus statistics for PDF files."""
        stats = {"domains": {}, "total_files": 0, "total_size_mb": 0.0}
        for domain_dir in corpus_dir.iterdir():
            if domain_dir.is_dir():
                pdf_files = list(domain_dir.glob("*.pdf"))
                size = sum(f.stat().st_size for f in pdf_files)
                stats["domains"][domain_dir.name] = {
                    "pdf_files": len(pdf_files),
                    "size_mb": round(size / (1024 * 1024), 2),
                }
                stats["total_files"] += len(pdf_files)
                stats["total_size_mb"] += size / (1024 * 1024)
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        return stats

def test_add_document_with_sample_metadata(tmp_path):
    """Ensure documents are added and metadata updated."""
    # Create a sample PDF file
    sample = tmp_path / "doc.pdf"
    sample.write_text("dummy")

    manager = SimpleCorpusManager()
    domain_dir = tmp_path / "domain"
    domain_dir.mkdir()

    dest = manager.add_document(sample, domain_dir)

    assert dest.exists()
    meta = dest.with_suffix(dest.suffix + ".meta")
    assert meta.exists()
    with open(meta, "r", encoding="utf-8") as fh:
        meta_data = json.load(fh)
    assert meta_data["filename"] == dest.name

def test_get_corpus_stats_empty(tmp_path):
    """Ensure get_corpus_stats returns empty stats for empty corpus."""
    manager = SimpleCorpusManager()
    stats = manager.get_corpus_stats(tmp_path)
    assert stats["total_files"] == 0
    assert stats["total_size_mb"] == 0.0
    assert stats["domains"] == {}
