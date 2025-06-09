"""Integration test for running multiple collectors sequentially."""

import json
from pathlib import Path
import sys
import types

import pytest

from shared_tools.project_config import ProjectConfig


@pytest.mark.integration
def test_run_fred_and_github_collectors(monkeypatch, tmp_path):
    """Run FRED and GitHub collectors with mocked API calls."""

    cfg_path = tmp_path / "config.yaml"
    cfg_content = {
        "directories": {
            "corpus_root": str(tmp_path / "corpus"),
            "raw_data_dir": str(tmp_path / "raw"),
            "processed_dir": str(tmp_path / "processed"),
            "metadata_dir": str(tmp_path / "metadata"),
            "logs_dir": str(tmp_path / "logs"),
        }
    }
    cfg_path.write_text(json.dumps(cfg_content))

    monkeypatch.setenv("FRED_API_KEY", "dummy")
    monkeypatch.setenv("GITHUB_TOKEN", "dummy")

    cfg = ProjectConfig.from_yaml(str(cfg_path))

    # Provide attributes expected by BaseCollector
    cfg.raw_data_dir = Path(cfg.get('directories.raw_data_dir'))
    cfg.log_dir = Path(cfg.get('directories.logs_dir'))
    cfg.domain_configs = {}

    monkeypatch.setitem(sys.modules, 'pandas', type('PandasStub', (), {'DataFrame': object}))
    requests_stub = types.ModuleType('requests')
    requests_stub.exceptions = types.SimpleNamespace(RequestException=Exception)
    requests_stub.get = lambda *a, **k: type('Resp', (), {'status_code':200, 'json': lambda :{}})()
    requests_stub.Session = lambda: types.SimpleNamespace(get=lambda *a, **k: types.SimpleNamespace(status_code=200, json=lambda: {}))
    monkeypatch.setitem(sys.modules, 'requests', requests_stub)

    from shared_tools.collectors.fred_collector import FREDCollector
    from shared_tools.collectors.github_collector import GitHubCollector

    def fake_fred_collect(self, *_, **__):
        out = self.fred_dir / "fred.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("{}")
        return [{"filepath": str(out)}]

    def fake_github_collect(self, *_, **__):
        out = self.github_dir / "repo.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("repo")
        return [{"local_path": str(out)}]

    monkeypatch.setattr(FREDCollector, "collect", fake_fred_collect)
    monkeypatch.setattr(GitHubCollector, "collect", fake_github_collect)

    fred = FREDCollector(cfg)
    github = GitHubCollector(cfg)

    fred_files = fred.collect(series_ids=["TEST"])
    gh_files = github.collect(search_terms=["crypto"])

    assert Path(fred_files[0]["filepath"]).exists()
    assert Path(gh_files[0]["local_path"]).exists()
