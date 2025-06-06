import sys
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup  # type: ignore
import argparse
import logging
import json
import datetime
from .base_collector import BaseCollector
from CryptoFinanceCorpusBuilder.shared_tools.utils.domain_utils import get_domain_for_file

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import enhanced client first, then fall back to CookieAuthClient
try:
    from .enhanced_client import CookieAuthClient
    logger.info("Successfully imported enhanced client")
except ImportError:
    logger.info("Enhanced client not found, trying to locate CookieAuthClient")
    # Add project directories to path and locate CookieAuthClient
    current_dir = os.getcwd()
    sys.path.append(current_dir)
    client_paths = []
    for root, dirs, files in os.walk(current_dir):
        if 'CookieAuthClient.py' in files:
            client_paths.append(os.path.join(root, 'CookieAuthClient.py'))
            sys.path.append(root)
    if client_paths:
        logger.info(f"Found CookieAuthClient.py at: {client_paths[0]}")
        from CookieAuthClient import CookieAuthClient  # type: ignore
    else:
        logger.error("Could not find CookieAuthClient.py. Please check your project structure.")
        raise ImportError("Could not find CookieAuthClient in any location")

# Import ProjectConfig if available
try:
    from CryptoFinanceCorpusBuilder.config.project_config import ProjectConfig  # type: ignore
    logger.info("Successfully imported ProjectConfig")
except ImportError:
    logger.warning("ProjectConfig not found. Legacy mode will be used if --project-config is not provided.")
    ProjectConfig = None

def normalize_title(title):
    return re.sub(r'[^\w\s]', '', title.lower()).strip()

def load_existing_titles(existing_titles_path):
    existing_titles = set()
    if existing_titles_path and os.path.exists(existing_titles_path):
        with open(existing_titles_path, 'r', encoding='utf-8') as f:
            for line in f:
                existing_titles.add(line.strip())
    return existing_titles

def safe_filename(s):
    import re
    return re.sub(r'[^a-zA-Z0-9_\-\.]+', '_', s)[:128]

class AnnasMainLibraryCollector(BaseCollector):
    def __init__(self, config, account_cookie=None):
        if isinstance(config, str):
            from CryptoFinanceCorpusBuilder.config.project_config import ProjectConfig
            config = ProjectConfig(config, environment='test')
        super().__init__(config)
        self.account_cookie = account_cookie
        if not self.account_cookie:
            load_dotenv()
            self.account_cookie = os.getenv("AA_ACCOUNT_COOKIE")
            if not self.account_cookie:
                logger.error("Error: AA_ACCOUNT_COOKIE not found in .env file")
                raise ValueError("AA_ACCOUNT_COOKIE not found")

        # Initialize domain mapping based on ProjectConfig domains
        self.domain_mapping = {}
        for domain, config in self.config.domain_configs.items():
            # Add domain's search terms to mapping
            for term in config.search_terms:
                self.domain_mapping[term.lower()] = domain

        # Initialize CookieAuthClient
        try:
            self.client = CookieAuthClient(download_dir=str(self.raw_data_dir), account_cookie=self.account_cookie)
            if self.client.is_authenticated:
                logger.info("Authentication successful.")
            else:
                logger.error("Authentication failed. Please check your cookie.")
                raise ValueError("Authentication failed")
        except Exception as e:
            logger.error(f"Error initializing CookieAuthClient: {e}")
            raise

    def _determine_domain(self, title, search_term=None):
        """Determine the domain for a paper based on its title and search term"""
        # Check title for domain keywords
        text_to_check = title.lower()
        
        # First check domain mapping (which comes from ProjectConfig search terms)
        for keyword, domain in self.domain_mapping.items():
            if keyword in text_to_check:
                return domain
        
        # Then check search term if provided
        if search_term:
            search_term = search_term.lower()
            for keyword, domain in self.domain_mapping.items():
                if keyword in search_term:
                    return domain
        
        # If no match found, use domain with highest quality threshold
        # This ensures important papers go to domains with higher standards
        best_domain = None
        highest_threshold = -1
        for domain, config in self.config.domain_configs.items():
            if config.quality_threshold > highest_threshold:
                highest_threshold = config.quality_threshold
                best_domain = domain
        
        return best_domain or 'high_frequency_trading'  # Fallback to HFT if something goes wrong

    def _get_output_path(self, filename, content_type='papers'):
        """Get the correct output path for Anna's Archive content."""
        # Extract title from filename
        title = filename.split('_')[2] if '_' in filename else filename
        
        # Determine domain based on title
        domain = self._determine_domain(title)
        
        # Create domain directory if it doesn't exist
        domain_dir = self.raw_data_dir / domain / content_type
        domain_dir.mkdir(parents=True, exist_ok=True)
        
        return domain_dir / filename

    def collect(self, search_query, max_attempts=5):
        """Collect content from Anna's Archive."""
        logger.info(f"Searching for: '{search_query}'")
        
        # Use client's search method which has proper form handling
        results = self.client.search(search_query, content_type="book", language="en", ext="pdf")
        
        if not results:
            logger.warning(f"No results found for: {search_query}")
            return []
            
        # Download top results
        downloaded_files = []
        for result in results[:max_attempts]:
            try:
                filepath = self.client.download_file(result["md5"])
                if not filepath:
                    logger.error("Download failed - no filepath returned")
                    continue
                filepath = Path(filepath)
                logger.info(f"Downloaded file to: {filepath}")
                if not filepath.exists():
                    logger.error(f"Downloaded file not found at {filepath}")
                    continue
                output_filename = f"Unknown_{result.get('year', 'Unknown')}_{safe_filename(result['title'])}_{result['md5']}.pdf"
                domain = get_domain_for_file(str(filepath), text=result['title'], debug=True)
                logger.info(f"Classified '{result['title']}' into domain: {domain}")
                if domain != 'unknown':
                    target_dir = self.raw_data_dir / domain / 'papers'
                else:
                    target_dir = self.raw_data_dir / 'other' / 'papers'
                target_dir.mkdir(parents=True, exist_ok=True)
                target_pdf = target_dir / output_filename
                # Move PDF
                if not target_pdf.exists():
                    try:
                        filepath.rename(target_pdf)
                        logger.info(f"Moved PDF to {target_pdf}")
                    except Exception as e:
                        logger.error(f"Error moving PDF: {e}")
                else:
                    logger.info(f"PDF already exists at {target_pdf}, removing duplicate in main folder")
                    try:
                        filepath.unlink()
                    except Exception as e:
                        logger.error(f"Error deleting duplicate PDF: {e}")
                # Move meta file
                meta_path = filepath.with_suffix('.pdf.meta')
                target_meta = target_dir / (output_filename + '.meta')
                if meta_path.exists():
                    if not target_meta.exists():
                        try:
                            meta_path.rename(target_meta)
                            logger.info(f"Moved meta file to {target_meta}")
                        except Exception as e:
                            logger.error(f"Error moving meta file: {e}")
                    else:
                        logger.info(f"Meta file already exists at {target_meta}, removing duplicate in main folder")
                        try:
                            meta_path.unlink()
                        except Exception as e:
                            logger.error(f"Error deleting duplicate meta file: {e}")
                else:
                    logger.warning(f"Meta file not found for {filepath}")
                downloaded_files.append({
                    'title': result['title'],
                    'filepath': str(target_pdf),
                    'quality_score': result['quality_score'],
                    'domain': domain
                })
            except Exception as e:
                logger.error(f"Error downloading {result['title']}: {e}")
                continue
        return downloaded_files

def run_annas_main_library_collector(args, source_config, base_dir, batch_json=None):
    """Legacy entry point for backward compatibility."""
    try:
        # Create proper config structure
        config = {
            'raw_data_dir': base_dir,
            'domains': {
                'portfolio_construction': {'path': 'portfolio_construction'},
                'risk_management': {'path': 'risk_management'},
                'regulation_compliance': {'path': 'regulation_compliance'},
                'decentralized_finance': {'path': 'decentralized_finance'},
                'valuation_models': {'path': 'valuation_models'},
                'high_frequency_trading': {'path': 'high_frequency_trading'},
                'market_microstructure': {'path': 'market_microstructure'},
                'crypto_derivatives': {'path': 'crypto_derivatives'},
                'unknown': {'path': 'unknown'}
            }
        }
        
        collector = AnnasMainLibraryCollector(config)
        
        # Handle batch mode
        if batch_json:
            with open(batch_json, 'r', encoding='utf-8') as f:
                books = json.load(f)
            book_titles = [entry['title'] if isinstance(entry, dict) else entry for entry in books]
        else:
            book_titles = ["Mastering Bitcoin Antonopoulos"]  # Legacy fallback
            
        results = []
        for title in book_titles:
            try:
                downloaded = collector.collect(title)
                results.extend(downloaded)
            except Exception as e:
                logger.error(f"Error collecting {title}: {e}")
                continue
                
        return results
    except Exception as e:
        logger.error(f"Error in Anna's Archive collector: {e}")
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect content from Anna's Archive")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--batch-json", help="JSON file with book titles")
    args = parser.parse_args()
    
    results = run_annas_main_library_collector(args, None, args.output_dir, args.batch_json)
    print(f"\nCollected {len(results)} files") 