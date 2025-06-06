import pytest

try:
    from PySide6.QtWidgets import QApplication, QLabel
except Exception:  # pragma: no cover - PySide6 unavailable
    pytest.skip("Qt bindings not available", allow_module_level=True)

from app.ui.widgets.card_wrapper import CardWrapper
from app.ui.widgets.section_header import SectionHeader
from app.ui.widgets.status_dot import StatusDot


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

