import sys
import types
import pytest

pytestmark = pytest.mark.optional_dependency

# Ensure required Qt classes exist before importing the tab module
from PySide6 import QtWidgets, QtGui, QtCore

widget_names = [
    "QWidget", "QVBoxLayout", "QHBoxLayout", "QGroupBox", "QLabel",
    "QPushButton", "QProgressBar", "QSpinBox", "QTableWidget",
    "QTableWidgetItem", "QHeaderView", "QComboBox", "QCheckBox",
    "QMessageBox", "QSlider", "QSystemTrayIcon", "QMenu", "QStatusBar",
]
for name in widget_names:
    if not hasattr(QtWidgets, name):
        setattr(QtWidgets, name, type(name, (), {}))
        sys.modules["PySide6.QtWidgets"].__dict__[name] = getattr(QtWidgets, name)
if not hasattr(QtWidgets.QHeaderView, "ResizeMode"):
    QtWidgets.QHeaderView.ResizeMode = types.SimpleNamespace(Stretch=0)

for name in ["QColor", "QBrush", "QPalette", "QIcon", "QAction"]:
    if not hasattr(QtGui, name):
        setattr(QtGui, name, type(name, (), {}))
        sys.modules["PySide6.QtGui"].__dict__[name] = getattr(QtGui, name)

Qt = QtCore.Qt
if not hasattr(Qt, "ItemFlag"):
    Qt.ItemFlag = types.SimpleNamespace(ItemIsEditable=1)

from app.ui.tabs import balancer_tab as bt


class DummySignal:
    def __init__(self):
        self._slots = []
    def connect(self, slot):
        self._slots.append(slot)
    def emit(self, *args, **kwargs):
        for s in self._slots:
            s(*args, **kwargs)


class DummyWrapper:
    def __init__(self):
        self.start_called = False
        self.stop_called = False
    def set_quality_threshold(self, *a, **k):
        pass
    def set_balance_method(self, *a, **k):
        pass
    def set_auto_classify(self, *a, **k):
        pass
    def set_preserve_existing(self, *a, **k):
        pass
    def set_domain_targets(self, *a, **k):
        pass
    def start(self):
        self.start_called = True
    def stop(self):
        self.stop_called = True


class DummyNotificationManager:
    def __init__(self):
        self.notification_requested = DummySignal()
    def show_notification(self, title, message, notification_type="info", duration=5000):
        self.notification_requested.emit(title, message, notification_type, duration)


class DummyMessageBox:
    StandardButton = types.SimpleNamespace(Yes=0, No=1)
    @staticmethod
    def question(*a, **k):
        return DummyMessageBox.StandardButton.Yes


def _make_tab(monkeypatch):
    tab = bt.BalancerTab.__new__(bt.BalancerTab)
    tab.balancer = DummyWrapper()
    tab.notification_manager = DummyNotificationManager()
    tab.enable_notifications = types.SimpleNamespace(isChecked=lambda: True)
    tab.balance_btn = types.SimpleNamespace(clicked=DummySignal(), setEnabled=lambda v: None)
    tab.stop_btn = types.SimpleNamespace(clicked=DummySignal(), setEnabled=lambda v: None)
    tab.status_label = types.SimpleNamespace(setText=lambda *a, **k: None)
    tab.quality_threshold = types.SimpleNamespace(value=lambda: 70)
    tab.balance_method = types.SimpleNamespace(currentText=lambda: "Target Percentage")
    tab.auto_classify = types.SimpleNamespace(isChecked=lambda: True)
    tab.preserve_existing = types.SimpleNamespace(isChecked=lambda: True)
    tab.domain_table = types.SimpleNamespace(rowCount=lambda: 0, item=lambda *a, **k: None)
    tab.overall_progress = types.SimpleNamespace(setValue=lambda v: None)
    monkeypatch.setattr(bt, "QMessageBox", DummyMessageBox)
    return tab


def test_start_stop_notifications_emitted(monkeypatch):
    tab = _make_tab(monkeypatch)

    tab.balance_btn.clicked.connect(lambda: bt.BalancerTab.balance_corpus(tab))
    tab.stop_btn.clicked.connect(lambda: bt.BalancerTab.stop_balancing(tab))

    captured = []
    tab.notification_manager.notification_requested.connect(lambda *args: captured.append(args))

    tab.balance_btn.clicked.emit()
    tab.stop_btn.clicked.emit()

    assert tab.balancer.start_called
    assert tab.balancer.stop_called
    assert ("Corpus Balancing Started", "Beginning automatic corpus balancing...", "info", 5000) in captured
    assert ("Balancing Stopped", "Corpus balancing was stopped by user", "warning", 5000) in captured
