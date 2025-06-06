import pytest
from CryptoFinanceCorpusBuilder.shared_tools.project_config import ProjectConfig

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
