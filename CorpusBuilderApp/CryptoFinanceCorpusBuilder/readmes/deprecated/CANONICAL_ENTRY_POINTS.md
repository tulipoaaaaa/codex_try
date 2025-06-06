# Canonical Entry Points for Pipeline Stages

This document outlines the canonical entry points for each stage of the corpus building pipeline. All orchestration scripts should use these entry points to ensure consistency and maintainability.

## Data Collection

### 1. Curated List Collection
```bash
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources curated --output-dir <output_dir> --config <config_path>
```

### 2. Academic/API Collection
```bash
# SciDB Collection
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources scidb --output-dir <output_dir> --config <config_path>

# FRED Collection
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources fred --output-dir <output_dir> --config <config_path>

# arXiv Collection
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources arxiv --output-dir <output_dir> --config <config_path>
```

### 3. Web Collection
```bash
# GitHub Collection
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources github --output-dir <output_dir> --config <config_path>

# Web Document Collection
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources web --output-dir <output_dir> --config <config_path>
```

## Text Extraction

### 1. Batch Text Extraction
```bash
python -m CryptoFinanceCorpusBuilder.processors.batch_text_extractor --input-dir <input_dir> --output-dir <output_dir> --domain <domain>
```

### 2. Enhanced Text Extraction (with Quality Control)
```bash
python -m CryptoFinanceCorpusBuilder.processors.batch_text_extractor_enhanced --input-dir <input_dir> --output-dir <output_dir> --domain <domain>
```

## Corpus Management

### 1. Corpus Combination
```bash
python -m CryptoFinanceCorpusBuilder.processors.combine_corpora --sources <source_dirs> --target <target_dir> --track-origin
```

### 2. Deduplication
```bash
python -m CryptoFinanceCorpusBuilder.processors.deduplicator --input-dir <input_dir> --output-dir <output_dir> --similarity-threshold <threshold>
```

### 3. Metadata Enhancement
```bash
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli enhance_metadata --corpus-dir <corpus_dir>
```

## Analysis & Monitoring

### 1. Coverage Analysis
```bash
python -m CryptoFinanceCorpusBuilder.processors.coverage_analyzer --corpus-dir <corpus_dir> --output <output_path> --visualize
```

### 2. Progress Monitoring
```bash
python -m CryptoFinanceCorpusBuilder.processors.monitor_progress --corpus-dir <corpus_dir> --output <output_path>
```

## Utility Scripts

### 1. Recovery Scripts
```bash
# Recover Orphaned Text Files
python -m CryptoFinanceCorpusBuilder.processors.recover_orphaned_txts --corpus <corpus_dir> --metadata <metadata_path>

# Tag Priority Documents
python -m CryptoFinanceCorpusBuilder.processors.tag_priority_high --corpus <corpus_dir> --metadata <metadata_path>
```

### 2. Validation Scripts
```bash
# Verify Setup
python -m CryptoFinanceCorpusBuilder.utils.verify_setup

# Verify Installation
python -m CryptoFinanceCorpusBuilder.utils.verify_install
```

## Notes

1. All paths should be absolute or relative to the project root
2. Configuration files should be placed in `CryptoFinanceCorpusBuilder/config/`
3. Logs are automatically written to `CryptoFinanceCorpusBuilder/logs/`
4. Temporary files are stored in `CryptoFinanceCorpusBuilder/temp_workers/`
5. All scripts support `--help` for detailed usage information 