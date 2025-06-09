import sys
import types
from unittest.mock import patch, MagicMock
import pytest

# Stub heavy dependencies
class _DummySignal:
    def emit(self, *a, **k):
        pass

qtcore = types.SimpleNamespace(
    QObject=object,
    Signal=lambda *a, **k: _DummySignal(),
    QThread=object,
    QTimer=object,
    Slot=lambda *a, **k: lambda *a, **k: None,
    QDir=object,
)
qtwidgets = types.SimpleNamespace(QApplication=type('QApplication', (), {'instance': staticmethod(lambda: None)}))
sys.modules.setdefault('PySide6', types.SimpleNamespace(QtCore=qtcore, QtWidgets=qtwidgets))
sys.modules.setdefault('PySide6.QtCore', qtcore)
sys.modules.setdefault('PySide6.QtWidgets', qtwidgets)
for mod in ['fitz','pytesseract','cv2','numpy','matplotlib','matplotlib.pyplot','seaborn']:
    sys.modules.setdefault(mod, types.ModuleType(mod))
# Stub PIL
dummy_image_mod = types.ModuleType('PIL.Image')
class DummyImage: ...
dummy_image_mod.Image = DummyImage
dummy_enhance_mod = types.ModuleType('PIL.ImageEnhance')
class DummyEnhance: ...
dummy_enhance_mod.ImageEnhance = DummyEnhance
dummy_pil = types.ModuleType('PIL')
dummy_pil.Image = dummy_image_mod
dummy_pil.ImageEnhance = dummy_enhance_mod
sys.modules.setdefault('PIL', dummy_pil)
sys.modules.setdefault('PIL.Image', dummy_image_mod)
sys.modules.setdefault('PIL.ImageEnhance', dummy_enhance_mod)
if 'langdetect' not in sys.modules:
    langdetect = types.ModuleType('langdetect')
    langdetect.detect_langs = lambda *a, **k: []
    langdetect.LangDetectException = Exception
    sys.modules['langdetect'] = langdetect

from shared_tools.ui_wrappers.processors.deduplicator_wrapper import DeduplicatorWrapper
from shared_tools.ui_wrappers.processors.domain_classifier_wrapper import DomainClassifierWrapper
from shared_tools.ui_wrappers.processors.financial_symbol_processor_wrapper import FinancialSymbolProcessorWrapper
from shared_tools.ui_wrappers.processors.language_confidence_detector_wrapper import LanguageConfidenceDetectorWrapper
from shared_tools.ui_wrappers.processors.machine_translation_detector_wrapper import MachineTranslationDetectorWrapper

@pytest.mark.parametrize(
    "wrapper_cls,worker_path,processor_path,start_args",
    [
        (
            DeduplicatorWrapper,
            "shared_tools.ui_wrappers.processors.deduplicator_wrapper.DeduplicatorWorkerThread",
            "shared_tools.ui_wrappers.processors.deduplicator_wrapper.Deduplicator",
            (["f1"],),
        ),
        (
            DomainClassifierWrapper,
            "shared_tools.ui_wrappers.processors.domain_classifier_wrapper.DomainClassifierWorkerThread",
            "shared_tools.ui_wrappers.processors.domain_classifier_wrapper.DomainClassifier",
            ({"doc": {"text": "t"}},),
        ),
        (
            FinancialSymbolProcessorWrapper,
            "shared_tools.ui_wrappers.processors.financial_symbol_processor_wrapper.FinancialSymbolWorkerThread",
            "shared_tools.ui_wrappers.processors.financial_symbol_processor_wrapper.FinancialSymbolProcessor",
            (["f1"],),
        ),
        (
            LanguageConfidenceDetectorWrapper,
            "shared_tools.ui_wrappers.processors.language_confidence_detector_wrapper.LanguageDetectorWorkerThread",
            "shared_tools.ui_wrappers.processors.language_confidence_detector_wrapper.LanguageConfidenceDetector",
            (["f1"],),
        ),
        (
            MachineTranslationDetectorWrapper,
            "shared_tools.ui_wrappers.processors.machine_translation_detector_wrapper.MTDetectorWorkerThread",
            "shared_tools.ui_wrappers.processors.machine_translation_detector_wrapper.MachineTranslationDetector",
            (["f1"],),
        ),
    ],
)
def test_start_respects_enabled_flag(mock_project_config, wrapper_cls, worker_path, processor_path, start_args):
    with patch(processor_path):
        wrapper = wrapper_cls(mock_project_config)
    wrapper.processor = MagicMock()
    for attr in ["_on_progress_updated", "_on_status_updated", "_on_error"]:
        setattr(wrapper, attr, lambda *a, **k: None)

    wrapper.set_enabled(False)
    with patch(worker_path) as worker_cls:
        result = wrapper.start(*start_args)
        assert result is False
        worker_cls.assert_not_called()
        assert wrapper.is_running() is False

    wrapper.set_enabled(True)
    with patch(worker_path) as worker_cls:
        worker = MagicMock()
        worker_cls.return_value = worker
        result = wrapper.start(*start_args)
        assert result is True
        worker.start.assert_called_once()
        assert wrapper.is_running() is True
