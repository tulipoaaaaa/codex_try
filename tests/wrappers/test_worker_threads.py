import types
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest

# Add project paths for imports
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
sys.path.insert(1, str(root / "CorpusBuilderApp"))

# Stub heavy third-party dependencies
dummy = types.ModuleType("dummy")
sys.modules.setdefault("PyPDF2", dummy)
sys.modules.setdefault("fitz", dummy)
pdfminer_high = types.ModuleType("pdfminer.high_level")
pdfminer_high.extract_text = lambda *a, **k: ""
pdfminer_high.extract_pages = lambda *a, **k: []
sys.modules.setdefault("pdfminer.high_level", pdfminer_high)
pdfminer_layout = types.ModuleType("pdfminer.layout")
pdfminer_layout.LTTextContainer = object
pdfminer_layout.LTChar = object
pdfminer_layout.LTFigure = object
sys.modules.setdefault("pdfminer.layout", pdfminer_layout)

# Provide dummy extractor modules to avoid heavy dependencies
dummy_pdf_extractor_mod = types.ModuleType("shared_tools.processors.pdf_extractor")
class DummyPDFExtractor:
    def __init__(self, *a, **k):
        self.num_workers = k.get("num_workers")
dummy_pdf_extractor_mod.PDFExtractor = DummyPDFExtractor
sys.modules.setdefault("shared_tools.processors.pdf_extractor", dummy_pdf_extractor_mod)

dummy_text_extractor_mod = types.ModuleType("shared_tools.processors.text_extractor")
class DummyTextExtractor:
    def __init__(self, *a, **k):
        self.num_workers = k.get("num_workers")
dummy_text_extractor_mod.TextExtractor = DummyTextExtractor
sys.modules.setdefault("shared_tools.processors.text_extractor", dummy_text_extractor_mod)

qtcore = types.SimpleNamespace(
    QObject=object,
    Signal=lambda *a, **k: lambda *a, **k: None,
    QThread=object,
    QTimer=object,
)
sys.modules.setdefault("PySide6", types.SimpleNamespace(QtCore=qtcore))
sys.modules.setdefault("PySide6.QtCore", qtcore)

from shared_tools.ui_wrappers.processors.pdf_extractor_wrapper import PDFExtractorWrapper
from shared_tools.ui_wrappers.processors.text_extractor_wrapper import TextExtractorWrapper


def test_pdf_worker_threads(tmp_path):
    cfg = SimpleNamespace(
        raw_data_dir=tmp_path / "raw",
        pdf_extracted_dir=tmp_path / "pdf",
    )
    wrapper = PDFExtractorWrapper(cfg)
    wrapper.set_worker_threads(6)
    extractor = wrapper._create_target_object()
    assert extractor.num_workers == 6
    wrapper.set_worker_threads(2)
    assert extractor.num_workers == 2


def test_text_worker_threads(tmp_path):
    cfg = SimpleNamespace(
        raw_data_dir=tmp_path / "raw",
        nonpdf_extracted_dir=tmp_path / "text",
    )
    wrapper = TextExtractorWrapper(cfg)
    wrapper.set_worker_threads(8)
    extractor = wrapper._create_target_object()
    assert extractor.num_workers == 8
    wrapper.set_worker_threads(3)
    assert extractor.num_workers == 3
