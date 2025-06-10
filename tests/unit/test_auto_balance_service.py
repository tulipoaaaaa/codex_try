import sys
import types
import pytest

pytestmark = pytest.mark.optional_dependency

# minimal Qt stubs
class _Signal:
    def __init__(self, *a, **k):
        self._slots = []
    def connect(self, slot):
        self._slots.append(slot)
    def emit(self, *a, **k):
        for s in self._slots:
            s(*a, **k)

qtcore_stub = types.SimpleNamespace(
    QObject=type("QObject", (), {}),
    QThread=type("QThread", (), {}),
    Signal=lambda *a, **k: _Signal(),
)

qtcore = sys.modules.setdefault("PySide6.QtCore", qtcore_stub)
sys.modules.setdefault("PySide6", types.SimpleNamespace(QtCore=qtcore))
qtcore.QObject.__init__ = lambda self, *a, **k: None
qtcore.QThread.__init__ = lambda self, *a, **k: None
qtcore.QThread.isRunning = lambda self: False
qtcore.QThread.start = lambda self: None
qtcore.QThread.wait = lambda self: None
qtcore.QThread.msleep = staticmethod(lambda x: None)

class DummySignal:
    def __init__(self):
        self._slots = []
    def connect(self, slot):
        self._slots.append(slot)
    def emit(self, *a, **k):
        for s in self._slots:
            s(*a, **k)

qtcore.Signal = lambda *a, **k: DummySignal()

from shared_tools.services import auto_balance_service as abs
abs.pyqtSignal = lambda *a, **k: DummySignal()

abs.QObject = type("QObject", (), {"__init__": lambda self, *a, **k: None})

class DummySignal:
    def __init__(self):
        self._slots = []
    def connect(self, slot):
        self._slots.append(slot)
    def emit(self, *a, **k):
        for s in self._slots:
            s(*a, **k)

class DummyThread:
    def __init__(self, wrapper, thresholds, check_interval=900, start_balancing=False, parent=None):
        self.wrapper = wrapper
        self.thresholds = thresholds
        self.start_balancing = start_balancing
        self.running = False
        self.progress = DummySignal()
        self.finished = DummySignal()
    def isRunning(self):
        return self.running
    def start(self):
        self.running = True
        self.run()
    def stop(self):
        self.running = False
    def wait(self):
        pass
    def run(self):
        while self.running:
            res = self.wrapper.analyze_corpus()
            domain = res.get('domain_analysis', {})
            missing = domain.get('missing_domains', [])
            ratio = domain.get('dominance_ratio', 1)
            if missing or ratio > self.thresholds.get('dominance_ratio', 5.0):
                self.wrapper.collect_for_missing_domains()
                if self.start_balancing:
                    self.wrapper.start_balancing()
            else:
                self.running = False
            break
        self.finished.emit()

class DummyWrapper:
    def __init__(self, results):
        self.results = list(results)
        self.collect_calls = 0
        self.balance_calls = 0
    def analyze_corpus(self):
        return self.results.pop(0)
    def collect_for_missing_domains(self):
        self.collect_calls += 1
    def start_balancing(self):
        self.balance_calls += 1

class DummyConfig:
    def get(self, key, default=None):
        return {
            'auto_balance.dominance_ratio': 5.0,
            'auto_balance.check_interval': 0,
            'auto_balance.start_balancing': True,
        }.get(key, default)


def test_auto_balance_collects_until_balanced(monkeypatch):
    monkeypatch.setattr(abs, 'AutoBalanceThread', DummyThread)
    results = [
        {'domain_analysis': {'missing_domains': ['foo'], 'dominance_ratio': 6.0}},
        {'domain_analysis': {'missing_domains': [], 'dominance_ratio': 1.0}},
    ]
    wrapper = DummyWrapper(results)
    svc = abs.AutoBalanceService(wrapper, DummyConfig())
    svc.start()
    assert wrapper.collect_calls == 1
    assert wrapper.balance_calls == 1
    assert svc._thread is None
