import os
import pytest

try:
    from PySide6.QtCore import Qt
    from app.ui.tabs.configuration_tab import ConfigurationTab
    from PySide6.QtWidgets import QMessageBox
except Exception:  # pragma: no cover - PySide6 unavailable
    pytest.skip("Qt bindings not available", allow_module_level=True)


def _make_config(mock_project_config, tmp_path, invalid=False):
    """Prepare mock project config with config_path and required methods."""
    if invalid:
        mock_project_config.config_path = tmp_path / "missing" / "config.yaml"
    else:
        path = tmp_path / "config.yaml"
        mock_project_config.config_path = path
    # ensure attributes exist
    mock_project_config.set = lambda *a, **k: None
    mock_project_config.save = lambda *a, **k: None
    return mock_project_config


@pytest.fixture
def config_tab(qtbot, mock_project_config, tmp_path):
    cfg = _make_config(mock_project_config, tmp_path)
    tab = ConfigurationTab(cfg)
    qtbot.addWidget(tab)
    return tab


def test_save_emits_signal(config_tab, qtbot):
    with qtbot.waitSignal(config_tab.configuration_saved, timeout=1000):
        qtbot.mouseClick(config_tab.save_btn, Qt.MouseButton.LeftButton)


def test_invalid_path_shows_error(qtbot, mock_project_config, tmp_path, monkeypatch):
    cfg = _make_config(mock_project_config, tmp_path, invalid=True)
    errors = []

    def fake_critical(self, title, msg):
        errors.append(msg)

    monkeypatch.setattr(QMessageBox, "critical", fake_critical)
    tab = ConfigurationTab(cfg)
    qtbot.addWidget(tab)
    qtbot.mouseClick(tab.save_btn, Qt.MouseButton.LeftButton)
    assert errors and "Failed to save configuration" in errors[0]


def test_import_config_populates_fields(tmp_path, qtbot, mock_project_config):
    cfg = _make_config(mock_project_config, tmp_path)
    tab = ConfigurationTab(cfg)
    qtbot.addWidget(tab)

    config_data = {
        "environment": {
            "active": "production",
            "config_path": "cfg.yaml",
            "python_path": "/usr/bin/python",
        },
        "api_keys": {"fred_key": "abc"},
        "directories": {"corpus_root": "/data"},
        "processing": {"pdf": {"enable_ocr": False}},
    }
    config_file = tmp_path / "import.yaml"
    import yaml
    config_file.write_text(yaml.safe_dump(config_data))

    with qtbot.waitSignal(tab.configuration_saved, timeout=1000):
        tab.import_config_file(str(config_file))

    assert tab.env_selector.currentText() == "production"
    assert tab.config_path.text() == "cfg.yaml"
    assert tab.fred_key.text() == "abc"
    assert tab.corpus_root.text() == "/data"
    assert not tab.enable_ocr.isChecked()
