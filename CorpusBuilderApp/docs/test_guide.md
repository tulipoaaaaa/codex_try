
# Test Execution Guide

This guide explains how to run the project's full test suite locally.

## 1. Install Requirements

Create and activate a Python 3.10+ virtual environment and install the base dependencies:

```bash
pip install -r CorpusBuilderApp/requirements.txt
```

Additional packages are required for running the tests, including Qt bindings and common pytest plugins:

```bash
pip install PySide6 pytest pytest-qt pytest-mock pytest-xdist pytest-cov nbformat pytesseract PyPDF2 selenium
```

## 2. Folder Requirements Per Test File

The table below lists all test modules and the directories or inputs they expect. Temporary folders are created automatically unless noted.

| Test File | Required Folder or Input | Description |
|-----------|-------------------------|-------------|
<<<<<<< HEAD
| corpusbuilder/tests/deprecated/test_annas_library_collector.py | AA_ACCOUNT_COOKIE env var, config/test_config.yaml | Downloads PDFs from Anna's Archive |
| corpusbuilder/tests/deprecated/test_api_collector.py | None (uses temp dirs) | Exercises generic API collector |
| corpusbuilder/tests/deprecated/test_arxiv_collector.py | Internet access, config/test_config.yaml | Collects papers from arXiv |
| corpusbuilder/tests/deprecated/test_arxiv_collector_projectconfig.py | config/master_config.yaml | Arxiv collector with ProjectConfig |
| corpusbuilder/tests/deprecated/test_bitmex_collector.py | mock_bitmex_research.html file | Parses BitMEX research posts |
| corpusbuilder/tests/deprecated/test_chunking_behavior.py | data/test_collect/chunking_tests/* | Chunking of CSV/py/ipynb/JSON files |
| corpusbuilder/tests/deprecated/test_domain_keyword_helper.py | None | Domain keyword helper logic |
| corpusbuilder/tests/deprecated/test_fred_collector.py | FRED_API_KEY env var, config/test_config.yaml | Downloads data from FRED |
| corpusbuilder/tests/deprecated/test_general_web_collector.py | None | Web scraping collector |
| corpusbuilder/tests/deprecated/test_github_collector.py | GitHub token env var, output dir | Clones GitHub repos |
| corpusbuilder/tests/deprecated/test_github_collector_projectconfig.py | master_config.yaml | GitHub collector with ProjectConfig |
| corpusbuilder/tests/deprecated/test_isda_collector.py | None | ISDA website collector |
| corpusbuilder/tests/deprecated/test_pdf_extractor.py | tests/pdf_extraction/test_pdfs/ | Runs real PDF extraction |
| corpusbuilder/tests/deprecated/test_processors.py | None | Processor integration tests |
| corpusbuilder/tests/deprecated/test_quantopian_collector.py | None | Quantopian data collector |
| corpusbuilder/tests/deprecated/test_repo_collector.py | config/test_config.yaml | Repository collector downloads |
| corpusbuilder/tests/deprecated/test_scidb_collector.py | SciDB credentials | SciDB data fetch |
| corpusbuilder/tests/deprecated/test_scidb_collector_projectconfig.py | master_config.yaml | SciDB collector with ProjectConfig |
| corpusbuilder/tests/deprecated/test_web_collector.py | None | Generic website scraping |
| corpusbuilder/tests/test_base_extractor.py | temp input/output dirs with sample text | Base extractor pipeline |
| corpusbuilder/tests/test_bitmex_collector.py | mock_bitmex_research.html | Old BitMEX collector |
| corpusbuilder/tests/test_collectors.py | temp dirs | Basic collector behaviours |
| corpusbuilder/tests/test_corpus_balance.py | temp corpus with _extracted & low_quality | Corpus balancing analysis |
| corpusbuilder/tests/test_extractor_utils.py | temp files | Utility functions |
| corpusbuilder/tests/test_quality_config.py | config/quality_control_config.json | Model config validation |
| corpusbuilder/tests/test_quality_control_config.py | config/quality_control_config.json | Quality control config validation |
=======
| CryptoCorpusBuilder/tests/deprecated/test_annas_library_collector.py | AA_ACCOUNT_COOKIE env var, config/test_config.yaml | Downloads PDFs from Anna's Archive |
| CryptoCorpusBuilder/tests/deprecated/test_api_collector.py | None (uses temp dirs) | Exercises generic API collector |
| CryptoCorpusBuilder/tests/deprecated/test_arxiv_collector.py | Internet access, config/test_config.yaml | Collects papers from arXiv |
| CryptoCorpusBuilder/tests/deprecated/test_arxiv_collector_projectconfig.py | config/master_config.yaml | Arxiv collector with ProjectConfig |
| CryptoCorpusBuilder/tests/deprecated/test_bitmex_collector.py | mock_bitmex_research.html file | Parses BitMEX research posts |
| CryptoCorpusBuilder/tests/deprecated/test_chunking_behavior.py | data/test_collect/chunking_tests/* | Chunking of CSV/py/ipynb/JSON files |
| CryptoCorpusBuilder/tests/deprecated/test_domain_config_wrapper.py | None | Domain config wrapper logic |
| CryptoCorpusBuilder/tests/deprecated/test_fred_collector.py | FRED_API_KEY env var, config/test_config.yaml | Downloads data from FRED |
| CryptoCorpusBuilder/tests/deprecated/test_general_web_collector.py | None | Web scraping collector |
| CryptoCorpusBuilder/tests/deprecated/test_github_collector.py | GitHub token env var, output dir | Clones GitHub repos |
| CryptoCorpusBuilder/tests/deprecated/test_github_collector_projectconfig.py | master_config.yaml | GitHub collector with ProjectConfig |
| CryptoCorpusBuilder/tests/deprecated/test_isda_collector.py | None | ISDA website collector |
| CryptoCorpusBuilder/tests/deprecated/test_pdf_extractor.py | tests/pdf_extraction/test_pdfs/ | Runs real PDF extraction |
| CryptoCorpusBuilder/tests/deprecated/test_processors.py | None | Processor integration tests |
| CryptoCorpusBuilder/tests/deprecated/test_quantopian_collector.py | None | Quantopian data collector |
| CryptoCorpusBuilder/tests/deprecated/test_repo_collector.py | config/test_config.yaml | Repository collector downloads |
| CryptoCorpusBuilder/tests/deprecated/test_scidb_collector.py | SciDB credentials | SciDB data fetch |
| CryptoCorpusBuilder/tests/deprecated/test_scidb_collector_projectconfig.py | master_config.yaml | SciDB collector with ProjectConfig |
| CryptoCorpusBuilder/tests/deprecated/test_web_collector.py | None | Generic website scraping |
| CryptoCorpusBuilder/tests/test_base_extractor.py | temp input/output dirs with sample text | Base extractor pipeline |
| CryptoCorpusBuilder/tests/test_bitmex_collector.py | mock_bitmex_research.html | Old BitMEX collector |
| CryptoCorpusBuilder/tests/test_collectors.py | temp dirs | Basic collector behaviours |
| CryptoCorpusBuilder/tests/test_corpus_balance.py | temp corpus with _extracted & low_quality | Corpus balancing analysis |
| CryptoCorpusBuilder/tests/test_extractor_utils.py | temp files | Utility functions |
| CryptoCorpusBuilder/tests/test_quality_config.py | config/quality_control_config.json | Model config validation |
| CryptoCorpusBuilder/tests/test_quality_control_config.py | config/quality_control_config.json | Quality control config validation |
>>>>>>> my-feature-branch
| tests/deprecated/test_corpus_management.py | temp corpus directories with sample file | Corpus manager UI integration |
| tests/deprecated/test_data_collectors.py | API keys env vars; network access | Collector behaviours across services |
| tests/deprecated/test_ui_integration.py | PySide6 installed | Basic UI widget integration |
| tests/integration/test_end_to_end_workflows.py | temp_workspace with downloads/processed/config subdirs | Full workflow simulation |
| tests/integration/test_error_handling.py | temp files | Error handling scenarios |
| tests/integration/test_multi_collector_flow.py | FRED & GitHub API tokens | Placeholder multi-collector flow |
| tests/integration/test_performance.py | none | Performance benchmarks |
| tests/integration/test_project_config_edges.py | project_config.yaml with edge cases | Placeholder config tests |
| tests/integration/test_security_critical.py | env vars for API keys, temp files | Credential and input validation |
| tests/test_domain_classifier_wrapper.py | none | Domain classifier wrapper logic |
| tests/test_file_browser.py | temp_dir with sample_files | File browser widget |
| tests/ui/test_collectors_tab.py | none (Qt required) | Collectors tab signals |
| tests/ui/test_collectors_tab_integration.py | Qt environment | Placeholder collectors tab integration |
| tests/ui/test_dashboard_tab.py | none (Qt required) | Dashboard tab widgets |
| tests/ui/test_full_activity_tab.py | none (Qt required) | Card widgets and styles |
| tests/unit/test_cli_consolidate.py | project config, CLI args | Placeholder consolidation CLI |
| tests/unit/test_corpus_manager.py | corpus folder | Placeholder corpus manager |
| tests/unit/test_quality_control_wrapper.py | none | Wrapper start/stop logic |

## 3. Running Tests

Execute the whole suite with:

```bash
pytest tests/ --maxfail=2 --disable-warnings
```

Generate coverage information:


```bash
coverage run -m pytest && coverage report -m
```


Skip Qt based tests on headless systems:


```bash
pytest -k "not qtbot"
```

## 4. Troubleshooting


| Issue | Resolution |
|-------|-----------|
| `ModuleNotFoundError: PySide6` | Ensure PySide6 is installed or run tests with the `-k "not qtbot"` flag. |
| `libEGL` or display errors | Use a virtual framebuffer (e.g. Xvfb) or skip UI tests. |
| `TesseractNotFoundError` | Install the Tesseract OCR engine and ensure `pytesseract` can locate it. |
| Selenium `WebDriverException` | Confirm the correct browser driver is installed and on your `PATH`. |
| Network timeouts during collector tests | Verify internet access or set the necessary API keys. |

