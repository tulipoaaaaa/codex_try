# codex_try

[![Tests](https://github.com/OWNER/REPO/actions/workflows/test.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/test.yml)

## Running tests

The primary test suite lives in the `tests/` directory and can be executed with:

```bash
pytest -q
```

Additional integration tests under `CorpusBuilderApp/tests` rely on optional
packages such as `requests`, `PyMuPDF` (providing the `fitz` module),
`PySide6` and `aiohttp`. These tests are skipped automatically when the
dependencies are missing. To run the entire suite, install the extras:

```bash
pip install requests PyMuPDF PySide6 aiohttp
```
