import pytest
import shutil
import os
from pathlib import Path

def get_test_output_dir():
    return Path('G:/data/TEST_COLLECTORS/ARXIV')

@pytest.fixture(scope='module')
def arxiv_output_dir():
    outdir = get_test_output_dir()
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    yield outdir
    # Clean up after test
    if outdir.exists():
        shutil.rmtree(outdir)

@pytest.fixture(scope='module')
def arxiv_config(arxiv_output_dir):
    class DummyConfig:
        raw_data_dir = arxiv_output_dir
        log_dir = arxiv_output_dir / 'logs'
        metadata_dir = arxiv_output_dir / 'meta'
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

def test_arxiv_collector_production(arxiv_config, arxiv_output_dir):
    try:
        from CorpusBuilderApp.shared_tools.collectors.arxiv_collector import ArxivCollector
    except ImportError:
        pytest.skip('ArxivCollector not importable')
    collector = ArxivCollector(arxiv_config)
    # Use a simple query and limit to 5 docs
    collector.collect('quantitative finance', max_items=5)
    # Check for output files (should be in arxiv_output_dir or subfolders)
    files = list(arxiv_output_dir.rglob('*'))
    output_files = [f for f in files if f.is_file() and f.suffix in {'.pdf', '.json', '.xml'}]
    assert len(output_files) > 0, 'No output files created by ArxivCollector' 