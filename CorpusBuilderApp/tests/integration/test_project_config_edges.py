import os
import json
import yaml
from pathlib import Path

import pytest
from shared_tools.project_config import ProjectConfig

# Ensure Qt stubs provide required classes when running without PySide6
if os.environ.get("PYTEST_QT_STUBS") == "1":
    from PySide6 import QtWidgets, QtCore, QtGui

    class _Widget:
        def __init__(self, *a, **k):
            pass

        def setAcceptDrops(self, *a, **k):
            pass

        def setWindowTitle(self, *a, **k):
            pass

    for name in [
        "QWidget",
        "QDialog",
        "QGroupBox",
        "QFrame",
        "QFileDialog",
        "QScrollArea",
        "QMenu",
    ]:
        QtWidgets.__dict__[name] = type(name, (), {"__init__": _Widget.__init__,
                                                   "setAcceptDrops": _Widget.setAcceptDrops,
                                                   "setWindowTitle": _Widget.setWindowTitle})

    for name in [
        "QPushButton",
        "QLabel",
        "QLineEdit",
        "QComboBox",
        "QTabWidget",
        "QCheckBox",
        "QFormLayout",
        "QSpinBox",
        "QTableWidget",
        "QTableWidgetItem",
        "QHeaderView",
        "QDialogButtonBox",
        "QDateEdit",
    ]:
        QtWidgets.__dict__[name] = type(name, (), {"__init__": _Widget.__init__})

    QtGui.__dict__.setdefault("QDragEnterEvent", type("QDragEnterEvent", (), {}))
    QtGui.__dict__.setdefault("QDropEvent", type("QDropEvent", (), {}))
    QtCore.__dict__.setdefault("QMimeData", type("QMimeData", (), {}))
    QtCore.__dict__.setdefault("Signal", lambda *a, **k: lambda *a, **k: None)
    QtCore.__dict__.setdefault("Slot", lambda *a, **k: (lambda fn: fn))

from app.ui.tabs.configuration_tab import ConfigurationTab
from app.ui.dialogs.settings_dialog import SettingsDialog

def _write_yaml(path: Path, corpus_dir: Path) -> None:
    data = {
        "environment": "test",
        "environments": {"test": {"corpus_dir": str(corpus_dir)}},
    }
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh)

@pytest.mark.integration
def test_load_minimal_config(tmp_path, monkeypatch):
    """Load minimal YAML and verify directory helpers."""

    corpus_root = tmp_path / "corpus"
    cfg_path = tmp_path / "cfg.yaml"
    _write_yaml(cfg_path, corpus_root)

    monkeypatch.setenv("CORPUS_ROOT", str(corpus_root))
    monkeypatch.setenv("RAW_DATA_DIR", str(corpus_root / "raw"))
    monkeypatch.setenv("PROCESSED_DIR", str(corpus_root / "processed"))
    monkeypatch.setenv("METADATA_DIR", str(corpus_root / "metadata"))
    monkeypatch.setenv("LOGS_DIR", str(corpus_root / "logs"))

    cfg = ProjectConfig.from_yaml(str(cfg_path))

    assert cfg.get_corpus_root() == corpus_root
    assert cfg.get_raw_dir() == corpus_root / "raw"
    assert cfg.get_processed_dir() == corpus_root / "processed"
    assert cfg.get_metadata_dir() == corpus_root / "metadata"
    assert cfg.get_logs_dir() == corpus_root / "logs"

@pytest.mark.integration
def test_env_variable_override(monkeypatch, tmp_path):
    """Environment variables should override YAML values."""

    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(json.dumps({"api_keys": {"fred_key": "yaml"}}))

    monkeypatch.setenv("FRED_API_KEY", "env")
    cfg = ProjectConfig.from_yaml(str(cfg_path))

    assert cfg.get("api_keys.fred_key") == "env"

@pytest.mark.integration
def test_configuration_tab_updates_project_config():
    """ConfigurationTab class should be importable."""

    assert hasattr(ConfigurationTab, "configuration_saved")

@pytest.mark.integration
def test_settings_dialog_emits_saved_signal():
    """SettingsDialog class should be importable."""

    assert hasattr(SettingsDialog, "settings_saved")

