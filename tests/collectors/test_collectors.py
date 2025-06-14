import pytest
import importlib
import pkgutil
import os
import shutil
import yaml
from pathlib import Path
from tempfile import TemporaryDirectory
import logging

@pytest.fixture(scope='function')
def temp_dir(tmp_path):
    out_dir = tmp_path / "collector_test_output"
    out_dir.mkdir(parents=True, exist_ok=True)
    yield out_dir
    # Keep generated files for inspection; only close log handlers.
    logging.shutdown()
    # If you want to clean up automatically, uncomment the next line.
    # shutil.rmtree(out_dir, ignore_errors=True)

@pytest.fixture(scope='function')
def dummy_config():
    class DummyProjectConfig:
        def get(self, *a, **k):
            return {}
        def get_input_dir(self):
            return '/tmp'
        def get_logs_dir(self):
            return '/tmp'
    return DummyProjectConfig()

def find_collector_classes():
    collectors = []
    pkg = 'CorpusBuilderApp.shared_tools.collectors'
    pkg_path = os.path.join('CorpusBuilderApp', 'shared_tools', 'collectors')
    for _, modname, _ in pkgutil.iter_modules([pkg_path]):
        mod = importlib.import_module(f'{pkg}.{modname}')
        for name in dir(mod):
            obj = getattr(mod, name)
            if isinstance(obj, type) and 'Collector' in name and callable(getattr(obj, 'collect', None)):
                collectors.append(obj)
    return collectors

@pytest.mark.slow
@pytest.mark.productionlike
@pytest.mark.parametrize('Collector', find_collector_classes())
def test_collector_collect(Collector, temp_dir, dummy_config):
    inst = Collector(dummy_config)
    try:
        # Load YAML configuration for the collector
        config_path = Path('tests/collectors/config_yaml') / f"{Collector.__name__.lower()}.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            # Use the loaded configuration
            if Collector.__name__ == 'ISDADocumentationCollector':
                results = inst.collect(max_sources=config['max_sources'], keywords=config['keywords'])
            elif Collector.__name__ == 'FREDCollector':
                if os.getenv("FRED_API_KEY") is None:
                    pytest.skip("No FRED_API_KEY set")
                results = inst.collect(series_ids=config['series_ids'], max_results=config['max_results'])
            elif Collector.__name__ == 'QuantopianCollector':
                results = inst.collect()
            elif Collector.__name__ == 'BitMEXCollector':
                results = inst.collect(max_pages=config['max_pages'])
            elif Collector.__name__ == 'ArxivCollector':
                results = inst.collect(max_results=config['max_results'])
            elif Collector.__name__ == 'AnnasMainLibraryCollector':
                results = inst.collect(max_attempts=config['max_attempts'])
            elif Collector.__name__ == 'SciDBCollector':
                results = inst.collect(max_results=config['max_results'])
            elif Collector.__name__ == 'GitHubCollector':
                results = inst.collect(max_repos=config['max_repos'])
            else:
                results = inst.collect(temp_dir)
        else:
            results = inst.collect(temp_dir)
        assert isinstance(results, list)
        # At least one output file should be created
        found = False
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith('.pdf') or file.endswith('.json') or file.endswith('.csv'):
                    found = True
        assert found
    except Exception as e:
        pytest.fail(f'Collector {Collector.__name__} failed: {e}') 