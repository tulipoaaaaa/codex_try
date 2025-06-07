# codex_try

[![Tests](https://github.com/OWNER/REPO/actions/workflows/test.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/test.yml)

## Installation

1. Create and activate a virtual environment (Python 3.8+ recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
2. Install the project dependencies:
   ```bash
   pip install -r CorpusBuilderApp/requirements.txt
   ```
   The requirements file contains all mandatory packages. If you plan to use the
   graphical interface, ensure that `PySide6` is installed. It is already listed
   in the requirements but can be installed separately with `pip install PySide6`.

## Running the Application

The main UI can be launched with:
```bash
python CorpusBuilderApp/app/main.py
```
For command-line operations, use the CLI helper:
```bash
python cli/execute_from_config.py --help
```

## Running Tests

The primary test suite lives in the tests/ directory and can be executed with:

bash
Copy
Edit
pytest -q
Some integration tests under CorpusBuilderApp/tests rely on optional packages
such as requests, PyMuPDF (for the fitz module), PySide6, and aiohttp.

These tests are skipped automatically when dependencies are missing.
To run the full suite with all optional tests, install the extras:

pip install requests PyMuPDF PySide6 aiohttp