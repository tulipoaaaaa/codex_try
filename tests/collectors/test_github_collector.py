import pytest
import shutil
import os
from pathlib import Path

def get_test_output_dir():
    return Path('G:/data/TEST_COLLECTORS/GITHUB')

@pytest.fixture(scope='module')
def github_output_dir():
    outdir = get_test_output_dir()
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    yield outdir
    # Clean up after test
    if outdir.exists():
        shutil.rmtree(outdir)

@pytest.fixture(scope='module')
def github_config(github_output_dir):
    class DummyConfig:
        raw_data_dir = github_output_dir
        log_dir = github_output_dir / 'logs'
        metadata_dir = github_output_dir / 'meta'
        domain_configs = {'other': {}}
        def get(self, *a, **k):
            return {}
        def get_raw_dir(self):
            return self.raw_data_dir
        def get_logs_dir(self):
            return self.log_dir
        def get_metadata_dir(self):
            return self.metadata_dir
        def get_processor_config(self, name):
            return {'domain_configs': {'other': {}}}
    return DummyConfig()

def test_github_collector_production(github_config, github_output_dir):
    try:
        from CorpusBuilderApp.shared_tools.collectors.github_collector import GitHubCollector
    except ImportError:
        pytest.skip('GitHubCollector not importable')
    collector = GitHubCollector(github_config)
    # Use a simple query and limit to 2 repos for speed
    collector.collect('python', max_items=2)
    # Check for output files or repo folders (should be in github_output_dir or subfolders)
    files = list(github_output_dir.rglob('*'))
    output_items = [f for f in files if f.is_file() or f.is_dir()]
    assert len(output_items) > 0, 'No output files or folders created by GitHubCollector' 