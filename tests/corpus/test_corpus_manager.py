from shared_tools.storage.corpus_manager import CorpusManager
from conftest import DummyProjectConfig


def test_corpus_manager_basic(tmp_path):
    cfg = DummyProjectConfig(tmp_path)
    cm = CorpusManager()
    created = cm.copy_files([], cfg.get_raw_dir())
    assert created == []
    moved = cm.move_files([], cfg.get_raw_dir())
    assert moved == []
