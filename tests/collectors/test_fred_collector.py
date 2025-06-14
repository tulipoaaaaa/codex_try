import os
import shutil
import pytest
from pathlib import Path
from CorpusBuilderApp.shared_tools.collectors.fred_collector import FREDCollector
import logging

# ---------------------------------------------------------------------------
# Persistent output directory helpers (mirror BitMEX test pattern)
# ---------------------------------------------------------------------------

def get_test_output_dir() -> Path:
    """Return persistent FRED test directory on G: drive (matches other collectors)."""
    return Path("G:/data/TEST_COLLECTORS/FRED")

@pytest.fixture(scope="module")
def fred_output_dir():
    out_dir = get_test_output_dir()
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    yield out_dir
    # Keep generated files for manual inspection; only release log handlers.
    logging.shutdown()
    # To auto-clean, uncomment:
    # shutil.rmtree(out_dir, ignore_errors=True)

@pytest.mark.slow
@pytest.mark.productionlike
@pytest.mark.skipif(os.getenv("FRED_API_KEY") is None, reason="No FRED_API_KEY set")
def test_fred_collector_production(fred_output_dir):
    dummy_cfg = _make_dummy_config(fred_output_dir)

    # Use a well-known public FRED series ID (available without special access)
    series_id = "GDP"

    collector = FREDCollector(dummy_cfg)
    results = collector.collect(series_ids=[series_id], max_results=1)
    assert isinstance(results, list)
    assert len(results) >= 1
    for record in results:
        assert os.path.exists(record["filepath"])
        assert record["title"]

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_dummy_config(output_dir: Path):
    """Create a lightweight config object exposing the attributes/methods that
    BaseCollector (and friends) expect. This mirrors the pattern used in the
    other collector test suites (e.g. BitMEX, GitHub)."""

    class DummyConfig:
        raw_data_dir = output_dir
        log_dir = output_dir / "logs"
        metadata_dir = output_dir / "meta"

        # Minimal domain mapping – for FRED we categorise everything under
        # 'valuation_models' by default.
        domain_configs = {"valuation_models": {}}

        # ------------------------------------------------------------------
        # Accessor helpers expected by BaseCollector via _get_path_attr
        # ------------------------------------------------------------------
        def get(self, *a, **k):
            return {}

        def get_raw_dir(self):
            return self.raw_data_dir

        def get_logs_dir(self):
            return self.log_dir

        def get_metadata_dir(self):
            return self.metadata_dir

        def get_processor_config(self, name):
            # Provide a fallback shape similar to the real ProjectConfig
            return {"domain_configs": {"other": {}}}

    return DummyConfig() 