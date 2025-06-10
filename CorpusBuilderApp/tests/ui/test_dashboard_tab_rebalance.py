import sys
import pytest
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


def test_rebalance_emits_signal(dashboard_tab, qtbot):
    triggered = []
    dashboard_tab.rebalance_requested.connect(lambda: triggered.append(True))
    qtbot.mouseClick(dashboard_tab.rebalance_now_btn, Qt.MouseButton.LeftButton)
    assert triggered
