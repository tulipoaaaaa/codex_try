import os
from pathlib import Path
import yaml

import pytest

from shared_tools.project_config import ProjectConfig

def _write_yaml(path: Path, corpus_dir: Path) -> None:
    data = {
        "environment": "test",
        "environments": {"test": {"corpus_dir": str(corpus_dir)}},
    }
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh)


def test_load_minimal_config(tmp_path):
    """Load config with minimal fields and verify defaults."""
    corpus_root = tmp_path / "corpus"
    cfg_path = tmp_path / "config.yaml"
    _write_yaml(cfg_path, corpus_root)

    cfg = ProjectConfig.from_yaml(str(cfg_path))
    cfg.raw_data_dir = cfg.get_raw_dir()
    cfg.processed_dir = cfg.get_processed_dir()
    cfg.metadata_dir = cfg.get_metadata_dir()
    cfg.log_dir = cfg.get_logs_dir()

    default_root = Path("~/crypto_corpus").expanduser()
    assert cfg.get_corpus_root() == default_root
    assert cfg.raw_data_dir == Path("~/crypto_corpus/raw").expanduser()
    assert cfg.processed_dir == Path("~/crypto_corpus/processed").expanduser()

def test_env_variable_override(monkeypatch, tmp_path):
    """Environment variables should override YAML paths."""

    cfg_path = tmp_path / "config.yaml"
    _write_yaml(cfg_path, tmp_path / "default")

    corpus_root = tmp_path / "corpus"
    monkeypatch.setenv("CORPUS_ROOT", str(corpus_root))
    monkeypatch.setenv("RAW_DATA_DIR", str(corpus_root / "raw"))
    monkeypatch.setenv("PROCESSED_DIR", str(corpus_root / "processed"))
    monkeypatch.setenv("METADATA_DIR", str(corpus_root / "metadata"))
    monkeypatch.setenv("LOGS_DIR", str(corpus_root / "logs"))
    monkeypatch.setenv("FRED_API_KEY", "dummy")

    cfg = ProjectConfig.from_yaml(str(cfg_path))
    cfg.raw_data_dir = cfg.get_raw_dir()
    cfg.processed_dir = cfg.get_processed_dir()
    cfg.metadata_dir = cfg.get_metadata_dir()
    cfg.log_dir = cfg.get_logs_dir()

    assert cfg.get_corpus_root() == corpus_root
    assert cfg.get_raw_dir() == corpus_root / "raw"
    assert cfg.get("api_keys.fred_key") == "dummy"


@pytest.mark.skip("Integration placeholder - configuration persistence")
def test_configuration_tab_updates_project_config(qtbot):
    """Saving the ConfigurationTab should persist values via ProjectConfig."""
    from app.ui.tabs.configuration_tab import ConfigurationTab
    from unittest.mock import MagicMock
    pc = MagicMock()
    tab = ConfigurationTab(pc)
    qtbot.addWidget(tab)

    tab.env_selector.setCurrentText("production")
    tab.save_configuration()

    pc.set.assert_any_call('environment.active', 'production')
    pc.save.assert_called()


@pytest.mark.skip("Integration placeholder - settings persistence")
def test_settings_dialog_emits_saved_signal(qtbot):
    """Settings dialog should emit updated values when accepted."""
    from app.ui.dialogs.settings_dialog import SettingsDialog
    from unittest.mock import MagicMock

    dialog = SettingsDialog()
    qtbot.addWidget(dialog)
    handler = MagicMock()
    dialog.settings_saved.connect(handler)
    dialog.accept()

    handler.assert_called()
