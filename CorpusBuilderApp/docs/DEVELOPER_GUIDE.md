# Developer Guide: CryptoFinance Corpus Builder

## Table of Contents

1. Project Structure
2. Architecture Overview
3. Adding Collectors/Processors
4. UI Development
5. Testing
6. Coding Standards
7. Contributing

---

## Project Structure

```
CryptoFinanceCorpusBuilder/
├── app/                  # Main application code
│   ├── main.py
│   ├── main_window.py
│   └── ui/
│       ├── tabs/
│       ├── widgets/
│       └── dialogs/
├── shared_tools/
│   ├── collectors/
│   ├── processors/
│   ├── ui_wrappers/
│   └── project_config.py
├── tests/
├── docs/
├── requirements.txt
├── setup.py
└── launch_app.bat
```

---

## Architecture Overview

See [ARCHITECTURE.md](./ARCHITECTURE.md) for diagrams and data flow.

---

## Adding Collectors/Processors

- Create a new class in `shared_tools/collectors/` or `shared_tools/processors/`.
- Add a UI wrapper in `shared_tools/ui_wrappers/`.
- Register in the factory function.
- Add tests in `tests/`.

---

## UI Development

- Use PyQt6 widgets and layouts.
- Follow the QSS style guide for consistency.
- Use `IconManager` for all icons.

---

## Testing

- Unit tests: `pytest tests/unit/`
- Integration tests: `pytest tests/integration/`
- UI tests: `pytest tests/ui/ --qt-api pyqt6`

---

## Coding Standards

- Format code with Black.
- Use type hints and docstrings.
- Follow PEP8 and project conventions.

---

## Contributing

- Fork, branch, commit, and PR as per [README.md](./README.md#contributing).
