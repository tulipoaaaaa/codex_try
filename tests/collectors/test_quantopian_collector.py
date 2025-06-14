import os
import shutil
import pytest
from pathlib import Path
from CorpusBuilderApp.shared_tools.collectors.quantopian_collector import QuantopianCollector
import logging

# ---------------------------------------------------------------------------
# Persistent output directory helpers (mirror other collector tests)
# ---------------------------------------------------------------------------


def get_test_output_dir() -> Path:
    return Path("G:/data/TEST_COLLECTORS/QUANTOPIAN")


@pytest.fixture(scope="module")
def quantopian_output_dir():
    out_dir = get_test_output_dir()
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    yield out_dir
    logging.shutdown()
    # Uncomment below to auto-clean
    # shutil.rmtree(out_dir, ignore_errors=True)

@pytest.mark.slow
@pytest.mark.productionlike
def test_quantopian_collector_production(quantopian_output_dir):
    class DummyConfig:
        raw_data_dir = quantopian_output_dir
        log_dir = quantopian_output_dir / 'logs'
        metadata_dir = quantopian_output_dir / 'meta'
        domain_configs = {'portfolio_construction': {}}

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

    collector = QuantopianCollector(DummyConfig())
    results = collector.collect()
    assert isinstance(results, list)
    # At least one output file should be created
    found = False
    for root, dirs, files in os.walk(quantopian_output_dir):
        for file in files:
            if file.endswith('.json') or file.endswith('.csv'):
                found = True
    assert found 