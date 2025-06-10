import sys
import types
import pytest

# Provide minimal stubs for heavy dependencies before importing the wrapper
class _Signal:
    def __init__(self, *a, **k):
        self._slots = []
    def connect(self, slot):
        if hasattr(slot, "emit"):
            self._slots.append(slot.emit)
        else:
            self._slots.append(slot)
    def emit(self, *a, **k):
        for s in self._slots:
            s(*a, **k)

qtcore = types.SimpleNamespace(
    QObject=object,
    Signal=lambda *a, **k: _Signal(),
    QThread=object,
    QTimer=object,
)
qtwidgets = types.SimpleNamespace(
    QApplication=type(
        "QApplication",
        (),
        {"instance": staticmethod(lambda: None), "__init__": lambda self, *a, **k: None, "quit": lambda self: None},
    )
)

sys.modules.setdefault("PySide6", types.SimpleNamespace(QtCore=qtcore, QtWidgets=qtwidgets))
sys.modules.setdefault("PySide6.QtCore", qtcore)
sys.modules.setdefault("PySide6.QtWidgets", qtwidgets)

plotly_subplots = types.ModuleType("plotly.subplots")
plotly_subplots.make_subplots = lambda *a, **k: None
sys.modules["plotly.subplots"] = plotly_subplots

for mod in [
    "pandas",
    "numpy",
    "matplotlib",
    "matplotlib.pyplot",
    "seaborn",
    "plotly",
    "plotly.graph_objects",
    "plotly.express",
]:
    sys.modules.setdefault(mod, types.ModuleType(mod))

pd = sys.modules.setdefault("pandas", types.ModuleType("pandas"))
pd.DataFrame = object
pd.read_csv = lambda *a, **k: None
pd.to_datetime = lambda *a, **k: None

np = sys.modules.setdefault("numpy", types.ModuleType("numpy"))
np.ndarray = object
np.array = lambda *a, **k: None
np.log2 = lambda x: 1
np.sort = lambda x: x
np.cumsum = lambda x: [1]

scipy_stats = types.ModuleType("scipy.stats")
scipy_stats.entropy = lambda *a, **k: None
scipy_stats.chi2_contingency = lambda *a, **k: (None, None, None, None)
scipy = types.ModuleType("scipy")
scipy.stats = scipy_stats
sys.modules.setdefault("scipy", scipy)
sys.modules.setdefault("scipy.stats", scipy_stats)

from shared_tools.ui_wrappers.processors import corpus_balancer_wrapper as cbw
from PySide6.QtWidgets import QApplication

class DummyBalancer:
    def __init__(self, *a, **k):
        pass
    def analyze_corpus(self):
        return {}
    def calculate_balance_operations(self):
        return {"A": [], "B": []}
    def execute_domain_operations(self, domain, ops):
        return {"current_count": 1, "target_count": 2}
    def get_domains(self):
        return ["A", "B"]
    def set_target_allocations(self, allocs):
        self.allocs = allocs

class DummyWorker:
    progress = cbw.pyqtSignal(int, int, str)
    error = cbw.pyqtSignal(str)
    finished = cbw.pyqtSignal(dict)
    domain_processed = cbw.pyqtSignal(str, int, int)
    def __init__(self, balancer, domains, **kw):
        self.balancer = balancer
        self.domains = domains
    def start(self):
        try:
            self.progress.emit(0, 100, "analyze")
            stats = self.balancer.analyze_corpus()
            self.progress.emit(25, 100, "calc")
            ops = self.balancer.calculate_balance_operations()
            for d, o in ops.items():
                res = self.balancer.execute_domain_operations(d, o)
                DummyWorker.wrapper.domain_processed.emit(d, res.get("current_count", 0), res.get("target_count", 0))
            final = self.balancer.analyze_corpus()
            self.finished.emit({"initial_stats": stats, "balance_operations": ops, "final_stats": final})
        except Exception as e:
            self.error.emit(str(e))

class ErrorWorker(DummyWorker):
    def start(self):
        self.error.emit("boom")

@pytest.fixture
def dummy_config(tmp_path):
    return type("Cfg", (), {"corpus_dir": tmp_path})()

@pytest.fixture
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app
    app.quit()

def test_signals_emitted(qapp, monkeypatch, dummy_config):
    monkeypatch.setattr(cbw, "CorpusBalancer", DummyBalancer)
    monkeypatch.setattr(cbw, "CorpusBalancerWorker", DummyWorker)
    wrapper = cbw.CorpusBalancerWrapper(dummy_config)
    DummyWorker.wrapper = wrapper
    wrapper.domain_processed._slots.clear()
    wrapper.balance_completed._slots.clear()
    domains = []
    completed = []
    wrapper.domain_processed.connect(lambda d, c, t: domains.append((d, c, t)))
    wrapper.balance_completed.connect(lambda r: completed.append(r))
    wrapper.start_balancing()
    assert len(domains) == 2
    assert domains[0][0] == "A"
    assert completed
    assert not wrapper.is_running()

def test_error_handled(qapp, monkeypatch, dummy_config):
    monkeypatch.setattr(cbw, "CorpusBalancer", DummyBalancer)
    monkeypatch.setattr(cbw, "CorpusBalancerWorker", ErrorWorker)
    wrapper = cbw.CorpusBalancerWrapper(dummy_config)
    DummyWorker.wrapper = wrapper
    wrapper.error_occurred._slots.clear()
    ErrorWorker.error._slots.clear()
    errors = []
    wrapper.error_occurred.connect(lambda m: errors.append(m))
    wrapper.start_balancing()
    assert errors == ["boom"]
    assert not wrapper.is_running()


class MissingDomainBalancer(DummyBalancer):
    def analyze_corpus(self):
        return {
            "recommendations": [
                {
                    "action": "collect_data",
                    "description": "Collect data for missing domains: foo, bar",
                }
            ]
        }


class DummyCollector:
    def __init__(self):
        self.started = False
        self.search_terms = []

    def set_search_terms(self, terms):
        self.search_terms = terms

    def start(self):
        self.started = True


def test_collect_for_missing_domains_triggers_collectors(qapp, monkeypatch, dummy_config):
    monkeypatch.setattr(cbw, "CorpusBalancer", MissingDomainBalancer)
    wrapper = cbw.CorpusBalancerWrapper(dummy_config)
    c1 = DummyCollector()
    c2 = DummyCollector()
    wrapper.collector_wrappers = {"c1": c1, "c2": c2}

    wrapper.collect_for_missing_domains()

    assert c1.started and c2.started
    assert "foo" in c1.search_terms and "bar" in c1.search_terms
