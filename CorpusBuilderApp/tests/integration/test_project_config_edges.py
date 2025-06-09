import pytest
from CorpusBuilderApp.shared_tools.project_config import ProjectConfig

@pytest.mark.skip("Audit stub – implement later")
def test_load_minimal_config(tmp_path):
    """Load config with minimal fields and verify defaults."""
    # TODO: write minimal YAML into tmp_path / 'config.yaml'
    # TODO: invoke ProjectConfig on that file
    # TODO: assert directories created and defaults applied
    pass

@pytest.mark.skip("Audit stub – implement later")
def test_env_variable_override(monkeypatch, tmp_path):
    """Environment variables should override YAML paths."""
    # TODO: set env vars like FRED_API_KEY
    # TODO: load config and confirm overrides
    pass


@pytest.mark.skip("Integration placeholder - configuration persistence")
def test_configuration_tab_updates_project_config(qtbot):
    """Saving the ConfigurationTab should persist values via ProjectConfig."""
    from app.ui.tabs.configuration_tab import ConfigurationTab
    from unittest.mock import MagicMock
    pc = MagicMock()
    tab = ConfigurationTab(pc)
    qtbot.addWidget(tab)

    tab.env_selector.setCurrentText("production")
    tab.save_configuration()

    pc.set.assert_any_call('environment.active', 'production')
    pc.save.assert_called()


@pytest.mark.skip("Integration placeholder - settings persistence")
def test_settings_dialog_emits_saved_signal(qtbot):
    """Settings dialog should emit updated values when accepted."""
    from app.ui.dialogs.settings_dialog import SettingsDialog
    from unittest.mock import MagicMock

    dialog = SettingsDialog()
    qtbot.addWidget(dialog)
    handler = MagicMock()
    dialog.settings_saved.connect(handler)
    dialog.accept()

    handler.assert_called()
