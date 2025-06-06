# CryptoFinance Corpus Builder v3

A comprehensive PyQt6 desktop application for building and managing cryptocurrency research corpora. This application integrates with multiple data sources, provides advanced text processing capabilities, and offers real-time analytics for corpus management.

## 🚀 Live Demo

**Desktop Application Demo**: [CryptoCorpus Builder v3](https://ppl-ai-code-interpreter-files.s3.amazonaws.com/web/direct-files/a23dd5175e6f1164f0304f6c1827178f/06f9a596-21b3-46af-890e-3e0b16657099/index.html)

*Note: The link above shows a web-based demonstration of the interface. The actual application is a native PyQt6 desktop application.*

## ✨ Features

### 📊 Dashboard
- Real-time corpus statistics with interactive charts
- Domain distribution visualization
- Recent activity monitoring
- Storage usage analysis
- System health indicators

### 🔍 Data Collection
- **9 Integrated Collectors**:
  - ISDA Documentation
  - Anna's Archive (Books)
  - GitHub Repositories
  - Quantopian Research
  - arXiv Papers
  - FRED Economic Data
  - BitMEX Market Data
  - SciDB Academic Papers
  - Web Content Scraper

### ⚙️ Data Processing
- **PDF Processing**: Multi-engine text extraction with OCR fallback
- **Non-PDF Processing**: Support for HTML, DOCX, TXT, and other formats
- **Batch Operations**: Concurrent processing with progress tracking
- **Quality Control**: Automated quality assessment and validation

### 📁 Corpus Management
- **File Browser**: Navigate domain-organized corpus structure
- **Metadata Viewer**: Inspect document metadata and quality scores
- **Search & Filter**: Advanced search capabilities across the corpus
- **Export/Import**: Flexible data exchange and backup options

### ⚖️ Corpus Balancing
- **Domain Allocation**: Visual allocation management
- **Automatic Rebalancing**: One-click corpus optimization
- **Quality Thresholds**: Per-domain quality standards
- **Target Distribution**: Configurable domain weights

### 📈 Analytics
- **Content Analysis**: Document type and format distribution
- **Language Confidence**: Multi-language detection and scoring
- **Temporal Trends**: Collection and processing timeline analysis
- **Keyword Analysis**: Frequency analysis and topic modeling

### ⚙️ Configuration
- **Environment Management**: Test/Production environment switching
- **API Key Management**: Secure credential storage
- **Domain Configuration**: Customizable domain definitions
- **Processing Parameters**: Adjustable extraction settings

### 📝 Logging
- **Real-time Logs**: Live log monitoring with filtering
- **Error Tracking**: Comprehensive error categorization
- **Performance Metrics**: System performance monitoring
- **Export Capabilities**: Log export for analysis

## 🏗️ Architecture

### Core Components

1. **Collector Wrappers** - UI-compatible interfaces for all data collectors
2. **Processor Wrappers** - Thread-safe processing with progress reporting
3. **Configuration System** - Flexible YAML-based configuration management
4. **UI Framework** - Professional PyQt6 interface with modern design

### Integration System

The application uses a sophisticated wrapper system that provides:
- **Thread Safety**: All operations run in background threads
- **Progress Reporting**: Real-time status updates and progress tracking
- **Error Handling**: Comprehensive error recovery and reporting
- **Signal/Slot Communication**: Loose coupling between components

## 📋 Requirements

- Python 3.8+
- PyQt6 6.6.0+
- Windows 10/11 (for provided launcher)
- 4GB+ RAM
- 10GB+ disk space

## 🚀 Quick Start

### 1. Virtual Environment Setup
```bash
python -m venv G:\venv\ai_trading_dev_1
G:\venv\ai_trading_dev_1\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file with your API keys:
```env
GITHUB_TOKEN=your_github_token
AA_ACCOUNT_COOKIE=your_anna_cookie
FRED_API_KEY=your_fred_key
```

### 4. Launch Application
**Windows**: Double-click `launch_app.bat`
**Command Line**: `python app/main.py`

## 🎯 Usage

### Basic Workflow

1. **Configure Environment**: Set up API keys and directories in the Configuration tab
2. **Start Collection**: Use the Collectors tab to gather data from multiple sources
3. **Process Data**: Process collected files using the Processors tab
4. **Manage Corpus**: Organize and search your corpus in the Corpus Manager
5. **Balance Domains**: Use the Balancer to maintain proper domain distribution
6. **Analyze Results**: View analytics and insights in the Analytics tab

### Advanced Features

- **Batch Operations**: Process hundreds of files simultaneously
- **Custom Domains**: Define your own research domains and allocation targets
- **Quality Control**: Set quality thresholds and automatic filtering
- **Export/Import**: Share corpus subsets or backup your data

## 🔧 Collector Integration

Each collector includes a specialized wrapper that provides:

```python
# Example: Using the ISDA collector wrapper
from shared_tools.ui_wrappers.collectors.isda_wrapper import ISDAWrapper

wrapper = ISDAWrapper(config)
wrapper.set_search_keywords(["derivatives", "protocol"])
wrapper.set_max_sources(10)

# Connect to UI signals
wrapper.progress_updated.connect(progress_bar.setValue)
wrapper.status_updated.connect(status_label.setText)
wrapper.collection_completed.connect(on_collection_complete)

# Start collection
wrapper.start()
```

## 🛠️ Processor Integration

Processors are integrated through wrapper classes that handle:

```python
# Example: Using the PDF processor wrapper
from shared_tools.ui_wrappers.processors.pdf_extractor_wrapper import PDFExtractorWrapper

wrapper = PDFExtractorWrapper(config)
wrapper.set_ocr_enabled(True)
wrapper.set_table_extraction(True)

# Connect signals
wrapper.progress_updated.connect(progress_bar.setValue)
wrapper.file_processed.connect(on_file_processed)

# Start batch processing
files_to_process = ["file1.pdf", "file2.pdf", "file3.pdf"]
wrapper.start_batch_processing(files_to_process)
```

## 📊 Domain Configuration

The application supports 8 predefined domains with customizable allocations:

- **Crypto Derivatives** (20%) - Futures, options, perpetual swaps
- **High Frequency Trading** (15%) - Algorithmic trading, market making
- **Risk Management** (15%) - Portfolio risk, volatility models
- **Market Microstructure** (15%) - Order book dynamics, liquidity
- **DeFi** (12%) - Decentralized finance protocols
- **Portfolio Construction** (10%) - Asset allocation, optimization
- **Valuation Models** (8%) - Token valuation, fundamental analysis
- **Regulation & Compliance** (5%) - Legal frameworks, compliance

## 🔍 Testing

Run the test suite:
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# UI tests
pytest tests/ui/ --qt-api pyqt6
```

## 📁 Project Structure

```
CryptoFinanceCorpusBuilder/
├── app/                          # Main application
│   ├── main.py                   # Entry point
│   ├── main_window.py            # Main window
│   └── ui/                       # UI components
│       ├── tabs/                 # Tab implementations
│       ├── widgets/              # Reusable widgets
│       └── dialogs/              # Dialog windows
├── shared_tools/                 # Core functionality
│   ├── collectors/               # Data collectors
│   ├── processors/               # Data processors
│   ├── ui_wrappers/              # UI integration
│   └── project_config.py         # Configuration
├── requirements.txt              # Dependencies
├── setup.py                      # Package setup
└── launch_app.bat               # Windows launcher
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: See the `docs/` directory for detailed guides
- **Issues**: Report bugs and request features via GitHub Issues
- **Logs**: Check `~/.cryptofinance/logs/` for debugging information

## 🙏 Acknowledgments

- Built with PyQt6 for cross-platform desktop functionality
- Integrates with multiple academic and industry data sources
- Designed for cryptocurrency and blockchain research workflows

---

**Note**: This is a research tool designed for academic and professional use. Always comply with the terms of service of data sources and respect rate limits.