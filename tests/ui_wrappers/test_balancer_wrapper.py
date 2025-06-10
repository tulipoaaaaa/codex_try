import sys
import types
import pytest

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

pytest.importorskip("PySide6")

# Stub heavy dependencies used during module import
for mod_name in [
    "pandas",
    "numpy",
    "matplotlib",
    "matplotlib.pyplot",
    "seaborn",
    "yaml",
    "plotly",
    "plotly.graph_objects",
    "plotly.express",
    "plotly.subplots",
    "scipy",
    "scipy.stats",
]:
    sys.modules.setdefault(mod_name, types.ModuleType(mod_name))

sys.modules.setdefault("yaml", types.ModuleType("yaml"))

plotly_subplots = types.ModuleType("plotly.subplots")
plotly_subplots.make_subplots = lambda *a, **k: None
sys.modules["plotly.subplots"] = plotly_subplots
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
sys.modules["scipy.stats"] = scipy_stats

from shared_tools.ui_wrappers.processors import corpus_balancer_wrapper as cbw
cbw.pyqtSignal = lambda *a, **k: _Signal()

class DummyBalancer:
    def __init__(self, *a, **k):
        pass
    def analyze_corpus(self):
        return {}
    def calculate_balance_operations(self):
        return {"A": []}
    def execute_domain_operations(self, domain, ops):
        return {"current_count": 1, "target_count": 1}
    def get_domains(self):
        return ["A"]

class DummyWorker:
    progress = cbw.pyqtSignal(int, int, str)
    error = cbw.pyqtSignal(str)
    finished = cbw.pyqtSignal(dict)
    domain_processed = cbw.pyqtSignal(str, int, int)
    def __init__(self, balancer, domains, **kw):
        self.balancer = balancer
        self.domains = domains
    def start(self):
        DummyWorker.domain_processed.emit("A", 1, 1)
        DummyWorker.finished.emit({"done": True})


def test_emits_signals(monkeypatch, tmp_path):
    monkeypatch.setattr(cbw, "CorpusBalancer", DummyBalancer)
    monkeypatch.setattr(cbw, "CorpusBalancerWorker", DummyWorker)

    wrapper = cbw.CorpusBalancerWrapper(types.SimpleNamespace(corpus_dir=tmp_path), test_mode=True)
    seen_domains = []
    seen_results = []
    wrapper.domain_processed.connect(lambda d, c, t: seen_domains.append((d, c, t)))
    wrapper.balance_completed.connect(lambda r: seen_results.append(r))

    wrapper.start_balancing()

    assert seen_domains == [("A", 1, 1)]
    assert seen_results
