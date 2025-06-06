import sys
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import argparse

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

def run_annas_main_library_collector(args, source_config, base_dir, batch_json=None):
    print("\nStarting Anna's Archive main library search...")
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
    # Set up output directories
    hft_dir = Path("./data/corpus_1/high_frequency_trading")
    hft_extracted_dir = Path("./data/corpus_1/high_frequency_trading_extracted")
    debug_dir = Path("./data/corpus_1/debug")
    for d in [hft_dir, hft_extracted_dir, debug_dir]:
        d.mkdir(parents=True, exist_ok=True)
    # Initialize CookieAuthClient
    output_dir = Path(base_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    client = CookieAuthClient(download_dir=str(output_dir), account_cookie=account_cookie)
    print("Client initialized with cookie auth.")
    # Batch mode: load books from JSON if batch_json is provided
    book_titles = []
    if batch_json:
        import json
        with open(batch_json, 'r', encoding='utf-8') as f:
            books = json.load(f)
        for entry in books:
            if isinstance(entry, dict) and 'title' in entry:
                book_titles.append(entry['title'])
            elif isinstance(entry, str):
                book_titles.append(entry)
    else:
        # Single book fallback (legacy/test logic)
        book_titles = ["Mastering Bitcoin Antonopoulos"]
    for search_query in book_titles:
        print(f"Searching for: '{search_query}'")
        # Use client to get search HTML (assume client has a .session attribute)
        search_url = f"https://annas-archive.org/search?q={search_query}&ext=pdf"
        response = client.session.get(search_url)
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        result_divs = soup.find_all("div", class_=lambda c: c and "mb-4" in c)
        for div in result_divs:
            link_elem = div.find("a", href=lambda h: h and "/md5/" in h)
            if not link_elem:
                continue
            href = link_elem.get("href", "")
            md5_match = re.search(r"/md5/([a-f0-9]+)", href)
            if not md5_match:
                continue
            md5 = md5_match.group(1)
            title = link_elem.get_text().strip()
            file_info = "Unknown format and size"
            info_div = div.find("div", class_=lambda c: c and "text-xs" in c)
            if info_div:
                file_info = info_div.get_text().strip()
            size_mb = 0
            size_match = re.search(r'(\d+(?:\.\d+)?)\s*MB', file_info)
            if size_match:
                size_mb = float(size_match.group(1))
            year = None
            year_match = re.search(r'\b(19|20)\d{2}\b', file_info)
            if year_match:
                year = int(year_match.group(0))
            quality_score = 0
            if "english" in file_info.lower():
                quality_score += 20
            quality_score += min(size_mb * 2, 30)
            if "retail" in file_info.lower():
                quality_score += 15
            if "official" in file_info.lower():
                quality_score += 10
            if year and year > 2000:
                quality_score += min((year - 2000), 10)
            results.append({
                "title": title,
                "md5": md5,
                "link": f"https://annas-archive.org/md5/{md5}",
                "file_info": file_info,
                "size_mb": size_mb,
                "quality_score": quality_score
            })
        if not results:
            print(f"No results found for the book: {search_query}")
            continue
        # Deduplication logic
        existing_titles_path = getattr(args, 'existing_titles', None) if hasattr(args, 'existing_titles') else None
        existing_titles = load_existing_titles(existing_titles_path)
        if existing_titles:
            before_count = len(results)
            results = [r for r in results if normalize_title(r.get('title', '')) not in existing_titles]
            skipped = before_count - len(results)
            print(f"Deduplication: Skipped {skipped} results already in the existing titles cache.")
        if not results:
            print(f"All candidate results for '{search_query}' are already present in the corpus (by title). Skipping download.")
            continue
        results.sort(key=lambda x: x["quality_score"], reverse=True)
        print("\nTop 3 results by quality score:")
        for i, result in enumerate(results[:min(3, len(results))]):
            print(f"{i+1}. {result['title']} - Size: {result['size_mb']}MB - Score: {result['quality_score']}")
            print(f"   Info: {result['file_info']}")
            print()
        # Robust PDF selection and download logic
        max_attempts = 5
        found_high_quality = False
        for result in results[:max_attempts]:
            print(f"Attempting download for: {result['title']} - {result['file_info']}")
            md5 = result["md5"]
            detail_url = f"https://annas-archive.org/md5/{md5}"
            client.session.get(detail_url)
            download_url = f"https://annas-archive.org/fast_download/{md5}/0/0"
            download_response = client.session.get(download_url, headers={"Referer": detail_url}, allow_redirects=True)
            book_path = output_dir / f"{safe_filename(result['title'])}.pdf"
            if "application/pdf" in download_response.headers.get("Content-Type", ""):
                with open(book_path, "wb") as f:
                    f.write(download_response.content)
                print(f"✅ Successfully downloaded book to {book_path}")
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(book_path)
                    text = ""
                    has_text = False
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text and len(page_text.strip()) > 0:
                            has_text = True
                        text += (page_text or "") + "\n\n"
                    print(f"Text length: {len(text)} characters, {len(text.split())} tokens")
                    # Quality check: meaningful content
                    content_sample = text[:1000].strip()
                    meaningful_words = ["bitcoin", "blockchain", "wallet", "transaction", "address", "key", "network", "chapter"]
                    has_meaningful_content = any(word in content_sample.lower() for word in meaningful_words)
                    word_count = len(text.split())
                    print(f"Extracted text has {word_count} words")
                    print(f"Text appears to have meaningful content: {has_meaningful_content}")
                    if has_meaningful_content and word_count > 100:
                        print(f"✅ High-quality PDF found and saved: {book_path}")
                        found_high_quality = True
                        break
                    else:
                        print("⚠️ Low-quality or image-based PDF, trying next result...")
                        book_path.unlink(missing_ok=True)
                except Exception as e:
                    print(f"Error extracting text from book: {e}")
                    book_path.unlink(missing_ok=True)
            else:
                print("❌ Could not download PDF, trying next result...")
        if not found_high_quality:
            print(f"❌ No high-quality PDF found for '{search_query}' after trying top {max_attempts} results.")
    return True 