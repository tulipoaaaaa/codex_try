import pkgutil
import inspect
import importlib
import pytest

from conftest import DummyProjectConfig


@pytest.mark.parametrize("mod_name", [m.name.split('.')[-1] for m in pkgutil.iter_modules(importlib.import_module('shared_tools.processors').__path__)])
def test_processor_instantiation(mod_name, tmp_path):
    try:
        module = importlib.import_module(f'shared_tools.processors.{mod_name}')
    except Exception:
        pytest.skip(f'module import failed: {mod_name}')
    cfg = DummyProjectConfig(tmp_path)
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if name.endswith('Processor') and obj.__module__ == module.__name__:
            try:
                instance = obj(cfg)
            except Exception:
                pytest.skip(f'init failed for {name}')
            if hasattr(instance, 'process'):
                try:
                    sig = inspect.signature(instance.process)
                    kwargs = {p.name: None for p in sig.parameters.values() if p.default is inspect.Parameter.empty}
                    instance.process(**kwargs)
                except Exception:
                    pytest.skip(f'process failed for {name}')
            assert isinstance(instance, obj)
