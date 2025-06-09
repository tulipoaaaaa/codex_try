import os
import sys
import pytest
from PySide6.QtCore import Qt

from app.ui.tabs.logs_tab import LogsTab
from app.ui.widgets.card_wrapper import CardWrapper
from app.ui.widgets.section_header import SectionHeader
from app.ui.widgets.status_dot import StatusDot


@pytest.fixture
def logs_tab(qapp, mock_project_config, qtbot):
    tab = LogsTab(mock_project_config)
    qtbot.addWidget(tab)
    return tab


@pytest.fixture
def logs_with_files(tmp_path, qapp, mock_project_config, qtbot):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "first.log").write_text("[2024-01-01 00:00:00] INFO comp - hello\n")
    (log_dir / "second.log").write_text("[2024-01-01 00:01:00] ERROR comp - fail\n")
    mock_project_config.get_logs_dir = lambda: str(log_dir)
    tab = LogsTab(mock_project_config)
    qtbot.addWidget(tab)
    return tab


def test_logs_widgets(logs_tab):
    headers = logs_tab.findChildren(SectionHeader)
    assert any(h.text() == "Logs" for h in headers)
    cards = logs_tab.findChildren(CardWrapper)
    assert cards


def test_status_dot_in_table(logs_tab):
    entry = {"time": "2024", "level": "ERROR", "component": "c", "message": "m", "details": "d"}
    logs_tab.populate_log_table([entry])
    widget = logs_tab.log_table.cellWidget(0, 1)
    assert isinstance(widget, StatusDot)
    assert widget.label.objectName() == "status--error"


def test_scan_directory(logs_with_files):
    names = [logs_with_files.log_selector.itemText(i) for i in range(logs_with_files.log_selector.count())]
    assert "first.log" in names
    assert "second.log" in names
    assert logs_with_files.log_table.rowCount() == 1
