import os
import sys
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from app.ui.tabs.analytics_tab import AnalyticsTab
from app.ui.widgets.card_wrapper import CardWrapper
from app.ui.widgets.section_header import SectionHeader


@pytest.fixture
def analytics_tab(qapp, mock_project_config, qtbot):
    tab = AnalyticsTab(mock_project_config)
    qtbot.addWidget(tab)
    return tab


def test_widgets_present(analytics_tab):
    headers = analytics_tab.findChildren(SectionHeader)
    assert any(h.text() == "Analytics" for h in headers)
    cards = analytics_tab.findChildren(CardWrapper)
    assert cards


def test_filter_signals_trigger_update(monkeypatch, analytics_tab, qtbot):
    called = []
    def updated():
        called.append(True)
    monkeypatch.setattr(analytics_tab, "update_charts", updated)
    qtbot.mouseClick(analytics_tab.apply_filters_btn, Qt.MouseButton.LeftButton)
    assert called
