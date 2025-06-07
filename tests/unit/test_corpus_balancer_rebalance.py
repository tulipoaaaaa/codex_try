import sys
import json
from pathlib import Path
import types

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
sys.path.insert(1, str(root / "CorpusBuilderApp"))

# Stub heavy dependencies
for mod in ["pandas", "numpy", "matplotlib", "matplotlib.pyplot", "seaborn", "plotly", "plotly.graph_objects", "plotly.express", "scipy", "scipy.stats"]:
    sys.modules.setdefault(mod, types.ModuleType(mod))
qtcore = types.SimpleNamespace(QObject=object, Signal=lambda *a, **k: lambda *a, **k: None)
sys.modules.setdefault("PySide6", types.SimpleNamespace(QtCore=qtcore))
sys.modules.setdefault("PySide6.QtCore", qtcore)

from shared_tools.processors.corpus_balancer import CorpusAnalyzer, CorpusRebalancer


def setup_balancer(tmp_path: Path, stats_data: dict):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    stats_file = corpus / "corpus_stats.json"
    with open(stats_file, "w") as f:
        json.dump(stats_data, f)
    cfg = {
        "domains": {
            "foo": {"target_weight": 0.5, "min_documents": 3},
            "bar": {"target_weight": 0.5, "min_documents": 3},
        }
    }
    analyzer = CorpusAnalyzer(str(corpus), project_config=cfg)
    return CorpusRebalancer(analyzer), stats_file


def test_should_rebalance_true(tmp_path):
    balancer, _ = setup_balancer(tmp_path, {"domain_distribution": {"foo": 1, "bar": 9}, "total_documents": 10})
    assert balancer.should_rebalance() is True


def test_should_rebalance_false(tmp_path):
    balancer, stats_file = setup_balancer(tmp_path, {"domain_distribution": {"foo": 5, "bar": 5}, "total_documents": 10})
    assert balancer.should_rebalance() is False
