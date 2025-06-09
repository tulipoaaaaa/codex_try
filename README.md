# codex_try

[![Tests](https://github.com/OWNER/REPO/actions/workflows/test.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/test.yml)

## Testing

The test suite can run without PySide6 installed by setting the environment
variable `PYTEST_QT_STUBS=1`. This enables stubbed Qt classes so tests work in
headless or CI environments. Only limited behaviour is covered, so full UI
tests should still be executed locally with PySide6 available.
