import pytest
from PySide6.QtWidgets import QApplication
from app.ui.tabs.collectors_tab import CollectorsTab

@pytest.mark.skip("Audit stub – implement later")
def test_collectors_tab_sequential_flow(qtbot, monkeypatch):
    """Verify tab signals integrate across multiple collectors."""
    # TODO: create mock ProjectConfig and collectors
    # TODO: trigger start/stop via UI and assert status updates
    pass


@pytest.mark.skip("Integration placeholder - collector state")
def test_collectors_tab_persists_state(qtbot):
    """Collector completion should update ProjectConfig."""
    from unittest.mock import MagicMock
    pc = MagicMock()
    tab = CollectorsTab(pc)
    qtbot.addWidget(tab)

    tab.on_collection_completed('isda', {})
    pc.set.assert_called_with('collectors.isda.running', False)
    pc.save.assert_called()
