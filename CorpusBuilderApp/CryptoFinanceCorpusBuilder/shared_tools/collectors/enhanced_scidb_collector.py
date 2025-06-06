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

from .base_collector import BaseCollector
from .enhanced_client import CookieAuthClient

class SciDBCollector(BaseCollector):
    """Collector for SciDB academic papers with focus on finance and crypto"""
    
    def __init__(self, config, delay_range=(3, 7), account_cookie=None):
        """
        Initialize SciDBCollector with ProjectConfig.
        
        Args:
            config: ProjectConfig instance or path to config file
            delay_range: Tuple of (min, max) delay between requests
            account_cookie: Optional account cookie for authentication
        """
        if isinstance(config, str):
            from shared_tools.project_config import ProjectConfig
            config = ProjectConfig(config, environment='test')
        
        super().__init__(config, delay_range)
        
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
                # First get paper info
                paper_info = self._search_by_doi(doi)
                if not paper_info:
                    self.logger.warning(f"Could not find paper info for DOI: {doi}")
                    continue
                
                # Download to temp location first
                temp_dir = Path(self.output_dir) / 'temp'
                temp_dir.mkdir(exist_ok=True)
                client.download_dir = str(temp_dir)
                
                # Download the paper
                downloaded_file = client.download_scidb_doi(doi)
                
                if downloaded_file:
                    # Move to correct domain directory
                    if domain:
                        domain_dir = Path(self.output_dir) / domain
                        domain_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Move file to domain directory
                        file_path = Path(downloaded_file)
                        new_path = domain_dir / file_path.name
                        file_path.rename(new_path)
                        
                        # Move meta file if it exists
                        meta_file = file_path.with_suffix('.meta')
                        if meta_file.exists():
                            meta_file.rename(new_path.with_suffix('.meta'))
                        
                        final_paper_info = {
                            'doi': doi,
                            'title': paper_info.get('title', f"DOI {doi}"),
                            'domain': domain,
                            'filepath': str(new_path),
                            'download_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'source': 'scidb'
                        }
                    else:
                        final_paper_info = {
                            'doi': doi,
                            'title': paper_info.get('title', f"DOI {doi}"),
                            'filepath': downloaded_file,
                            'download_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'source': 'scidb'
                        }
                    
                    collected_papers.append(final_paper_info)
                    self.logger.info(f"Successfully downloaded paper: {doi}")
                
                # Clean up temp directory
                if temp_dir.exists():
                    for file in temp_dir.glob('*'):
                        file.unlink()
                    temp_dir.rmdir()
                
            except Exception as e:
                self.logger.error(f"Error collecting DOI {doi}: {e}")
            
            # Delay between papers
            delay = random.uniform(*self.delay_range)
            time.sleep(delay)
        
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
        """Check if a file is valid PDF and meets size requirements"""
        try:
            filepath = Path(filepath) if isinstance(filepath, str) else filepath
            if not filepath.exists():
                return False
            
            # Check file size
            size = filepath.stat().st_size
            if size < 10000 or size > 10000000:  # 10KB to 10MB
                return False
            
            # Check if it's a PDF
            if filepath.suffix.lower() != '.pdf':
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error checking file validity: {e}")
            return False
    
    def _determine_domain(self, paper_info, search_term=None, prefer_domain=None):
        """Determine the domain for a paper based on its content and search term"""
        # Use preferred domain if provided
        if prefer_domain:
            return prefer_domain
        
        # Check title for domain keywords
        text_to_check = paper_info.get('title', '').lower()
        
        for keyword, domain in self.domain_mapping.items():
            if keyword in text_to_check:
                return domain
        
        # Default to a domain based on title analysis
        if 'portfolio' in text_to_check or 'asset allocation' in text_to_check:
            return 'portfolio_construction'
        elif 'risk' in text_to_check or 'var' in text_to_check:
            return 'risk_management'
        elif 'regulation' in text_to_check or 'compliance' in text_to_check:
            return 'regulation_compliance'
        elif 'defi' in text_to_check or 'decentralized finance' in text_to_check:
            return 'decentralized_finance'
        elif 'valuation' in text_to_check or 'pricing' in text_to_check:
            return 'valuation_models'
        elif 'high frequency' in text_to_check or 'algorithmic trading' in text_to_check:
            return 'high_frequency_trading'
        elif 'microstructure' in text_to_check or 'order book' in text_to_check:
            return 'market_microstructure'
        elif 'derivative' in text_to_check or 'futures' in text_to_check or 'options' in text_to_check:
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
    
    else:
        print("Error: --doi-list must be provided")
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

                