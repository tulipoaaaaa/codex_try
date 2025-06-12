import pytest
import shutil
import os
from pathlib import Path
import os

def get_test_output_dir():
    return Path('G:/data/TEST_COLLECTORS/ANNAS_MAIN_LIBRARY')

@pytest.fixture(scope='module')
def annas_output_dir():
    outdir = get_test_output_dir()
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    yield outdir
    # Clean up after test
    if outdir.exists():
        shutil.rmtree(outdir)

@pytest.fixture(scope='module')
def annas_config(annas_output_dir):
    class DummyConfig:
        raw_data_dir = annas_output_dir
        log_dir = annas_output_dir / 'logs'
        metadata_dir = annas_output_dir / 'meta'
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

def test_annas_main_library_collector_production(annas_config, annas_output_dir):
    try:
        from CorpusBuilderApp.shared_tools.collectors.collect_annas_main_library import AnnasMainLibraryCollector
    except ImportError:
        pytest.skip('AnnasMainLibraryCollector not importable')
    account_cookie = os.getenv('AA_ACCOUNT_COOKIE')
    if not account_cookie:
        pytest.skip('AA_ACCOUNT_COOKIE not set in environment')
    collector = AnnasMainLibraryCollector(annas_config, account_cookie=account_cookie)
    # Use a simple query and limit to 2 attempts for speed
    collector.collect('bitcoin', max_attempts=2)
    # Check for output files (should be in annas_output_dir or subfolders)
    files = list(annas_output_dir.rglob('*'))
    output_files = [f for f in files if f.is_file() and f.suffix in {'.pdf', '.json', '.xml'}]
    assert len(output_files) > 0, 'No output files created by AnnasMainLibraryCollector' 