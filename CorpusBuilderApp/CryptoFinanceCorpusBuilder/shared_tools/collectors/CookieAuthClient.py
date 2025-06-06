# CookieAuthClient.py - Balanced quality and PDF focus
import re
import os
import json
import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import time
import logging

class CookieAuthClient:
    """Client for Anna's Archive with focus on high-quality PDFs"""
    
    def __init__(self, download_dir=None, account_cookie=None):
        """Initialize the client with proper authentication"""
        # Set up download directory
        if download_dir:
            self.download_dir = Path(download_dir)
        else:
            self.download_dir = Path("/workspace/data/corpus_1/temp")
            print("WARNING: Using default (legacy) download directory. Please pass a harmonized output directory for proper domain-based organization.")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Use provided cookie or load from environment
        self.account_cookie = account_cookie
        if not self.account_cookie:
            load_dotenv("/workspace/notebooks/.env")
            self.account_cookie = os.getenv("AA_ACCOUNT_COOKIE")
            
        if not self.account_cookie:
            print("WARNING: No account cookie provided or found in environment")
        
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
            print("Set aa_account_id2 authentication cookie")
        
        # Verify authentication
        self.is_authenticated = self._verify_authentication()
    
    def _verify_authentication(self):
        """Check if the authentication cookie is valid"""
        try:
            account_url = "https://annas-archive.org/account"
            response = self.session.get(account_url)
            
            # Check for authenticated indicators
            if "Downloaded files" in response.text:
                print("[OK] Successfully authenticated with account cookie")
                return True
            else:
                print("[ERROR] Not authenticated - invalid or expired cookie")
                return False
        except Exception as e:
            print(f"Error verifying authentication: {e}")
            return False
    
    def search(self, query, extended_search=True):
        """Two-phase search: First try PDF-only, then try without filter if needed"""
        print(f"Searching for: '{query}'")
        
        # Phase 1: Try with PDF filter
        search_url = "https://annas-archive.org/search"
        params = {
            "q": query,
            "ext": "pdf"  # Start with PDF filter
        }
        
        try:
            print("Searching for PDFs...")
            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            results = self._parse_search_results(response.text)
            
            # If no results and extended_search is enabled, try without PDF filter
            if not results and extended_search:
                print("No PDF results found. Trying without PDF filter...")
                params = {"q": query}  # Remove PDF filter
                
                response = self.session.get(search_url, params=params, timeout=30)
                response.raise_for_status()
                
                # Parse all results, but note which ones are PDFs
                all_results = self._parse_search_results(response.text, mark_pdf=True)
                
                # Filter out non-PDFs if possible
                pdf_results = [r for r in all_results if r.get('is_pdf', False)]
                
                if pdf_results:
                    print(f"Found {len(pdf_results)} PDF results in extended search")
                    results = pdf_results
                else:
                    print("No PDF results found even in extended search")
            else:
                print(f"Found {len(results)} PDF results in initial search")
                
            return results
            
        except Exception as e:
            print(f"Error searching for '{query}': {e}")
            return []
    
    def _parse_search_results(self, html_content, mark_pdf=False):
        """Parse search results from HTML content"""
        soup = BeautifulSoup(html_content, "html.parser")
        results = []
        
        # Find all result containers
        result_divs = soup.find_all("div", class_=lambda c: c and "mb-4" in c)
        
        for div in result_divs:
            # Extract MD5 hash from link
            link_elem = div.find("a", href=lambda h: h and "/md5/" in h)
            if not link_elem:
                continue
            
            href = link_elem.get("href", "")
            md5_match = re.search(r"/md5/([a-f0-9]+)", href)
            
            if not md5_match:
                continue
            
            md5 = md5_match.group(1)
            
            # Extract title
            title = link_elem.get_text().strip()
            
            # Extract file info
            file_info = "Unknown format and size"
            info_div = div.find("div", class_=lambda c: c and "text-xs" in c)
            if info_div:
                file_info = info_div.get_text().strip()
            
            # Check if it's a PDF
            is_pdf = "pdf" in file_info.lower()
            
            # Skip non-PDFs unless mark_pdf is True
            if not mark_pdf and not is_pdf:
                continue
            
            # Extract publisher if present
            publisher = ""
            publisher_match = re.search(r"([^,]+)(Press|Publishing|Publisher|Random House|Penguin|Springer|O'Reilly|Wiley|Academic)", file_info)
            if publisher_match:
                publisher = publisher_match.group(0)
            
            # Parse file size
            file_size = "Unknown"
            size_mb = 0
            size_match = re.search(r"(\d+(\.\d+)?)\s*(MB|KB)", file_info)
            if size_match:
                file_size = size_match.group(0)
                size_val = float(size_match.group(1))
                size_unit = size_match.group(3)
                
                # Convert KB to MB for consistent comparison
                if size_unit.upper() == 'KB':
                    size_mb = size_val / 1024
                else:
                    size_mb = size_val
            
            result = {
                "title": title,
                "md5": md5,
                "link": f"https://annas-archive.org/md5/{md5}",
                "file_size": file_size,
                "size_mb": size_mb,
                "file_info": file_info,
                "publisher": publisher
            }
            
            if mark_pdf:
                result["is_pdf"] = is_pdf
                
            results.append(result)
        
        return results
    
    def download_file(self, md5, output_path=None):
        """Download PDF using its MD5 hash"""
        if not self.is_authenticated:
            print("Cannot download - not authenticated")
            return None
        
        try:
            # First visit the details page to set up proper referrer
            detail_url = f"https://annas-archive.org/md5/{md5}"
            print(f"Visiting details page: {detail_url}")
            
            detail_response = self.session.get(detail_url, timeout=30)
            detail_response.raise_for_status()
            
            # Extract title for filename if output_path not provided
            title = "unknown"
            soup = BeautifulSoup(detail_response.text, "html.parser")
            title_elem = soup.find("h1")
            if title_elem:
                title = title_elem.get_text().strip()
                # Clean title for filename
                title = re.sub(r'[\\/*?:"<>|]', "", title)
                # Limit length
                if len(title) > 80:
                    title = title[:77] + "..."
            
            # Create output path if not provided
            if not output_path:
                output_path = self.download_dir / f"{title} [{md5[:8]}].pdf"
            
            # Direct access to server 0 which usually works best
            download_url = f"https://annas-archive.org/fast_download/{md5}/0/0"
            print(f"Downloading PDF from: {download_url}")
            
            download_response = self.session.get(
                download_url,
                headers={"Referer": detail_url},
                allow_redirects=True,
                timeout=60  # Increase timeout for large files
            )
            
            # Check if it's a PDF
            content_type = download_response.headers.get("Content-Type", "").lower()
            
            if "application/pdf" in content_type:
                print(f"Received PDF content. Saving to file...")
                with open(output_path, "wb") as f:
                    f.write(download_response.content)
                
                print(f"✅ PDF saved to: {output_path}")
                
                # Check if the PDF is valid
                if self.check_file_validity(output_path):
                    return output_path
                else:
                    print("Downloaded file is not a valid PDF. Trying another server...")
                    # Try to remove invalid file
                    try:
                        os.remove(output_path)
                    except:
                        pass
            else:
                # If we got HTML instead of PDF, check if it has membership wall
                if "Become a member" in download_response.text:
                    print("❌ Hit membership wall - authentication may have failed")
                    return None
            
            # First server didn't work, try server 1
            alt_download_url = f"https://annas-archive.org/fast_download/{md5}/0/1"
            print(f"Trying alternative server: {alt_download_url}")
            
            alt_response = self.session.get(
                alt_download_url,
                headers={"Referer": detail_url},
                allow_redirects=True,
                timeout=60
            )
            
            # Check if it's a PDF
            alt_content_type = alt_response.headers.get("Content-Type", "").lower()
            
            if "application/pdf" in alt_content_type:
                print(f"Received PDF from alternative server. Saving to file...")
                with open(output_path, "wb") as f:
                    f.write(alt_response.content)
                
                # Check if the PDF is valid
                if self.check_file_validity(output_path):
                    print(f"✅ PDF saved to: {output_path}")
                    return output_path
                else:
                    print("Downloaded file is not a valid PDF.")
                    # Try to remove invalid file
                    try:
                        os.remove(output_path)
                    except:
                        pass
            
            print("❌ Could not download a valid PDF.")
            return None
            
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None
    
    def download_best_result(self, query, domain_dir=None):
        """Search for query and download the best PDF result"""
        # Set up domain directory
        if domain_dir:
            target_dir = self.download_dir / domain_dir
            target_dir.mkdir(parents=True, exist_ok=True)
        else:
            target_dir = self.download_dir
            
        # Search for PDFs
        results = self.search(query)
        
        if not results:
            print("No PDF results found, cannot download")
            return None
            
        # Select the best result
        best_result = self.select_best_result(results)
        
        if not best_result:
            print("Could not select a suitable result")
            return None
            
        # Create filepath with improved naming
        title = best_result.get('title', 'Unknown')
        # Clean up title for filename
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
        if len(safe_title) > 80:
            safe_title = safe_title[:77] + "..."
        
        md5 = best_result.get('md5', '')
        
        filepath = target_dir / f"{safe_title} [{md5[:8]}].pdf"
        
        # Download the file
        downloaded_file = self.download_file(md5, filepath)
        
        if downloaded_file:
            # Save metadata
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
    
    def download_from_list(self, download_list, domain_dir=None):
        """Download PDFs from a curated list"""
        results = {
            "successful": [],
            "failed": []
        }
        
        for i, item in enumerate(download_list):
            title = item.get("title", "")
            author = item.get("author", "")
            domain = item.get("domain", domain_dir)
            
            # Create search query
            search_query = title
            if author:
                search_query += f" {author}"
            
            print(f"\n[{i+1}/{len(download_list)}] Processing: {search_query}")
            
            # Set up domain directory
            if domain:
                target_dir = self.download_dir / domain
                target_dir.mkdir(parents=True, exist_ok=True)
            else:
                target_dir = self.download_dir
            
            # Search for PDFs with extended search if needed
            search_results = self.search(search_query)
            
            if not search_results:
                print(f"No PDF results found for: {search_query}")
                
                # Try with a broader query - just the title
                if author and len(title.split()) >= 2:
                    print(f"Trying with broader query: {title}")
                    search_results = self.search(title)
                
                if not search_results:
                    results["failed"].append({
                        "item": item,
                        "reason": "No PDF results found"
                    })
                    continue
            
            # Select best result
            best_result = self.select_best_result(search_results)
            
            if not best_result:
                print(f"Could not select a suitable result for: {search_query}")
                results["failed"].append({
                    "item": item,
                    "reason": "No suitable result found"
                })
                continue
            
            # Create a clean filename
            clean_title = re.sub(r'[\\/*?:"<>|]', "", title)
            if len(clean_title) > 80:
                clean_title = clean_title[:77] + "..."
            
            md5 = best_result.get('md5', '')
            
            filepath = target_dir / f"{clean_title} [{md5[:8]}].pdf"
            
            # Download the file - with just one retry
            download_attempts = 0
            max_attempts = 2
            downloaded_file = None
            
            while download_attempts < max_attempts and not downloaded_file:
                if download_attempts > 0:
                    print(f"Retry attempt...")
                    time.sleep(3)  # Short wait before retrying
                    
                downloaded_file = self.download_file(md5, filepath)
                download_attempts += 1
            
            if downloaded_file:
                # Save metadata
                meta_file = filepath.with_suffix(f"{filepath.suffix}.meta")
                with open(meta_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'title': title,
                        'author': author,
                        'md5': md5,
                        'file_info': best_result.get('file_info', ''),
                        'download_date': str(datetime.datetime.now()),
                        'domain': domain,
                        'original_search': search_query
                    }, f, indent=2)
                
                results["successful"].append({
                    "item": item,
                    "filepath": str(downloaded_file),
                    "md5": md5
                })
                
                print(f"✅ Successfully downloaded: {downloaded_file.name}")
            else:
                results["failed"].append({
                    "item": item,
                    "reason": "Download failed",
                    "md5": md5
                })
                
                print(f"❌ Failed to download: {clean_title}")
            
            # Add a short delay between downloads
            if i < len(download_list) - 1:
                delay = 2
                print(f"Waiting {delay} seconds before next download...")
                time.sleep(delay)
        
        # Print summary
        print("\n===== Download Summary =====")
        print(f"Total items: {len(download_list)}")
        print(f"Successful: {len(results['successful'])}")
        print(f"Failed: {len(results['failed'])}")
        
        # Save results to file
        results_file = self.download_dir / "download_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to: {results_file}")
        
        return results
    
    def select_best_result(self, results):
        """Select the best PDF result based on quality indicators"""
        if not results:
            print("No results to select from")
            return None
            
        print(f"Selecting best result from {len(results)} options...")
        
        # Score each result based on quality indicators
        scored_results = []
        for result in results:
            score = 0
            
            # Look for quality indicators in title and file info
            info_text = (result.get('title', '') + ' ' + result.get('file_info', '')).lower()
            
            # Prefer official/published versions
            if any(term in info_text for term in ['official', 'publisher', 'random house', 'penguin', 'springer', 'wiley', "o'reilly"]):
                score += 15
                
            # Prefer specific publisher mentioned in result
            if result.get('publisher'):
                score += 10
                
            # Prefer higher quality indicators
            if 'retail' in info_text:
                score += 8
                
            if 'properly formatted' in info_text:
                score += 5
                
            # Strong preference for large files
            size_mb = result.get('size_mb', 0)
            if size_mb > 0:
                # Exponential scoring for size - strongly prefer larger PDFs
                if size_mb >= 20:  # Very large PDFs (likely high quality)
                    score += 25
                elif size_mb >= 10:  # Large PDFs
                    score += 20
                elif size_mb >= 5:   # Medium-sized PDFs
                    score += 15
                elif size_mb >= 2:   # Smaller PDFs
                    score += 10
                elif size_mb >= 1:   # Very small PDFs
                    score += 5
                else:               # Tiny PDFs (likely poor quality)
                    score += 0
            
            scored_results.append((result, score))
            
        # Sort by score, highest first
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        # Print top 3 scored results
        print("\nTop results by quality score:")
        for i, (result, score) in enumerate(scored_results[:min(3, len(scored_results))]):
            size_info = f"{result.get('size_mb', 0):.1f} MB" if result.get('size_mb', 0) > 0 else result.get('file_size', 'Unknown size')
            print(f"Result #{i+1} (Score: {score}):")
            print(f"  Title: {result.get('title', 'Unknown')}")
            print(f"  Size: {size_info}")
            print(f"  Info: {result.get('file_info', 'Unknown')}")
            
        # Return the highest scored result
        best_result = scored_results[0][0]
        print(f"\nSelected best result: {best_result.get('title', 'Unknown')}")
        return best_result
    
    def check_file_validity(self, filepath):
        """Check if file is a valid PDF"""
        if not os.path.exists(filepath):
            print(f"File does not exist: {filepath}")
            return False
            
        try:
            # Check file size - reject extremely small files
            file_size = os.path.getsize(filepath)
            if file_size < 10000:  # Less than 10KB
                print(f"File too small to be a valid PDF: {file_size/1024:.1f} KB")
                return False
                
            with open(filepath, 'rb') as f:
                header = f.read(4)  # First 4 bytes for PDF signature
                
                if not header.startswith(b'%PDF'):
                    print(f"Invalid PDF file: {filepath}")
                    print(f"Header: {header}")
                    return False
                    
            # If we reached here, file is a valid PDF
            print(f"Valid PDF verified: {filepath.name} ({file_size/1024/1024:.2f} MB)")
            return True
        except Exception as e:
            print(f"Error checking file validity: {e}")
            return False
