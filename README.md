# codex_try


[![Tests](https://github.com/tulipoaaaaa/codex_try/actions/workflows/test.yml/badge.svg)](https://github.com/tulipoaaaaa/codex_try/actions/workflows/test.yml)

## Installation

Install the runtime requirements and then the development extras:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

These files are kept separate so the core application dependencies remain
lightweight.

## Testing

The test suite can run without PySide6 installed by setting the environment
variable `PYTEST_QT_STUBS=1`. This enables stubbed Qt classes so tests work in
headless or CI environments. Only limited behaviour is covered, so full UI
tests should still be executed locally with PySide6 available.

## Pre-push hook

A convenience script is provided at `scripts/pre_push.sh` to run linting and the
unit tests before code is pushed. Install the hook by linking it into your local
Git hooks directory:

```bash
ln -s ../../scripts/pre_push.sh .git/hooks/pre-push
```

The script will run `ruff` if it is installed, or fall back to `flake8`. It then
executes `pytest`. The push will be blocked if any of these steps fail.

## 🖥️ Running GUI on Linux or headless environments

Install Qt system dependencies:

```bash
sudo apt install libegl1 libxcb-icccm4 libxkbcommon-x11-0
```

Launch the application with offscreen rendering:

```bash
HEADLESS=1 python app/main.py
```

## License

This project is proprietary and all rights are reserved by Bored AI Labs.
To inquire about licensing, contact [legal@boredailabs.com](mailto:legal@boredailabs.com).

