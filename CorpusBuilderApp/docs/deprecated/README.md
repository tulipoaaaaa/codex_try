# CryptoFinance Corpus Builder

A comprehensive desktop application for building, managing, and analyzing a corpus of crypto-finance documents.

## Overview

The CryptoFinance Corpus Builder is a PyQt6-based desktop application designed to automate the collection, processing, and management of a large corpus of crypto-finance documents. The application supports multiple data sources, advanced document processing capabilities, and comprehensive corpus management features.

## Features

- **Data Collection**: Automated collection from multiple sources:
  - ISDA Documentation
  - GitHub Repositories
  - Anna's Archive (Main Library)
  - arXiv Papers
  - FRED Economic Data
  - BitMEX Market Data
  - Quantopian Research
  - Web Content

- **Document Processing**:
  - PDF text extraction with OCR fallback
  - Text extraction from various formats
  - Quality control and scoring
  - Domain classification
  - Deduplication
  - Formula and chart extraction
  - Language detection and confidence scoring
  - Machine translation detection

- **Corpus Management**:
  - File browser with metadata editing
  - Corpus statistics and analytics
  - Domain distribution visualization
  - Automated balancing across domains
  - Quality metrics and analysis

- **Configuration and Customization**:
  - Multiple environment support (test, master, production)
  - API key management
  - Directory configuration
  - Processing settings

## Installation

### Prerequisites

- Python 3.8 or higher
- Windows OS (for BAT launcher)
- G:\venv\ai_trading_dev_1 virtual environment (as specified in the project)

### Setup

1. Clone the repository:
git clone https://github.com/your-username/CryptoFinanceCorpusBuilder.git
cd CryptoFinanceCorpusBuilder


2. Install dependencies:
pip install -r requirements.txt


3. Install required NLTK data:
import nltk
nltk.download('punkt')
nltk.download('stopwords')


4. Install required Spacy models:
python -m spacy download en_core_web_sm


5. Configure your API keys in the application (Settings > API Keys)

## Usage

### Starting the Application

On Windows, double-click the `launch_app.bat` file to start the application.

Alternatively, you can run:
python app/main.py


### Initial Configuration

1. When first launched, configure your directory structure in the Configuration tab
2. Add your API keys in the API Keys section
3. Configure your desired domain distribution

### Collecting Documents

1. Navigate to the Collectors tab
2. Configure the collector you want to use
3. Click "Start Collection" to begin collecting documents

### Processing Documents

1. Navigate to the Processors tab
2. Add files to process or use batch processing
3. Configure processing options
4. Click "Start Processing" to begin

### Managing Your Corpus

1. Use the Corpus Manager tab to browse and edit your corpus
2. View corpus statistics and analytics in the Dashboard
3. Check domain distribution in the Balancer tab
4. Use the Analytics tab for deeper insights

## Project Structure

CryptoFinanceCorpusBuilder/
├── app/ # Application code
│ ├── main.py # Entry point
│ ├── ui/ # User interface components
│ │ ├── tabs/ # Main application tabs
│ │ ├── widgets/ # Reusable UI widgets
│ │ └── dialogs/ # Dialog windows
│ └── resources/ # Application resources
├── shared_tools/ # Shared functionality
│ ├── collectors/ # Data collectors
│ ├── processors/ # Document processors
│ ├── ui_wrappers/ # UI wrapper classes
│ └── config/ # Configuration management
├── tests/ # Test suite
├── docs/ # Documentation
├── requirements.txt # Dependencies
├── setup.py # Installation script
└── launch_app.bat # Windows launcher

## Development

### Running Tests

pytest tests/


### Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
