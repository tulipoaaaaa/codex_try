import pytest
import shutil
import os
from pathlib import Path
import logging
import time, random

# Remove dotenv imports as they cause shadowing issues; we'll fall back to env var and manual parser
# from dotenv import load_dotenv  # Not needed now

# Helper to manually read a key from .env if env var is missing

def read_env_value(path: str, key: str):
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            if k.strip() == key:
                return v.strip()
    return None

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
    # Keep generated files for inspection; only close log handlers.
    logging.shutdown()
    # If you want to clean up automatically, uncomment the next line.
    # shutil.rmtree(outdir)

@pytest.fixture(scope='module')
def annas_config(annas_output_dir):
    # Stub to mimic the structure the collector expects (objects with .search_terms & .quality_threshold)
    class _StubDomainCfg:
        def __init__(self, search_terms, quality_threshold=0):
            self.search_terms = search_terms
            self.quality_threshold = quality_threshold

    class DummyConfig:
        def __init__(self):
            self.raw_data_dir = annas_output_dir
            self.log_dir = annas_output_dir / 'logs'
            self.metadata_dir = annas_output_dir / 'meta'
            # Provide minimal realistic domain configurations
            self.domain_configs = {
                'high_frequency_trading': _StubDomainCfg(['bitcoin', 'high frequency trading'], quality_threshold=1),
                'other': _StubDomainCfg(['misc'])
            }

        # Legacy dict-style accessors used by some collectors
        def get(self, key, default=None):
            return getattr(self, key, default)

        def get_raw_dir(self):
            return self.raw_data_dir

        def get_logs_dir(self):
            return self.log_dir

        def get_metadata_dir(self):
            return self.metadata_dir

        def get_processor_config(self, name):
            return {'domain_configs': self.domain_configs}

    return DummyConfig()

def test_annas_main_library_collector_production(annas_config, annas_output_dir):
    try:
        from CorpusBuilderApp.shared_tools.collectors.collect_annas_main_library import AnnasMainLibraryCollector
    except ImportError:
        pytest.skip('AnnasMainLibraryCollector not importable')
    # Try environment variable first
    account_cookie = os.getenv('AA_ACCOUNT_COOKIE')
    if account_cookie:
        print(f"AA_ACCOUNT_COOKIE found in environment (length={len(account_cookie)})")
    else:
        # Fallback: manual read from .env
        env_path = os.path.join(os.getcwd(), '.env')
        print(f"AA_ACCOUNT_COOKIE not in environment; trying to load from: {env_path}")
        account_cookie = read_env_value(env_path, 'AA_ACCOUNT_COOKIE')
        print(f"AA_ACCOUNT_COOKIE length from .env: {len(account_cookie) if account_cookie else 'None'}")
        if not account_cookie:
            pytest.skip('AA_ACCOUNT_COOKIE not found in environment or .env file')
    collector = AnnasMainLibraryCollector(annas_config, account_cookie=account_cookie)
    GOOD_QUERY = "The Black Swan Nassim Taleb pdf"
    MAX_RESULTS = 10  # how many results to examine per query
    MAX_QUERY_ATTEMPTS = 2  # retry the same query in case AA is temporarily flaky

    success = False
    for attempt in range(MAX_QUERY_ATTEMPTS):
        search_results = collector.client.search(GOOD_QUERY, ext='pdf')
        # Iterate over first N candidates looking for a downloadable PDF
        for hit in search_results[:MAX_RESULTS]:
            md5 = hit['md5']
            target_path = annas_output_dir / f"{md5}.pdf"
            dl_path = collector.client.download_file(md5, output_path=target_path, query=GOOD_QUERY)
            if dl_path and Path(dl_path).exists():
                success = True
                break
        if success:
            break
        time.sleep(10)  # back-off before retry

    if not success:
        pytest.xfail("Could not download 'The Black Swan' PDF – Anna's Archive mirrors may be temporarily unavailable")

    output_files = [f for f in annas_output_dir.rglob('*') if f.is_file() and f.suffix == '.pdf']
    assert output_files, 'Download reported success but no PDF file found in output directory' 