import json
import sys
from pathlib import Path

# Ensure package imports resolve
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
sys.path.insert(1, str(root / "CorpusBuilderApp"))

# Stub heavy dependencies
import types
np = types.ModuleType("numpy")
sys.modules.setdefault("numpy", np)
qtcore = types.SimpleNamespace(QObject=object, Signal=lambda *a, **k: lambda *a, **k: None)
sys.modules.setdefault("PySide6", types.SimpleNamespace(QtCore=qtcore))
sys.modules.setdefault("PySide6.QtCore", qtcore)
sys.modules.setdefault("yaml", types.ModuleType("yaml"))
sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda *a, **k: None))

from shared_tools.processors.deduplicator import Deduplicator

class DummyConfig:
    def __init__(self, input_dir: Path, log_dir: Path):
        self._input_dir = input_dir
        self._log_dir = log_dir
    def get_input_dir(self):
        return str(self._input_dir)
    def get_logs_dir(self):
        return self._log_dir
    def get_processor_config(self, name: str):
        return {}


def test_deduplicator_logging(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    log_dir = tmp_path / "logs"
    cfg = DummyConfig(corpus, log_dir)
    f1 = corpus / "f1.txt"
    f2 = corpus / "f2.txt"
    f1.write_text("dup")
    f2.write_text("dup")

    dedup = Deduplicator(cfg)
    dedup.deduplicate([str(f1), str(f2)])
    log_path = log_dir / "dedup_log.jsonl"
    assert log_path.exists()
    with open(log_path) as f:
        logs = [json.loads(l) for l in f if l.startswith("{")]
    assert any(e["file"] == str(f2) for e in logs)


def test_deduplicator_skip_logic(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    log_dir = tmp_path / "logs"
    cfg = DummyConfig(corpus, log_dir)
    f1 = corpus / "one.txt"
    f2 = corpus / "two.txt"
    f1.write_text("same")
    f2.write_text("same")

    dedup = Deduplicator(cfg)
    dedup.deduplicate([str(f1), str(f2)])

    dedup2 = Deduplicator(cfg)
    assert dedup2.should_skip(str(f2)) is True
