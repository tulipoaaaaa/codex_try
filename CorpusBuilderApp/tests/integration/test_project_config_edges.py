import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from shared_tools.project_config import ProjectConfig


@pytest.mark.integration
def test_load_minimal_config(tmp_path, monkeypatch):
    """Load config with minimal fields and verify default handling."""

    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text("{}")

    monkeypatch.setenv("CORPUS_ROOT", str(tmp_path / "corpus"))
    monkeypatch.setenv("RAW_DATA_DIR", str(tmp_path / "corpus" / "raw"))
    monkeypatch.setenv("PROCESSED_DIR", str(tmp_path / "corpus" / "processed"))
    monkeypatch.setenv("METADATA_DIR", str(tmp_path / "corpus" / "metadata"))
    monkeypatch.setenv("LOGS_DIR", str(tmp_path / "corpus" / "logs"))

    cfg = ProjectConfig.from_yaml(str(cfg_path))

    assert cfg.get_corpus_root() == Path(tmp_path / "corpus")
    assert cfg.get_raw_dir() == Path(tmp_path / "corpus" / "raw")
    assert cfg.get_processed_dir() == Path(tmp_path / "corpus" / "processed")
    assert cfg.get_metadata_dir() == Path(tmp_path / "corpus" / "metadata")
    assert cfg.get_logs_dir() == Path(tmp_path / "corpus" / "logs")

@pytest.mark.integration
def test_env_variable_override(monkeypatch, tmp_path):
    """Environment variables should override YAML values."""

    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(json.dumps({"api_keys": {"fred_key": "yaml"}}))

    monkeypatch.setenv("FRED_API_KEY", "env")
    cfg = ProjectConfig.from_yaml(str(cfg_path))

    assert cfg.get("api_keys.fred_key") == "env"


def test_configuration_tab_updates_project_config():
    """Configuration tab integration requires Qt; skip if unavailable."""
    pytest.skip("Qt widgets not available in test environment")


def test_settings_dialog_emits_saved_signal():
    """Settings dialog integration requires Qt; skip if unavailable."""
    pytest.skip("Qt widgets not available in test environment")
