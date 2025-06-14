import os
import shutil
import pytest
from pathlib import Path
from CorpusBuilderApp.shared_tools.collectors.collect_isda import ISDADocumentationCollector
import logging

# ---------------------------------------------------------------------------
# Persistent output directory helpers (mirror BitMEX / GitHub test pattern)
# ---------------------------------------------------------------------------

def get_test_output_dir() -> Path:
    return Path("G:/data/TEST_COLLECTORS/ISDA")

@pytest.fixture(scope="module")
def isda_output_dir():
    out_dir = get_test_output_dir()
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    yield out_dir
    # Keep generated files for inspection; only close log handlers.
    logging.shutdown()
    # Uncomment below to auto-clean after tests
    # shutil.rmtree(out_dir, ignore_errors=True)

@pytest.mark.slow
@pytest.mark.productionlike
def test_isda_documentation_collector_production(isda_output_dir):
    # Provide a DummyConfig with necessary attributes for BaseCollector
    class DummyConfig:
        raw_data_dir = isda_output_dir
        log_dir = isda_output_dir / 'logs'
        metadata_dir = isda_output_dir / 'meta'
        domain_configs = {'regulation_compliance': {}}

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

    collector = ISDADocumentationCollector(DummyConfig())
    # Use a keyword filter to limit downloads
    results = collector.collect(max_sources=2, keywords=["protocol"])
    assert isinstance(results, list)
    assert len(results) <= 2
    for doc in results:
        assert os.path.exists(doc["filepath"])
        assert os.path.exists(doc["metadata_path"])
        with open(doc["metadata_path"], "r", encoding="utf-8") as f:
            meta = f.read()
            assert "protocol" in meta or "Protocol" in meta 