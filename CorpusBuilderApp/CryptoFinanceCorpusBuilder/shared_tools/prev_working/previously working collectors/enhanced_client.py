# enhanced_client.py - COMPLETE FINAL FIXED VERSION
import re
import os
import json
import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import time
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import shutil
from CryptoFinanceCorpusBuilder.utils.extractor_utils import safe_filename

class CookieAuthClient:
    """Client for Anna's Archive that uses cookie-based authentication"""
    
    def __init__(self, download_dir=None, account_cookie=None):
        """Initialize the client with proper authentication"""
        # Set up download directory
        self.download_dir = Path(download_dir) if download_dir else Path("/workspace/data/corpus_1/temp")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Use provided cookie or load from environment
        self.account_cookie = account_cookie
        if not self.account_cookie:
            load_dotenv("/workspace/notebooks/.env")
            self.account_cookie = os.getenv("AA_ACCOUNT_COOKIE")
            
        if not self.account_cookie:
            pass  # Minimal: removed debug print
        
        # Initialize session with browser-like headers
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
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
        
        # Verify authentication
        self.is_authenticated = self._verify_authentication()
    
    def _verify_authentication(self):
        """Check if the authentication cookie is valid"""
        try:
            account_url = "https://annas-archive.org/account"
            response = self.session.get(account_url)
            if "Downloaded files" in response.text:
                print("Authenticated with Anna's Archive.")
                return True
            else:
                print("Authentication failed: invalid or expired cookie.")
                return False
        except Exception:
            print("Authentication check error.")
            return False
    
    def search(self, query, content_type="book", language="en", ext="pdf"):
        """FIXED: Form-based search with proper checkbox handling"""
        print(f"Searching for: '{query}'")
        
        try:
            # Step 1: Navigate to search page 
            search_url = "https://annas-archive.org/search"
            search_response = self.session.get(search_url)
            search_response.raise_for_status()
            
            # Step 2: Submit form with proper checkboxes
            params = {
                'q': query,
                'ext': 'pdf',                    # ✅ PDF checkbox (Include only)     # ✅ Partner Server (Include only) 
            }
            
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            
            # Look for result containers
            result_containers = soup.find_all("div", class_=lambda c: c and "mb-4" in c)
            
            for container in result_containers:
                link_elem = container.find("a", href=lambda h: h and "/md5/" in h)
                if not link_elem:
                    continue
                    
                href = link_elem.get("href", "")
                md5_match = re.search(r"/md5/([a-f0-9]+)", href)
                if not md5_match:
                    continue
                    
                md5 = md5_match.group(1)
                title = link_elem.get_text().strip()
                
                # Extract file info
                file_info = "Unknown"
                info_candidates = container.find_all(["div", "span"], class_=lambda c: c and ("text-xs" in (c or "") or "text-sm" in (c or "")))
                
                for info_elem in info_candidates:
                    text = info_elem.get_text().strip()
                    if any(indicator in text.lower() for indicator in ["pdf", "epub", "mb", "kb", "azw"]):
                        file_info = text
                        break
                
                # Check if it's actually a PDF
                is_pdf = "pdf" in file_info.lower()
                has_partner_server = any(term in file_info.lower() for term in ["fast", "partner", "download"])
                
                # Calculate quality score
                quality_score = self._calculate_generic_quality_score(title, file_info, ext)
                size_mb = self._extract_file_size(file_info)
                year = self._extract_year(file_info)
                
                results.append({
                    "title": title,
                    "md5": md5,
                    "link": f"https://annas-archive.org/md5/{md5}",
                    "file_type": ext,
                    "file_size": f"{size_mb}MB" if size_mb > 0 else "Unknown",
                    "file_info": file_info,
                    "size_mb": size_mb,
                    "year": year,
                    "quality_score": quality_score
                })
            
            # Step 4: Filter and sort
            if ext:
                pdf_results = [r for r in results if ext.lower() in r["file_info"].lower()]
                
                if pdf_results:
                    results = pdf_results
            
            results.sort(key=lambda x: x["quality_score"], reverse=True)
            
            return results
            
        except Exception:
            return []
    
    def _calculate_generic_quality_score(self, title, file_info, preferred_format):
        """Generic quality scoring for any book type"""
        score = 0
        info_lower = (title + " " + file_info).lower()
        
        # Format matching bonus
        if preferred_format and preferred_format.lower() in info_lower:
            score += 40
        
        # Language bonus
        if "english" in info_lower:
            score += 25
        elif any(lang in info_lower for lang in ["eng", "en", "american", "british"]):
            score += 20
        
        # Size-based quality (larger files often better quality)
        size_mb = self._extract_file_size(file_info)
        if size_mb >= 50:
            score += 35
        elif size_mb >= 20:
            score += 30
        elif size_mb >= 10:
            score += 25
        elif size_mb >= 5:
            score += 20
        elif size_mb >= 1:
            score += 10
        elif size_mb > 0:
            score += 5
        
        # Quality indicators (generic across all book types)
        quality_terms = {
            "retail": 30,
            "official": 25,
            "publisher": 25,
            "original": 20,
            "clean": 15,
            "high quality": 15,
            "properly formatted": 15,
            "complete": 10,
            "unabridged": 10,
            "full": 8,
            "good": 5
        }
        
        for term, bonus in quality_terms.items():
            if term in info_lower:
                score += bonus
        
        # Negative indicators
        negative_terms = {
            "sample": -20,
            "preview": -20,
            "excerpt": -15,
            "damaged": -15,
            "corrupt": -15,
            "incomplete": -10,
            "poor quality": -10,
            "scan": -5
        }
        
        for term, penalty in negative_terms.items():
            if term in info_lower:
                score += penalty
        
        # Recency bonus
        year = self._extract_year(file_info)
        if year:
            if year >= 2020:
                score += 15
            elif year >= 2010:
                score += 10
            elif year >= 2000:
                score += 5
        
        return max(score, 0)
    
    def _extract_file_size(self, file_info):
        """Extract file size in MB from file info string"""
        size_match = re.search(r'(\d+(?:\.\d+)?)\s*(MB|KB|GB|bytes)', file_info, re.IGNORECASE)
        if size_match:
            size_val = float(size_match.group(1))
            size_unit = size_match.group(2).upper()
            
            if size_unit == "GB":
                return size_val * 1024
            elif size_unit == "KB":
                return size_val / 1024
            elif size_unit == "BYTES":
                return size_val / (1024 * 1024)
            else:  # MB
                return size_val
        return 0
    
    def _extract_year(self, file_info):
        """Extract publication year from file info"""
        year_match = re.search(r'\b(19|20)\d{2}\b', file_info)
        return int(year_match.group(0)) if year_match else None
    
    def _clean_title_for_filename(self, title):
        return "".join(c if c.isalnum() or c in ['-', '_', ' '] else '_' for c in title)[:80]

    def _write_metadata(self, meta_path, meta_dict):
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta_dict, f, indent=2)

    def _extract_title_and_info(self, soup):
        # Try <h1> first
        title = None
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)
        # Fallback: <title> tag
        if not title:
            t = soup.find('title')
            if t:
                title = t.get_text(strip=True)
        if not title:
            title = 'Unknown'
        # Clean for filename
        safe_title = self._clean_title_for_filename(title)
        file_info = ''
        info_div = soup.find('div', class_=lambda c: c and ("text-xs" in c or "text-sm" in c))
        if info_div:
            file_info = info_div.get_text(strip=True)
        return safe_title, file_info

    def download_file(self, md5, output_path=None, query=None):
        if not self.is_authenticated:
            print("Not authenticated.")
            return None
        print(f"Download started for {md5}.")
        try:
            detail_url = f"https://annas-archive.org/md5/{md5}"
            detail_response = self.session.get(detail_url)
            detail_response.raise_for_status()
            soup = BeautifulSoup(detail_response.text, "html.parser")
            safe_title, file_info = self._extract_title_and_info(soup)
            if not output_path:
                output_path = self.download_dir / f"{safe_title}_{md5}.pdf"
            success = self._try_no_redirect_download(md5, detail_url, output_path)
            if success:
                meta_path = output_path.with_suffix(output_path.suffix + ".meta")
                self._write_metadata(meta_path, {
                    'title': safe_title,
                    'md5': md5,
                    'file_info': file_info,
                    'download_date': str(datetime.datetime.now()),
                    'query': query or ''
                })
                print(f"Download complete for {md5}.")
                return success
            success = self._try_standard_download(md5, detail_url, output_path)
            if success:
                meta_path = output_path.with_suffix(output_path.suffix + ".meta")
                self._write_metadata(meta_path, {
                    'title': safe_title,
                    'md5': md5,
                    'file_info': file_info,
                    'download_date': str(datetime.datetime.now()),
                    'query': query or ''
                })
                print(f"Download complete for {md5}.")
                return success
            print(f"Download failed for {md5}.")
            return None
        except Exception:
            print(f"Error downloading file {md5}.")
            return None
    
    def _try_no_redirect_download(self, md5, detail_url, output_path):
        """Try the no-redirect download method with improved link filtering"""
        try:
            no_redirect_url = f"https://annas-archive.org/fast_download/{md5}/0/0?no_redirect=1"
            
            no_redirect_response = self.session.get(
                no_redirect_url,
                headers={"Referer": detail_url}
            )
            
            if no_redirect_response.status_code == 200:
                soup = BeautifulSoup(no_redirect_response.text, "html.parser")
                
                # Look for download links with better filtering
                download_links = []
                all_links = soup.find_all("a", href=True)
                
                for i, link in enumerate(all_links):
                    href = link.get("href", "")
                    text = link.get_text().strip()
                    
                    # Categorize links - ONLY try external download servers
                    if href.startswith('http') and 'annas-archive.org' not in href:
                        download_links.append(("external", href))
                    elif any(phrase in text.lower() for phrase in ["download now", "download"]) and not any(skip in href.lower() for skip in ['/account/', '/md5/', '/search']):
                        if href.startswith('/'):
                            full_url = "https://annas-archive.org" + href
                            download_links.append(("download_button", full_url))
                    elif any(skip in href.lower() for skip in ['/account/', '/md5/', '/search']):
                        continue
                    else:
                        continue
                
                # Prioritize external links first 
                external_links = [url for cat, url in download_links if cat == "external"]
                button_links = [url for cat, url in download_links if cat == "download_button"]
                
                all_links_to_try = external_links + button_links
                
                if not all_links_to_try:
                    return None
                
                # Try each download link with detailed debugging
                for i, download_url in enumerate(all_links_to_try):
                    try:
                        pdf_response = self.session.get(
                            download_url,
                            headers={"Referer": no_redirect_url},
                            timeout=30
                        )
                        
                        # Check response details
                        content_type = pdf_response.headers.get("Content-Type", "")
                        content_length = pdf_response.headers.get("Content-Length", "unknown")
                        
                        # Check if we got a PDF
                        if "application/pdf" in content_type or download_url.endswith(".pdf"):
                            with open(output_path, "wb") as f:
                                f.write(pdf_response.content)
                            
                            # Verify PDF
                            if self._verify_pdf(output_path):
                                return output_path
                            else:
                                if os.path.exists(output_path):
                                    os.remove(output_path)
                                continue
                        else:
                            # Debug: Show first part of response
                            if pdf_response.text:
                                preview = pdf_response.text[:300]
                                if "<html" in preview.lower():
                                    continue
                            continue
                        
                    except Exception as e:
                        continue
                
                return None
            
            return None
        except Exception:
            return None
    
    def _try_standard_download(self, md5, detail_url, output_path):
        """Try standard fast_download method"""
        try:
            standard_url = f"https://annas-archive.org/fast_download/{md5}/0/0"
            standard_response = self.session.get(
                standard_url,
                headers={"Referer": detail_url},
                allow_redirects=True
            )
            
            content_type = standard_response.headers.get("Content-Type", "")
            if "application/pdf" in content_type:
                with open(output_path, "wb") as f:
                    f.write(standard_response.content)
                
                if self._verify_pdf(output_path):
                    return output_path
                else:
                    if os.path.exists(output_path):
                        os.remove(output_path)
            
            return None
        except Exception:
            return None
    
    def _verify_pdf(self, filepath):
        """Verify that a downloaded file is a valid PDF with content"""
        try:
            # Check file size
            if os.path.getsize(filepath) < 10000:  # Less than 10KB
                return False
            
            # Check PDF header
            with open(filepath, 'rb') as f:
                header = f.read(8)
                if not header.startswith(b'%PDF'):
                    return False
            
            # Try to extract some text to verify it's not corrupted
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(filepath)
                
                if len(reader.pages) == 0:
                    return False
                    
                # Try to extract text from first few pages
                text_found = False
                for i, page in enumerate(reader.pages[:3]):  # Check first 3 pages
                    try:
                        text = page.extract_text()
                        if text and len(text.strip()) > 50:  # At least some meaningful text
                            text_found = True
                            break
                    except:
                        continue
                
                return True
                
            except Exception as e:
                return False
                
        except Exception:
            return False
    
    def download_main_library_file(self, query, output_path=None):
        """
        Selenium fallback: fully mimic the HTML/requests logic for Anna's Archive main library download.
        Accepts a full search query, performs the same search, result parsing, best result selection, and download attempts.
        """
        if not self.is_authenticated:
            print("Not authenticated.")
            return None
        print(f"[Selenium] Download started for query: {query}")
        base_url = "https://annas-archive.org"
        search_url = f"{base_url}/search"
        download_dir = str(self.download_dir.resolve())

        # Set up Chrome options
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-blink-features=AutomationControlled')
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)

        driver = None
        pdf_file = None
        try:
            driver = uc.Chrome(options=options)
            driver.get(base_url)
            driver.add_cookie({
                "name": "aa_account_id2",
                "value": self.account_cookie,
                "domain": "annas-archive.org",
                "path": "/"
            })
            driver.get(search_url)
            time.sleep(2)
            # Enter search query
            search_input = driver.find_element(By.NAME, "q")
            search_input.clear()
            search_input.send_keys(query)
            # Click search button
            search_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Search') or @type='submit']")
            search_button.click()
            time.sleep(4)
            # Parse results: find all result containers
            result_divs = driver.find_elements(By.XPATH, "//div[contains(@class, 'mb-4')]")
            results = []
            for div in result_divs:
                try:
                    link_elem = div.find_element(By.XPATH, ".//a[contains(@href, '/md5/')]")
                    href = link_elem.get_attribute("href")
                    md5_match = re.search(r"/md5/([a-f0-9]+)", href)
                    if not md5_match:
                        continue
                    md5 = md5_match.group(1)
                    title = link_elem.text.strip()
                    info_elem = div.find_element(By.XPATH, ".//*[contains(@class, 'text-xs') or contains(@class, 'text-sm')]")
                    file_info = info_elem.text.strip() if info_elem else "Unknown"
                    size_mb = self._extract_file_size(file_info)
                    year = self._extract_year(file_info)
                    quality_score = self._calculate_generic_quality_score(title, file_info, "pdf")
                    results.append({
                        "title": title,
                        "md5": md5,
                        "link": href,
                        "file_info": file_info,
                        "size_mb": size_mb,
                        "year": year,
                        "quality_score": quality_score
                    })
                except Exception:
                    continue
            if not results:
                print("[Selenium] No results found for the query.")
                return None
            results.sort(key=lambda x: x["quality_score"], reverse=True)
            best_result = results[0]
            md5 = best_result["md5"]
            title = best_result["title"]
            file_info = best_result["file_info"]
            # Go to detail page
            detail_url = f"{base_url}/md5/{md5}"
            driver.get(detail_url)
            time.sleep(2)
            # Try fast_download endpoint
            fast_download_url = f"{base_url}/fast_download/{md5}/0/0"
            driver.get(fast_download_url)
            time.sleep(2)
            # Check if PDF downloaded
            pdf_file = self._wait_for_pdf_download(download_dir)
            if pdf_file:
                print(f"[Selenium] PDF downloaded via fast_download: {pdf_file}")
            else:
                # Try <a class='fast-download-link'>
                driver.get(detail_url)
                time.sleep(2)
                try:
                    fast_link = driver.find_element(By.CLASS_NAME, "fast-download-link")
                    fast_link.click()
                    time.sleep(2)
                    pdf_file = self._wait_for_pdf_download(download_dir)
                    if pdf_file:
                        print(f"[Selenium] PDF downloaded via fast-download-link: {pdf_file}")
                except Exception:
                    pass
            if not pdf_file:
                # Try iframe
                try:
                    iframe = driver.find_element(By.TAG_NAME, "iframe")
                    iframe_src = iframe.get_attribute("src")
                    driver.get(iframe_src)
                    time.sleep(2)
                    pdf_file = self._wait_for_pdf_download(download_dir)
                    if pdf_file:
                        print(f"[Selenium] PDF downloaded via iframe: {pdf_file}")
                except Exception:
                    pass
            if not pdf_file:
                # Try all <a> links with 'download' or '.pdf'
                links = driver.find_elements(By.TAG_NAME, "a")
                for a in links:
                    href = a.get_attribute("href")
                    text = a.text.lower()
                    if href and ("download" in href.lower() or "download" in text or ".pdf" in href.lower()):
                        try:
                            driver.get(href)
                            time.sleep(2)
                            pdf_file = self._wait_for_pdf_download(download_dir)
                            if pdf_file:
                                print(f"[Selenium] PDF downloaded via generic link: {pdf_file}")
                                break
                        except Exception:
                            continue
            if not pdf_file:
                print("[Selenium] All download attempts failed.")
                return None
            # Save with normalized filename
            author = "Unknown"
            year = best_result.get("year", "Unknown")
            norm_title = safe_filename(title)
            final_path = Path(download_dir) / f"{author}_{year}_{norm_title}_{md5}.pdf"
            shutil.move(pdf_file, final_path)
            # Save metadata
            meta_path = final_path.with_suffix(final_path.suffix + ".meta")
            meta_dict = {
                "title": title,
                "author": author,
                "year": year,
                "md5": md5,
                "file_info": file_info,
                "download_date": str(datetime.datetime.now()),
                "query": query
            }
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta_dict, f, indent=2)
            print(f"[Selenium] Download and metadata complete: {final_path}")
            return str(final_path)
        except Exception as e:
            print(f"[Selenium] Error: {e}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def _wait_for_pdf_download(self, download_dir, timeout=90):
        """Wait for a PDF file to appear in the download directory."""
        time_waited = 0
        while time_waited < timeout:
            files = [f for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f))]
            pdfs = [f for f in files if f.lower().endswith('.pdf')]
            if pdfs:
                most_recent = max([os.path.join(download_dir, f) for f in pdfs], key=os.path.getmtime)
                if os.path.exists(most_recent):
                    size1 = os.path.getsize(most_recent)
                    time.sleep(2)
                    size2 = os.path.getsize(most_recent)
                    if size1 == size2 and size1 > 1000:
                        return most_recent
            time.sleep(2)
            time_waited += 2
        return None

    # MAINTAINED: All other methods stay exactly the same
    
    def download_best_result(self, query, prefer_format="pdf", domain_dir=None):
        """Download the best result for a query"""
        if domain_dir:
            target_dir = self.download_dir / domain_dir
            target_dir.mkdir(parents=True, exist_ok=True)
        else:
            target_dir = self.download_dir
            
        results = self.search(query, ext=prefer_format)
        
        if not results:
            print("No results found, cannot download")
            return None
            
        best_result = self.select_best_result(results, prefer_format)
        
        if not best_result:
            print("Could not select a suitable result")
            return None
            
        title = best_result.get('title', 'Unknown')
        safe_title = "".join(c if c.isalnum() or c in ['-', '_', ' '] else '_' for c in title)
        safe_title = safe_title[:80]
        
        md5 = best_result.get('md5', '')
        file_ext = prefer_format
        
        filepath = target_dir / f"{safe_title}_{md5}.{file_ext}"
        
        downloaded_file = self.download_file(md5, filepath)
        
        if downloaded_file:
            meta_file = filepath.with_suffix(f"{filepath.suffix}.meta")
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'title': title,
                    'md5': md5,
                    'file_info': best_result.get('file_info', ''),
                    'download_date': str(datetime.datetime.now()),
                    'query': query
                }, f, indent=2)
                
            return downloaded_file
        else:
            print("Download failed")
            return None
    
    def select_best_result(self, results, prefer_format="pdf"):
        """Select the best result from search results"""
        if not results:
            print("No results to select from")
            return None
            
        if results:
            return results[0]
        
        return None
    
    def check_file_validity(self, filepath):
        """Check if a file appears to be valid"""
        if not os.path.exists(filepath):
            print(f"File does not exist: {filepath}")
            return False
            
        try:
            with open(filepath, 'rb') as f:
                header = f.read(8)
                
                if filepath.suffix.lower() == '.pdf' and not header.startswith(b'%PDF'):
                    print(f"Invalid PDF file: {filepath}")
                    return False
                elif filepath.suffix.lower() == '.epub' and not header.startswith(b'PK\x03\x04'):
                    print(f"Invalid EPUB file: {filepath}")
                    return False
                    
            return True
        except Exception as e:
            print(f"Error checking file validity: {e}")
            return False
    
    def download_scidb_doi(self, doi, domain=None):
        """Download a paper using its DOI from SciDB (requests first, Selenium fallback)"""
        if not self.is_authenticated:
            print("Cannot download - not authenticated")
            return None

        if not self.account_cookie:
            print("Cannot download - no account cookie provided")
            return None

        print(f"[Requests] Attempting HTML-only download for DOI: {doi}")
        base_url = "https://annas-archive.org"
        direct_url = f"{base_url}/scidb/{doi}/"

        target_dir = self.download_dir / domain if domain else self.download_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        download_dir = str(target_dir.resolve())

        # --- Step 1: Try requests-based download ---
        try:
            detail_response = self.session.get(direct_url)
            soup = BeautifulSoup(detail_response.text, "html.parser")
            # 1. Try to find the <a> with text 'Download'
            pdf_url = None
            for a in soup.find_all('a', href=True):
                if a.text.strip().lower() == 'download':
                    pdf_url = a['href']
                    break
            # 2. If not found, try to extract from the iframe
            if not pdf_url:
                iframe = soup.find('iframe', src=True)
                if iframe and 'file=' in iframe['src']:
                    from urllib.parse import parse_qs, urlparse, unquote
                    qs = parse_qs(urlparse(iframe['src']).query)
                    file_url = qs.get('file', [None])[0]
                    if file_url:
                        pdf_url = unquote(file_url)
            # 3. If found, try to download
            if pdf_url:
                print(f"[Requests] Found PDF link: {pdf_url}")
                pdf_response = self.session.get(pdf_url, headers={"Referer": direct_url}, stream=True, timeout=60)
                content_type = pdf_response.headers.get("Content-Type", "").lower()
                if "application/pdf" in content_type or "application/octet-stream" in content_type:
                    # Save to temp file
                    temp_pdf_path = os.path.join(download_dir, f"temp_{doi.replace('/', '_')}.pdf")
                    with open(temp_pdf_path, 'wb') as f:
                        for chunk in pdf_response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    # Check validity
                    if os.path.getsize(temp_pdf_path) > 10000:
                        with open(temp_pdf_path, 'rb') as f:
                            header = f.read(8)
                            if header.startswith(b'%PDF'):
                                print(f"[Requests] Successfully downloaded PDF for DOI: {doi}")
                                pdf_file = temp_pdf_path
                                method = 'requests'
                    else:
                        os.remove(temp_pdf_path)
                        pdf_file = None
                else:
                    print(f"[Requests] Content-Type not PDF: {content_type}")
                    pdf_file = None
            else:
                print(f"[Requests] No direct PDF link found on page for DOI: {doi}")
                pdf_file = None
        except Exception as e:
            print(f"[Requests] Error during HTML-only download for DOI {doi}: {e}")
            pdf_file = None

        # --- Step 2: If requests failed, fall back to Selenium ---
        if not pdf_file or not os.path.exists(pdf_file):
            print(f"[Requests] HTML-only download failed, falling back to Selenium for DOI: {doi}")
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-blink-features=AutomationControlled')
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True,
                "safebrowsing.enabled": True
            }
            options.add_experimental_option("prefs", prefs)
            driver = None
            try:
                driver = uc.Chrome(options=options)
                driver.get(base_url)
                cookie_dict = {
                    "name": "aa_account_id2",
                    "value": str(self.account_cookie),
                    "domain": "annas-archive.org",
                    "path": "/"
                }
                try:
                    driver.add_cookie(cookie_dict)
                    print("[Selenium] Successfully set authentication cookie")
                except Exception as cookie_error:
                    print(f"[Selenium] Error setting cookie: {cookie_error}")
                    return None
                driver.get(direct_url)
                time.sleep(3)
                try:
                    download_link = driver.find_element(By.LINK_TEXT, "Download")
                except NoSuchElementException:
                    try:
                        download_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Download")
                    except NoSuchElementException:
                        print(f"[Selenium] No Download link found for DOI: {doi}")
                        return None
                download_link.click()
                print(f"[Selenium] Clicked Download for DOI: {doi}")
                time_waited = 0
                while time_waited < 60:
                    files = [f for f in os.listdir(download_dir) if f.lower().endswith('.pdf')]
                    if files:
                        files = sorted(files, key=lambda f: os.path.getmtime(os.path.join(download_dir, f)), reverse=True)
                        pdf_file = os.path.join(download_dir, files[0])
                        size1 = os.path.getsize(pdf_file)
                        time.sleep(2)
                        size2 = os.path.getsize(pdf_file)
                        if size1 == size2:
                            break
                    time.sleep(2)
                    time_waited += 2
                if not pdf_file or not os.path.exists(pdf_file):
                    print(f"[Selenium] PDF file not found after download for DOI: {doi}")
                    return None
                with open(pdf_file, 'rb') as f:
                    header = f.read(8)
                    if not header.startswith(b'%PDF'):
                        print(f"[Selenium] Downloaded file for DOI {doi} is not a valid PDF")
                        os.remove(pdf_file)
                        return None
                if os.path.getsize(pdf_file) < 10000:
                    print(f"[Selenium] Downloaded file for DOI {doi} is too small")
                    os.remove(pdf_file)
                    return None
                method = 'selenium'
            except Exception as e:
                print(f"[Selenium] Error during download process for DOI {doi}: {e}")
                if pdf_file and os.path.exists(pdf_file) and os.path.getsize(pdf_file) > 10000:
                    method = 'selenium'
                    # continue to metadata extraction
                else:
                    return None
            finally:
                if driver:
                    try:
                        driver.quit()
                    except Exception as quit_error:
                        print(f"[Selenium] Error quitting driver: {quit_error}")
                        pass
        else:
            method = 'requests'

        # --- Metadata extraction and filename construction (same for both methods) ---
        try:
            # Use the same soup as above if available, else re-fetch
            if 'soup' not in locals() or soup is None:
                detail_response = self.session.get(direct_url)
                soup = BeautifulSoup(detail_response.text, "html.parser")
            authors_div = soup.find('div', class_='italic')
            authors = authors_div.get_text(strip=True) if authors_div else None
            citation_div = soup.find('div', class_='font-bold')
            citation = citation_div.get_text(strip=True) if citation_div else None
            import re
            year = None
            if citation:
                year_match = re.search(r'(19|20)\\d{2}', citation)
                if year_match:
                    year = year_match.group(0)
            journal = None
            if citation:
                parts = citation.split(',')
                for part in parts:
                    if 'journal' in part.lower() or 'cytopathology' in part.lower():
                        journal = part.strip()
                        break
            title = f'DOI {doi}'
            md5 = None
            md5_elem = soup.find('a', href=lambda h: h and '/md5/' in h)
            if md5_elem:
                md5_match = re.search(r'/md5/([a-f0-9]+)', md5_elem['href'])
                if md5_match:
                    md5 = md5_match.group(1)
            if not md5:
                md5 = "unknownmd5"
            fields = [title, authors, journal, year, doi.replace('/', '_'), md5[:8]]
            safe_fields = [safe_filename(str(f)) for f in fields if f and f != 'unknown' and f != 'None']
            filename = " -- ".join(safe_fields)[:120] + ".pdf"
            new_filepath = os.path.join(download_dir, filename)
            if os.path.abspath(pdf_file) != os.path.abspath(new_filepath):
                shutil.move(pdf_file, new_filepath)
            meta = {
                'title': title,
                'authors': authors,
                'journal': journal,
                'year': year,
                'doi': doi,
                'md5': md5,
                'download_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'SciDB',
                'download_url': direct_url,
                'download_method': method
            }
            meta_file = new_filepath + ".meta"
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2)
            print(f"✅ [{method.upper()}] Downloaded: {new_filepath}")
            return new_filepath
        except Exception as e:
            print(f"[Meta] Error during metadata extraction/renaming for DOI {doi}: {e}")
            return None