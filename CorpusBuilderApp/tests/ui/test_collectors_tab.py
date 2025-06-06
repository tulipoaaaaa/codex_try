import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.ui.tabs.collectors_tab import CollectorsTab


@pytest.fixture
def mock_project_config():
    return MagicMock()


@pytest.fixture
def collectors_tab(qtbot, mock_project_config):
    with patch('app.ui.tabs.collectors_tab.ISDAWrapper') as mock_isda, \
         patch('app.ui.tabs.collectors_tab.GitHubWrapper') as mock_github, \
         patch('shared_tools.ui_wrappers.collectors.annas_archive_wrapper.AnnasArchiveWrapper') as mock_anna:
        mock_isda.return_value = MagicMock()
        mock_github.return_value = MagicMock()
        mock_anna.return_value = MagicMock()
        tab = CollectorsTab(mock_project_config)
        qtbot.addWidget(tab)
        yield tab


def test_tab_initialization(collectors_tab):
    assert 'isda' in collectors_tab.cards
    assert 'github' in collectors_tab.cards


def test_isda_collection_start(collectors_tab, qtbot):
    card = collectors_tab.cards['isda']
    wrapper = collectors_tab.collector_wrappers['isda']
    qtbot.mouseClick(card.start_btn, Qt.MouseButton.LeftButton)
    wrapper.start.assert_called_once()
    assert not card.start_btn.isEnabled()
    assert card.stop_btn.isEnabled()


def test_isda_collection_stop(collectors_tab, qtbot):
    card = collectors_tab.cards['isda']
    wrapper = collectors_tab.collector_wrappers['isda']
    card.start_btn.setEnabled(False)
    card.stop_btn.setEnabled(True)
    qtbot.mouseClick(card.stop_btn, Qt.MouseButton.LeftButton)
    wrapper.stop.assert_called_once()
    assert card.start_btn.isEnabled()
    assert not card.stop_btn.isEnabled()


def test_handle_signals_update_card(collectors_tab):
    card = collectors_tab.cards['isda']
    collectors_tab._handle_progress('isda', 50)
    assert card.progress_bar.value() == 50
    collectors_tab._handle_status('isda', 'Running')
    assert not card.start_btn.isEnabled()
    assert card.stop_btn.isEnabled()


def test_collection_completed_handler(collectors_tab):
    card = collectors_tab.cards['isda']
    results = {'docs': 2}
    collectors_tab.on_collection_completed('isda', results)
    assert card.start_btn.isEnabled()
    assert not card.stop_btn.isEnabled()
    assert 'completed' in collectors_tab.collection_status_label.text().lower()
