import types
from pathlib import Path

from PySide6.QtCore import QObject

from shared_tools.services.corpus_validator_service import CorpusValidatorService
from tools.check_corpus_structure import validate_metadata_files
import json
import logging


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


def test_validate_metadata_files_success(tmp_path, caplog):
    meta_dir = tmp_path / "metadata" / "a"
    meta_dir.mkdir(parents=True)
    good = meta_dir / "good.json"
    with open(good, "w", encoding="utf-8") as fh:
        json.dump({"domain": "a", "author": "me", "year": 2024}, fh)
    cfg = DummyCfg(tmp_path)
    with caplog.at_level(logging.WARNING, logger="tools.check_corpus_structure"):
        validate_metadata_files(cfg)
    assert not caplog.records


def test_validate_metadata_files_warns(tmp_path, caplog):
    meta_dir = tmp_path / "metadata"
    meta_dir.mkdir(parents=True)
    bad = meta_dir / "bad.json"
    bad.write_text("{bad}")
    cfg = DummyCfg(tmp_path)
    with caplog.at_level(logging.WARNING, logger="tools.check_corpus_structure"):
        validate_metadata_files(cfg)
    assert any("Invalid metadata" in r.message for r in caplog.records)


def test_service_passes_flag(monkeypatch, tmp_path, qapp):
    for sub in ["raw", "processed", "metadata", "logs"]:
        (tmp_path / sub).mkdir()
    cfg = DummyCfg(tmp_path)
    captured = {}

    def fake_check(_cfg, *, validate_metadata=False):
        captured["flag"] = validate_metadata

    monkeypatch.setattr(
        "shared_tools.services.corpus_validator_service.check_corpus_structure",
        fake_check,
    )

    service = CorpusValidatorService(cfg)
    service.validate_structure(validate_metadata=True)
    assert captured.get("flag") is True


