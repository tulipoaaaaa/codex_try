import sys
import pytest
from PySide6.QtWidgets import QApplication, QFrame
from PySide6.QtCore import Qt

pytestmark = pytest.mark.skipif(
    "PySide6.QtWidgets" not in sys.modules, reason="GUI not available"
)

from app.ui.tabs.dashboard_tab import DashboardTab


@pytest.fixture
def dashboard_tab(qapp, mock_project_config, qtbot):
    tab = DashboardTab(mock_project_config)
    qtbot.addWidget(tab)
    return tab


def test_stat_cards_exist(dashboard_tab):
    cards = dashboard_tab.findChildren(QFrame, "stat-card")
    assert len(cards) == 3


def test_view_all_activity_signal(dashboard_tab, qtbot):
    triggered = []

    def on_request():
        triggered.append(True)

    dashboard_tab.view_all_activity_requested.connect(on_request)
    qtbot.mouseClick(dashboard_tab.view_all_btn, Qt.MouseButton.LeftButton)
    assert triggered


def test_rebalance_now_signal(dashboard_tab, qtbot):
    triggered = []

    def on_request():
        triggered.append(True)

    dashboard_tab.rebalance_requested.connect(on_request)
    qtbot.mouseClick(dashboard_tab.rebalance_now_btn, Qt.MouseButton.LeftButton)
    assert triggered
