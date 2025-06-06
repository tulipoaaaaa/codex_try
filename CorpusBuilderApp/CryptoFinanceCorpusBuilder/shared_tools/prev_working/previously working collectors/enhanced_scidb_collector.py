# sources/specific_collectors/scidb_collector.py
"""
Collector for SciDB academic papers
"""

import os
import re
import json
import time
import random
import logging
from pathlib import Path
from urllib.parse import quote, unquote, urlparse, parse_qs
from dotenv import load_dotenv

# Add parent directory to path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sources.base_collector import BaseCollector
from .enhanced_client import CookieAuthClient

class SciDBCollector(BaseCollector):
    """Collector for SciDB academic papers with focus on finance and crypto"""
    
    def __init__(self, output_dir, delay_range=(3, 7), account_cookie=None):
        super().__init__(output_dir, delay_range)
        
        # Load API key from environment if not provided
        self.account_cookie = account_cookie
        if not self.account_cookie:
            # Try loading from current directory first
            load_dotenv()
            self.account_cookie = os.getenv("AA_ACCOUNT_COOKIE")
            
            # If not found, try project root
            if not self.account_cookie:
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
                load_dotenv(os.path.join(project_root, '.env'))
                self.account_cookie = os.getenv("AA_ACCOUNT_COOKIE")
                
            if not self.account_cookie:
                self.logger.warning("No AA_ACCOUNT_COOKIE found in environment or .env files")
        
        # Set up specialized headers for SciDB
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        })
        
        # Set authentication cookie if available
        if self.account_cookie:
            self.session.cookies.set(
                "aa_account_id2", 
                self.account_cookie, 
                domain="annas-archive.org",
                path="/"
            )
            self.logger.info("Set aa_account_id2 authentication cookie")
        else:
            self.logger.warning("No authentication cookie available")
        
        # Initialize domain mapping for classification
        self.domain_mapping = {
            "portfolio management": "portfolio_construction",
            "portfolio optimization": "portfolio_construction",
            "asset allocation": "portfolio_construction",
            "factor investing": "portfolio_construction",
            
            "risk management": "risk_management",
            "value at risk": "risk_management",
            "volatility": "risk_management",
            "hedging": "risk_management",
            
            "regulation": "regulation_compliance",
            "compliance": "regulation_compliance",
            "legal": "regulation_compliance",
            "law": "regulation_compliance",
            
            "defi": "decentralized_finance",
            "decentralized finance": "decentralized_finance",
            "automated market maker": "decentralized_finance",
            "liquidity pool": "decentralized_finance",
            
            "valuation": "valuation_models",
            "pricing model": "valuation_models",
            "token economics": "valuation_models",
            "asset pricing": "valuation_models",
            
            "high frequency": "high_frequency_trading",
            "algorithmic trading": "high_frequency_trading",
            "market making": "high_frequency_trading",
            "execution algorithm": "high_frequency_trading",
            
            "market microstructure": "market_microstructure",
            "order book": "market_microstructure",
            "limit order": "market_microstructure",
            "price discovery": "market_microstructure",
            
            "derivative": "crypto_derivatives",
            "futures": "crypto_derivatives",
            "options": "crypto_derivatives",
            "swap": "crypto_derivatives"
        }
    
    def collect_by_doi(self, doi_list, domain_mapping=None):
        """
        Collect papers by DOI using CookieAuthClient for robust downloads.
        
        Args:
            doi_list (list): List of DOIs to collect
            domain_mapping (dict): Optional mapping of DOIs to domains
            
        Returns:
            list: List of collected papers with metadata
        """
        collected_papers = []
        
        # Initialize CookieAuthClient for DOI downloads
        client = CookieAuthClient(download_dir=str(self.output_dir), account_cookie=self.account_cookie)
        
        for i, doi_item in enumerate(doi_list):
            # Extract DOI and domain
            if isinstance(doi_item, dict):
                doi = doi_item.get('doi')
                domain = doi_item.get('domain')
            else:
                doi = doi_item
                domain = None
                
            # Use domain from mapping if provided
            if domain_mapping and doi in domain_mapping:
                domain = domain_mapping[doi]
            
            self.logger.info(f"Collecting paper {i+1}/{len(doi_list)}: DOI {doi}")
            
            try:
                # Use CookieAuthClient to download the paper by DOI
                downloaded_file = client.download_scidb_doi(doi, domain=domain)
                
                if downloaded_file:
                    # Create paper_info from downloaded file metadata
                    meta_file = downloaded_file + ".meta"
                    if os.path.exists(meta_file):
                        with open(meta_file, 'r', encoding='utf-8') as f:
                            paper_info = json.load(f)
                    else:
                        paper_info = {'doi': doi, 'title': f"DOI {doi}", 'domain': domain}
                    
                    paper_info['filepath'] = downloaded_file
                    collected_papers.append(paper_info)
                    self.logger.info(f"Successfully downloaded paper: {paper_info.get('title')}")
                else:
                    self.logger.warning(f"Failed to download paper with DOI: {doi}")
                
                # Delay between papers
                delay = random.uniform(*self.delay_range)
                time.sleep(delay)
                
            except Exception as e:
                self.logger.error(f"Error collecting DOI {doi}: {e}")
        
        return collected_papers
    
    def collect_by_search(self, search_terms, max_results_per_term=10, prefer_domain=None):
        """
        Collect papers by search terms
        
        Args:
            search_terms (list): List of search terms
            max_results_per_term (int): Maximum results per search term
            prefer_domain (str): Preferred domain for classification
            
        Returns:
            list: List of collected papers with metadata
        """
        collected_papers = []
        
        for i, term in enumerate(search_terms):
            self.logger.info(f"Searching for term {i+1}/{len(search_terms)}: '{term}'")
            
            try:
                # Search for papers
                search_results = self._search_by_term(term, max_results=max_results_per_term)
                
                if not search_results:
                    self.logger.warning(f"No results found for term: '{term}'")
                    continue
                
                self.logger.info(f"Found {len(search_results)} results for term: '{term}'")
                
                # Process each result
                for j, paper_info in enumerate(search_results):
                    # Determine domain from search term or title
                    domain = self._determine_domain(paper_info, term, prefer_domain)
                    paper_info['domain'] = domain
                    
                    # Download the paper
                    downloaded_file = self._download_paper(paper_info)
                    
                    if downloaded_file:
                        paper_info['filepath'] = str(downloaded_file)
                        collected_papers.append(paper_info)
                        self.logger.info(f"Successfully downloaded paper ({j+1}/{len(search_results)}): {paper_info.get('title')}")
                    else:
                        self.logger.warning(f"Failed to download paper: {paper_info.get('title')}")
                    
                    # Delay between papers
                    delay = random.uniform(*self.delay_range)
                    time.sleep(delay)
                
                # Delay between search terms
                delay = random.uniform(*self.delay_range) * 2
                time.sleep(delay)
                
            except Exception as e:
                self.logger.error(f"Error searching for term '{term}': {e}")
        
        return collected_papers
    
    def _search_by_doi(self, doi):
        """Search for a paper by DOI (robust, browser-like logic)"""
        from bs4 import BeautifulSoup
        from urllib.parse import unquote, urlparse, parse_qs
        encoded_doi = quote(doi)
        # Use the browser-mimicking endpoint
        direct_url = f"https://annas-archive.org/scidb/{doi}/"
        response = self.session.get(direct_url, allow_redirects=True)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Try to find iframe for PDF viewer
        download_url = None
        iframe = soup.find('iframe', src=lambda x: x and 'viewer.html?file=' in x)
        if iframe:
            src = iframe['src']
            parsed = urlparse(src)
            qs = parse_qs(parsed.query)
            file_url = qs.get('file', [None])[0]
            if file_url:
                download_url = unquote(file_url)
        # Fallback: look for direct PDF links
        if not download_url:
            for link in soup.find_all('a'):
                link_text = link.text.lower() if link.text else ""
                href = link.get('href', '')
                if ('download' in link_text or 'pdf' in link_text) and ('.pdf' in href or '/lib/' in href):
                    download_url = href if href.startswith('http') else "https://annas-archive.org" + href
                    break
        # Extract paper information
        paper_info = {'doi': doi}
        # Parse title
        title = None
        for elem in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            text = elem.text.strip()
            if text and len(text) > 10 and text not in ["Anna's Archive", "SciDB"]:
                title = text
                break
        if title:
            paper_info['title'] = title
        # If we found a download URL, try to extract MD5 from it if possible
        if download_url:
            md5_match = re.search(r'/md5/([a-f0-9]+)', download_url)
            if md5_match:
                paper_info['md5'] = md5_match.group(1)
            paper_info['download_url'] = download_url
        # If we have at least a title and download_url, return the info
        if 'title' in paper_info and 'download_url' in paper_info:
            return paper_info
        return None
    
    def _search_by_term(self, term, max_results=10):
        """Search for papers by term"""
        # URL encode the term
        encoded_term = quote(term)
        
        # Search URL
        search_url = f"https://annas-archive.org/search?q=site:scidb.org+{encoded_term}"
        
        try:
            # Fetch the search page
            response = self.session.get(search_url)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check if results found
            if "No results found" in response.text:
                return []
            
            # Find all result containers
            results = []
            result_divs = soup.find_all("div", class_=lambda c: c and "mb-4" in c)
            
            for div in result_divs[:max_results]:
                # Extract title and URL
                link_elem = div.find("a", href=lambda h: h and "/md5/" in h)
                if not link_elem:
                    continue
                
                href = link_elem.get("href", "")
                md5_match = re.search(r"/md5/([a-f0-9]+)", href)
                
                if not md5_match:
                    continue
                
                md5 = md5_match.group(1)
                title = link_elem.get_text().strip()
                
                # Extract file info
                file_info = "Unknown format and size"
                info_div = div.find("div", class_=lambda c: c and "text-xs" in c)
                if info_div:
                    file_info = info_div.get_text().strip()
                
                # Check if it's a PDF
                if "pdf" not in file_info.lower():
                    continue
                
                # Create paper info
                paper_info = {
                    "title": title,
                    "md5": md5,
                    "link": f"https://annas-archive.org/md5/{md5}",
                    "file_info": file_info,
                    "search_term": term
                }
                
                results.append(paper_info)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching for term {term}: {e}")
            return []
    
    def _download_paper(self, paper_info):
        """Download a paper using its MD5 hash"""
        md5 = paper_info.get('md5')
        if not md5:
            return None
        
        title = paper_info.get('title', 'Unknown')
        domain = paper_info.get('domain', 'unknown')
        
        # Create domain directory if it doesn't exist
        domain_dir = self.output_dir / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean filename
        safe_title = re.sub(r'[^\w\s-]', '', title).strip()
        safe_title = re.sub(r'[-\s]+', '-', safe_title)
        if len(safe_title) > 100:
            safe_title = safe_title[:100]
            
        # Create filepath
        filepath = domain_dir / f"{safe_title}_{md5[:8]}.pdf"
        
        # Check if already downloaded
        if filepath.exists():
            self.logger.info(f"File already exists: {filepath}")
            return filepath
        
        try:
            # First visit the details page to set up proper referrer
            detail_url = f"https://annas-archive.org/md5/{md5}"
            self.logger.info(f"Visiting details page: {detail_url}")
            
            detail_response = self.session.get(detail_url)
            detail_response.raise_for_status()
            
            # Direct access to server 0 which usually works best for academic papers
            download_url = f"https://annas-archive.org/fast_download/{md5}/0/0"
            self.logger.info(f"Downloading PDF from: {download_url}")
            
            download_response = self.session.get(
                download_url,
                headers={"Referer": detail_url},
                allow_redirects=True,
                timeout=60  # Increase timeout for large files
            )
            
            # Check if it's a PDF
            content_type = download_response.headers.get("Content-Type", "").lower()
            
            if "application/pdf" in content_type:
                self.logger.info(f"Received PDF content. Saving to file...")
                with open(filepath, "wb") as f:
                    f.write(download_response.content)
                
                self.logger.info(f"PDF saved to: {filepath}")
                
                # Check if the PDF is valid
                if self._check_file_validity(filepath):
                    # Save metadata
                    meta_file = filepath.with_suffix(f"{filepath.suffix}.meta")
                    with open(meta_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'title': title,
                            'md5': md5,
                            'file_info': paper_info.get('file_info', ''),
                            'doi': paper_info.get('doi', ''),
                            'authors': paper_info.get('authors', ''),
                            'domain': domain,
                            'publication_info': paper_info.get('publication_info', ''),
                            'search_term': paper_info.get('search_term', ''),
                            'download_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'source': 'scidb'
                        }, f, indent=2)
                    
                    return filepath
                else:
                    self.logger.warning(f"Downloaded file is not a valid PDF. Removing...")
                    # Try to remove invalid file
                    try:
                        os.remove(filepath)
                    except:
                        pass
            else:
                # If we got HTML instead of PDF, check if it has membership wall
                if "Become a member" in download_response.text:
                    self.logger.error(f"Hit membership wall - authentication may have failed")
                    return None
            
            # First server didn't work, try server 1
            alt_download_url = f"https://annas-archive.org/fast_download/{md5}/0/1"
            self.logger.info(f"Trying alternative server: {alt_download_url}")
            
            alt_response = self.session.get(
                alt_download_url,
                headers={"Referer": detail_url},
                allow_redirects=True,
                timeout=60
            )
            
            # Check if it's a PDF
            alt_content_type = alt_response.headers.get("Content-Type", "").lower()
            
            if "application/pdf" in alt_content_type:
                self.logger.info(f"Received PDF from alternative server. Saving to file...")
                with open(filepath, "wb") as f:
                    f.write(alt_response.content)
                
                # Check if the PDF is valid
                if self._check_file_validity(filepath):
                    self.logger.info(f"PDF saved to: {filepath}")
                    
                    # Save metadata
                    meta_file = filepath.with_suffix(f"{filepath.suffix}.meta")
                    with open(meta_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'title': title,
                            'md5': md5,
                            'file_info': paper_info.get('file_info', ''),
                            'doi': paper_info.get('doi', ''),
                            'authors': paper_info.get('authors', ''),
                            'domain': domain,
                            'publication_info': paper_info.get('publication_info', ''),
                            'search_term': paper_info.get('search_term', ''),
                            'download_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'source': 'scidb'
                        }, f, indent=2)
                    
                    return filepath
                else:
                    self.logger.warning(f"Downloaded file is not a valid PDF.")
                    # Try to remove invalid file
                    try:
                        os.remove(filepath)
                    except:
                        pass
            
            self.logger.error(f"Could not download a valid PDF.")
            return None
            
        except Exception as e:
            self.logger.error(f"Error downloading file: {e}")
            return None
    
    def _check_file_validity(self, filepath):
        """Check if file is a valid PDF"""
        if not os.path.exists(filepath):
            self.logger.error(f"File does not exist: {filepath}")
            return False
            
        try:
            # Check file size - reject extremely small files
            file_size = os.path.getsize(filepath)
            if file_size < 10000:  # Less than 10KB
                self.logger.warning(f"File too small to be a valid PDF: {file_size/1024:.1f} KB")
                return False
                
            with open(filepath, 'rb') as f:
                header = f.read(4)  # First 4 bytes for PDF signature
                
                if not header.startswith(b'%PDF'):
                    self.logger.warning(f"Invalid PDF file: {filepath}")
                    self.logger.warning(f"Header: {header}")
                    return False
                    
            # If we reached here, file is a valid PDF
            self.logger.info(f"Valid PDF verified: {filepath.name} ({file_size/1024/1024:.2f} MB)")
            return True
        except Exception as e:
            self.logger.error(f"Error checking file validity: {e}")
            return False
    
    def _determine_domain(self, paper_info, search_term, prefer_domain=None):
        """Determine the domain for a paper based on its content and search term"""
        # Use preferred domain if provided
        if prefer_domain:
            return prefer_domain
        
        # Check search term and title for domain keywords
        text_to_check = (search_term + " " + paper_info.get('title', '')).lower()
        
        for keyword, domain in self.domain_mapping.items():
            if keyword in text_to_check:
                return domain
        
        # Default to a domain based on search term analysis
        if 'portfolio' in search_term.lower() or 'asset allocation' in search_term.lower():
            return 'portfolio_construction'
        elif 'risk' in search_term.lower() or 'var' in search_term.lower():
            return 'risk_management'
        elif 'regulation' in search_term.lower() or 'compliance' in search_term.lower():
            return 'regulation_compliance'
        elif 'defi' in search_term.lower() or 'decentralized finance' in search_term.lower():
            return 'decentralized_finance'
        elif 'valuation' in search_term.lower() or 'pricing' in search_term.lower():
            return 'valuation_models'
        elif 'high frequency' in search_term.lower() or 'algorithmic trading' in search_term.lower():
            return 'high_frequency_trading'
        elif 'microstructure' in search_term.lower() or 'order book' in search_term.lower():
            return 'market_microstructure'
        elif 'derivative' in search_term.lower() or 'futures' in search_term.lower() or 'options' in search_term.lower():
            return 'crypto_derivatives'
        else:
            # Default to risk_management as a reasonable fallback
            return 'risk_management'

def main():
    """Main entry point when script is run directly"""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='Collect papers from SciDB')
    parser.add_argument('--output-dir', required=True, help='Output directory for collected papers')
    parser.add_argument('--doi-list', default=os.path.join(os.path.dirname(__file__), '../../config/dois.json'), help='JSON file with DOI list (default: config/dois.json)')
    parser.add_argument('--search-terms', default=os.path.join(os.path.dirname(__file__), '../../config/dois.csv'), help='Text file with search terms (default: config/dois.csv)')
    parser.add_argument('--domain', help='Preferred domain for classification')
    parser.add_argument('--max-results', type=int, default=10, help='Maximum results per search term')
    
    args = parser.parse_args()
    
    collector = SciDBCollector(args.output_dir)
    
    if args.doi_list:
        # Load DOI list from JSON file
        with open(args.doi_list, 'r') as f:
            doi_list = json.load(f)
        
        collected_papers = collector.collect_by_doi(doi_list)
        print(f"Collected {len(collected_papers)} papers by DOI")
    
    elif args.search_terms:
        # Load search terms from text file
        with open(args.search_terms, 'r') as f:
            search_terms = [line.strip() for line in f if line.strip()]
        
        collected_papers = collector.collect_by_search(search_terms, args.max_results, args.domain)
        print(f"Collected {len(collected_papers)} papers by search terms")
    
    else:
        print("Error: Either --doi-list or --search-terms must be provided")
        sys.exit(1)
    
    # Print summary of collected papers
    print("\nCollection Summary:")
    by_domain = {}
    for paper in collected_papers:
        domain = paper.get('domain', 'unknown')
        if domain not in by_domain:
            by_domain[domain] = 0
        by_domain[domain] += 1
    
    for domain, count in sorted(by_domain.items()):
        print(f"  {domain}: {count} papers")

if __name__ == "__main__":
    main()

                