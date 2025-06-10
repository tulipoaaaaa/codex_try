import sys
from pathlib import Path as _Path, Path
import types
from typing import List
import yaml



# Stub heavy dependencies required by imported modules
qtcore = types.SimpleNamespace(QObject=object, Signal=lambda *a, **k: lambda *a, **k: None, QThread=object, QTimer=object)
plotly_subplots = types.ModuleType("plotly.subplots")
plotly_subplots.make_subplots = lambda *a, **k: None
sys.modules["plotly.subplots"] = plotly_subplots
for mod in ["pandas", "numpy", "matplotlib", "matplotlib.pyplot", "seaborn", "plotly", "plotly.graph_objects", "plotly.express"]:
    sys.modules.setdefault(mod, types.ModuleType(mod))
pd = types.ModuleType("pandas"); pd.DataFrame = object; pd.read_csv = lambda *a, **k: None; sys.modules["pandas"] = pd
np = types.ModuleType("numpy"); np.ndarray = object; np.array = lambda *a, **k: None; sys.modules["numpy"] = np
scipy_stats = types.ModuleType("scipy.stats"); scipy_stats.entropy = lambda *a, **k: None; scipy_stats.chi2_contingency = lambda *a, **k: (None, None, None, None)
scipy = types.ModuleType("scipy"); scipy.stats = scipy_stats
sys.modules["scipy"] = scipy
sys.modules["scipy.stats"] = scipy_stats
sys.modules.setdefault("PySide6", types.SimpleNamespace(QtCore=qtcore))
sys.modules.setdefault("PySide6.QtCore", qtcore)
sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda *a, **k: None))

import pytest
import cli.execute_from_config as efc



def test_cli_argument_parsing():
    """Ensure CLI parses arguments correctly."""
    args = efc.parse_args(["--config", "cfg.yaml", "--run-all"])
    assert args.config == "cfg.yaml"
    assert args.run_all is True
    assert args.collect is False
    assert args.extract is False
    assert args.balance is False
    assert args.preview_only is False


def test_cli_consolidation_flow(tmp_path: Path, monkeypatch):
    """Run execute_from_config main with mocked modules."""
    config_data = {
        "enabled_collectors": ["foo"],
        "enabled_processors": ["pdf"],
        "processors": {"corpus_balancer": {"enabled": True}},
    }

    cfg_path = tmp_path / "config.yaml"
    with open(cfg_path, "w") as fh:
        yaml.safe_dump(config_data, fh)

    calls: List[str] = []

    monkeypatch.setattr(efc, "load_config", lambda p: config_data)
    monkeypatch.setattr(efc, "run_collectors", lambda c, n, p: calls.append("collect"))
    monkeypatch.setattr(efc, "run_processors", lambda c, n, p: calls.append("process"))
    monkeypatch.setattr(efc, "run_balancer", lambda c, p: calls.append("balance"))

    efc.main(["--config", str(cfg_path), "--run-all"])

    assert calls == ["collect", "process", "balance"]
