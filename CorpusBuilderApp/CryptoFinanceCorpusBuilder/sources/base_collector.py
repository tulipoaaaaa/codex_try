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
    
    def __init__(self, output_dir, delay_range=(2, 5)):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.delay_range = delay_range
        self.session = requests.Session()
        
        # Configure logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
            # Add file handler
            file_handler = logging.FileHandler(f"{self.__class__.__name__.lower()}.log")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
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