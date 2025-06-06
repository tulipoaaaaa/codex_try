# Comprehensive Testing Plan for CryptoFinanceCorpusBuilder

## Overview
This document outlines the comprehensive testing strategy for the CryptoFinanceCorpusBuilder system, focusing on the new environment-aware configuration system and all its components.

## Test Environment Setup

### 1. Configuration Testing
- **Test Configuration Files**
  - `test_config.yaml`: Test environment configuration
  - `master_config.yaml`: Production environment configuration
  - Verify environment-specific paths and settings

### 2. Environment Management
- Test environment switching
- Verify path management for different environments
- Test configuration validation

## Component Testing

### 1. Collectors Testing

#### 1.1 SciDB Collector
```python
def test_scidb_collector():
    config = ProjectConfig("test_config.yaml", environment="test")
    collector = SciDBCollector(config)
    
    # Test initialization
    assert collector.output_dir == config.raw_data_dir
    
    # Test collection methods
    papers = collector.collect_by_search(["cryptocurrency derivatives"])
    assert isinstance(papers, list)
    
    # Test domain classification
    assert all('domain' in paper for paper in papers)
```

#### 1.2 arXiv Collector
```python
def test_arxiv_collector():
    config = ProjectConfig("test_config.yaml", environment="test")
    collector = ArxivCollector(config)
    
    # Test initialization
    assert collector.output_dir == config.raw_data_dir
    
    # Test collection methods
    papers = collector.collect_by_category(["q-fin.CP"])
    assert isinstance(papers, list)
```

#### 1.3 GitHub Collector
```python
def test_github_collector():
    config = ProjectConfig("test_config.yaml", environment="test")
    collector = GitHubCollector(config)
    
    # Test initialization
    assert collector.output_dir == config.raw_data_dir
    
    # Test collection methods
    repos = collector.collect_by_topic(["cryptocurrency"])
    assert isinstance(repos, list)
```

### 2. Processors Testing

#### 2.1 Quality Control
```python
def test_quality_control():
    config = ProjectConfig("test_config.yaml", environment="test")
    processor = QualityControl(config)
    
    # Test initialization
    assert processor.input_dir == config.raw_data_dir
    assert processor.output_dir == config.processed_dir
    
    # Test processing
    results = processor.process_directory()
    assert isinstance(results, dict)
```

#### 2.2 Corpus Balancer
```python
def test_corpus_balancer():
    config = ProjectConfig("test_config.yaml", environment="test")
    balancer = CorpusBalancer(config)
    
    # Test initialization
    assert balancer.corpus_dir == config.corpus_dir
    
    # Test balancing
    balance_report = balancer.analyze_corpus_balance()
    assert isinstance(balance_report, dict)
```

### 3. Storage Testing

#### 3.1 Corpus Manager
```python
def test_corpus_manager():
    config = ProjectConfig("test_config.yaml", environment="test")
    manager = CorpusManager(config)
    
    # Test initialization
    assert manager.base_dir == config.corpus_dir
    
    # Test document management
    doc_id = manager.add_document("test.pdf", "crypto_derivatives")
    assert doc_id is not None
    
    # Test metadata management
    stats = manager.get_corpus_stats()
    assert isinstance(stats, dict)
```

## Integration Testing

### 1. End-to-End Pipeline
```python
def test_complete_pipeline():
    config = ProjectConfig("test_config.yaml", environment="test")
    
    # 1. Collection
    collector = SciDBCollector(config)
    papers = collector.collect_by_search(["cryptocurrency derivatives"])
    
    # 2. Processing
    processor = QualityControl(config)
    processed = processor.process(papers)
    
    # 3. Corpus Management
    manager = CorpusManager(config)
    for paper in processed:
        manager.add_document(paper["path"], paper["domain"])
    
    # 4. Verify Results
    stats = manager.get_corpus_stats()
    assert stats["total_documents"] > 0
```

### 2. Environment Switching
```python
def test_environment_switching():
    # Test environment
    test_config = ProjectConfig("test_config.yaml", environment="test")
    test_collector = SciDBCollector(test_config)
    test_papers = test_collector.collect_by_search(["test"])
    
    # Production environment
    prod_config = ProjectConfig("master_config.yaml", environment="production")
    prod_collector = SciDBCollector(prod_config)
    prod_papers = prod_collector.collect_by_search(["test"])
    
    # Verify different paths
    assert test_collector.output_dir != prod_collector.output_dir
```

## Test Data Preparation

### 1. Test Files
- Sample PDFs in `tests/test_fourfiles/`
- Sample non-PDF documents in `tests/nonpdf_extraction/`
- Integration test PDFs in `tests/integration_pdfs/`

### 2. Test Configuration
```yaml
# test_config.yaml
environment: test

environments:
  test:
    corpus_dir: "tests/test_output"
    cache_dir: "tests/test_cache"
    log_dir: "tests/test_logs"
  production:
    corpus_dir: "tests/prod_output"
    cache_dir: "tests/prod_cache"
    log_dir: "tests/prod_logs"

domains:
  crypto_derivatives:
    enabled: true
    priority: 1
  # ... other domains
```

## Test Execution Plan

1. **Unit Tests**
   - Run individual component tests
   - Verify environment-specific behavior
   - Check error handling

2. **Integration Tests**
   - Test complete pipeline
   - Verify environment switching
   - Check data flow between components

3. **End-to-End Tests**
   - Run full collection and processing
   - Verify corpus management
   - Check reporting and statistics

## Test Results and Reporting

### 1. Test Reports
- Component test results
- Integration test results
- Environment-specific results

### 2. Coverage Reports
- Code coverage by component
- Environment-specific coverage
- Integration coverage

## Next Steps

1. **Test Implementation**
   - Create test files for each component
   - Implement environment-specific tests
   - Add integration tests

2. **Test Execution**
   - Run tests in both environments
   - Verify results
   - Document findings

3. **Documentation**
   - Update README with test results
   - Document environment-specific behavior
   - Add troubleshooting guide

## Notes on Corpus Balancer Feedback Loop

The corpus balancer feedback loop is implemented in the following way:

1. **Collection Phase**
   - Collectors use domain-specific configurations
   - Initial domain classification based on content

2. **Processing Phase**
   - Quality control validates domain classification
   - Corpus balancer analyzes domain distribution

3. **Feedback Loop**
   - Balancer provides feedback to collectors
   - Adjusts collection priorities based on balance
   - Maintains target domain ratios

## Test Environment Setup

1. **Directory Structure**
   ```
   tests/
   ├── test_output/
   ├── test_cache/
   ├── test_logs/
   ├── test_fourfiles/
   ├── nonpdf_extraction/
   └── integration_pdfs/
   ```

2. **Configuration**
   - Test-specific configuration in `test_config.yaml`
   - Environment-specific paths
   - Test data locations

3. **Dependencies**
   - Required Python packages
   - External tools (Tesseract, etc.)
   - Environment variables
