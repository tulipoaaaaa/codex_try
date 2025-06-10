import sys
import types
from pathlib import Path
import yaml

# Minimal stubs for heavy dependencies
qtcore = types.SimpleNamespace(QObject=object, Signal=lambda *a, **k: lambda *a, **k: None, QThread=object, QTimer=object)
sys.modules.setdefault("PySide6", types.SimpleNamespace(QtCore=qtcore))
sys.modules.setdefault("PySide6.QtCore", qtcore)

for mod in ["pandas", "numpy", "matplotlib", "matplotlib.pyplot", "seaborn"]:
    sys.modules.setdefault(mod, types.ModuleType(mod))

from cli import execute_from_config as efc


def test_run_collectors_from_config(tmp_path, monkeypatch):
    cfg = {"enabled_collectors": ["foo"]}
    cfg_path = tmp_path / "c.yaml"
    yaml.safe_dump(cfg, open(cfg_path, "w"))
    calls = []
    monkeypatch.setattr(efc, "run_collectors", lambda c, n, p: calls.append(n))
    efc.main(["--config", str(cfg_path), "--collect"])
    assert calls == [["foo"]]
