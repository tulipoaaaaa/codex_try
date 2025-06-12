import pytest
import shutil
import os
from pathlib import Path

def get_test_output_dir():
    return Path('G:/data/TEST_COLLECTORS/SCIDB')

@pytest.fixture(scope='module')
def scidb_output_dir():
    outdir = get_test_output_dir()
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    yield outdir
    # Clean up after test
    if outdir.exists():
        shutil.rmtree(outdir)

@pytest.fixture(scope='module')
def scidb_config(scidb_output_dir):
    class DummyConfig:
        raw_data_dir = scidb_output_dir
        log_dir = scidb_output_dir / 'logs'
        metadata_dir = scidb_output_dir / 'meta'
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

def test_scidb_collector_production(scidb_config, scidb_output_dir):
    try:
        from CorpusBuilderApp.shared_tools.collectors.enhanced_scidb_collector import SciDBCollector
    except ImportError:
        pytest.skip('SciDBCollector not importable')
    account_cookie = os.getenv('AA_ACCOUNT_COOKIE')
    if not account_cookie:
        pytest.skip('AA_ACCOUNT_COOKIE not set in environment')
    collector = SciDBCollector(scidb_config, account_cookie=account_cookie)
    # Try to collect a small number of docs (adapt signature if needed)
    try:
        collector.collect('blockchain', max_items=2)
    except TypeError:
        # If signature is different, try without query
        collector.collect()
    # Check for output files (should be in scidb_output_dir or subfolders)
    files = list(scidb_output_dir.rglob('*'))
    output_files = [f for f in files if f.is_file() and f.suffix in {'.pdf', '.json', '.xml'}]
    assert len(output_files) > 0, 'No output files created by SciDBCollector' 