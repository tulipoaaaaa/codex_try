import os
import time
import json
import logging
import datetime
from pathlib import Path
from dotenv import load_dotenv
from CryptoFinanceCorpusBuilder.config.domain_config import DOMAINS
from CryptoFinanceCorpusBuilder.shared_tools.collectors.enhanced_client import CookieAuthClient
from CryptoFinanceCorpusBuilder.shared_tools.collectors.base_collector import BaseCollector
import importlib.util

class GeneralWebCorpusCollector(BaseCollector):
    def __init__(self, config, account_cookie=None):
        if isinstance(config, str):
            from shared_tools.project_config import ProjectConfig
            config = ProjectConfig(config, environment='test')
        super().__init__(config)
        self.account_cookie = account_cookie
        self.client = None
        self.tracker = {'downloads': [], 'domains': {}, 'total': 0}
        
    def initialize(self):
        """Initialize the collector with authentication."""
        if not self.account_cookie:
            load_dotenv()
            self.account_cookie = os.getenv("AA_ACCOUNT_COOKIE")
            if not self.account_cookie:
                raise ValueError("AA_ACCOUNT_COOKIE not found in .env file")
                
        self.client = CookieAuthClient(
            download_dir=str(self.output_dir),
            account_cookie=self.account_cookie
        )
        self.logger.info("Client initialized with cookie auth")
        
    def _get_output_path(self, filename, content_type='reports'):
        """Get the correct output path for web corpus content."""
        # Web corpus content is organized by domain
        domain = self.current_domain
        return super()._get_output_path(domain, content_type, filename)
        
    def collect(self, max_total=20, max_retries=3, rate_limit=5):
        """Collect content from the web corpus."""
        if not self.client:
            self.initialize()
            
        self.logger.info(f"Starting collection with max {max_total} downloads")
        total_downloaded = 0
        
        for domain, config in DOMAINS.items():
            self.current_domain = domain
            allocation = int(max_total * config.get('allocation', 0.1))
            self.tracker['domains'][domain] = {'completed': 0, 'allocation': allocation}
            self.logger.info(f"Processing domain: {domain} | Allocation: {allocation}")
            
            for search_term in config.get('search_terms', []):
                if (self.tracker['domains'][domain]['completed'] >= allocation or 
                    total_downloaded >= max_total):
                    break
                    
                self.logger.info(f"Searching for: '{search_term}'")
                for attempt in range(max_retries):
                    filepath = self.client.download_best_result(
                        search_term,
                        prefer_format="pdf",
                        domain_dir=domain
                    )
                    
                    if filepath:
                        self.logger.info(f"Downloaded: {filepath}")
                        self.tracker['downloads'].append({
                            'domain': domain,
                            'search_term': search_term,
                            'filepath': str(filepath),
                            'success': True
                        })
                        self.tracker['domains'][domain]['completed'] += 1
                        total_downloaded += 1
                        time.sleep(rate_limit)
                        break
                    else:
                        self.logger.warning(f"Retry {attempt+1}/{max_retries} failed for '{search_term}'")
                        if attempt == max_retries - 1:
                            self.tracker['downloads'].append({
                                'domain': domain,
                                'search_term': search_term,
                                'filepath': None,
                                'success': False
                            })
                            
                if total_downloaded >= max_total:
                    break
                    
        # Save tracker
        self.tracker['total'] = total_downloaded
        tracker_path = self.output_dir / "web_corpus_downloads.json"
        with open(tracker_path, 'w') as f:
            json.dump(self.tracker, f, indent=2)
            
        self.logger.info(f"Download summary saved to: {tracker_path}")
        self.logger.info(f"Total downloaded: {total_downloaded}")
        for domain, stats in self.tracker['domains'].items():
            self.logger.info(f"{domain}: {stats['completed']} / {stats['allocation']} downloads")
            
        return True

def run_general_web_corpus_collector(args, source_config, base_dir):
    """Legacy entry point for backward compatibility."""
    try:
        collector = GeneralWebCorpusCollector(base_dir)
        return collector.collect(
            max_total=getattr(args, 'web_max_downloads', 20),
            max_retries=getattr(args, 'web_max_retries', 3),
            rate_limit=getattr(args, 'web_rate_limit', 5)
        )
    except Exception as e:
        logging.error(f"Error in general web corpus collector: {e}")
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="General Web Corpus Collector")
    parser.add_argument("--output-dir", required=True, help="Output directory for collected data")
    parser.add_argument("--domain-config", help="Path to domain_config.py to use for domains")
    args = parser.parse_args()

    # Dynamically import domain_config if path is provided
    if args.domain_config:
        spec = importlib.util.spec_from_file_location("domain_config", args.domain_config)
        domain_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(domain_config)
        DOMAINS = domain_config.DOMAINS
    else:
        from CryptoFinanceCorpusBuilder.config.domain_config import DOMAINS

    run_general_web_corpus_collector(args, None, args.output_dir) 