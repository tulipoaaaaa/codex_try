import sys
import types

# Ensure package path
sys.path.insert(0, 'CorpusBuilderApp')

from PySide6.QtWidgets import QApplication

# Stub heavy wrapper modules before importing the tab module
class_names = {
    'shared_tools.ui_wrappers.processors.batch_nonpdf_extractor_enhanced_wrapper': 'BatchNonPDFExtractorEnhancedWrapper',
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
nm_mod.NotificationManager = type('NotificationManager', (), {})
sys.modules['app.ui.tabs.corpus_manager_tab'] = nm_mod

from app.ui.tabs import processors_tab as pt

class DummyIconManager:
    def get_icon_path(self, *a, **k):
        return None


def test_selected_domain_button_connected(monkeypatch):
    monkeypatch.setattr(pt, "IconManager", DummyIconManager)
    app = QApplication.instance() or QApplication([])

    tab = pt.ProcessorsTab.__new__(pt.ProcessorsTab)
    tab.project_config = None
    tab.processor_wrappers = {}
    # Call the method under test
    pt.ProcessorsTab.create_advanced_tab(tab)

    assert hasattr(tab.apply_to_selected_btn.clicked, "_slots")
    assert tab.apply_selected_domain in tab.apply_to_selected_btn.clicked._slots
