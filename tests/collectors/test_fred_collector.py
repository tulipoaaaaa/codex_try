import os
import shutil
import pytest
from pathlib import Path
from CorpusBuilderApp.shared_tools.collectors.fred_collector import FREDCollector

@pytest.fixture(scope="function")
def fred_output_dir(tmp_path):
    out_dir = tmp_path / "fred_test_output"
    out_dir.mkdir(parents=True, exist_ok=True)
    yield out_dir
    shutil.rmtree(out_dir, ignore_errors=True)

@pytest.mark.slow
@pytest.mark.productionlike
@pytest.mark.skipif(os.getenv("FRED_API_KEY") is None, reason="No FRED_API_KEY set")
def test_fred_collector_production(fred_output_dir):
    config = {
        'raw_data_dir': fred_output_dir,
        'domains': {'valuation_models': {'path': 'valuation_models'}}
    }
    # Use a well-known public FRED series ID
    series_id = "GDP"
    collector = FREDCollector(config)
    results = collector.collect(series_ids=[series_id], max_results=1)
    assert isinstance(results, list)
    assert len(results) >= 1
    for record in results:
        assert os.path.exists(record["filepath"])
        assert record["title"] 