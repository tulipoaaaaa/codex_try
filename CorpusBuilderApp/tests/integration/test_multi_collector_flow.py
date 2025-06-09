import os
import yaml
from pathlib import Path

import pytest

from shared_tools.project_config import ProjectConfig
from shared_tools.storage.corpus_manager import CorpusManager


def _write_yaml(path: Path, corpus_dir: Path) -> None:
    data = {
        "environment": "test",
        "environments": {"test": {"corpus_dir": str(corpus_dir)}},
    }
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh)


def test_run_fred_and_github_collectors(monkeypatch, tmp_path):
    """Run collectors sequentially using mocked APIs."""

    import sys, importlib
    sys.modules.pop("numpy", None)
    import numpy as _real_numpy
    sys.modules["numpy"] = _real_numpy
    from shared_tools.collectors.fred_collector import FREDCollector
    from shared_tools.collectors.github_collector import GitHubCollector

    corpus_root = tmp_path / "corpus"
    cfg_path = tmp_path / "cfg.yaml"
    _write_yaml(cfg_path, corpus_root)

    # Use environment variables so directories resolve within tmp_path
    monkeypatch.setenv("CORPUS_ROOT", str(corpus_root))
    monkeypatch.setenv("RAW_DATA_DIR", str(corpus_root / "raw"))
    monkeypatch.setenv("PROCESSED_DIR", str(corpus_root / "processed"))
    monkeypatch.setenv("METADATA_DIR", str(corpus_root / "metadata"))
    monkeypatch.setenv("LOGS_DIR", str(corpus_root / "logs"))

    cfg = ProjectConfig.from_yaml(str(cfg_path))
    # Provide attribute access used by collectors
    cfg.raw_data_dir = cfg.get_raw_dir()
    cfg.processed_dir = cfg.get_processed_dir()
    cfg.metadata_dir = cfg.get_metadata_dir()
    cfg.log_dir = cfg.get_logs_dir()
    cfg.domain_configs = cfg.get("domains", {})

    def fake_fred_api(self, endpoint, params=None):
        if endpoint == "series":
            return {"seriess": [{"series_id": params["series_id"], "info": {"title": "Fake"}}]}
        if endpoint == "series/observations":
            return {"observations": [{"date": "2024-01-01", "value": "1"}]}
        return {}

    def fake_github_api(self, endpoint, params=None):
        if endpoint.startswith("search/repositories"):
            return {
                "items": [
                    {
                        "name": "fake-repo",
                        "clone_url": "https://example.com/repo.git",
                        "owner": {"login": "tester"},
                    }
                ]
            }
        return {}

    def fake_clone(self, clone_url, target_dir):
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "dummy.txt").write_text("ok")
        return target_dir

    monkeypatch.setattr(FREDCollector, "api_request", fake_fred_api)
    monkeypatch.setattr(GitHubCollector, "api_request", fake_github_api)
    monkeypatch.setattr(GitHubCollector, "_clone_repo", fake_clone)

    fred = FREDCollector(cfg, api_key="token")
    fred.collect(series_ids=["TEST"])

    github = GitHubCollector(cfg, api_key="token")
    github.collect(search_terms=["crypto"], max_repos=1)

    cm = CorpusManager()
    fred_files = list((cfg.raw_data_dir / "FRED").glob("*.json"))
    repo_dirs = [p for p in (cfg.raw_data_dir / "Github").iterdir() if p.is_dir()]

    assert fred_files, "FRED collector should output JSON files"
    assert repo_dirs, "GitHub collector should clone at least one repo"
    cm.validate_path(fred_files[0], must_exist=True)
    cm.validate_path(repo_dirs[0], must_exist=True)