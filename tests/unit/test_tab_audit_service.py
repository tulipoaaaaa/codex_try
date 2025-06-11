import os
import pytest

# Ensure Qt is stubbed
os.environ.setdefault("PYTEST_QT_STUBS", "1")

pytestmark = pytest.mark.optional_dependency

from shared_tools.services.tab_audit_service import TabAuditService

# Patch TabAuditService.__init__ to avoid QObject dependency in stubs
def _patched_init(self, main_window, parent=None):
    self.main_window = main_window
    self.logger = __import__('logging').getLogger(self.__class__.__name__)

TabAuditService.__init__ = _patched_init

try:  # Ensure QObject in stubs accepts an initializer
    from PySide6 import QtCore
    if getattr(QtCore, "QObject", object) is object:
        class DummyQObject:
            def __init__(self, *a, **k):
                pass

        QtCore.QObject = DummyQObject
except Exception:  # pragma: no cover - best effort if stubs are missing
    pass


class DummySignal:
    def __init__(self):
        self._slots = []

    def connect(self, slot):
        self._slots.append(slot)

    def receivers(self):
        return len(self._slots)


class DummyCollectorsTab:
    def __init__(self):
        self.collection_started = DummySignal()
        self.collection_finished = DummySignal()


class DummyProcessorsTab:
    def __init__(self):
        self.processing_started = DummySignal()
        self.processing_finished = DummySignal()


class DummyDashboardTab:
    def __init__(self):
        self.view_all_activity_requested = DummySignal()
        self.rebalance_requested = DummySignal()


class DummyConfigurationTab:
    def __init__(self):
        self.configuration_saved = DummySignal()


class DummyBalancer:
    def __init__(self):
        self.balance_completed = DummySignal()


class DummyBalancerTab:
    def __init__(self):
        self.balancer = DummyBalancer()


class DummyMainWindow:
    def __init__(self):
        self.dashboard_tab = DummyDashboardTab()
        self.collectors_tab = DummyCollectorsTab()
        self.processors_tab = DummyProcessorsTab()
        self.corpus_manager_tab = object()
        self.balancer_tab = DummyBalancerTab()
        self.analytics_tab = object()
        self.configuration_tab = DummyConfigurationTab()
        self.logs_tab = object()
        self.full_activity_tab = None

        # Connect signals except one to trigger an audit warning
        self.collectors_tab.collection_started.connect(self.on_collection_started)
        self.collectors_tab.collection_finished.connect(self.on_collection_finished)
        self.processors_tab.processing_finished.connect(self.on_processing_finished)
        # processing_started intentionally left unconnected
        self.dashboard_tab.view_all_activity_requested.connect(self.show_full_activity_tab)
        self.dashboard_tab.rebalance_requested.connect(self.on_rebalance_requested)
        self.configuration_tab.configuration_saved.connect(self.on_config_saved)
        self.balancer_tab.balancer.balance_completed.connect(self.on_balance_completed)

        self.tab_registry = {
            "dashboard_tab": self.dashboard_tab,
            "collectors_tab": self.collectors_tab,
            "processors_tab": self.processors_tab,
            "corpus_manager_tab": self.corpus_manager_tab,
            "balancer_tab": self.balancer_tab,
            "analytics_tab": self.analytics_tab,
            "configuration_tab": self.configuration_tab,
            "logs_tab": self.logs_tab,
            "full_activity_tab": self.full_activity_tab,
        }

    def on_collection_started(self, *a, **k):
        pass

    def on_collection_finished(self, *a, **k):
        pass

    def on_processing_started(self, *a, **k):
        pass

    def on_processing_finished(self, *a, **k):
        pass

    def show_full_activity_tab(self, *a, **k):
        pass

    def on_rebalance_requested(self, *a, **k):
        pass

    def on_config_saved(self, *a, **k):
        pass

    def on_balance_completed(self, *a, **k):
        pass


def test_audit_detects_missing_connection(qapp):
    mw = DummyMainWindow()
    service = TabAuditService(mw)
    issues = service.audit()

    assert any(
        "DummyProcessorsTab.processing_started not connected (on_processing_started)" in msg
        for msg in issues
    )
