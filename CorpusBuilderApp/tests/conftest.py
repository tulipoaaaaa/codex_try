import importlib.util
import pathlib

shared_path = pathlib.Path(__file__).resolve().parents[2] / "tests" / "conftest.py"
spec = importlib.util.spec_from_file_location("conftest_shared", shared_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.__file__ = __file__
globals().update(mod.__dict__)
