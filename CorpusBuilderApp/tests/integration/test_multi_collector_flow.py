import pytest
from CryptoFinanceCorpusBuilder.shared_tools.project_config import ProjectConfig
from CryptoFinanceCorpusBuilder.shared_tools.collectors.fred_collector import FREDCollector
from CryptoFinanceCorpusBuilder.shared_tools.collectors.github_collector import GitHubCollector

@pytest.mark.skip("Audit stub – implement later")
def test_run_fred_and_github_collectors(monkeypatch, tmp_path):
    """Run collectors sequentially using mocked APIs."""
    # TODO: create ProjectConfig pointing corpus_dir to tmp_path
    # TODO: monkeypatch network calls for FREDCollector and GitHubCollector
    # TODO: execute collectors and verify output files in corpus manager
    pass
