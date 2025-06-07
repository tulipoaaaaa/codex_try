# DEPRECATED: This file belongs to the legacy CryptoFinanceCorpusBuilder package and should not be used in new modules.
# annas_archive_client.py
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import os
from pathlib import Path
from dotenv import load_dotenv

class SimpleAnnaArchiveClient:
    def __init__(self, download_dir=None):
        """Initialize a simplified Anna's Archive client"""
        # Load API key from environment
        load_dotenv("/workspace/notebooks/.env")
        self.api_key = os.getenv("ANNAS_API_KEY")
        
        # Base URL and download directory
        self.base_url = "https://annas-archive.org"
        self.download_dir = Path(download_dir) if download_dir else Path("/workspace/data/corpus_1/temp")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Session setup
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        # Add authentication cookie if API key is available
        if self.api_key:
            self.session.cookies.set("aa_key", self.api_key, domain="annas-archive.org")
            print("API key configured for authenticated requests")
        else:
            print("Warning: No API key found")
            
        print(f"SimpleAnnaArchiveClient initialized with download dir: {self.download_dir}")
    
    def search(self, query):
        """Search for books using regex to extract MD5s"""
        print(f"Searching for: '{query}'")
        
        # Make a GET request to the search page
        search_url = f"{self.base_url}/search"
        params = {"q": query}
        
        try:
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            # Extract MD5 hashes using regex
            md5_pattern = re.compile(r'md5:([a-f0-9]+)')
            md5_matches = md5_pattern.findall(response.text)
            
            print(f"Found {len(md5_matches)} MD5 hashes in the response")
            
            # If no results, return empty list
            if not md5_matches:
                print("No results found")
                return []
            
            # Parse HTML to extract more detailed info about the books
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for the result count text
            results_text = re.search(r'Results\s+(\d+)-(\d+)\s+\((\d+)\s+total\)', 
                                     response.text, re.IGNORECASE)
            if results_text:
                print(f"Results count: {results_text.group(0)}")
            
            # Find all book details divs
            results = []
            
            # First try to find result-like divs
            result_divs = soup.find_all('div', class_=lambda c: c and ('mb-4' in c))
            print(f"Found {len(result_divs)} result divs")
            
            # Process each result div
            for i, div in enumerate(result_divs):
                # Only process if we have MD5s left
                if i >= len(md5_matches):
                    break
                
                md5 = md5_matches[i]
                
                # Extract title - look for h3 tags
                title = "Unknown Title"
                h3 = div.find('h3')
                if h3:
                    title = h3.text.strip()
                
                # Extract file type and size info
                info_div = div.find('div', class_=lambda c: c and ('text-xs' in c))
                file_info = "Unknown format and size"
                if info_div:
                    file_info = info_div.text.strip()
                
                # Parse file type and size from info
                file_type = "Unknown"
                file_size = "Unknown"
                
                if 'pdf' in file_info.lower():
                    file_type = "pdf"
                elif 'epub' in file_info.lower():
                    file_type = "epub"
                
                size_match = re.search(r'(\d+(\.\d+)?\s*(MB|KB))', file_info)
                if size_match:
                    file_size = size_match.group(0)
                
                results.append({
                    "title": title,
                    "md5": md5,
                    "link": f"{self.base_url}/md5/{md5}",
                    "file_type": file_type,
                    "file_size": file_size,
                    "file_info": file_info
                })
            
            print(f"Successfully extracted {len(results)} book details")
            return results
            
        except Exception as e:
            print(f"Error searching for '{query}': {e}")
            return []
    
    def get_download_links(self, md5):
        """Get download links for a document with given MD5 hash"""
        print(f"Getting download links for MD5: {md5}")
        
        detail_url = f"{self.base_url}/md5/{md5}"
        
        try:
            response = self.session.get(detail_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            download_links = []
            
            # Find all links
            for link in soup.find_all("a", href=True):
                href = link.get("href")
                text = link.text.strip()
                
                # Check if it's a download link
                if href.startswith("http") and any(domain in href.lower() for domain in 
                                                ["libgen", "library", "sci-hub", "ipfs"]):
                    download_links.append({
                        "url": href,
                        "text": text
                    })
            
            print(f"Found {len(download_links)} download links")
            return download_links
            
        except Exception as e:
            print(f"Error getting download links: {e}")
            return []
    
    def download_file(self, url, filepath):
        """Download a file from given URL to specified filepath"""
        filepath = Path(filepath)
        
        # Check if file already exists
        if filepath.exists():
            print(f"File already exists: {filepath}")
            return filepath
        
        # Create parent directory if it doesn't exist
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            print(f"Downloading from {url} to {filepath}")
            
            # Download file with stream to handle large files
            with self.session.get(url, stream=True, timeout=60) as response:
                response.raise_for_status()
                
                # Stream the file to disk
                with open(filepath, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                
                print(f"Downloaded {downloaded / (1024*1024):.2f} MB")
            
            print(f"Successfully downloaded to {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error downloading: {e}")
            
            # Clean up partial download
            if filepath.exists():
                try:
                    os.remove(filepath)
                except:
                    pass
            
            return None