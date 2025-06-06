import os
import time
import json
import logging
import datetime
from pathlib import Path
from dotenv import load_dotenv
from CryptoFinanceCorpusBuilder.config.domain_config import DOMAINS
from CryptoFinanceCorpusBuilder.shared_tools.collectors.enhanced_client import CookieAuthClient
import importlib.util

def run_general_web_corpus_collector(args, source_config, base_dir):
    print("[DEBUG] Entered general_web_corpus collector block")
    print("\nStarting General Web Corpus Collector...")
    # Set up test-safe output directory
    output_dir = Path(args.output_dir) if hasattr(args, 'output_dir') else Path("data/test_collect/general_web_corpus")
    output_dir.mkdir(parents=True, exist_ok=True)
    # Load AA cookie from env
    load_dotenv()
    account_cookie = os.getenv("AA_ACCOUNT_COOKIE")
    if not account_cookie:
        print("Error: AA_ACCOUNT_COOKIE not found in .env file")
        return False
    # Initialize client
    client = CookieAuthClient(download_dir=str(output_dir), account_cookie=account_cookie)
    print("Client initialized with cookie auth.")
    # Download tracker
    tracker = { 'downloads': [], 'domains': {}, 'total': 0 }
    max_total = getattr(args, 'web_max_downloads', 20)
    max_retries = getattr(args, 'web_max_retries', 3)
    rate_limit = getattr(args, 'web_rate_limit', 5)
    total_downloaded = 0
    for domain, config in DOMAINS.items():
        allocation = int(max_total * config.get('allocation', 0.1))
        tracker['domains'][domain] = { 'completed': 0, 'allocation': allocation }
        print(f"\n=== Domain: {domain} | Allocation: {allocation} ===")
        for search_term in config.get('search_terms', []):
            if tracker['domains'][domain]['completed'] >= allocation or total_downloaded >= max_total:
                break
            print(f"Searching for: '{search_term}'")
            for attempt in range(max_retries):
                filepath = client.download_best_result(search_term, prefer_format="pdf", domain_dir=domain)
                if filepath:
                    print(f"✅ Downloaded: {filepath}")
                    tracker['downloads'].append({'domain': domain, 'search_term': search_term, 'filepath': str(filepath), 'success': True})
                    tracker['domains'][domain]['completed'] += 1
                    total_downloaded += 1
                    time.sleep(rate_limit)
                    break
                else:
                    print(f"Retry {attempt+1}/{max_retries} failed for '{search_term}'")
                    if attempt == max_retries - 1:
                        tracker['downloads'].append({'domain': domain, 'search_term': search_term, 'filepath': None, 'success': False})
            if total_downloaded >= max_total:
                break
    # Save tracker
    tracker['total'] = total_downloaded
    tracker_path = output_dir / "web_corpus_downloads.json"
    with open(tracker_path, 'w') as f:
        json.dump(tracker, f, indent=2)
    print(f"\nDownload summary saved to: {tracker_path}")
    print(f"Total downloaded: {total_downloaded}")
    for domain, stats in tracker['domains'].items():
        print(f"  {domain}: {stats['completed']} / {stats['allocation']} downloads")
    print("\nGeneral web corpus collection complete!")
    return True

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