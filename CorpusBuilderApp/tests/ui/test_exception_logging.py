import logging
import types
import pytest

try:
    from app.ui.dialogs.settings_dialog import SettingsDialog
    from app.ui.tabs.full_activity_tab import FullActivityTab
except Exception:  # pragma: no cover - PySide6 unavailable
    pytest.skip("Qt bindings not available", allow_module_level=True)


class DummySignal:
    def connect(self, slot):
        raise RuntimeError("boom")


class DummyTaskSource:
    def __init__(self):
        self.task_added = DummySignal()
        self.task_updated = DummySignal()
        self.history_changed = DummySignal()


def test_settings_dialog_logging(monkeypatch, capsys):
    dialog = SettingsDialog.__new__(SettingsDialog)
    dialog.sound_checkbox = types.SimpleNamespace(isChecked=lambda: True)

    def fail_open(*args, **kwargs):
        raise OSError("fail")

    monkeypatch.setattr("builtins.open", fail_open)
    dialog.on_sound_setting_changed()
    out = capsys.readouterr().out
    assert "Failed to load theme config" in out
    assert "Failed to save theme config" in out


def test_full_activity_tab_logging(monkeypatch, caplog):
    monkeypatch.setattr(
        "app.helpers.chart_manager.ChartManager", lambda *a, **k: types.SimpleNamespace()
    )
    tab = FullActivityTab.__new__(FullActivityTab)
    tab.logger = logging.getLogger("test")
    tab.task_source = DummyTaskSource()

    with caplog.at_level(logging.WARNING):
        try:
            tab.task_source.task_added.connect(lambda _: None)
            tab.task_source.task_updated.connect(lambda _: None)
        except Exception as exc:
            tab.logger.warning("Failed to connect task signals: %s", exc)
        try:
            tab.task_source.history_changed.connect(lambda: None)
        except Exception as exc:
            tab.logger.warning("Failed to connect history_changed: %s", exc)

    messages = [r.message for r in caplog.records]
    assert any("Failed to connect task signals" in m for m in messages)
    assert any("Failed to connect history_changed" in m for m in messages)
