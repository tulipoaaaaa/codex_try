import pytest

from PySide6.QtCore import Qt

try:
    from PySide6.QtWidgets import QApplication, QLabel
except Exception:  # pragma: no cover - PySide6 unavailable
    pytest.skip("Qt bindings not available", allow_module_level=True)

from app.ui.widgets.card_wrapper import CardWrapper
from app.ui.widgets.section_header import SectionHeader
from app.ui.widgets.status_dot import StatusDot
from app.ui.tabs.full_activity_tab import FullActivityTab
from shared_tools.services.activity_log_service import ActivityLogService

@pytest.fixture
def activity_tab(qapp, mock_project_config, qtbot):
    service = ActivityLogService()
    tab = FullActivityTab(mock_project_config, activity_log_service=service)
    qtbot.addWidget(tab)
    return tab, service


def test_cardwrapper_title(qtbot):
    card = CardWrapper(title="Hello")
    qtbot.addWidget(card)
    headers = card.findChildren(QLabel, "card__header")
    assert headers and headers[0].text() == "Hello"


def test_section_header_styles(qtbot):
    hdr1 = SectionHeader("Test")
    qtbot.addWidget(hdr1)
    assert "underline" not in hdr1.styleSheet()
    hdr2 = SectionHeader("Test", underlined=True)
    qtbot.addWidget(hdr2)
    assert "underline" in hdr2.styleSheet()


def test_status_dot_styles(qtbot):
    statuses = {
        "success": "status--success",
        "error": "status--error",
        "warning": "status--warning",
        "info": "status--info",
    }
    for status, obj_name in statuses.items():
        widget = StatusDot(status, status)
        qtbot.addWidget(widget)
        assert widget.label.objectName() == obj_name


def test_activity_table_updates(activity_tab, qtbot):
    tab, service = activity_tab
    initial = tab.activity_table.rowCount()
    service.log(
        "tester",
        "New Task",
        {
            "status": "success",
            "duration_seconds": 1,
            "progress": 100,
            "type": "Processing",
            "domain": "Test",
        },
    )

    qtbot.waitUntil(lambda: tab.activity_table.rowCount() == initial + 1, timeout=1000)


def test_retry_stop_signals(activity_tab, qtbot):
    tab, service = activity_tab
    service.log(
        "tester",
        "Fail Task",
        {
            "status": "error",
            "duration_seconds": 1,
            "progress": 0,
            "type": "Processing",
            "domain": "Test",
            "task_id": "task1",
        },
    )
    service.log(
        "tester",
        "Run Task",
        {
            "status": "running",
            "duration_seconds": 2,
            "progress": 50,
            "type": "Processing",
            "domain": "Test",
            "task_id": "task2",
        },
    )

    qtbot.waitUntil(lambda: tab.activity_table.rowCount() >= 2, timeout=1000)

    results = {}
    tab.retry_requested.connect(lambda tid: results.setdefault("retry", tid))
    tab.stop_requested.connect(lambda tid: results.setdefault("stop", tid))

    tab.activity_table.selectRow(0)
    qtbot.waitUntil(lambda: tab.retry_btn.isEnabled(), timeout=1000)
    qtbot.mouseClick(tab.retry_btn, Qt.MouseButton.LeftButton)

    tab.activity_table.selectRow(1)
    qtbot.waitUntil(lambda: tab.stop_btn.isEnabled(), timeout=1000)
    qtbot.mouseClick(tab.stop_btn, Qt.MouseButton.LeftButton)

    assert results.get("retry") == "task1"
    assert results.get("stop") == "task2"

