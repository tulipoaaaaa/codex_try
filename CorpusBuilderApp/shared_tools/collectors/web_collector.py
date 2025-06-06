# sources/web_collector.py
from CryptoFinanceCorpusBuilder.shared_tools.collectors.base_collector import BaseCollector
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import os
import time
from typing import List, Dict, Optional, Union, Any
from pathlib import Path

class WebCollector(BaseCollector):
    """Base class for web scraping collectors"""
    
    def __init__(self, 
                 config: Union[str, 'ProjectConfig'],
                 base_url: str,
                 delay_range: tuple = (3, 7)):
        """Initialize the web collector.
        
        Args:
            config: ProjectConfig instance or path to config file
            base_url: Base URL for web scraping
            delay_range: Tuple of (min_delay, max_delay) in seconds between requests
        """
        super().__init__(config, delay_range)
        self.base_url = base_url
        self.visited_urls = set()
        self.respect_robots_txt = True
        self._robotstxt_parsers = {}
        self.logger.info("WebCollector initialized with base_url: %s", base_url)
    
    def fetch_page(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Fetch a web page with rate limiting and user agent rotation.
        
        Args:
            url: URL to fetch
            params: Query parameters for the request
            
        Returns:
            Page content as string, or None if fetch failed
        """
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
    
    def get_soup(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[BeautifulSoup]:
        """Get BeautifulSoup object for a URL.
        
        Args:
            url: URL to parse
            params: Query parameters for the request
            
        Returns:
            BeautifulSoup object, or None if fetch failed
        """
        html = self.fetch_page(url, params)
        if html:
            return BeautifulSoup(html, 'html.parser')
        return None
    
    def extract_links(self, 
                     soup: BeautifulSoup,
                     base_url: str,
                     pattern: Optional[str] = None) -> List[Dict[str, str]]:
        """Extract links from BeautifulSoup object, optionally filtering by pattern.
        
        Args:
            soup: BeautifulSoup object to extract links from
            base_url: Base URL for resolving relative links
            pattern: Regex pattern to filter links
            
        Returns:
            List of dictionaries containing link URLs and text
        """
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
    
    def download_links(self, 
                      links: List[Union[str, Dict[str, str]]],
                      subfolder: Optional[str] = None,
                      file_ext: Optional[str] = None) -> List[Dict[str, str]]:
        """Download files from a list of links.
        
        Args:
            links: List of links to download (strings or dicts with 'url' key)
            subfolder: Subfolder to save files in
            file_ext: File extension to filter downloads by
            
        Returns:
            List of dictionaries containing download results
        """
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
    
    def download_file(self, 
                     url: str,
                     filename: str,
                     subfolder: Optional[str] = None) -> Optional[Path]:
        """Download a file from a URL.
        
        Args:
            url: URL to download from
            filename: Name to save the file as
            subfolder: Subfolder to save the file in
            
        Returns:
            Path to the downloaded file, or None if download failed
        """
        try:
            # Determine domain from URL
            domain = urlparse(url).netloc
            domain = domain.replace('www.', '')
            
            # Create output path using domain-based structure
            if subfolder:
                filepath = self._get_output_path(domain, subfolder, filename)
            else:
                filepath = self._get_output_path(domain, 'downloads', filename)
            
            # Create parent directory if it doesn't exist
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Download the file
            self.logger.info(f"Downloading {url} to {filepath}")
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error downloading {url}: {e}")
            return None
    
    def _can_fetch(self, url: str) -> bool:
        """Check if robots.txt allows access to URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if robots.txt allows access, False otherwise
        """
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

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect data from a web source")
    parser.add_argument("--config", required=True, help="Path to config file")
    parser.add_argument("--url", required=True, help="URL of the web page to collect")
    parser.add_argument("--pattern", type=str, help="Regex pattern to filter links for download")
    parser.add_argument("--file-ext", type=str, help="Download only links with this file extension (e.g., pdf, csv)")
    parser.add_argument("--no-robots", action="store_true", help="Ignore robots.txt (not recommended)")
    
    args = parser.parse_args()
    
    collector = WebCollector(args.config, base_url=args.url)
    if args.no_robots:
        collector.respect_robots_txt = False
        
    print(f"[DEBUG] CLI args: {args}")
    print(f"[DEBUG] Respect robots.txt: {collector.respect_robots_txt}")
    print(f"[DEBUG] Fetching: {args.url}")
    
    soup = collector.get_soup(args.url)
    if not soup:
        print("[ERROR] Failed to fetch or parse the web page.")
        exit(1)
        
    links = collector.extract_links(soup, args.url, pattern=args.pattern)
    print(f"[DEBUG] Extracted {len(links)} links.")
    
    if args.file_ext:
        print(f"[DEBUG] Downloading links with extension: {args.file_ext}")
        
    results = collector.download_links(links, file_ext=args.file_ext)
    print(f"Collected {len(results)} web records. Output dir: {collector.output_dir}")
    
    if results:
        print("[DEBUG] Downloaded files:")
        for r in results:
            print(f"  - {r['filename']} from {r['url']}")