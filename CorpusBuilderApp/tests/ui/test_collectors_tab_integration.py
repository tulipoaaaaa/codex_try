import pytest
from PySide6.QtWidgets import QApplication
from app.ui.tabs.collectors_tab import CollectorsTab

@pytest.mark.skip("Audit stub – implement later")
def test_collectors_tab_sequential_flow(qtbot, monkeypatch):
    """Verify tab signals integrate across multiple collectors."""
    # TODO: create mock ProjectConfig and collectors
    # TODO: trigger start/stop via UI and assert status updates
    pass
