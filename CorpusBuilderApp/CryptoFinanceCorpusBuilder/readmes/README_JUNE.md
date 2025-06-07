# CryptoFinanceCorpusBuilder - Complete Pipeline Documentation

## Overview
The CryptoFinanceCorpusBuilder is a comprehensive system for collecting, processing, and managing a corpus of crypto-finance related documents. This document provides a complete guide to the system's architecture and usage.

## Prerequisites

### Required Python Packages
```bash
pip install -r requirements.txt
```

Required packages include:
- beautifulsoup4
- PyMuPDF (fitz)
- langdetect
- pytesseract
- opencv-python
- numpy
- pandas
- scikit-learn
- requests
- python-dotenv
- pyyaml
- pydantic

### External Dependencies
1. **Tesseract OCR** (for image text extraction):
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: `sudo apt-get install tesseract-ocr`
   - Mac: `brew install tesseract`

2. **Environment Variables**:
   Create a `.env` file in the project root:
   ```
   AA_ACCOUNT_COOKIE=your_cookie_here  # For SciDB collector
   ARXIV_API_KEY=your_key_here         # For arXiv collector
   GITHUB_TOKEN=your_token_here        # For GitHub collector
   ```

## Project Structure
```
corpusbuilder/
├── config/
│   ├── master_config.yaml           # Main configuration file
│   ├── domain_config.py             # Domain definitions
│   └── test_master_config.yaml      # Test configuration
├── shared_tools/
│   ├── collectors/                  # Collection modules
│   ├── processors/                  # Processing modules
│   ├── storage/                     # Storage management
│   └── utils/                       # Utility functions
├── data/                           # Corpus data directory
│   ├── raw_data/                   # Raw collected data
│   ├── extracted/                  # Extracted text
│   └── processed/                  # Processed data
└── logs/                           # Log files
```

## System Architecture

### 1. Configuration System
The system uses a centralized configuration management through `ProjectConfig`:
- Located in: `corpusbuilder/shared_tools/project_config.py`
- Main config file: `corpusbuilder/config/master_config.yaml`
- Environment-specific settings for production and test environments
- Domain-specific configurations for different crypto-finance topics

### 2. Collection Pipeline

#### 2.1 Collectors
Located in: `corpusbuilder/shared_tools/collectors/`

##### a) SciDB Collector (`enhanced_scidb_collector.py`)
- **Purpose**: Collects academic papers from SciDB
- **Features**:
  - DOI-based collection
  - Search term-based collection
  - Automatic domain classification
  - Robust download handling
- **Configuration**:
  ```yaml
  collectors:
    scidb:
      enabled: true
      max_results_per_term: 10
      delay_range: [3, 7]
      output_dir: "{corpus_dir}/raw_data/scidb"
  ```
- **Usage**:
  ```python
  collector = SciDBCollector(output_dir, project_config=config)
  # Collect by DOI
  papers = collector.collect_by_doi(doi_list)
  # Collect by search
  papers = collector.collect_by_search(search_terms)
  ```

##### b) arXiv Collector
- **Purpose**: Collects papers from arXiv
- **Features**:
  - Category-based collection
  - Automatic metadata extraction
  - Quality filtering
- **Configuration**:
  ```yaml
  collectors:
    arxiv:
      enabled: true
      categories: ["q-fin", "cs.AI", "cs.LG"]
      max_results: 100
  ```

##### c) GitHub Collector
- **Purpose**: Collects crypto-finance related repositories
- **Features**:
  - Topic-based collection
  - Star-based filtering
  - README and code analysis
- **Configuration**:
  ```yaml
  collectors:
    github:
      enabled: true
      topics: ["cryptocurrency", "trading", "defi"]
      min_stars: 100
  ```

### 3. Processing Pipeline

#### 3.1 Extractors
Located in: `corpusbuilder/shared_tools/processors/`

##### a) PDF Extractor
- **Purpose**: Extracts text from PDF documents
- **Features**:
  - Text extraction
  - Metadata preservation
  - Quality checks
- **Configuration**:
  ```yaml
  extractors:
    pdf:
      enabled: true
      min_tokens: 200
      quality_threshold: 0.8
      chunk_size: 1000
  ```

##### b) Non-PDF Extractor
- **Purpose**: Handles various non-PDF document formats
- **Features**:
  - Multiple format support
  - Text cleaning
  - Metadata extraction
- **Configuration**:
  ```yaml
  extractors:
    nonpdf:
      enabled: true
      min_tokens: 100
      quality_threshold: 0.7
  ```

#### 3.2 Processors

##### a) Quality Control (`quality_control.py`)
- **Purpose**: Ensures document quality
- **Features**:
  - Language detection
  - Corruption detection
  - Duplication detection
  - Translation detection
- **Configuration**:
  ```yaml
  processors:
    quality_control:
      enabled: true
      min_token_count: 100
      min_quality_score: 0.7
      checks:
        language:
          enabled: true
          min_confidence: 0.8
  ```

##### b) Corpus Balancer (`corpus_balancer.py`)
- **Purpose**: Maintains balanced domain distribution
- **Features**:
  - Domain ratio analysis
  - Entropy calculation
  - Gini coefficient analysis
- **Configuration**:
  ```yaml
  processors:
    corpus_balancer:
      enabled: true
      balance_thresholds:
        entropy_min: 2.0
        gini_max: 0.7
  ```

##### c) Specialized Processors

###### Chart Image Extractor (`chart_image_extractor.py`)
- **Purpose**: Extracts and analyzes charts from documents
- **Features**:
  - Chart detection
  - OCR for chart text
  - Chart type classification
- **Configuration**:
  ```yaml
  processors:
    specialized:
      charts:
        enabled: true
        ocr_enabled: true
        detect_chart_type: true
  ```

###### Formula Extractor (`formula_extractor.py`)
- **Purpose**: Extracts mathematical formulas
- **Features**:
  - LaTeX formula detection
  - Formula preservation
  - Context extraction
- **Configuration**:
  ```yaml
  processors:
    specialized:
      formulas:
        enabled: true
        formula_patterns:
          - pattern: '\$.*?\$'
            type: 'inline'
  ```

###### Domain Classifier (`domain_classifier.py`)
- **Purpose**: Classifies documents into domains
- **Features**:
  - Multi-domain classification
  - Confidence scoring
  - Domain-specific rules
- **Configuration**:
  ```yaml
  processors:
    domain_classifier:
      enabled: true
      domains:
        crypto_derivatives:
          allocation: 0.20
        high_frequency_trading:
          allocation: 0.15
  ```

### 4. Storage and Management

#### 4.1 Corpus Manager (`corpus_manager.py`)
Located in: `corpusbuilder/shared_tools/storage/`

- **Purpose**: Manages corpus structure and metadata
- **Features**:
  - Directory management
  - Metadata tracking
  - Statistics generation
  - Backup management
- **Configuration**:
  ```yaml
  corpus_manager:
    enabled: true
    metadata:
      file: "corpus_metadata.json"
      backup_dir: "{corpus_dir}/metadata/backups"
    statistics:
      enabled: true
      update_interval: 3600
  ```

## Getting Started

### 1. Initial Setup

1. **Clone and Install**:
   ```bash
   git clone [repository_url]
   cd corpusbuilder
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   # Create necessary directories
   mkdir -p data/{raw_data,extracted,processed}
   mkdir -p logs
   
   # Copy and edit configuration
   cp config/master_config.yaml config/my_config.yaml
   ```

3. **Edit Configuration**:
   Open `config/my_config.yaml` and update:
   ```yaml
   environment: "production"  # or "test"
   
   environments:
     production:
       corpus_dir: "/path/to/your/data"
       cache_dir: "/path/to/your/cache"
       log_dir: "/path/to/your/logs"
   ```

### 2. Running the Pipeline

#### 2.1 Collection

1. **Prepare Search Terms**:
   Create a JSON file `config/search_terms.json`:
   ```json
   {
     "crypto_derivatives": [
       "cryptocurrency derivatives",
       "bitcoin futures",
       "crypto options"
     ],
     "high_frequency_trading": [
       "high frequency trading",
       "algorithmic trading",
       "market making"
     ]
   }
   ```

2. **Run Collection**:
   ```python
   from CryptoFinanceCorpusBuilder.shared_tools.collectors import SciDBCollector
   from shared_tools.project_config import ProjectConfig
   import json

   # Load configuration
   config = ProjectConfig.from_yaml("config/my_config.yaml")
   
   # Load search terms
   with open("config/search_terms.json", "r") as f:
       search_terms = json.load(f)
   
   # Initialize collector
   collector = SciDBCollector(config=config)
   
   # Collect papers for each domain
   for domain, terms in search_terms.items():
       print(f"Collecting papers for {domain}...")
       papers = collector.collect_by_search(terms)
       print(f"Collected {len(papers)} papers")
   ```

#### 2.2 Processing

1. **Run Quality Control**:
   ```python
   from CryptoFinanceCorpusBuilder.shared_tools.processors import QualityControl
   
   # Initialize quality control
   qc = QualityControl(config=config)
   
   # Process all collected papers
   results = qc.process_directory(config.get_input_dir())
   
   # Save results
   with open("logs/quality_control_results.json", "w") as f:
       json.dump(results, f, indent=2)
   ```

2. **Run Corpus Balancing**:
   ```python
   from CryptoFinanceCorpusBuilder.shared_tools.processors import CorpusBalancer
   
   # Initialize balancer
   balancer = CorpusBalancer(config=config)
   
   # Analyze and balance corpus
   balance_results = balancer.analyze_corpus_balance()
   
   # Save analysis
   with open("logs/corpus_balance_analysis.json", "w") as f:
       json.dump(balance_results, f, indent=2)
   ```

### 3. Monitoring and Maintenance

#### 3.1 Logging
Logs are stored in `{log_dir}/` with the following structure:
```
logs/
├── collectors.log
├── extractors.log
├── processors.log
└── corpus_manager.log
```

Example log entry:
```
2024-03-14 10:15:23 - SciDBCollector - INFO - Collecting papers for crypto_derivatives
2024-03-14 10:15:25 - SciDBCollector - INFO - Found 15 papers for term "cryptocurrency derivatives"
```

#### 3.2 Statistics
Statistics are generated in `{corpus_dir}/reports/`:
```
reports/
├── corpus_stats.json
├── domain_balance.csv
└── quality_metrics.json
```

### 4. Common Operations

#### 4.1 Adding New Search Terms
1. Edit `config/search_terms.json`
2. Add new terms to appropriate domains
3. Run collection script

#### 4.2 Updating Domain Configuration
1. Edit `config/domain_config.py`
2. Add new domain definitions
3. Update `master_config.yaml` with new domain settings

#### 4.3 Checking Corpus Status
```python
from CryptoFinanceCorpusBuilder.shared_tools.storage import CorpusManager

# Initialize corpus manager
manager = CorpusManager(config=config)

# Get corpus statistics
stats = manager.get_corpus_stats()
print(f"Total documents: {stats['total_documents']}")
print(f"Documents by domain: {stats['domain_distribution']}")
```

## Troubleshooting

### Common Issues and Solutions

1. **Collection Failures**:
   - **Error**: "No authentication cookie available"
     - Solution: Check `.env` file for `AA_ACCOUNT_COOKIE`
   - **Error**: "Rate limit exceeded"
     - Solution: Increase `delay_range` in config

2. **Processing Errors**:
   - **Error**: "Tesseract not found"
     - Solution: Install Tesseract and add to PATH
   - **Error**: "Invalid PDF"
     - Solution: Check file integrity and try re-downloading

3. **Storage Issues**:
   - **Error**: "Disk space low"
     - Solution: Clean up temporary files in `data/temp/`
   - **Error**: "Permission denied"
     - Solution: Check directory permissions

## Example Workflows

### 1. Complete Collection and Processing
```bash
# 1. Set up environment
python scripts/setup_environment.py

# 2. Run collection
python scripts/run_collection.py --config config/my_config.yaml

# 3. Run processing
python scripts/run_processing.py --config config/my_config.yaml

# 4. Generate reports
python scripts/generate_reports.py --config config/my_config.yaml
```

### 2. Adding New Domain
1. Update `config/domain_config.py`
2. Add domain to `master_config.yaml`
3. Create domain directory
4. Run collection for new domain
5. Process new documents
6. Rebalance corpus

## Best Practices

1. **Configuration Management**
   - Always use ProjectConfig for new components
   - Keep configuration in YAML format
   - Use environment variables for sensitive data

2. **Collection**
   - Use appropriate delays between requests
   - Implement proper error handling
   - Validate collected data

3. **Processing**
   - Run quality control before other processors
   - Monitor domain balance
   - Regular backup of metadata

4. **Storage**
   - Regular metadata backups
   - Monitor disk space
   - Clean up temporary files

## Contributing

1. Follow the existing code structure
2. Use ProjectConfig for configuration
3. Add appropriate logging
4. Include tests
5. Update documentation

## License
[Your License Information]
