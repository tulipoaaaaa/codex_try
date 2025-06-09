from unittest.mock import MagicMock, patch

from app.ui.tabs.collectors_tab import CollectorsTab


def test_collectors_tab_sequential_flow(qtbot):
    """Verify tab signals integrate across multiple collectors."""
    pc = MagicMock()
    with patch('app.ui.tabs.collectors_tab.ISDAWrapper') as mock_isda, \
         patch('app.ui.tabs.collectors_tab.GitHubWrapper') as mock_github:
        isda_wrapper = MagicMock()
        github_wrapper = MagicMock()
        mock_isda.return_value = isda_wrapper
        mock_github.return_value = github_wrapper

        tab = CollectorsTab(pc)
        qtbot.addWidget(tab)

        started = []
        finished = []
        tab.collection_started.connect(lambda n: started.append(n))
        tab.collection_finished.connect(lambda n, s: finished.append((n, s)))

        tab.start_collection('isda')
        isda_wrapper.start.assert_called_once()
        pc.set.assert_called_with('collectors.isda.running', True)
        assert not tab.cards['isda'].start_btn.isEnabled()
        assert tab.cards['isda'].stop_btn.isEnabled()

        tab.stop_collection('isda')
        isda_wrapper.stop.assert_called_once()
        pc.set.assert_called_with('collectors.isda.running', False)

        tab.start_collection('github')
        github_wrapper.start.assert_called_once()
        tab.on_collection_completed('github', {'docs': 1})
        pc.set.assert_called_with('collectors.github.running', False)

        assert started == ['isda', 'github']
        assert finished[-1] == ('github', True)


def test_collectors_tab_persists_state(qtbot):
    """Collector completion should update ProjectConfig."""
    pc = MagicMock()
    tab = CollectorsTab(pc)
    qtbot.addWidget(tab)

    tab.on_collection_completed('isda', {})
    pc.set.assert_called_with('collectors.isda.running', False)
    pc.save.assert_called()
