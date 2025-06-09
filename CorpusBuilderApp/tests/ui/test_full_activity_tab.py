import pytest

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

