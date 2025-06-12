# Test Suite User Guide

This guide provides a comprehensive overview of the test suite structure and functionality.

## Directory Structure

```
tests/
├── collectors/              # Collector-specific tests
│   ├── config_yaml/        # YAML configurations for collectors
│   └── test_collectors.py  # Collector test implementations
├── processors/             # Processor-specific tests
│   ├── test_batch_nonpdf_extractor.py
│   ├── test_batch_text_extractor.py
│   └── test_e2e_pipeline.py
├── corpus/                 # Corpus management tests
│   ├── test_corpus_manager.py
│   └── test_corpus_balancer.py
└── e2e/                    # End-to-end tests
    └── test_pipeline_run.py
```

## Test Components

### 1. Collectors Tests

Located in `tests/collectors/`, these tests verify the functionality of various data collectors:

#### Available Collectors:
- `ArxivCollector`: Tests academic paper collection
- `BitMEXCollector`: Tests cryptocurrency market data collection
- `FREDCollector`: Tests economic data collection
- `GitHubCollector`: Tests repository and code collection
- `ISDADocumentationCollector`: Tests financial documentation collection
- `QuantopianCollector`: Tests algorithmic trading data collection
- `AnnasMainLibraryCollector`: Tests library data collection
- `SciDBCollector`: Tests scientific database collection

Each collector has its own YAML configuration in `config_yaml/` directory.

### 2. Processors Tests

Located in `tests/processors/`, these tests verify text extraction and processing:

#### Batch Non-PDF Extractor
- Tests extraction from various file formats (Python, Markdown, HTML, JSON, CSV)
- Verifies metadata handling
- Tests quality control mechanisms
- Validates domain classification

#### Batch Text Extractor
- Tests PDF text extraction
- Verifies table and formula extraction
- Tests image handling
- Validates quality metrics
- Tests error handling

### 3. Corpus Management Tests

Located in `tests/corpus/`, these tests verify corpus management functionality:

#### Corpus Manager
- Tests document addition and retrieval
- Verifies metadata management
- Tests domain-specific operations
- Validates quality control
- Tests error handling

#### Corpus Balancer
- Tests corpus analysis
- Verifies rebalancing plan creation
- Tests plan execution
- Validates collector configuration updates
- Tests quality metrics

### 4. End-to-End Tests

Located in `tests/e2e/`, these tests verify the complete pipeline:

- Tests full data collection process
- Verifies processing pipeline
- Tests corpus management integration
- Validates end-to-end functionality

## Test Data Locations

- Collector Tests: `G:/data/test_processors/collectors/`
- Processor Tests: `G:/data/test_processors/`
- Corpus Manager Tests: `G:/data/TEST_CORPUS_MANAGER/`
- Corpus Balancer Tests: `G:/data/test_corPUS_balancer/`
- E2E Tests: `G:/data/e2E/`

## Test Configuration

Each test component uses specific configurations:

1. **Collector Configurations**
   - YAML files in `tests/collectors/config_yaml/`
   - Contains domain-specific settings
   - Includes API configurations where applicable

2. **Processor Configurations**
   - Quality thresholds
   - Processing parameters
   - Domain-specific settings

3. **Corpus Configurations**
   - Balance thresholds
   - Quality metrics
   - Domain weights

## Running Tests

See `COMMAND_GUIDE.md` for detailed instructions on running tests.

## Test Outputs

Each test generates:
- Processed data files
- Log files
- Quality reports
- Balance metrics (for corpus tests)

## Best Practices

1. **Before Running Tests**
   - Ensure all required directories exist
   - Verify API keys and credentials
   - Check available disk space

2. **During Test Execution**
   - Monitor log files
   - Check for error messages
   - Verify output directories

3. **After Test Completion**
   - Review test reports
   - Check output quality
   - Clean up temporary files if needed

## Troubleshooting

Common issues and solutions:

1. **Directory Not Found**
   - Verify directory paths
   - Check permissions
   - Create missing directories

2. **API Errors**
   - Verify API keys
   - Check rate limits
   - Validate API endpoints

3. **Processing Errors**
   - Check input file formats
   - Verify dependencies
   - Review error logs

## Adding New Tests

To add new tests:

1. Create test file in appropriate directory
2. Add necessary fixtures
3. Implement test cases
4. Update configuration if needed
5. Add to test suite

## Maintenance

Regular maintenance tasks:

1. Update API configurations
2. Refresh test data
3. Clean up old test outputs
4. Update documentation 