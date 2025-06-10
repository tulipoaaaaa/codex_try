import json
import json
import sys
import types

dummy_mod = types.ModuleType("shared_tools.processors.monitor_progress")

class _DummyMonitor:
    def configure(self, *a, **k):
        pass

dummy_mod.MonitorProgress = _DummyMonitor
sys.modules.setdefault("shared_tools.processors.monitor_progress", dummy_mod)

from CorpusBuilderApp.shared_tools.ui_wrappers.processors.monitor_progress_wrapper import (
    MonitorProgressWrapper,
)

class DummyItem:
    def __init__(self, text: str):
        self._text = text

    def text(self) -> str:
        return self._text


class DummyTable:
    def __init__(self, rows):
        self._rows = rows

    def rowCount(self):
        return len(self._rows)

    def columnCount(self):
        return len(self._rows[0]) if self._rows else 0

    def item(self, r, c):
        return DummyItem(self._rows[r][c])


def test_export_history_json(tmp_path):
    rows = [[
        "1",
        "Task",
        "completed",
        "2024-01-01 00:00:00",
        "1s",
        "ok",
        "",
    ]]
    wrapper = types.SimpleNamespace(history_table=DummyTable(rows))

    out = tmp_path / "history.json"
    MonitorProgressWrapper._export_history_json(wrapper, str(out))

    exported = json.loads(out.read_text())
    expected = [
        {
            "Task ID": "1",
            "Name": "Task",
            "Status": "completed",
            "Start Time": "2024-01-01 00:00:00",
            "Duration": "1s",
            "Result": "ok",
            "Error": "",
        }
    ]
    assert exported == expected
