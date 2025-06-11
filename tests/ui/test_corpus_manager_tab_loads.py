def test_corpus_manager_tab_has_manager(qtbot, mock_project_config):
    from app.ui.tabs.corpus_manager_tab import CorpusManagerTab
    tab = CorpusManagerTab(mock_project_config)
    assert hasattr(tab, "corpus_manager") 