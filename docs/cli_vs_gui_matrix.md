# CLI vs GUI Feature Matrix

The table below outlines which parts of the project are available via command-line tools and which require the graphical interface.

| Feature | Command Line (`cli/execute_from_config.py` and `CorpusBuilderApp/cli.py`) | GUI Application |
|--------|:--:|:--:|
| Run collectors to download data | ✅ | ✅ |
| Run processing modules | ✅ | ✅ |
| Corpus balancing | ✅ | ✅ |
| Browse and edit corpus files | ❌ | ✅ |
| Real-time progress UI | ❌ | ✅ |
| Analytics dashboards | ❌ | ✅ |
| Theme and notification settings | ❌ | ✅ |
| Configuration management | ✅ (via YAML) | ✅ (via settings tabs) |
| View logs | ✅ (console) | ✅ (dedicated tab) |
| Start individual collectors with custom arguments | ✅ | ✅ |
| diff-corpus command | ✅ | ❌ |
| export-corpus command | ✅ | ✅ |
| Import corpus action | ❌ | ✅ |
| --matrix option | ✅ | ❌ |
| --version option | ✅ | ❌ |

Use the command-line tools for headless batch operations or automation scripts. Launch the GUI for an interactive experience with corpus management, analytics and visual feedback.
