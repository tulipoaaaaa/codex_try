# Test Command Guide

This guide provides all commands needed to run the test suite from the project root directory (`G:\codex\codex_try`).

## Prerequisites

Ensure you are in the project root directory and have activated the virtual environment:
```powershell
(venv312) PS G:\codex\codex_try>
```

## Running All Tests

To run the entire test suite:
```powershell
pytest
```

## Running Specific Test Categories

### Collectors Tests
```powershell
# Run all collector tests
pytest tests/collectors/

# Run specific collector test
pytest tests/collectors/test_collectors.py -k "test_arxiv_collector"
pytest tests/collectors/test_collectors.py -k "test_bitmex_collector"
pytest tests/collectors/test_collectors.py -k "test_fred_collector"
pytest tests/collectors/test_collectors.py -k "test_github_collector"
pytest tests/collectors/test_collectors.py -k "test_isda_collector"
pytest tests/collectors/test_collectors.py -k "test_quantopian_collector"
pytest tests/collectors/test_collectors.py -k "test_annas_library_collector"
pytest tests/collectors/test_collectors.py -k "test_scidb_collector"
```

### Processors Tests
```powershell
# Run all processor tests
pytest tests/processors/

# Run specific processor tests
pytest tests/processors/test_batch_nonpdf_extractor.py
pytest tests/processors/test_batch_text_extractor.py
pytest tests/processors/test_e2e_pipeline.py
```

### Corpus Management Tests
```powershell
# Run all corpus management tests
pytest tests/corpus/

# Run specific corpus tests
pytest tests/corpus/test_corpus_manager.py
pytest tests/corpus/test_corpus_balancer.py
```

### End-to-End Tests
```powershell
# Run all E2E tests
pytest tests/e2e/

# Run specific E2E test
pytest tests/e2e/test_pipeline_run.py
```

## Test Options

### Verbose Output
```powershell
pytest -v
```

### Show Print Statements
```powershell
pytest -s
```

### Run Tests in Parallel
```powershell
pytest -n auto
```

### Generate HTML Report
```powershell
pytest --html=report.html
```

### Stop on First Failure
```powershell
pytest -x
```

### Run Tests with Specific Markers
```powershell
pytest -m "collector"
pytest -m "processor"
pytest -m "corpus"
pytest -m "e2e"
```

## Common Test Patterns

### Run Tests Matching a Pattern
```powershell
pytest -k "pattern"
```

### Run Tests from a Specific File
```powershell
pytest path/to/test_file.py
```

### Run a Specific Test Function
```powershell
pytest path/to/test_file.py::test_function_name
```

## Debugging Tests

### Run with Debugger
```powershell
pytest --pdb
```

### Show Extra Test Summary
```powershell
pytest -ra
```

### Show Slowest Tests
```powershell
pytest --durations=10
```

## Test Coverage

### Generate Coverage Report
```powershell
pytest --cov=CorpusBuilderApp
```

### Generate HTML Coverage Report
```powershell
pytest --cov=CorpusBuilderApp --cov-report=html
```

## Example Test Runs

### Run All Collector Tests with Verbose Output
```powershell
pytest tests/collectors/ -v
```

### Run Processor Tests with Coverage
```powershell
pytest tests/processors/ --cov=CorpusBuilderApp.shared_tools.processors
```

### Run Corpus Tests with HTML Report
```powershell
pytest tests/corpus/ --html=corpus_report.html
```

### Run E2E Tests with Debugger
```powershell
pytest tests/e2e/ --pdb
```

## Notes

1. All test outputs will be created in their respective directories:
   - Collector tests: `G:/data/test_processors/collectors/`
   - Processor tests: `G:/data/test_processors/`
   - Corpus Manager tests: `G:/data/TEST_CORPUS_MANAGER/`
   - Corpus Balancer tests: `G:/data/test_corPUS_balancer/`
   - E2E tests: `G:/data/e2E/`

2. Ensure all required directories exist before running tests

3. Check test logs in the respective log directories for detailed information

4. For more information about test options, run:
```powershell
pytest --help
``` 