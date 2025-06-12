import sys
import types

import pytest

try:
    from PySide6.QtCore import Qt, Signal as pyqtSignal
    from PySide6.QtWidgets import QApplication
    from PySide6 import QtWidgets

    class _Widget(QtWidgets.QWidget):
        def __init__(self, *a, **k):
            pass
    QtWidgets.QWidget = _Widget
except Exception:  # pragma: no cover - PySide6 unavailable
    pytest.skip("Qt bindings not available", allow_module_level=True)

# Stub heavy wrapper modules before importing the tab module
class_names = {
    'shared_tools.ui_wrappers.processors.batch_nonpdf_extractor_enhanced_wrapper': 'BatchNonPDFExtractorWrapper',
    'shared_tools.ui_wrappers.processors.pdf_extractor_wrapper': 'PDFExtractorWrapper',
    'shared_tools.ui_wrappers.processors.base_extractor_wrapper': 'BaseExtractorWrapper',
    'shared_tools.ui_wrappers.processors.text_extractor_wrapper': 'TextExtractorWrapper',
    'shared_tools.ui_wrappers.processors.batch_text_extractor_enhanced_prerefactor_wrapper': 'BatchTextExtractorEnhancedPrerefactorWrapper',
    'shared_tools.ui_wrappers.processors.deduplicate_nonpdf_outputs_wrapper': 'DeduplicateNonPDFOutputsWrapper',
    'shared_tools.ui_wrappers.processors.deduplicator_wrapper': 'DeduplicatorWrapper',
    'shared_tools.ui_wrappers.processors.quality_control_wrapper': 'QualityControlWrapper',
    'shared_tools.ui_wrappers.processors.corruption_detector_wrapper': 'CorruptionDetectorWrapper',
    'shared_tools.ui_wrappers.processors.domain_classifier_wrapper': 'DomainClassifierWrapper',
    'shared_tools.ui_wrappers.processors.domainsmanager_wrapper': 'DomainsManagerWrapper',
    'shared_tools.ui_wrappers.processors.monitor_progress_wrapper': 'MonitorProgressWrapper',
    'shared_tools.ui_wrappers.processors.machine_translation_detector_wrapper': 'MachineTranslationDetectorWrapper',
    'shared_tools.ui_wrappers.processors.language_confidence_detector_wrapper': 'LanguageConfidenceDetectorWrapper',
    'shared_tools.ui_wrappers.processors.financial_symbol_processor_wrapper': 'FinancialSymbolProcessorWrapper',
    'shared_tools.ui_wrappers.processors.chart_image_extractor_wrapper': 'ChartImageExtractorWrapper',
    'shared_tools.ui_wrappers.processors.formula_extractor_wrapper': 'FormulaExtractorWrapper',
    'shared_tools.ui_wrappers.processors.corpus_balancer_wrapper': 'CorpusBalancerWrapper',
}
for name, cls_name in class_names.items():
    mod = types.ModuleType(name)
    setattr(mod, cls_name, type(cls_name, (), {}))
    sys.modules[name] = mod

# Stub NotificationManager to avoid heavy UI dependencies
nm_mod = types.ModuleType('app.ui.tabs.corpus_manager_tab')
nm_mod.NotificationManager = type('NotificationManager', (), {'__init__': lambda self, *a, **k: None, 'add_notification': lambda *a, **k: None})
sys.modules['app.ui.tabs.corpus_manager_tab'] = nm_mod

from app.ui.tabs import processors_tab as pt


class DummyIconManager:
    def get_icon_path(self, *a, **k):
        return None

class DummyNotificationManager:
    def __init__(self, *a, **k):
        pass
    def add_notification(self, *a, **k):
        pass


class DummyWrapper:
    """Minimal processor wrapper used for UI workflow tests."""

    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    batch_completed = pyqtSignal(dict)

    def __init__(self, *a, **k):
        self.started = False
        self.stopped = False

    def set_ocr_enabled(self, *a, **k):
        pass

    def set_table_extraction(self, *a, **k):
        pass

    def set_formula_extraction(self, *a, **k):
        pass

    def set_worker_threads(self, *a, **k):
        pass

    def start_batch_processing(self, files):
        self.started = True
        # In real implementation this would spawn a worker

    def stop(self):
        self.stopped = True


class WorkflowTab(pt.ProcessorsTab):
    """Subclass exposing processing signals for testing."""

    processing_started = pyqtSignal(str)
    processing_finished = pyqtSignal(str, bool)

    def start_pdf_processing(self):
        self.processing_started.emit("pdf")
        super().start_pdf_processing()

    def on_pdf_batch_completed(self, results):
        super().on_pdf_batch_completed(results)

@pytest.fixture
def processors_tab(qtbot, mock_project_config, monkeypatch):
    monkeypatch.setattr(pt, "IconManager", DummyIconManager)
    monkeypatch.setattr(pt, "NotificationManager", DummyNotificationManager)
    # Patch all wrapper classes used by init_processors to DummyWrapper
    monkeypatch.setattr(pt, "PDFExtractorWrapper", DummyWrapper)
    monkeypatch.setattr(pt, "TextExtractorWrapper", DummyWrapper)
    monkeypatch.setattr(pt, "CorpusBalancerWrapper", DummyWrapper)
    monkeypatch.setattr(pt, "DeduplicatorWrapper", DummyWrapper)
    monkeypatch.setattr(pt, "DomainClassifierWrapper", DummyWrapper)
    monkeypatch.setattr(pt, "FormulaExtractorWrapper", DummyWrapper)
    monkeypatch.setattr(pt, "ChartImageExtractorWrapper", DummyWrapper)
    monkeypatch.setattr(pt, "QualityControlWrapper", DummyWrapper)
    monkeypatch.setattr(pt, "LanguageConfidenceDetectorWrapper", DummyWrapper)
    monkeypatch.setattr(pt, "MachineTranslationDetectorWrapper", DummyWrapper)
    monkeypatch.setattr(pt, "FinancialSymbolProcessorWrapper", DummyWrapper)

    tab = WorkflowTab(mock_project_config)
    qtbot.addWidget(tab)
    return tab


def test_pdf_processing_workflow(processors_tab, qtbot):
    processors_tab.pdf_file_list.addItem("file1.pdf")

    started = []
    finished = []
    processors_tab.processing_started.connect(lambda n: started.append(n))
    processors_tab.processing_finished.connect(lambda n, s: finished.append((n, s)))

    qtbot.mouseClick(processors_tab.pdf_start_btn, Qt.MouseButton.LeftButton)

    wrapper = processors_tab.processor_wrappers["pdf"]
    assert wrapper.started
    assert not processors_tab.pdf_start_btn.isEnabled()
    assert processors_tab.pdf_stop_btn.isEnabled()
    assert started == ["pdf"]

    processors_tab.on_pdf_batch_completed({"success_count": 1, "fail_count": 0})

    assert processors_tab.pdf_start_btn.isEnabled()
    assert not processors_tab.pdf_stop_btn.isEnabled()
    assert finished == [("pdf", True)]
