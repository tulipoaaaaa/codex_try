# CryptoFinance Corpus Builder v3 - Installation Guide

## Prerequisites

- Python 3.8 or higher
- Windows 10/11 or Linux/macOS
- At least 4GB RAM
- 10GB free disk space (more for large corpora)

## Installation Steps

### 1. Virtual Environment Setup

Create and activate your virtual environment:

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```
#### Linux/macOS
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

With the virtual environment activated:

```bash
pip install -r requirements.txt
```

### 3. Editable Install (Recommended for Development)

```bash
pip install -e .
```

### 4. Configuration

Copy the sample configuration files:

```bash
cp shared_tools/test_config.yaml.sample shared_tools/test_config.yaml
cp shared_tools/master_config.yaml.sample shared_tools/master_config.yaml
```

Edit the configuration files to match your system paths and API keys.

### 5. Environment Variables

Create a `.env` file in the project root with your API keys:

```
# GitHub API Token
GITHUB_TOKEN=your_github_token_here

# Anna's Archive Cookie (if available)
AA_ACCOUNT_COOKIE=your_cookie_here

# FRED API Key
FRED_API_KEY=your_fred_key_here
```

### 6. Launch Application

```bash
python app/main.py
```

Or use the provided `launch_app.bat` (Windows only). 