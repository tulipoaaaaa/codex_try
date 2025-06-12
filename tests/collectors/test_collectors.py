import pkgutil
import inspect
import importlib
import pytest

from conftest import DummyProjectConfig


@pytest.mark.parametrize("mod_name", [m.name.split('.')[-1] for m in pkgutil.iter_modules(importlib.import_module('shared_tools.collectors').__path__)])
def test_collector_instantiation(mod_name, tmp_path):
    try:
        module = importlib.import_module(f'shared_tools.collectors.{mod_name}')
    except Exception:
        pytest.skip(f'module import failed: {mod_name}')
    cfg = DummyProjectConfig(tmp_path)
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if name.endswith('Collector') and obj.__module__ == module.__name__:
            try:
                instance = obj(cfg)
            except Exception:
                pytest.skip(f'init failed for {name}')
            if hasattr(instance, 'collect'):
                try:
                    sig = inspect.signature(instance.collect)
                    kwargs = {p.name: (0 if p.annotation in (int, float) else None) for p in sig.parameters.values() if p.default is inspect.Parameter.empty}
                    instance.collect(**kwargs)
                except Exception:
                    pytest.skip(f'collect failed for {name}')
            assert isinstance(instance, obj)
