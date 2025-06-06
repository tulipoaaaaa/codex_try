Crypto-Finance Corpus Builder
A comprehensive system for collecting, processing, and organizing a corpus of crypto-finance content from multiple free resources. This tool builds a domain-specific corpus for research, analysis, and educational purposes.
Overview
The Crypto-Finance Corpus Builder systematically gathers content from various sources including academic repositories, research platforms, financial data providers, and specialized crypto resources. It extracts text, classifies content by domain, and organizes everything into a structured corpus.
Features

Multi-source Collection: Retrieve content from APIs, websites, and repositories
Domain Classification: Automatically categorize content into crypto-finance domains
Text Extraction: Process multiple file formats (PDF, HTML, EPUB, Jupyter notebooks)
Deduplication: Identify and remove duplicate content
Metadata Management: Track sources, domains, and content properties
Rate Limiting: Respect source limitations with configurable delays
Parallel Processing: Optional concurrent collection for faster execution

Project Structure
CryptoFinanceCorpus/
├── sources/                   # Source-specific collectors
│   ├── base_collector.py      # Abstract base class for all collectors
│   ├── api_collector.py       # Base class for API-based sources
│   ├── web_collector.py       # Base class for web scraping sources
│   ├── repo_collector.py      # Base class for repository sources
│   └── specific_collectors/   # Implementation for each source
│       ├── arxiv_collector.py
│       ├── github_collector.py
│       ├── fred_collector.py
│       ├── quantopian_collector.py
│       ├── bitmex_collector.py
│       ├── isda_collector.py
│       └── ...
├── processors/                # Content processors
│   ├── text_extractor.py      # Extract text from various formats
│   ├── deduplicator.py        # Remove duplicates
│   └── domain_classifier.py   # Classify by domain
├── storage/                   # Storage management
│   └── corpus_manager.py      # Manage the corpus structure
├── cli/                       # Command-line interface
│   └── crypto_corpus_cli.py   # Main CLI entry point
├── config/                    # Configuration files
│   ├── domain_config.py       # Domain definitions
│   └── sources.json           # Source-specific settings
└── data/                      # Output directory
    └── corpus/                # Corpus storage location
        ├── crypto_derivatives/
        ├── high_frequency_trading/
        ├── market_microstructure/
        └── ...
Installation

Clone the repository:

bashgit clone https://github.com/yourusername/crypto-finance-corpus.git
cd crypto-finance-corpus

Install dependencies:

bashpip install -r requirements.txt

Set up API keys (if needed):

bash# Create .env file with your API keys
echo "FRED_API_KEY=your_fred_api_key" > .env
Usage
Collecting Data
Collect data from all configured sources:
bashpython cli/crypto_corpus_cli.py collect --config config/sources.json --output-dir data/corpus
Collect from specific sources:
bashpython cli/crypto_corpus_cli.py collect --sources arxiv github fred --output-dir data/corpus
Collect for specific domains:
bashpython cli/crypto_corpus_cli.py collect --domains crypto_derivatives high_frequency_trading --output-dir data/corpus
Enable parallel collection:
bashpython cli/crypto_corpus_cli.py collect --parallel --output-dir data/corpus
Processing Data
Process previously collected data:
bashpython cli/crypto_corpus_cli.py process --input-dir data/collected --output-dir data/corpus
Generating Statistics
Get corpus statistics:
bashpython cli/crypto_corpus_cli.py stats --corpus-dir data/corpus
Configuration
Source Configuration
Edit config/sources.json to configure sources:
json{
  "arxiv": {
    "source_type": "api",
    "search_terms": ["cryptocurrency trading", "bitcoin price prediction"],
    "max_results": 200
  },
  "github": {
    "source_type": "repository",
    "topics": ["cryptocurrency-trading", "crypto-trading-bot"],
    "max_repos": 20
  }
}
Domain Configuration
Edit config/domain_config.py to configure domains:
pythonDOMAINS = {
    "crypto_derivatives": {
        "allocation": 0.20,
        "search_terms": [
            "cryptocurrency derivatives", "bitcoin futures", "crypto options"
        ]
    },
    "high_frequency_trading": {
        "allocation": 0.15,
        "search_terms": [
            "high frequency trading cryptocurrency", "algorithmic crypto trading"
        ]
    }
}
Adding New Sources

Create a new collector class in sources/specific_collectors/
Implement the collect() method to retrieve data
Add the source to config/sources.json
Register the collector in the CLI script

Domain Organization
The corpus is organized into the following domains:

crypto_derivatives (20%): Cryptocurrency derivatives, futures, options
high_frequency_trading (15%): Algorithmic and high-frequency trading
market_microstructure (15%): Order books, liquidity, price formation
risk_management (15%): Risk models, hedging, portfolio protection
decentralized_finance (12%): DeFi protocols, lending, AMMs
portfolio_construction (10%): Asset allocation, correlation analysis
valuation_models (8%): Token metrics, pricing frameworks
regulation_compliance (5%): Legal frameworks, taxation, compliance

License
This project is licensed under the MIT License - see the LICENSE file for details.
Acknowledgments

arXiv for research papers
GitHub for open-source trading repositories
Federal Reserve Economic Data (FRED) for market data
Quantopian for algorithmic trading resources
BitMEX Research for crypto derivatives analysis
And all other data providers

Updates to README.md (Adding Quickstart and Example Workflow)
Let me add a quickstart guide and example workflow to the README:
markdown## Quickstart Guide

### Minimum Setup (5 minutes)

1. Install dependencies:
```bash
pip install requests beautifulsoup4 pandas numpy scikit-learn pypdf2 ebooklib python-docx

Configure API keys (create a .env file in the project root):

FRED_API_KEY=your_fred_api_key
GITHUB_API_KEY=your_github_personal_access_token

Run a quick test collection from a single source:

bashpython cli/crypto_corpus_cli.py collect --sources arxiv --config config/sources.json --output-dir data/test_corpus

View collection statistics:

bashpython cli/crypto_corpus_cli.py stats --corpus-dir data/test_corpus
Example Workflow
1. Collect from High-Priority Sources (1-2 hours)
bash# Create base directories
mkdir -p data/corpus

# Collect from arXiv (academic papers)
python cli/crypto_corpus_cli.py collect --sources arxiv --config config/sources.json --output-dir data/corpus

# Collect from BitMEX Research (crypto derivatives analysis)
python cli/crypto_corpus_cli.py collect --sources bitmex_research --config config/sources.json --output-dir data/corpus

# Collect from Quantopian (algorithmic trading)
python cli/crypto_corpus_cli.py collect --sources quantopian --config config/sources.json --output-dir data/corpus
2. Process and Classify Content (20-30 minutes)
bash# Extract text from all collected documents
python cli/crypto_corpus_cli.py process --input-dir data/corpus --output-dir data/corpus_processed

# Check statistics after processing
python cli/crypto_corpus_cli.py stats --corpus-dir data/corpus_processed
3. Run Deduplication (10-15 minutes)
bash# Create a deduplication report without removing files
python -c "from processors.deduplicator import Deduplicator; d = Deduplicator('data/corpus_processed'); d.find_duplicates()"

# Run deduplication, keeping the largest file in each duplicate group
python -c "from processors.deduplicator import Deduplicator; d = Deduplicator('data/corpus_processed'); d.deduplicate(strategy='keep_largest', output_file='data/dedup_report.json')"
4. Collect from More Sources (2-3 hours)
bash# Collect from FRED (economic data)
python cli/crypto_corpus_cli.py collect --sources fred --config config/sources.json --output-dir data/corpus_processed

# Collect from GitHub repositories
python cli/crypto_corpus_cli.py collect --sources github --config config/sources.json --output-dir data/corpus_processed
5. Generate Final Statistics (5 minutes)
bash# Generate comprehensive statistics
python cli/crypto_corpus_cli.py stats --corpus-dir data/corpus_processed

Common Tasks
Add a New Source

Create a new collector in sources/specific_collectors/:

python# sources/specific_collectors/new_source_collector.py
from ..web_collector import WebCollector

class NewSourceCollector(WebCollector):
    def __init__(self, output_dir, delay_range=(3, 7)):
        super().__init__(output_dir, base_url='https://example.com/research', delay_range=delay_range)
    
    def collect(self, max_pages=5):
        # Implementation here
        pass

Add the source to config/sources.json:

json{
  "new_source": {
    "source_type": "web",
    "base_url": "https://example.com/research",
    "max_pages": 5,
    "domain": "market_microstructure"
  }
}

Register the collector in cli/crypto_corpus_cli.py (in the collect_from_source function).

Extract Text from a Specific Format
pythonfrom processors.text_extractor import TextExtractor

# Initialize text extractor
extractor = TextExtractor()

# Extract text from a PDF
pdf_result = extractor.extract("path/to/document.pdf")

# Extract text from a Jupyter notebook
notebook_result = extractor.extract("path/to/notebook.ipynb")

# Print extracted text
print(pdf_result["text"])
Classify Content into Domains
pythonfrom processors.domain_classifier import DomainClassifier

# Initialize classifier
classifier = DomainClassifier()

# Classify a document by its text and title
classification = classifier.classify(text_content, document_title)

# Print classification results
print(f"Best domain: {classification['domain']}")
print(f"Confidence: {classification['confidence']}")
print(f"All scores: {classification['scores']}")

# Generic Web Collector Implementation

Let's improve the implementation of the generic WebCollector to make it more robust for handling new web sources:

```python
# sources/web_collector.py
# Updated with more robust generic collection capabilities

from .base_collector import BaseCollector
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import os
import time
import json
import logging
from pathlib import Path

class WebCollector(BaseCollector):
    """Base class for web scraping collectors with generic collection capabilities"""
    
    def __init__(self, output_dir, base_url, delay_range=(3, 7)):
        super().__init__(output_dir, delay_range)
        self.base_url = base_url
        self.visited_urls = set()
        self.respect_robots_txt = True
        self._robotstxt_parsers = {}
        
        # For generic collection
        self.target_file_types = ['.pdf', '.html', '.txt', '.md', '.ipynb', '.csv']
    
    def collect(self, max_pages=5, file_types=None, search_terms=None, domain=None):
        """Generic collection method for any web source
        
        Args:
            max_pages (int): Maximum number of pages to crawl
            file_types (list): List of file extensions to download (e.g., ['.pdf', '.html'])
            search_terms (list): Optional search terms to append to URLs
            domain (str): Domain to categorize the collected data
            
        Returns:
            list: Collected resources
        """
        self.logger.info(f"Starting generic collection from {self.base_url}")
        
        # Use specified file types or default ones
        target_file_types = file_types if file_types else self.target_file_types
        self.logger.info(f"Targeting file types: {target_file_types}")
        
        # Track all collected resources
        collected_resources = []
        
        # Start URLs - either base URL or search URLs if search terms provided
        start_urls = []
        if search_terms:
            for term in search_terms:
                # Construct search URL - handles common patterns
                search_url = self._construct_search_url(term)
                if search_url:
                    start_urls.append((search_url, term))
        else:
            start_urls.append((self.base_url, None))
        
        # Process each start URL
        for start_url, search_term in start_urls:
            self.logger.info(f"Processing URL: {start_url}" + 
                            (f" (search: {search_term})" if search_term else ""))
            
            # Queue of pages to process (URL, page number)
            page_queue = [(start_url, 1)]
            processed_pages = set()
            
            # Process pages until queue is empty or max_pages reached
            while page_queue and len(processed_pages) < max_pages:
                # Get next URL and page number from queue
                current_url, page_num = page_queue.pop(0)
                
                # Skip if already processed
                if current_url in processed_pages:
                    continue
                
                self.logger.info(f"Fetching page {page_num}: {current_url}")
                
                # Fetch and parse page
                soup = self.get_soup(current_url)
                if not soup:
                    self.logger.warning(f"Failed to fetch: {current_url}")
                    continue
                
                # Mark as processed
                processed_pages.add(current_url)
                
                # Extract links from the page
                all_links = self.extract_links(soup, current_url)
                
                # Process download links (files with target extensions)
                download_links = [link for link in all_links 
                                  if any(link['url'].lower().endswith(ext) for ext in target_file_types)]
                
                if download_links:
                    self.logger.info(f"Found {len(download_links)} downloadable files on page")
                    
                    # Download files
                    downloads = self.download_links(download_links)
                    
                    # Add to collected resources
                    for download in downloads:
                        resource = {
                            'url': download['url'],
                            'filepath': download['filepath'],
                            'filename': download['filename'],
                            'source_url': current_url,
                            'search_term': search_term
                        }
                        collected_resources.append(resource)
                
                # Find pagination links for next pages
                if len(processed_pages) < max_pages:
                    next_page_url = self._find_next_page(soup, current_url, page_num)
                    if next_page_url and next_page_url not in processed_pages:
                        page_queue.append((next_page_url, page_num + 1))
                    
                # Add delay between pages
                time.sleep(self.delay_range[1])
        
        # Save collection metadata
        self._save_collection_metadata(collected_resources, domain)
        
        self.logger.info(f"Completed generic collection with {len(collected_resources)} resources")
        return collected_resources
    
    def _construct_search_url(self, search_term):
        """Construct a search URL based on common patterns"""
        # Try to determine search pattern based on base URL
        parsed_url = urlparse(self.base_url)
        domain = parsed_url.netloc
        
        # Common search URL patterns by domain
        if 'arxiv.org' in domain:
            return f"{self.base_url}search/?query={search_term}&searchtype=all"
        elif 'github.com' in domain:
            return f"{self.base_url}/search?q={search_term}"
        elif 'ssrn.com' in domain:
            return f"{self.base_url}/search?q={search_term}"
        elif 'researchgate.net' in domain:
            return f"{self.base_url}/search?q={search_term}"
        elif 'nber.org' in domain:
            return f"{self.base_url}/papers?q={search_term}"
        elif 'bis.org' in domain:
            return f"{self.base_url}/search.htm?q={search_term}"
        elif 'imf.org' in domain:
            return f"{self.base_url}/search?q={search_term}"
        
        # Generic approach - append 'search' and 'q' parameter
        return f"{self.base_url}/search?q={search_term}"
    
    def _find_next_page(self, soup, current_url, current_page):
        """Find URL for the next page of results"""
        # Strategy 1: Look for 'next' links
        next_links = soup.find_all('a', text=re.compile(r'next|>', re.I))
        if not next_links:
            next_links = soup.find_all('a', title=re.compile(r'next|>', re.I))
        if not next_links:
            next_links = soup.find_all('a', class_=re.compile(r'next', re.I))
        
        if next_links:
            for link in next_links:
                if link.has_attr('href'):
                    return urljoin(current_url, link['href'])
        
        # Strategy 2: Modify current URL - pagination pattern with page=X
        parsed_url = urlparse(current_url)
        query_params = parsed_url.query.split('&')
        
        # Check if there's a 'page' parameter
        page_param_found = False
        new_query_parts = []
        
        for param in query_params:
            if 'page=' in param:
                page_param_found = True
                # Extract page number and increment
                page_match = re.search(r'page=(\d+)', param)
                if page_match:
                    page_num = int(page_match.group(1))
                    new_query_parts.append(f"page={page_num + 1}")
                else:
                    new_query_parts.append(f"page={current_page + 1}")
            else:
                new_query_parts.append(param)
        
        # If no page parameter found, add it
        if not page_param_found:
            new_query_parts.append(f"page={current_page + 1}")
        
        # Construct new URL
        new_query = '&'.join(new_query_parts)
        next_url_parts = list(parsed_url)
        next_url_parts[4] = new_query
        
        from urllib.parse import urlunparse
        return urlunparse(next_url_parts)
    
    def _save_collection_metadata(self, resources, domain=None):
        """Save metadata about collected resources"""
        if not resources:
            return
        
        # Create metadata object
        metadata = {
            'source': self.base_url,
            'collection_date': datetime.datetime.now().isoformat(),
            'resources': resources,
            'domain': domain,
            'total_count': len(resources)
        }
        
        # Save metadata to file
        metadata_file = self.output_dir / "collection_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.logger.info(f"Saved collection metadata to {metadata_file}")
    
    UPDATE

    markdown# Crypto-Finance Corpus Builder

A comprehensive system for building a domain-specific corpus of cryptocurrency and financial documents from multiple sources.

## Overview

This project aims to create a substantial corpus (15-20GB) of high-quality crypto-finance content organized by domain. It automatically downloads content from various sources (academic repositories, trading forums, research sites) and structures it for research and analysis.

## Installation

### Prerequisites
- Python 3.8+
- Git
- Docker (optional, for containerized execution)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/crypto-finance-corpus-builder.git
   cd crypto-finance-corpus-builder

Install dependencies:
bashpip install -r requirements.txt

API Keys setup (optional but recommended):

Create a .env file in the project root with your API keys:
FRED_API_KEY=your_fred_api_key
GITHUB_API_KEY=your_github_api_key
AA_ACCOUNT_COOKIE=your_annas_archive_cookie




Directory Structure
CryptoFinanceCorpusBuilder/
├── sources/                   # Source collectors
│   ├── __init__.py            # Package init (IMPORTANT!)
│   ├── base_collector.py      # Base collector class
│   ├── api_collector.py       # API-based collector
│   ├── web_collector.py       # Web scraping collector
│   ├── repo_collector.py      # Repository collector
│   └── specific_collectors/   # Specific implementations
│       ├── __init__.py        # Package init (IMPORTANT!)
│       ├── arvix_collector.py # arXiv papers collector
│       ├── github_collector.py # GitHub repositories collector
│       ├── fred_collector.py  # FRED economic data collector
│       └── ...
├── processors/                # Content processors
├── storage/                   # Storage management
├── cli/                       # Command-line interface
└── data/                      # Output directory
    └── corpus/                # Corpus storage location
Important Notes on Python Imports
This project uses absolute imports for modules. When running scripts directly or in notebooks, you need to add the project directory to your Python path:
pythonimport sys
import os

# Add project root to Python path
sys.path.append('/path/to/CryptoFinanceCorpusBuilder')

# Now you can import modules like:
from sources.specific_collectors.arvix_collector import ArxivCollector
Example Usage
Testing Individual Collectors
arXiv Collector
pythonimport sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Add project root to Python path
sys.path.append('/path/to/CryptoFinanceCorpusBuilder')

# Create output directory
output_dir = Path("/path/to/output/arxiv")
os.makedirs(output_dir, exist_ok=True)

# Import and initialize the collector
from sources.specific_collectors.arvix_collector import ArxivCollector
collector = ArxivCollector(output_dir)

# Run the collector
results = collector.collect(
    search_terms=["cryptocurrency trading", "bitcoin price prediction"],
    max_results=3
)

# Print results
print(f"Downloaded {len(results)} papers")
for paper in results:
    print(f"Title: {paper.get('title')}")
    print(f"File: {paper.get('filepath', 'Not downloaded')}")
    print('-' * 50)
GitHub Collector (ZIP approach)
pythonimport sys
import os
import requests
import zipfile
import io
from pathlib import Path

# Add project root to Python path
sys.path.append('/path/to/CryptoFinanceCorpusBuilder')

# Create output directory
output_dir = Path("/path/to/output/github")
os.makedirs(output_dir, exist_ok=True)

# Function to download GitHub repo as ZIP
def download_github_repo(repo_name, output_path):
    zip_url = f"https://github.com/{repo_name}/archive/refs/heads/main.zip"
    print(f"Downloading from: {zip_url}")
    
    response = requests.get(zip_url, stream=True)
    if response.status_code == 404:
        zip_url = f"https://github.com/{repo_name}/archive/refs/heads/master.zip"
        print(f"Trying master branch: {zip_url}")
        response = requests.get(zip_url, stream=True)
    
    response.raise_for_status()
    
    z = zipfile.ZipFile(io.BytesIO(response.content))
    z.extractall(output_path)
    
    # Get the extracted directory name
    extracted_dirs = [d for d in os.listdir(output_path) if os.path.isdir(os.path.join(output_path, d))]
    if extracted_dirs:
        return os.path.join(output_path, extracted_dirs[0])
    return None

# Download a repository
repo_path = download_github_repo("freqtrade/freqtrade", output_dir)
print(f"Downloaded to: {repo_path}")
Command Line Usage
To run the corpus builder with default settings:
bashpython cli/crypto_corpus_cli.py collect --config config/sources.json --output-dir data/corpus
To collect from specific sources:
bashpython cli/crypto_corpus_cli.py collect --sources arxiv github --output-dir data/corpus
Troubleshooting
Import Errors
If you see errors like ModuleNotFoundError: No module named 'sources.web_collector':

Make sure the project root is in your Python path
Verify that __init__.py files exist in both sources/ and sources/specific_collectors/ directories
Use absolute imports (e.g., from sources.web_collector import WebCollector) rather than relative imports

Permission Errors with GitHub Collector
If you get permission errors when cloning repositories, try the ZIP download approach as shown in the examples.
Rate Limiting
Many collectors implement rate limiting to respect API usage policies. If you're hitting rate limits:

Reduce the number of requests by limiting max_results or max_pages
Use valid API keys where possible
Add delay parameters to slow down requests

License
MIT License