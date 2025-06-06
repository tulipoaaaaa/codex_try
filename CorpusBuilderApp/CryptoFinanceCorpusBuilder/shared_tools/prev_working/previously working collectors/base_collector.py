# sources/base_collector.py
import os
import logging
import random
import time
import requests
from urllib.parse import urlparse
from pathlib import Path

class BaseCollector:
    """Base class for all data collectors"""
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36'
    ]
    
    def __init__(self, output_dir, *args, **kwargs):
        # Accept either a ProjectConfig or a string path
        if hasattr(output_dir, 'raw_data_dir'):
            self.project_config = output_dir
            self.raw_data_dir = Path(output_dir.raw_data_dir)
        else:
            self.project_config = None
            self.raw_data_dir = Path(output_dir)
        self._setup_domain_directories()
        self.output_dir = self.raw_data_dir
        self.delay_range = (2, 5)
        self.session = requests.Session()
        
        # Configure logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
            # Add file handler with UTF-8 encoding
            file_handler = logging.FileHandler(f"{self.__class__.__name__.lower()}.log", encoding="utf-8")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _setup_domain_directories(self):
        """Create domain-based directory structure."""
        domains = [
            'crypto_derivatives',
            'high_frequency_trading',
            'portfolio_construction',
            'risk_management',
            'market_microstructure',
            'trading_strategies',
            'other'
        ]
        
        content_types = ['papers', 'reports', 'articles']
        
        for domain in domains:
            domain_dir = self.raw_data_dir / domain
            for content_type in content_types:
                (domain_dir / content_type).mkdir(parents=True, exist_ok=True)
    
    def _get_output_path(self, domain: str, content_type: str, filename: str) -> Path:
        """Get the correct output path based on domain and content type."""
        if domain not in ['crypto_derivatives', 'high_frequency_trading', 'portfolio_construction',
                         'risk_management', 'market_microstructure', 'trading_strategies']:
            domain = 'other'
            
        if content_type not in ['papers', 'reports', 'articles']:
            content_type = 'articles'
            
        return self.raw_data_dir / domain / content_type / filename
    
    def collect(self, query, max_items=100):
        """Main collection method to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement the collect method")
    
    def download_file(self, url, filename=None, subfolder=None):
        """Download a file with rate limiting and random user agent"""
        # Apply rate limiting
        self._respect_rate_limits(url)
        
        # Set destination path
        target_dir = self.output_dir
        if subfolder:
            target_dir = self.output_dir / subfolder
            target_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            url_parts = urlparse(url)
            filename = os.path.basename(url_parts.path)
            if not filename:
                filename = f"download_{int(time.time())}"
        
        filepath = target_dir / filename
        
        # Download the file
        headers = {'User-Agent': self._get_random_user_agent()}
        
        try:
            self.logger.info(f"Downloading {url} to {filepath}")
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            self.logger.info(f"Successfully downloaded {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Error downloading {url}: {e}")
            return None
    
    def _get_random_user_agent(self):
        """Return a random user agent string"""
        return random.choice(self.USER_AGENTS)
    
    def _respect_rate_limits(self, url):
        """Implement rate limiting based on domain"""
        domain = urlparse(url).netloc
        delay = random.uniform(*self.delay_range)
        self.logger.debug(f"Waiting {delay:.2f}s before requesting from {domain}")
        time.sleep(delay)