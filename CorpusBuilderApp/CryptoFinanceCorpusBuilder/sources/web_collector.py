# DEPRECATED: This file belongs to the legacy CryptoFinanceCorpusBuilder package and should not be used in new modules.
# sources/web_collector.py
from .base_collector import BaseCollector
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import os
import time

class WebCollector(BaseCollector):
    """Base class for web scraping collectors"""
    
    def __init__(self, output_dir, base_url, delay_range=(3, 7)):
        super().__init__(output_dir, delay_range)
        self.base_url = base_url
        self.visited_urls = set()
        self.respect_robots_txt = True
        self._robotstxt_parsers = {}
    
    def fetch_page(self, url, params=None):
        """Fetch a web page with rate limiting and user agent rotation"""
        self._respect_rate_limits(url)
        
        # Check robots.txt if enabled
        if self.respect_robots_txt and not self._can_fetch(url):
            self.logger.warning(f"Robots.txt disallows access to {url}")
            return None
        
        # Add to visited URLs
        self.visited_urls.add(url)
        
        # Make the request
        headers = {'User-Agent': self._get_random_user_agent()}
        try:
            self.logger.debug(f"Fetching page: {url}")
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None
    
    def get_soup(self, url, params=None):
        """Get BeautifulSoup object for a URL"""
        html = self.fetch_page(url, params)
        if html:
            return BeautifulSoup(html, 'html.parser')
        return None
    
    def extract_links(self, soup, base_url, pattern=None):
        """Extract links from BeautifulSoup object, optionally filtering by pattern"""
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(base_url, href)
            
            # Filter by pattern if provided
            if pattern and not re.search(pattern, full_url):
                continue
                
            links.append({
                'url': full_url,
                'text': a_tag.get_text(strip=True)
            })
            
        return links
    
    def download_links(self, links, subfolder=None, file_ext=None):
        """Download files from a list of links"""
        results = []
        
        for link in links:
            url = link['url'] if isinstance(link, dict) else link
            
            # Skip if not matching file extension
            if file_ext and not url.lower().endswith(file_ext.lower()):
                continue
                
            # Generate filename based on URL
            filename = os.path.basename(urlparse(url).path)
            if not filename:
                filename = f"download_{int(time.time())}"
                
            # Add extension if needed
            if file_ext and not filename.lower().endswith(file_ext.lower()):
                filename = f"{filename}.{file_ext.lstrip('.')}"
                
            # Download the file
            filepath = self.download_file(url, filename, subfolder)
            if filepath:
                results.append({
                    'url': url, 
                    'filepath': str(filepath),
                    'filename': filename
                })
                
        return results
    
    def _can_fetch(self, url):
        """Check if robots.txt allows access to URL"""
        try:
            from urllib.robotparser import RobotFileParser
            
            parsed_url = urlparse(url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Cache robotstxt parser
            if domain not in self._robotstxt_parsers:
                parser = RobotFileParser()
                parser.set_url(f"{domain}/robots.txt")
                parser.read()
                self._robotstxt_parsers[domain] = parser
            
            return self._robotstxt_parsers[domain].can_fetch(self._get_random_user_agent(), url)
        except Exception as e:
            self.logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True  # Default to allowing if error