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

def run_annas_main_library_collector(args, source_config, base_dir, batch_json=None):
    print("\nStarting Anna's Archive main library search...")
    logger.info(f"Batch JSON path: {batch_json}")
    # Load environment variables
    load_dotenv()
    account_cookie = os.getenv("AA_ACCOUNT_COOKIE")
    if not account_cookie:
        logger.error("Error: AA_ACCOUNT_COOKIE not found in .env file")
                return False

    # Set up output directories using ProjectConfig if available
    if hasattr(args, 'project_config') and args.project_config and ProjectConfig:
        try:
            config = ProjectConfig.from_yaml(args.project_config)
            output_dir = config.get_domain_dir("high_frequency_trading", "papers")
            logger.info(f"Using ProjectConfig output directory: {output_dir}")
            base_dir = str(output_dir)  # Ensure base_dir is set for legacy fallback
        except Exception as e:
            logger.error(f"Error loading ProjectConfig: {e}")
            return False
    else:
        output_dir = Path(base_dir) if base_dir else Path(os.getcwd())
        logger.info(f"Using legacy output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize CookieAuthClient
    try:
        client = CookieAuthClient(download_dir=str(output_dir), account_cookie=account_cookie)
        if client.is_authenticated:
            logger.info("Authentication successful.")
        else:
            logger.error("Authentication failed. Please check your cookie.")
            return False
    except Exception as e:
        logger.error(f"Error initializing CookieAuthClient: {e}")
        return False

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
        logger.info(f"Loaded book titles from batch JSON: {book_titles}")
    else:
        # Single book fallback (legacy/test logic)
        book_titles = ["Mastering Bitcoin Antonopoulos"]
        logger.info(f"Using fallback book title: {book_titles}")
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
            download_url = f"https://annas-archive.org/fast_download/{md5}/0/0"
            # Normalize filename: {author}_{year}_{title}_{md5}.pdf
            author = "Unknown"
            year = result.get("year", "Unknown")
            title = safe_filename(result['title'])
            book_path = output_dir / f"{author}_{year}_{title}_{md5}.pdf"
            valid_pdf = False
            # 1. GET detail page with browser-like headers
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://annas-archive.org/"
            }
            print(f"[HTTP] Session cookies before detail page: {client.session.cookies.get_dict()}")
            detail_response = client.session.get(detail_url, headers=headers)
            print(f"[HTTP] Detail page status: {detail_response.status_code}")
            print(f"[HTTP] Session cookies after detail page: {client.session.cookies.get_dict()}")
            print(f"[HTTP] Detail page HTML (truncated):\n{detail_response.text[:1000]}")
            # 2. Try fast_download endpoint
            print(f"[HTTP] Trying fast_download URL: {download_url}")
            download_response = client.session.get(download_url, headers={**headers, "Referer": detail_url}, allow_redirects=True)
            print(f"[HTTP] fast_download Content-Type: {download_response.headers.get('Content-Type','')}")
            if "application/pdf" in download_response.headers.get("Content-Type", ""):
                with open(book_path, "wb") as f:
                    f.write(download_response.content)
                valid_pdf = True
            else:
                print(f"[HTTP] fast_download response (truncated):\n{download_response.text[:500]}")
            # 3. Try <a class='fast-download-link'>
            if not valid_pdf:
                soup = BeautifulSoup(detail_response.text, "html.parser")
                fast_link = soup.find("a", class_="fast-download-link")
                if fast_link and fast_link.get("href"):
                    fast_href = fast_link.get("href")
                    if not fast_href.startswith("http"):
                        fast_href = "https://annas-archive.org" + fast_href if fast_href.startswith("/") else fast_href
                    print(f"[HTTP] Trying <a class='fast-download-link'>: {fast_href}")
                    fast_resp = client.session.get(fast_href, headers={**headers, "Referer": detail_url}, allow_redirects=True)
                    print(f"[HTTP] fast-download-link Content-Type: {fast_resp.headers.get('Content-Type','')}")
                    if "application/pdf" in fast_resp.headers.get("Content-Type", ""):
                        with open(book_path, "wb") as f:
                            f.write(fast_resp.content)
                        valid_pdf = True
                    else:
                        print(f"[HTTP] fast-download-link response (truncated):\n{fast_resp.text[:500]}")
            # 4. Try iframe or alternative links if above fail
            if not valid_pdf:
                soup = BeautifulSoup(download_response.text, "html.parser")
                # Try iframe
                iframe = soup.find("iframe")
                if iframe and iframe.get("src"):
                    iframe_src = iframe.get("src")
                    if not iframe_src.startswith("http"):
                        iframe_src = "https://annas-archive.org" + iframe_src if iframe_src.startswith("/") else iframe_src
                    print(f"[HTTP] Trying iframe: {iframe_src}")
                    iframe_response = client.session.get(iframe_src, headers={**headers, "Referer": detail_url})
                    print(f"[HTTP] iframe Content-Type: {iframe_response.headers.get('Content-Type','')}")
                    if "application/pdf" in iframe_response.headers.get("Content-Type", ""):
                        with open(book_path, "wb") as f:
                            f.write(iframe_response.content)
                        valid_pdf = True
                    else:
                        print(f"[HTTP] iframe response (truncated):\n{iframe_response.text[:500]}")
                # Try download links
                if not valid_pdf:
                    download_links = []
                    for a in soup.find_all("a", href=True):
                        href = a.get("href")
                        text = a.get_text().strip()
                        if "download" in href.lower() or "download" in text.lower() or ".pdf" in href.lower():
                            download_links.append((text, href))
                    print(f"[HTTP] Trying download links: {download_links}")
                    for text, href in download_links:
                        if not href.startswith("http"):
                            href = "https://annas-archive.org" + href if href.startswith("/") else href
                        link_response = client.session.get(href, headers={**headers, "Referer": detail_url})
                        print(f"[HTTP] download link Content-Type: {link_response.headers.get('Content-Type','')}")
                        if "application/pdf" in link_response.headers.get("Content-Type", ""):
                            with open(book_path, "wb") as f:
                                f.write(link_response.content)
                            valid_pdf = True
                            break
                        else:
                            print(f"[HTTP] download link response (truncated):\n{link_response.text[:500]}")
            # 5. Check PDF header, size, and content
            if valid_pdf and os.path.exists(book_path):
                with open(book_path, 'rb') as f:
                    header = f.read(8)
                    if not header.startswith(b'%PDF'):
                        print(f"Downloaded file for {result['title']} is not a valid PDF (header: {header}) - deleting.")
                        os.remove(book_path)
                        valid_pdf = False
                if valid_pdf and os.path.getsize(book_path) < 10000:
                    print(f"Downloaded file for {result['title']} is too small, likely invalid.")
                    os.remove(book_path)
                    valid_pdf = False
                if valid_pdf:
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
                        
                        # Get PDF metadata and structure info
                        num_pages = len(reader.pages)
                        print(f"PDF has {num_pages} pages")
                        
                        # Check if PDF is image-based
                        is_image_based = not has_text and num_pages > 0
                        if is_image_based:
                            print("PDF appears to be image-based (scanned document)")
                            # For image-based PDFs, we'll accept them if they have a reasonable number of pages
                            if num_pages >= 10:  # Minimum expected pages for a book
                                print(f"✅ Image-based PDF with {num_pages} pages - likely valid")
                                found_high_quality = True
                                # Save metadata
                                meta_path = book_path.with_suffix(book_path.suffix + ".meta")
                                meta_dict = {
                                    "title": result['title'],
                                    "author": author,
                                    "year": year,
                                    "md5": md5,
                                    "file_info": result['file_info'],
                                    "download_date": str(datetime.datetime.now()),
                                    "query": search_query,
                                    "is_image_based": True,
                                    "num_pages": num_pages
                                }
                                with open(meta_path, 'w', encoding='utf-8') as f:
                                    json.dump(meta_dict, f, indent=2)
                                break
                            else:
                                print(f"⚠️ Image-based PDF has only {num_pages} pages - likely incomplete")
                                os.remove(book_path)
                                valid_pdf = False
                        else:
                            # Original text-based validation logic
                    print(f"Text length: {len(text)} characters, {len(text.split())} tokens")
                    content_sample = text[:1000].strip()
                            meaningful_words = ["bitcoin", "blockchain", "wallet", "transaction", "address", "key", "network", "chapter", "portfolio", "investment", "risk", "return", "market", "asset", "financial"]
                    has_meaningful_content = any(word in content_sample.lower() for word in meaningful_words)
                    word_count = len(text.split())
                    print(f"Extracted text has {word_count} words")
                    print(f"Text appears to have meaningful content: {has_meaningful_content}")
                    if has_meaningful_content and word_count > 100:
                                print(f"✅ High-quality text-based PDF found and saved: {book_path}")
                        found_high_quality = True
                                # Save metadata
                                meta_path = book_path.with_suffix(book_path.suffix + ".meta")
                                meta_dict = {
                                    "title": result['title'],
                                    "author": author,
                                    "year": year,
                                    "md5": md5,
                                    "file_info": result['file_info'],
                                    "download_date": str(datetime.datetime.now()),
                                    "query": search_query,
                                    "is_image_based": False,
                                    "num_pages": num_pages
                                }
                                with open(meta_path, 'w', encoding='utf-8') as f:
                                    json.dump(meta_dict, f, indent=2)
                        break
                    else:
                                print("⚠️ Low-quality text-based PDF, trying next result...")
                            os.remove(book_path)
                            valid_pdf = False
                except Exception as e:
                    print(f"Error extracting text from book: {e}")
                        os.remove(book_path)
                        valid_pdf = False
            # 6. Fallback to Selenium if all HTTP methods fail
            if not valid_pdf:
                print("Falling back to Selenium-based download...")
                book_path = client.download_main_library_file(md5)
                if book_path and os.path.exists(book_path):
                    with open(book_path, 'rb') as f:
                        header = f.read(8)
                        if not header.startswith(b'%PDF'):
                            print(f"[Selenium] Downloaded file for {result['title']} is not a valid PDF (header: {header}) - deleting.")
                            os.remove(book_path)
                            continue
                    if os.path.getsize(book_path) < 10000:
                        print(f"[Selenium] Downloaded file for {result['title']} is too small, likely invalid.")
                        os.remove(book_path)
                        continue
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
                        
                        # Get PDF metadata and structure info
                        num_pages = len(reader.pages)
                        print(f"PDF has {num_pages} pages")
                        
                        # Check if PDF is image-based
                        is_image_based = not has_text and num_pages > 0
                        if is_image_based:
                            print("PDF appears to be image-based (scanned document)")
                            # For image-based PDFs, we'll accept them if they have a reasonable number of pages
                            if num_pages >= 10:  # Minimum expected pages for a book
                                print(f"✅ Image-based PDF with {num_pages} pages - likely valid")
                                found_high_quality = True
                                # Save metadata
                                meta_path = book_path.with_suffix(book_path.suffix + ".meta")
                                meta_dict = {
                                    "title": result['title'],
                                    "author": author,
                                    "year": year,
                                    "md5": md5,
                                    "file_info": result['file_info'],
                                    "download_date": str(datetime.datetime.now()),
                                    "query": search_query,
                                    "is_image_based": True,
                                    "num_pages": num_pages
                                }
                                with open(meta_path, 'w', encoding='utf-8') as f:
                                    json.dump(meta_dict, f, indent=2)
                                break
                            else:
                                print(f"⚠️ Image-based PDF has only {num_pages} pages - likely incomplete")
                                os.remove(book_path)
                                valid_pdf = False
                        else:
                            # Original text-based validation logic
                            print(f"Text length: {len(text)} characters, {len(text.split())} tokens")
                        content_sample = text[:1000].strip()
                            meaningful_words = ["bitcoin", "blockchain", "wallet", "transaction", "address", "key", "network", "chapter", "portfolio", "investment", "risk", "return", "market", "asset", "financial"]
                        has_meaningful_content = any(word in content_sample.lower() for word in meaningful_words)
                        word_count = len(text.split())
                            print(f"Extracted text has {word_count} words")
                            print(f"Text appears to have meaningful content: {has_meaningful_content}")
                        if has_meaningful_content and word_count > 100:
                                print(f"✅ High-quality text-based PDF found and saved: {book_path}")
                            found_high_quality = True
                                # Save metadata
                                meta_path = book_path.with_suffix(book_path.suffix + ".meta")
                                meta_dict = {
                                    "title": result['title'],
                                    "author": author,
                                    "year": year,
                                    "md5": md5,
                                    "file_info": result['file_info'],
                                    "download_date": str(datetime.datetime.now()),
                                    "query": search_query,
                                    "is_image_based": False,
                                    "num_pages": num_pages
                                }
                                with open(meta_path, 'w', encoding='utf-8') as f:
                                    json.dump(meta_dict, f, indent=2)
                            break
            else:
                                print("⚠️ Low-quality text-based PDF, trying next result...")
                            os.remove(book_path)
                                valid_pdf = False
                    except Exception as e:
                        print(f"[Selenium] Error extracting text from book: {e}")
                        os.remove(book_path)
        if not found_high_quality:
            print(f"❌ No high-quality PDF found for '{search_query}' after trying top {max_attempts} results.")
    return True 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect books from Anna's Archive")
    parser.add_argument("--batch-json", help="Path to JSON file containing book titles", default="G:/ai_trading_dev/CryptoFinanceCorpusBuilder/config/curated_list.json")
    parser.add_argument("--output-dir", help="Directory to save downloaded books")
    parser.add_argument("--existing-titles", help="Path to file containing existing titles for deduplication")
    parser.add_argument("--project-config", help="Path to ProjectConfig YAML file")
    args = parser.parse_args()
    
    if not args.output_dir and not args.project_config:
        logger.error("Error: Either --output-dir or --project-config is required")
        sys.exit(1)
        
    success = run_annas_main_library_collector(args, None, args.output_dir, args.batch_json)
    if not success:
        sys.exit(1) 