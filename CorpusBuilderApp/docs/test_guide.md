# Testing Guide

This document explains how to run the automated tests for the **CryptoFinance Corpus Builder** desktop application. Tests are designed for real usage scenarios, so most require actual network access and real files rather than mocks.

## 1. Installation Requirements

The following dependencies are required to execute the entire test suite:

```bash
# Application and library dependencies
pip install -r CorpusBuilderApp/requirements.txt

# Testing utilities and extras
pip install pytest pytest-qt pytest-mock pytest-xdist coverage nbformat pytesseract PyPDF2 selenium
```

System packages:

- `tesseract-ocr` – required for OCR tests (install via your package manager, e.g. `sudo apt install tesseract-ocr` on Debian/Ubuntu)
- Any shared libraries needed by PySide6 (e.g. `libEGL.so.1` on Linux)

## 2. Test Folder Requirements (Per Test Group)

| Test File | Folder or Setup Required | Purpose |
|-----------|-------------------------|---------|
| `test_pdf_extractor.py` | Directory containing non-password-protected `.pdf` files | Validates real PDF text extraction |
| `test_nonpdf_extractor_projectconfig.py` | Folder with `.txt`, `.html`, `.md`, `.json`, etc. | Verifies plain text and metadata extraction |
| `test_github_collector.py` | GitHub access token via config along with a search keyword | Requires internet, fetches real repositories |
| `test_arxiv_collector.py` | A search term in `project_config.yaml` | Downloads academic PDFs from arXiv |
| `test_annas_scidb_collector.py` | None | Real web scraper query |
| `test_corpus_manager.py` | Temporary or existing corpus folder containing documents | Exercises file copy/move/rename/delete |
| `test_corpus_balance.py` | Corpus folder with diverse `.meta` files | Measures balancing effectiveness |
| `test_cli_consolidate.py` | One or more `input_dir/` folders with `.jsonl` or `.txt` files | Validates CLI‑based merging logic |
| `test_logs_tab.py` | Log directory with `.log` or `.txt` files in the app logger format | Simulates real application logging |

Many tests recursively traverse directories, so deep folder structures are acceptable. Avoid using mock data unless the test explicitly indicates otherwise. If PySide6 is not available on your system, UI tests that rely on Qt should be skipped automatically (`pytest.skip`).

## 3. Running Tests

Basic run:

```bash
pytest tests/ --maxfail=3 --disable-warnings -q
```

With coverage:

```bash
coverage run -m pytest && coverage report -m
```

On headless systems you can skip the Qt UI tests:

```bash
pytest -k "not qtbot"
```

## 4. Troubleshooting

| Issue | Fix |
|-------|-----|
| `ImportError: libEGL.so.1 not found` | Install the missing system library required for PySide6 rendering |
| `ModuleNotFoundError: pytesseract` | `pip install pytesseract` |
| `TesseractNotFoundError` | Install the `tesseract-ocr` package (e.g. `sudo apt install tesseract-ocr`) |

For further questions about the testing workflow see the [Developer Guide](./DEVELOPER_GUIDE.md).
