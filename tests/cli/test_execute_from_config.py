import sys
from pathlib import Path as _Path, Path
import types
from typing import List
import yaml

# Add project root and package paths
root = _Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
sys.path.insert(1, str(root / "CorpusBuilderApp"))

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


class DummyWrapper:
    def __init__(self, name: str, log: List[str]):
        self.name = name
        self.log = log
        self.worker = types.SimpleNamespace(wait=lambda: None)

    def start(self):
        self.log.append(self.name)


class DummyBalancer:
    def __init__(self, log: List[str]):
        self.log = log
        self.worker = types.SimpleNamespace(wait=lambda: None)

    def rebalance(self):
        self.log.append("balancer")
        return {}


@pytest.fixture()
def sample_config(tmp_path: Path) -> Path:
    data = {
        "enabled_collectors": ["foo"],
        "enabled_processors": ["pdf"],
        "processors": {"corpus_balancer": {"enabled": True}},
    }
    path = tmp_path / "config.yaml"
    with open(path, "w") as f:
        yaml.safe_dump(data, f)
    return path


def test_run_all_sequence(monkeypatch, sample_config):
    log: List[str] = []
    monkeypatch.setattr(efc, "create_collector_wrapper", lambda name, cfg: DummyWrapper(f"collector-{name}", log))
    monkeypatch.setattr(efc, "create_processor_wrapper", lambda name, cfg: DummyWrapper(f"processor-{name}", log))
    monkeypatch.setattr(efc, "CorpusBalancerWrapper", lambda cfg: DummyBalancer(log))

    efc.main(["--config", str(sample_config), "--run-all"])

    assert log == ["collector-foo", "processor-pdf", "balancer"]


def test_collect_only(monkeypatch, sample_config):
    log: List[str] = []
    monkeypatch.setattr(efc, "create_collector_wrapper", lambda n, c: DummyWrapper(n, log))
    efc.main(["--config", str(sample_config), "--collect"])
    assert log == ["foo"]


def test_extract_only(monkeypatch, sample_config):
    log: List[str] = []
    monkeypatch.setattr(efc, "create_processor_wrapper", lambda n, c: DummyWrapper(n, log))
    efc.main(["--config", str(sample_config), "--extract"])
    assert log == ["pdf"]


def test_balance_only(monkeypatch, sample_config):
    log: List[str] = []
    monkeypatch.setattr(efc, "CorpusBalancerWrapper", lambda c: DummyBalancer(log))
    efc.main(["--config", str(sample_config), "--balance"])
    assert log == ["balancer"]


def test_preview_only(monkeypatch, sample_config, capsys):
    monkeypatch.setattr(efc, "create_collector_wrapper", lambda n, c: DummyWrapper(n, []))
    monkeypatch.setattr(efc, "create_processor_wrapper", lambda n, c: DummyWrapper(n, []))
    monkeypatch.setattr(efc, "CorpusBalancerWrapper", lambda c: DummyBalancer([]))
    efc.main(["--config", str(sample_config), "--run-all", "--preview-only"])
    captured = capsys.readouterr().out
    assert "collector:foo" in captured
    assert "processor:pdf" in captured
    assert "balancer:corpus_balancer" in captured


def test_error_when_no_collectors(monkeypatch, tmp_path):
    config_path = tmp_path / "c.yaml"
    yaml.safe_dump({"enabled_collectors": []}, open(config_path, "w"))

    with pytest.raises(RuntimeError):
        efc.main(["--config", str(config_path), "--collect"])
