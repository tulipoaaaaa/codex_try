import os
import shutil
import pytest
from pathlib import Path
from CorpusBuilderApp.shared_tools.collectors.collect_isda import ISDADocumentationCollector

@pytest.fixture(scope="function")
def isda_output_dir(tmp_path):
    out_dir = tmp_path / "isda_test_output"
    out_dir.mkdir(parents=True, exist_ok=True)
    yield out_dir
    shutil.rmtree(out_dir, ignore_errors=True)

@pytest.mark.slow
@pytest.mark.productionlike
def test_isda_documentation_collector_production(isda_output_dir):
    # Use a minimal config dict for ProjectConfig fallback
    config = {
        'raw_data_dir': isda_output_dir,
        'domains': {'regulation_compliance': {'path': 'regulation_compliance'}}
    }
    collector = ISDADocumentationCollector(config)
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