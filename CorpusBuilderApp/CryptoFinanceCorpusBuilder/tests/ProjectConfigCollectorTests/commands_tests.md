# Collector Test Commands

## Individual Collector Tests

### SciDB Collector >tested
```powershell
# From project root
pytest CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests/test_scidb_collector.py -v

# From test directory
cd CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests
pytest test_scidb_collector.py -v
```

### Arxiv Collector >tested 
```powershell
# From project root
pytest CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests/test_arxiv_collector.py -v

# From test directory
cd CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests
pytest test_arxiv_collector.py -v
```

### GitHub Collector
```powershell
# From project root
pytest CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests/test_github_collector.py -v

# From test directory
cd CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests
pytest CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests/test_github_collector.py -v
```

### API Collector
```powershell
# From project root
pytest CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests/test_api_collector.py -v

# From test directory
cd CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests
pytest test_api_collector.py -v
```

### BitMEX Collector
```powershell
# From project root
pytest CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests/test_bitmex_collector.py -v

# From test directory
cd CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests
pytest test_bitmex_collector.py -v
```

### General Web Collector
```powershell
# From project root
pytest CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests/test_general_web_collector.py -v

# From test directory
cd CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests
pytest test_general_web_collector.py -v
```

### ISDA Collector
```powershell
# From project root
pytest CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests/test_isda_collector.py -v

# From test directory
cd CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests
pytest test_isda_collector.py -v
```

### FRED Collector
```powershell
# From project root
pytest CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests/test_fred_collector.py -v

# From test directory
cd CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests
pytest test_fred_collector.py -v
```

### Quantopian Collector
```powershell
# From project root
pytest CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests/test_quantopian_collector.py -v

# From test directory
cd CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests
pytest test_quantopian_collector.py -v
```

### Repo Collector
```powershell
# From project root
pytest CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests/test_repo_collector.py -v

# From test directory
cd CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests
pytest test_repo_collector.py -v
```

### Web Collector
```powershell
# From project root
pytest CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests/test_web_collector.py -v

# From test directory
cd CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests
pytest test_web_collector.py -v
```













## Run All Tests

### Using Test Runner
```powershell
# From project root
python CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests/run_collector_tests.py

# From test directory
cd CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests
python run_collector_tests.py
```

### Using Pytest Directly
```powershell
# From project root
pytest CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests/*.py -v

# From test directory
cd CryptoFinanceCorpusBuilder/tests/ProjectConfigCollectorTests
pytest *.py -v
```

## Notes
- Make sure you are in the correct directory or use the full path
- Ensure your virtual environment is activated
- These tests perform real downloads and API calls
- Test data will be saved to the test output directory specified in test_config.yaml
- Each test includes cleanup procedures to remove downloaded files after testing
