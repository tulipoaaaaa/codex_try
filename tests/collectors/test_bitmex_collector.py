import os
import shutil
import pytest
from pathlib import Path
from CorpusBuilderApp.shared_tools.collectors.collect_bitmex import BitMEXCollector

@pytest.fixture(scope="function")
def bitmex_output_dir(tmp_path):
    out_dir = tmp_path / "bitmex_test_output"
    out_dir.mkdir(parents=True, exist_ok=True)
    yield out_dir
    shutil.rmtree(out_dir, ignore_errors=True)

@pytest.mark.slow
@pytest.mark.productionlike
def test_bitmex_collector_production(bitmex_output_dir):
    collector = BitMEXCollector(bitmex_output_dir)
    results = collector.collect(max_pages=1)
    assert isinstance(results, list)
    # At least one output file should be created
    found = False
    for root, dirs, files in os.walk(bitmex_output_dir):
        for file in files:
            if file.endswith('.pdf') or file.endswith('.json'):
                found = True
    assert found 