import hashlib
import logging
from pathlib import Path
import sys
import types

# Stub heavy PDF libraries before importing PDFExtractor
dummy = types.ModuleType("dummy")
sys.modules.setdefault("PyPDF2", dummy)
sys.modules.setdefault("fitz", dummy)
camelot_mod = types.ModuleType("camelot")
camelot_mod.read_pdf = lambda *a, **k: []
sys.modules.setdefault("camelot", camelot_mod)
pandas_mod = types.ModuleType("pandas")
pandas_mod.DataFrame = object
sys.modules.setdefault("pandas", pandas_mod)
pdfminer_high = types.ModuleType("pdfminer.high_level")
pdfminer_high.extract_text = lambda *a, **k: ""
pdfminer_high.extract_pages = lambda *a, **k: []
sys.modules.setdefault("pdfminer.high_level", pdfminer_high)
pdfminer_layout = types.ModuleType("pdfminer.layout")
pdfminer_layout.LTTextContainer = object
pdfminer_layout.LTChar = object
pdfminer_layout.LTFigure = object
sys.modules.setdefault("pdfminer.layout", pdfminer_layout)

from shared_tools.processors.pdf_extractor import PDFExtractor


class DummyExtractor(PDFExtractor):
    def __init__(self):
        # bypass BaseExtractor
        self.logger = logging.getLogger("dummy")

    def extract_tables(self, file_path: Path):
        return []

    def extract_formulas(self, text: str):
        return []

    def _extract_with_pypdf2(self, fp: Path) -> str:
        return "short"

    def _extract_with_pymupdf(self, fp: Path) -> str:
        return "this is longer text"

    def _extract_with_pdfminer(self, fp: Path) -> str:
        return ""


def test_extract_text_adds_sha256_and_method(tmp_path):
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"content")
    ext = DummyExtractor()
    text, meta = ext.extract_text(pdf)
    assert meta["sha256"] == hashlib.sha256(b"content").hexdigest()
    assert meta["selected_text_method"] == "pymupdf"
