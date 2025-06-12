import os
import shutil
import pytest
from pathlib import Path
from CorpusBuilderApp.shared_tools.collectors.quantopian_collector import QuantopianCollector

@pytest.fixture(scope="function")
def quantopian_output_dir(tmp_path):
    out_dir = tmp_path / "quantopian_test_output"
    out_dir.mkdir(parents=True, exist_ok=True)
    yield out_dir
    shutil.rmtree(out_dir, ignore_errors=True)

@pytest.mark.slow
@pytest.mark.productionlike
def test_quantopian_collector_production(quantopian_output_dir):
    config = {
        'raw_data_dir': quantopian_output_dir,
        'domains': {'portfolio_construction': {'path': 'portfolio_construction'}}
    }
    collector = QuantopianCollector(config)
    results = collector.collect()
    assert isinstance(results, list)
    # At least one output file should be created
    found = False
    for root, dirs, files in os.walk(quantopian_output_dir):
        for file in files:
            if file.endswith('.json') or file.endswith('.csv'):
                found = True
    assert found 