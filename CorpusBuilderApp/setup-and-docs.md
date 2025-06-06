# CryptoFinance Corpus Builder v3 - Complete Package

## Requirements File

```
# File: requirements.txt
# CryptoFinance Corpus Builder Dependencies

# Core UI Framework
PyQt6>=6.6.0
PyQt6-Charts>=6.6.0
PyQt6-tools>=6.6.0

# Project Configuration
pydantic>=2.5.0
PyYAML>=6.0.1

# Web Scraping and HTTP
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.3
urllib3>=2.0.7

# PDF Processing
PyPDF2>=3.0.1
PyMuPDF>=1.23.0
pdfminer.six>=20221105
pdfplumber>=0.10.3

# Text Processing
python-docx>=1.1.0
chardet>=5.2.0
langdetect>=1.0.9

# Data Processing
pandas>=2.1.0
numpy>=1.24.0
tabula-py>=2.8.2

# Machine Learning (for text analysis)
scikit-learn>=1.3.0
spacy>=3.7.0

# Database and Storage
SQLAlchemy>=2.0.0
sqlite3
pathlib2>=2.3.7

# Environment and Configuration
python-dotenv>=1.0.0
configparser>=6.0.0

# Logging and Monitoring
loguru>=0.7.2

# API Clients
github3.py>=4.0.1
feedparser>=6.0.10
arxiv>=2.1.0

# Crypto/Finance Libraries
ccxt>=4.1.0
yfinance>=0.2.0

# Image Processing (for OCR)
Pillow>=10.0.0
pytesseract>=0.3.10

# Testing
pytest>=7.4.0
pytest-qt>=4.2.0
pytest-mock>=3.12.0

# Development Tools
black>=23.9.0
flake8>=6.1.0
mypy>=1.6.0
```

## Setup Script

```python
# File: setup.py
"""
Setup script for CryptoFinance Corpus Builder
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
with open('requirements.txt', 'r') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="crypto-corpus-builder",
    version="3.0.0",
    author="CryptoFinance Research Team",
    author_email="research@cryptofinance.org",
    description="A comprehensive tool for building and managing cryptocurrency research corpora",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cryptofinance/corpus-builder",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "crypto-corpus-builder=app.main:main",
            "ccb=app.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "app": ["ui/assets/*", "ui/styles/*"],
        "shared_tools": ["config/*.yaml", "config/*.json"],
    },
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-qt>=4.2.0",
            "black>=23.9.0",
            "flake8>=6.1.0",
            "mypy>=1.6.0",
        ]
    }
)
```

## Windows Launch Script

```batch
@echo off
REM File: launch_app.bat
REM Windows launcher for CryptoFinance Corpus Builder

echo Starting CryptoFinance Corpus Builder v3...

REM Check if virtual environment exists
if exist "G:\venv\ai_trading_dev_1\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "G:\venv\ai_trading_dev_1\Scripts\activate.bat"
) else (
    echo Virtual environment not found at G:\venv\ai_trading_dev_1
    echo Please ensure the virtual environment is created and dependencies are installed.
    pause
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found in virtual environment.
    echo Please ensure Python is properly installed in the virtual environment.
    pause
    exit /b 1
)

REM Navigate to application directory
cd /d "%~dp0"

REM Start the application
echo Launching application...
python app/main.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
```

## Installation Guide

```markdown
# File: INSTALLATION.md
# CryptoFinance Corpus Builder v3 - Installation Guide

## Prerequisites

- Python 3.8 or higher
- Windows 10/11 (for the provided launch script)
- At least 4GB RAM
- 10GB free disk space (more for large corpora)

## Installation Steps

### 1. Virtual Environment Setup

Create and activate your virtual environment at `G:\venv\ai_trading_dev_1`:

```bash
python -m venv G:\venv\ai_trading_dev_1
G:\venv\ai_trading_dev_1\Scripts\activate
```

### 2. Install Dependencies

With the virtual environment activated:

```bash
pip install -r requirements.txt
```

### 3. Configuration

Copy the sample configuration files:

```bash
cp shared_tools/test_config.yaml.sample shared_tools/test_config.yaml
cp shared_tools/master_config.yaml.sample shared_tools/master_config.yaml
```

Edit the configuration files to match your system paths and API keys.

### 4. Environment Variables

Create a `.env` file in the project root with your API keys:

```
# GitHub API Token
GITHUB_TOKEN=your_github_token_here

# Anna's Archive Cookie (if available)
AA_ACCOUNT_COOKIE=your_cookie_here

# FRED API Key
FRED_API_KEY=your_fred_key_here

# Other API keys as needed
```

### 5. Directory Structure

The application will automatically create the required directory structure on first run:

```
corpus/
├── raw_data/
│   ├── crypto_derivatives/
│   ├── decentralized_finance/
│   ├── high_frequency_trading/
│   └── ...
├── extracted/
├── pdf_extracted/
├── nonpdf_extracted/
├── processed/
└── reports/
```

## Running the Application

### Option 1: Windows Launcher

Double-click `launch_app.bat` to start the application.

### Option 2: Command Line

```bash
G:\venv\ai_trading_dev_1\Scripts\activate
python app/main.py
```

### Option 3: Installed Package

If installed via pip:

```bash
crypto-corpus-builder
# or
ccb
```

## Troubleshooting

### Common Issues

1. **Virtual environment not found**
   - Ensure the virtual environment exists at `G:\venv\ai_trading_dev_1`
   - Update the path in `launch_app.bat` if using a different location

2. **Missing dependencies**
   - Run `pip install -r requirements.txt` in the activated virtual environment

3. **Permission errors**
   - Run as administrator if needed
   - Check write permissions to the corpus directory

4. **API errors**
   - Verify API keys in the `.env` file
   - Check internet connectivity

### Logs

Application logs are stored in:
- Windows: `%USERPROFILE%\.cryptofinance\logs\`
- Default: `~/.cryptofinance/logs/`

## Development Setup

For development work:

```bash
pip install -e .[dev]
```

This installs additional development dependencies for testing and code quality.

## Testing

Run the test suite:

```bash
pytest tests/
```

For GUI tests:

```bash
pytest tests/ui/ --qt-api pyqt6
```
```

## Application Structure Documentation

```markdown
# File: ARCHITECTURE.md
# Application Architecture

## Directory Structure

```
CryptoFinanceCorpusBuilder/
├── app/                          # Main application code
│   ├── main.py                   # Application entry point
│   ├── main_window.py            # Main window class
│   └── ui/                       # User interface components
│       ├── tabs/                 # Tab implementations
│       │   ├── dashboard_tab.py
│       │   ├── collectors_tab.py
│       │   ├── processors_tab.py
│       │   ├── corpus_manager_tab.py
│       │   ├── balancer_tab.py
│       │   ├── analytics_tab.py
│       │   ├── configuration_tab.py
│       │   └── logs_tab.py
│       ├── widgets/              # Reusable widgets
│       │   ├── corpus_statistics.py
│       │   ├── activity_log.py
│       │   ├── domain_distribution.py
│       │   ├── file_browser.py
│       │   ├── metadata_viewer.py
│       │   └── log_viewer.py
│       └── dialogs/              # Dialog windows
│           ├── api_key_dialog.py
│           ├── settings_dialog.py
│           └── error_dialog.py
├── shared_tools/                 # Core functionality
│   ├── collectors/               # Data collectors
│   ├── processors/               # Data processors
│   ├── prev_working/             # Stable processor versions
│   ├── ui_wrappers/              # UI integration wrappers
│   │   ├── base_wrapper.py
│   │   ├── collectors/           # Collector wrappers
│   │   └── processors/           # Processor wrappers
│   ├── utils/                    # Utility functions
│   ├── config/                   # Configuration files
│   └── project_config.py         # Configuration management
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── ui/                       # UI tests
├── docs/                         # Documentation
├── requirements.txt              # Python dependencies
├── setup.py                      # Package setup
├── launch_app.bat               # Windows launcher
└── README.md                    # Project overview
```

## Key Components

### 1. Main Application (app/)

- **main.py**: Entry point with exception handling and configuration loading
- **main_window.py**: Main window with tab management and global UI state

### 2. User Interface (app/ui/)

- **Tabs**: Specialized interfaces for different functions
- **Widgets**: Reusable UI components for data display
- **Dialogs**: Modal windows for configuration and errors

### 3. Data Collection (shared_tools/collectors/)

- **Base Collector**: Common interface for all data sources
- **Specific Collectors**: ISDA, GitHub, arXiv, Anna's Archive, etc.
- **UI Wrappers**: Thread-safe UI integration for collectors

### 4. Data Processing (shared_tools/processors/)

- **PDF Extractor**: Text extraction from PDF documents
- **Text Extractor**: Processing of non-PDF documents
- **Corpus Balancer**: Domain distribution management

### 5. Configuration Management

- **ProjectConfig**: Environment and domain configuration
- **YAML Configuration**: Flexible configuration system
- **Environment Variables**: Secure API key management

## Design Patterns

### 1. Model-View-Controller (MVC)

- **Model**: Data collectors and processors
- **View**: PyQt6 UI components
- **Controller**: UI wrappers and signal/slot connections

### 2. Observer Pattern

- **Signals/Slots**: Qt's signal-slot mechanism for loose coupling
- **Event Handling**: Asynchronous communication between components

### 3. Factory Pattern

- **Wrapper Factory**: Dynamic creation of UI wrappers
- **Collector Factory**: Runtime collector instantiation

### 4. Worker Thread Pattern

- **Background Processing**: Non-blocking operations
- **Progress Reporting**: Real-time status updates
- **Thread Safety**: Proper Qt thread management

## Data Flow

1. **Configuration Loading**: ProjectConfig loads environment settings
2. **UI Initialization**: Main window creates all tabs and widgets
3. **Collector Integration**: Wrappers connect collectors to UI
4. **Data Collection**: Background threads collect data with progress reporting
5. **Data Processing**: Processors extract and clean collected data
6. **Corpus Management**: Balancer maintains domain distributions
7. **Analytics**: Real-time analysis and reporting of corpus state

## Extensibility

### Adding New Collectors

1. Create collector class inheriting from `BaseCollector`
2. Implement required methods (`collect`, etc.)
3. Create UI wrapper inheriting from `BaseWrapper`
4. Add to wrapper factory
5. Integrate into collectors tab

### Adding New Processors

1. Create processor class with standard interface
2. Create UI wrapper for thread management
3. Add to processor factory
4. Integrate into processors tab

### Adding New UI Components

1. Create widget/dialog inheriting from Qt components
2. Implement required signals and slots
3. Add styling and layout
4. Integrate into appropriate tab
```