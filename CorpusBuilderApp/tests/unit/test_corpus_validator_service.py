import types
from pathlib import Path

from PySide6.QtCore import QObject

from shared_tools.services.corpus_validator_service import CorpusValidatorService


class DummyCfg:
    def __init__(self, base: Path):
        self.base = base
        self.domains = {"a": {}, "b": {}}

    def get_corpus_dir(self):
        return str(self.base)

    def get_raw_dir(self):
        return str(self.base / "raw")

    def get_processed_dir(self):
        return str(self.base / "processed")

    def get_metadata_dir(self):
        return str(self.base / "metadata")

    def get_logs_dir(self):
        return str(self.base / "logs")

    def get(self, key, default=None):
        if key == "domains":
            return self.domains
        return default


def test_validation_emits_results(tmp_path, qapp):
    for sub in ["raw", "processed", "metadata", "logs"]:
        (tmp_path / sub).mkdir()
    cfg = DummyCfg(tmp_path)
    service = CorpusValidatorService(cfg)
    service.validate_structure()
    assert "messages" in service.results


def test_validation_failure_emits_error(monkeypatch, tmp_path, qapp):
    cfg = DummyCfg(tmp_path)
    service = CorpusValidatorService(cfg)
    monkeypatch.setattr(
        "shared_tools.services.corpus_validator_service.check_corpus_structure",
        lambda _cfg: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    service.validate_structure()
    assert service.results == {}


