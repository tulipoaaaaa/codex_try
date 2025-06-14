import pytest
import shutil
import os
from pathlib import Path
from CorpusBuilderApp.shared_tools.collectors.collect_bitmex import BitMEXCollector
import logging

def get_test_output_dir():
    """Return persistent BitMEX test directory on G: drive (matches other collectors)."""
    return Path('G:/data/TEST_COLLECTORS/BITMEX')

@pytest.fixture(scope="module")
def bitmex_output_dir():
    out_dir = get_test_output_dir()
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    yield out_dir
    # Keep generated files for inspection; only close log handlers.
    logging.shutdown()
    # If you want to clean up automatically, uncomment the next line.
    # shutil.rmtree(out_dir, ignore_errors=True)

@pytest.fixture(scope="module")
def bitmex_config(bitmex_output_dir):
    class DummyConfig:
        raw_data_dir = bitmex_output_dir
        log_dir = bitmex_output_dir / "logs"
        metadata_dir = bitmex_output_dir / "meta"
        domain_configs = {"research": {}, "crypto_trader_digest": {}}

        def get(self, *a, **k):
            return {}

        def get_raw_dir(self):
            return self.raw_data_dir

        def get_logs_dir(self):
            return self.log_dir

        def get_metadata_dir(self):
            return self.metadata_dir

        def get_processor_config(self, name):
            return {"domain_configs": {"other": {}}}

    return DummyConfig()

@pytest.mark.slow
@pytest.mark.productionlike
def test_bitmex_collector_production(bitmex_config, bitmex_output_dir):
    collector = BitMEXCollector(bitmex_config)
    results = collector.collect(max_pages=3, categories=['research', 'crypto-trader-digest'])
    assert isinstance(results, list)
    # At least one output file should be created in either subfolder
    found = False
    for root, dirs, files in os.walk(bitmex_output_dir):
        for file in files:
            if file.endswith('.pdf') or file.endswith('.json'):
                found = True
    assert found 