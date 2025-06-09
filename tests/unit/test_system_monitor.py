import importlib
import sys
import types

import pytest


class DummyTimer:
    def __init__(self, *args, **kwargs):
        self._callback = None
        self._interval = None
        self.active = False
        self.start_count = 0
        self.timeout = types.SimpleNamespace(connect=self._connect)

    def _connect(self, fn):
        self._callback = fn

    def start(self, interval):
        self._interval = interval
        self.start_count += 1
        self.active = True
        # Only trigger callback after the first start call
        if self.start_count > 1 and self._callback:
            self._callback()

    def stop(self):
        self.active = False

    def isActive(self):
        return self.active

    def interval(self):
        return self._interval


def test_system_metrics_emitted(monkeypatch, qapp):
    # Ensure a psutil module is available
    spec = importlib.util.find_spec("psutil")
    if spec is None:
        psutil = types.ModuleType("psutil")
        monkeypatch.setitem(sys.modules, "psutil", psutil)
    else:
        psutil = importlib.import_module("psutil")

    # Remove stubbed wrapper modules from previous tests if present
    stubbed = [
        "shared_tools.ui_wrappers.processors.batch_nonpdf_extractor_enhanced_wrapper",
        "shared_tools.ui_wrappers.processors.pdf_extractor_wrapper",
        "shared_tools.ui_wrappers.processors.base_extractor_wrapper",
        "shared_tools.ui_wrappers.processors.text_extractor_wrapper",
        "shared_tools.ui_wrappers.processors.batch_text_extractor_enhanced_prerefactor_wrapper",
        "shared_tools.ui_wrappers.processors.deduplicate_nonpdf_outputs_wrapper",
        "shared_tools.ui_wrappers.processors.deduplicator_wrapper",
        "shared_tools.ui_wrappers.processors.quality_control_wrapper",
        "shared_tools.ui_wrappers.processors.corruption_detector_wrapper",
        "shared_tools.ui_wrappers.processors.domain_classifier_wrapper",
        "shared_tools.ui_wrappers.processors.domainsmanager_wrapper",
        "shared_tools.ui_wrappers.processors.monitor_progress_wrapper",
        "shared_tools.ui_wrappers.processors.machine_translation_detector_wrapper",
        "shared_tools.ui_wrappers.processors.language_confidence_detector_wrapper",
        "shared_tools.ui_wrappers.processors.financial_symbol_processor_wrapper",
        "shared_tools.ui_wrappers.processors.chart_image_extractor_wrapper",
        "shared_tools.ui_wrappers.processors.formula_extractor_wrapper",
        "shared_tools.ui_wrappers.processors.corpus_balancer_wrapper",
    ]
    for mod in stubbed:
        sys.modules.pop(mod, None)
    import shared_tools.ui_wrappers.processors.pdf_extractor_wrapper as _pew
    import shared_tools.ui_wrappers.processors.text_extractor_wrapper as _tew
    importlib.reload(_pew)
    importlib.reload(_tew)

    monkeypatch.setattr(psutil, "cpu_percent", lambda: 12.3, raising=False)
    monkeypatch.setattr(psutil, "virtual_memory", lambda: types.SimpleNamespace(percent=45.6), raising=False)
    monkeypatch.setattr(psutil, "disk_usage", lambda p: types.SimpleNamespace(percent=78.9), raising=False)

    from PySide6 import QtCore

    class DummyQObject:
        def __init__(self, *a, **k):
            pass

    monkeypatch.setattr(QtCore, "QObject", DummyQObject, raising=False)
    monkeypatch.setattr(QtCore, "QTimer", DummyTimer, raising=False)

    from shared_tools.services.system_monitor import SystemMonitor

    monitor = SystemMonitor(interval_ms=100)
    monitor.stop()  # stop timer started during __init__

    received = []
    monitor.system_metrics.connect(lambda c, r, d: received.append((c, r, d)))

    monitor.start()

    assert received == [(12.3, 45.6, 78.9)]
