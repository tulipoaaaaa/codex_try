import pytest
from CryptoFinanceCorpusBuilder.shared_tools.cli import consolidate_corpus

@pytest.mark.skip("Audit stub – implement later")
def test_cli_argument_parsing(monkeypatch):
    """Ensure CLI parses arguments correctly."""
    # TODO: monkeypatch sys.argv to simulate command line
    # TODO: call consolidate_corpus.main and verify called with args
    pass

@pytest.mark.skip("Audit stub – implement later")
def test_cli_consolidation_flow(tmp_path, monkeypatch):
    """Run consolidate_corpus with temp dirs and check output."""
    # TODO: create dummy ProjectConfig YAML under tmp_path
    # TODO: monkeypatch DomainClassifier and file operations
    # TODO: assert output stats structure
    pass
