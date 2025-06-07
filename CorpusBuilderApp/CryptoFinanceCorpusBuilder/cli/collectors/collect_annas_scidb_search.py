# DEPRECATED: This file belongs to the legacy CryptoFinanceCorpusBuilder package and should not be used in new modules.
import sys
import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv

def run_annas_scidb_search_collector(args, source_config, base_dir):
    print("\nStarting Anna's Archive SCIDB search...")
    # Add project directories to path
    current_dir = os.getcwd()
    sys.path.append(current_dir)
    # Locate CookieAuthClient.py
    client_paths = []
    for root, dirs, files in os.walk(current_dir):
        if 'CookieAuthClient.py' in files:
            client_paths.append(os.path.join(root, 'CookieAuthClient.py'))
            sys.path.append(root)
    if client_paths:
        print(f"Found CookieAuthClient.py at: {client_paths[0]}")
    else:
        print("Could not find CookieAuthClient.py. Please check your project structure.")
        return False
    from CookieAuthClient import CookieAuthClient
    load_dotenv('.env')
    account_cookie = os.getenv("AA_ACCOUNT_COOKIE")
    if not account_cookie:
        print("Error: AA_ACCOUNT_COOKIE not found in .env file")
        return False
    # Set up test-safe output directory
    output_dir = Path(args.output_dir) if hasattr(args, 'output_dir') else Path("data/test_collect/annas_scidb")
    output_dir.mkdir(parents=True, exist_ok=True)
    # Initialize CookieAuthClient
    client = CookieAuthClient(download_dir=str(output_dir), account_cookie=account_cookie)
    print("Client initialized with cookie auth.")
    # Helper: download a single DOI
    def download_scidb_doi(doi, domain=None):
        from bs4 import BeautifulSoup
        import requests
        import datetime
        print(f"Searching for DOI: {doi}")
        # Try direct GET
        base_url = "https://annas-archive.org"
        session = client.session
        direct_url = f"{base_url}/scidb/{doi}/"
        response = session.get(direct_url, allow_redirects=True)
        if response.status_code == 200 and "not found" not in response.text.lower():
            soup = BeautifulSoup(response.text, 'html.parser')
        else:
            # Fallback: POST
            search_url = f"{base_url}/scidb"
            form_data = {"doi": doi}
            response = session.post(search_url, data=form_data, allow_redirects=True)
            if response.status_code == 200 and "not found" not in response.text.lower():
                soup = BeautifulSoup(response.text, 'html.parser')
            else:
                print(f"No paper found for DOI: {doi}")
                return None
        # Parse title
        title = None
        for elem in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            text = elem.text.strip()
            if text and len(text) > 10 and text not in ["Anna's Archive", "SciDB"]:
                title = text
                break
        if not title:
            title = f"Paper_{doi}"
        # Find download link
        download_url = None
        for link in soup.find_all('a'):
            link_text = link.text.lower() if link.text else ""
            href = link.get('href', '')
            if ('download' in link_text or 'pdf' in link_text) and ('.pdf' in href or '/lib/' in href):
                download_url = href if href.startswith('http') else base_url + href
                break
        if not download_url:
            # Try iframe
            iframe = soup.find('iframe', src=lambda x: x and 'viewer.html?file=' in x)
            if iframe:
                from urllib.parse import unquote, urlparse, parse_qs
                src = iframe['src']
                parsed = urlparse(src)
                qs = parse_qs(parsed.query)
                file_url = qs.get('file', [None])[0]
                if file_url:
                    download_url = unquote(file_url)
        if not download_url:
            print(f"No download link found for DOI: {doi}")
            return None
        # Set up domain directory
        target_dir = output_dir / domain if domain else output_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)[:50]
        safe_doi = doi.replace('/', '_')
        filepath = target_dir / f"{safe_title}_{safe_doi}.pdf"
        # Download PDF
        try:
            with session.get(download_url, stream=True) as r:
                r.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            if os.path.getsize(filepath) < 1000:
                print(f"Downloaded file for DOI {doi} is too small, likely invalid.")
                os.remove(filepath)
                return None
            # Save metadata
            meta_file = filepath.with_suffix(f"{filepath.suffix}.meta")
            with open(meta_file, 'w', encoding='utf-8') as f:
                metadata = {
                    'title': title,
                    'doi': doi,
                    'download_date': str(datetime.datetime.now()),
                    'source': 'SciDB',
                    'download_url': download_url
                }
                json.dump(metadata, f, indent=2)
            print(f"✅ Downloaded: {filepath}")
            return str(filepath)
        except Exception as e:
            print(f"Error downloading DOI {doi}: {e}")
            if filepath.exists():
                try:
                    os.remove(filepath)
                except:
                    pass
            return None
    # Single DOI mode
    if hasattr(args, 'scidb_doi') and args.scidb_doi:
        domain = getattr(args, 'scidb_domain', None)
        result = download_scidb_doi(args.scidb_doi, domain=domain)
        if result:
            print(f"\nDownloaded file: {result}")
        else:
            print("\nDownload failed or no file found.")
        return
    # Batch mode
    if hasattr(args, 'scidb_json_file') and args.scidb_json_file:
        try:
            with open(args.scidb_json_file, 'r') as f:
                papers = json.load(f)
            if not isinstance(papers, list):
                print("ERROR: JSON file should contain a list of paper objects")
                return
            print(f"Found {len(papers)} papers in {args.scidb_json_file}")
            default_domain = getattr(args, 'scidb_domain', None)
            results = {"successful": [], "failed": []}
            for i, paper in enumerate(papers):
                doi = paper.get("doi")
                domain = paper.get("domain") or default_domain
                if not doi:
                    print(f"[{i+1}/{len(papers)}] Missing DOI in paper entry")
                    results["failed"].append({"paper": paper, "reason": "Missing DOI"})
                    continue
                print(f"[{i+1}/{len(papers)}] Downloading DOI: {doi}, Domain: {domain}")
                result = download_scidb_doi(doi, domain=domain)
                if result:
                    results["successful"].append({"paper": paper, "filepath": result})
                else:
                    results["failed"].append({"paper": paper, "reason": "Download failed"})
            # Save results summary
            results_file = output_dir / "scidb_download_results.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nBatch download complete. Results saved to: {results_file}")
            print(f"Successful: {len(results['successful'])}, Failed: {len(results['failed'])}")
        except Exception as e:
            print(f"Error loading or processing JSON file: {e}")
        return
    print("No --scidb-doi or --scidb-json-file provided. Nothing to do.")
    return 

if __name__ == "__main__":
    class Args:
        scidb_doi = "10.1111/prd.12104"
        output_dir = "./test_outputs/annas_scidb"
    run_annas_scidb_search_collector(Args(), source_config=None, base_dir=".") 