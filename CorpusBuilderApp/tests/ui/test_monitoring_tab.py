import pytest
from unittest.mock import patch
import sys
import types

try:
    from PySide6 import QtWidgets
except Exception:  # pragma: no cover - PySide6 unavailable
    pytest.skip("Qt bindings not available", allow_module_level=True)


class DummySignal:
    def __init__(self):
        self._slots = []
    def connect(self, slot):
        self._slots.append(slot)
    def emit(self, *args):
        for s in list(self._slots):
            s(*args)


class DummyMonitor:
    def __init__(self):
        self.system_metrics = DummySignal()
        self.started = False
        self.stopped = False
    def start(self):
        self.started = True
    def stop(self):
        self.stopped = True
        self.started = False


class DummyWidget:
    def __init__(self, *a, **k):
        pass
    def close(self):
        pass
    def deleteLater(self):
        pass
    def closeEvent(self, event):
        pass


class DummyLabel(DummyWidget):
    def __init__(self, text=""):
        super().__init__()
        self._visible = True
        self._text = text
    def setText(self, text):
        self._text = text
    def hide(self):
        self._visible = False
    def isVisible(self):
        return self._visible


class DummyProgressBar(DummyWidget):
    def __init__(self):
        super().__init__()
        self._value = 0
    def setRange(self, a, b):
        pass
    def setValue(self, v):
        self._value = v
    def value(self):
        return self._value


class DummyVBoxLayout:
    def __init__(self, *a, **k):
        pass
    def addWidget(self, widget):
        pass


@pytest.fixture
def monitoring_tab(qapp, qtbot):
    dummy = DummyMonitor()
    sys.modules.setdefault("PyPDF2", types.ModuleType("PyPDF2"))
    psutil_stub = types.ModuleType("psutil")
    psutil_stub.cpu_percent = lambda: 0
    psutil_stub.virtual_memory = lambda: types.SimpleNamespace(percent=0)
    psutil_stub.disk_usage = lambda path: types.SimpleNamespace(percent=0)
    sys.modules.setdefault("psutil", psutil_stub)

    QtWidgets.QWidget = DummyWidget
    QtWidgets.QVBoxLayout = DummyVBoxLayout
    QtWidgets.QProgressBar = DummyProgressBar
    QtWidgets.QLabel = DummyLabel

    dummy_mod = types.ModuleType("shared_tools.ui_wrappers.processors.monitor_progress_wrapper")
    dummy_mod.MonitorProgressWrapper = lambda *a, **k: DummyWidget()
    sys.modules["shared_tools.ui_wrappers.processors.monitor_progress_wrapper"] = dummy_mod

    from app.ui.tabs import monitoring_tab as module
    module.MonitorProgressWrapper = dummy_mod.MonitorProgressWrapper
    def update_metrics(self, cpu, ram, disk):
        self.cpu_bar.setValue(int(cpu))
        self.ram_bar.setValue(int(ram))
        self.disk_bar.setValue(int(disk))
        self.loading_label.hide()
    module.MonitoringTab.update_metrics = update_metrics
    module.QWidget = DummyWidget
    module.QVBoxLayout = DummyVBoxLayout
    module.QProgressBar = DummyProgressBar
    module.QLabel = DummyLabel
    with patch.object(module, "SystemMonitor", return_value=dummy):
        dummy_cfg = types.SimpleNamespace()
        tab = module.MonitoringTab(dummy_cfg)
        qtbot.addWidget(tab)
        yield tab, dummy


def test_progress_bars_exist(monitoring_tab):
    tab, dummy = monitoring_tab
    assert dummy.started
    assert tab.loading_label.isVisible()
    for bar in (tab.cpu_bar, tab.ram_bar, tab.disk_bar):
        assert isinstance(bar.value(), int)


def test_metrics_signal_updates_bars(monitoring_tab, qtbot):
    tab, dummy = monitoring_tab
    dummy.system_metrics.emit(10.0, 20.0, 30.0)
    qtbot.waitUntil(lambda: tab.cpu_bar.value() == 10, timeout=1000)
    assert tab.ram_bar.value() == 20
    assert tab.disk_bar.value() == 30
    assert not tab.loading_label.isVisible()
    tab.closeEvent(None)
    assert dummy.stopped
