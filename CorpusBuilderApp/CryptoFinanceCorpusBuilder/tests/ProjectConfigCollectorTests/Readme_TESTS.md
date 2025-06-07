# CryptoFinanceCorpusBuilder Collector Tests

## Overview

This test suite verifies the functionality of various data collectors in the CryptoFinanceCorpusBuilder project. The collectors are responsible for gathering financial and cryptocurrency-related data from different sources, ensuring proper integration with the project's configuration system, and maintaining data quality standards.

## Purpose

The primary goals of these tests are to:

1. **Verify Collector Integration**: Ensure each collector properly integrates with the `ProjectConfig` system, using the correct configuration parameters and output directories.

2. **Validate Data Collection**: Test that collectors can successfully download and process data from their respective sources.

3. **Check Data Quality**: Verify that collected data meets size and format requirements, and is properly classified into domains.

4. **Test Error Handling**: Ensure collectors gracefully handle invalid inputs and error conditions.

5. **Verify Cleanup**: Confirm that temporary files are properly cleaned up after testing.

## Test Structure

Each collector test file follows a consistent structure:

- **ProjectConfig Integration Test**: Verifies basic collector functionality with the project's configuration system
- **Specific Collection Tests**: Tests collecting data by specific identifiers (IDs, URLs, etc.)
- **Domain Classification Tests**: Verifies proper categorization of collected data
- **File Validation Tests**: Checks file integrity and metadata
- **Error Handling Tests**: Tests behavior with invalid inputs
- **Cleanup Tests**: Ensures proper cleanup of test files

## Available Collectors

The test suite covers the following collectors:

1. **SciDB Collector**: Collects scientific papers and research data
2. **Arxiv Collector**: Gathers papers from the Arxiv repository
3. **GitHub Collector**: Collects code repositories and documentation
4. **API Collector**: Gathers data from various financial APIs
5. **BitMEX Collector**: Collects cryptocurrency trading data
6. **General Web Collector**: Gathers data from general web sources
7. **ISDA Collector**: Collects ISDA documentation and standards
8. **FRED Collector**: Gathers Federal Reserve Economic Data
9. **Quantopian Collector**: Collects algorithmic trading strategies
10. **Repo Collector**: Gathers repository-specific data
11. **Web Collector**: Collects web-specific content

## Prerequisites

Before running the tests, ensure you have:

1. Python 3.8+ installed
2. Virtual environment activated
3. Required dependencies installed:
   ```bash
   pip install pytest requests beautifulsoup4 pandas numpy
   ```
4. Access to the test configuration file at `config/test_config.yaml`
5. Write permissions in the test output directory

## Running the Tests

### Directory Structure
```
corpusbuilder/
├── tests/
│   └── ProjectConfigCollectorTests/
│       ├── test_arxiv_collector.py
│       ├── test_scidb_collector.py
│       └── ... (other test files)
```

### Using the Test Runner

The simplest way to run all tests is using the test runner. First, navigate to the test directory:

```powershell
cd corpusbuilder/tests/ProjectConfigCollectorTests
```

Then run:
```powershell
python run_collector_tests.py
```

### Running Individual Tests

You have two options to run individual tests:

1. **From the test directory** (recommended):
   ```powershell
   # First, change to the test directory
   cd corpusbuilder/tests/ProjectConfigCollectorTests
   
   # Then run the test
   pytest test_arxiv_collector.py -v
   ```

2. **From the project root** (using full path):
   ```powershell
   pytest corpusbuilder/tests/ProjectConfigCollectorTests/test_arxiv_collector.py -v
   ```

### Running All Tests

To run all collector tests, first ensure you're in the test directory:

```powershell
cd corpusbuilder/tests/ProjectConfigCollectorTests
pytest *.py -v
```

## Test Output

The tests will:
1. Download real data from the respective sources
2. Save files to the test output directory
3. Verify file contents and metadata
4. Clean up downloaded files after testing

Test results will show:
- Number of tests run
- Number of passed/failed tests
- Detailed error messages for failed tests
- Duration of each test

## Test Configuration

Tests use the `test_config.yaml` file, which specifies:
- Test environment settings
- Output directories
- Collector-specific parameters
- Domain configurations

## Troubleshooting

Common issues and solutions:

1. **Test Not Found Error**:
   - Ensure you're in the correct directory (`corpusbuilder/tests/ProjectConfigCollectorTests`)
   - Or use the full path to the test file
   - Check that the test file exists in the directory

2. **Test Failures Due to Network Issues**:
   - Check your internet connection
   - Verify API keys and access tokens
   - Check rate limits for the data sources

3. **File Permission Errors**:
   - Ensure write permissions in the test output directory
   - Check if files are locked by other processes

4. **Configuration Errors**:
   - Verify `test_config.yaml` exists and is properly formatted
   - Check environment variables if required

## Contributing

When adding new tests:
1. Follow the existing test structure
2. Include proper cleanup procedures
3. Add appropriate error handling
4. Update this README if necessary

## Notes

- Tests perform real downloads and API calls
- Test data is saved to the test output directory
- Each test includes cleanup procedures
- Tests are designed to be independent and can be run in any order
