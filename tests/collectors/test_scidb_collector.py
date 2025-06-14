import pytest
import shutil
import os
from pathlib import Path
import logging
import json

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
    # Keep generated files for inspection; only close log handlers.
    logging.shutdown()
    # If you want to clean up automatically, uncomment the next line.
    # shutil.rmtree(outdir)

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
    # Load DOIs from config_yaml/dois.json
    doi_path = Path(__file__).resolve().parent / 'config_yaml' / 'dois.json'
    with open(doi_path, 'r', encoding='utf-8') as f:
        doi_list = json.load(f)
    assert doi_list, 'No DOIs found in dois.json'
    papers = collector.collect_by_doi(doi_list)
    assert papers, 'SciDBCollector did not return any collected papers'
    # Additionally check at least one PDF exists anywhere under output_dir (if retained)
    files = list(scidb_output_dir.rglob('*.pdf'))
    assert papers or files, 'No PDF file present; collector may have cleaned temp directory' 