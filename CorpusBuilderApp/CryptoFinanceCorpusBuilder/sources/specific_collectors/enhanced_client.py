# enhanced_client.py
import re
import os
import json
import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

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
                print("✅ Successfully authenticated with account cookie")
                return True
            else:
                print("❌ Not authenticated - invalid or expired cookie")
                return False
        except Exception as e:
            print(f"Error verifying authentication: {e}")
            return False
    
    def search(self, query, content_type="book", language="en", ext="pdf"):
        """Search for books with specific parameters"""
        print(f"Searching for: '{query}'")
        
        # Make search request
        search_url = "https://annas-archive.org/search"
        params = {
            "q": query,
            "content": content_type,
            "lang": language,
            "ext": ext
        }
        
        try:
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            # Parse HTML to extract results
            soup = BeautifulSoup(response.text, "html.parser")
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
                
                # Parse file type and size
                file_type = ext
                file_size = "Unknown"
                
                if "pdf" in file_info.lower():
                    file_type = "pdf"
                elif "epub" in file_info.lower():
                    file_type = "epub"
                
                size_match = re.search(r"(\d+(\.\d+)?\s*(MB|KB))", file_info)
                if size_match:
                    file_size = size_match.group(0)
                
                results.append({
                    "title": title,
                    "md5": md5,
                    "link": f"https://annas-archive.org/md5/{md5}",
                    "file_type": file_type,
                    "file_size": file_size,
                    "file_info": file_info
                })
            
            print(f"Found {len(results)} results")
            return results
            
        except Exception as e:
            print(f"Error searching for '{query}': {e}")
            return []
    
    def download_file(self, md5, output_path=None):
        """Download a file using its MD5 hash"""
        if not self.is_authenticated:
            print("Cannot download - not authenticated")
            return None
        
        try:
            # First visit the details page to set up proper referrer
            detail_url = f"https://annas-archive.org/md5/{md5}"
            print(f"Visiting details page: {detail_url}")
            
            detail_response = self.session.get(detail_url)
            detail_response.raise_for_status()
            
            # Extract title for filename if output_path not provided
            title = "unknown"
            soup = BeautifulSoup(detail_response.text, "html.parser")
            title_elem = soup.find("h1")
            if title_elem:
                title = title_elem.get_text().strip()
                # Clean title for filename
                title = "".join(c if c.isalnum() or c in ['-', '_', ' '] else '_' for c in title)
                title = title[:50]  # Limit length
            
            # Create output path if not provided
            if not output_path:
                file_type = "pdf"  # Default to PDF
                output_path = self.download_dir / f"{title}_{md5}.{file_type}"
            
            # Now try the fast download link
            download_url = f"https://annas-archive.org/fast_download/{md5}/0/0"
            print(f"Accessing fast download: {download_url}")
            
            download_response = self.session.get(
                download_url,
                headers={"Referer": detail_url},
                allow_redirects=True
            )
            
            # Check if direct PDF download
            if "application/pdf" in download_response.headers.get("Content-Type", ""):
                print("Received direct PDF download")
                with open(output_path, "wb") as f:
                    f.write(download_response.content)
                
                print(f"✅ File saved to: {output_path}")
                return output_path
            
            # If not direct PDF, check for viewer or links
            print("No direct PDF download, checking for viewer or links")
            download_soup = BeautifulSoup(download_response.text, "html.parser")
            
            # Check if we hit the membership wall
            if "Become a member" in download_response.text:
                print("❌ Hit membership wall - authentication may have failed")
                return None
            
            # Check for iframe with PDF
            iframe = download_soup.find("iframe")
            if iframe and iframe.get("src"):
                iframe_src = iframe.get("src")
                
                # Make sure iframe URL is absolute
                if not iframe_src.startswith("http"):
                    iframe_src = "https://annas-archive.org" + iframe_src if iframe_src.startswith("/") else iframe_src
                
                print(f"Found PDF viewer iframe: {iframe_src}")
                
                iframe_response = self.session.get(
                    iframe_src,
                    headers={"Referer": download_url}
                )
                
                if "application/pdf" in iframe_response.headers.get("Content-Type", ""):
                    print("Downloading PDF from iframe")
                    with open(output_path, "wb") as f:
                        f.write(iframe_response.content)
                    
                    print(f"✅ File saved to: {output_path}")
                    return output_path
            
            # Look for download links
            download_links = []
            for a in download_soup.find_all("a", href=True):
                href = a.get("href")
                text = a.get_text().strip()
                
                if "download" in href.lower() or "download" in text.lower() or ".pdf" in href.lower():
                    download_links.append((text, href))
            
            print(f"Found {len(download_links)} potential download links")
            
            for text, href in download_links:
                print(f"Trying link: {text} - {href}")
                
                # Make sure URL is absolute
                if not href.startswith("http"):
                    href = "https://annas-archive.org" + href if href.startswith("/") else href
                
                link_response = self.session.get(
                    href,
                    headers={"Referer": download_url}
                )
                
                if "application/pdf" in link_response.headers.get("Content-Type", ""):
                    print("Downloading PDF from link")
                    with open(output_path, "wb") as f:
                        f.write(link_response.content)
                    
                    print(f"✅ File saved to: {output_path}")
                    return output_path
            
            print("❌ Could not find a way to download the file")
            return None
            
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None
    
    def download_best_result(self, query, prefer_format="pdf", domain_dir=None):
        """Search for query and download the best result"""
        # Set up domain directory
        if domain_dir:
            target_dir = self.download_dir / domain_dir
            target_dir.mkdir(parents=True, exist_ok=True)
        else:
            target_dir = self.download_dir
            
        # Search for the term
        results = self.search(query, ext=prefer_format)
        
        if not results:
            print("No results found, cannot download")
            return None
            
        # Select the best result
        best_result = self.select_best_result(results, prefer_format)
        
        if not best_result:
            print("Could not select a suitable result")
            return None
            
        # Create filepath
        title = best_result.get('title', 'Unknown')
        safe_title = "".join(c if c.isalnum() or c in ['-', '_', ' '] else '_' for c in title)
        safe_title = safe_title[:80]  # Limit filename length
        
        md5 = best_result.get('md5', '')
        file_ext = prefer_format
        
        filepath = target_dir / f"{safe_title}_{md5}.{file_ext}"
        
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
    
    def select_best_result(self, results, prefer_format="pdf"):
        """Select the best result from search results based on quality indicators"""
        if not results:
            print("No results to select from")
            return None
            
        print(f"Selecting best result from {len(results)} options...")
        
        # First filter by preferred format if specified
        format_matches = [r for r in results if prefer_format in r.get('file_info', '').lower()]
        
        # If no format matches, use all results
        candidates = format_matches if format_matches else results
        print(f"Found {len(candidates)} candidates in preferred format: {prefer_format}")
        
        # Score each result based on quality indicators
        scored_results = []
        for result in candidates:
            score = 0
            
            # Look for quality indicators in title and file info
            info_text = (result.get('title', '') + ' ' + result.get('file_info', '')).lower()
            
            # Prefer official/published versions
            if any(term in info_text for term in ['official', 'publisher', 'random house', 'penguin']):
                score += 10
                
            # Prefer higher quality
            if 'retail' in info_text:
                score += 5
                
            # Prefer properly formatted
            if 'properly formatted' in info_text:
                score += 3
                
            # File size considerations - prefer larger files as they tend to be better quality
            size_match = re.search(r'(\d+(\.\d+)?)\s*(MB|KB)', info_text)
            if size_match:
                size_val = float(size_match.group(1))
                size_unit = size_match.group(3)
                
                # Convert KB to MB for consistent comparison
                if size_unit == 'KB':
                    size_val /= 1024
                
                # Score based on size (prefer larger files)
                if size_val >= 10:  # Larger files often better quality
                    score += 8
                elif 5 <= size_val < 10:
                    score += 6
                elif 1 <= size_val < 5:
                    score += 4
                elif 0.5 <= size_val < 1:
                    score += 2
                else:  # Too small, likely poor quality
                    score -= 2
            
            scored_results.append((result, score))
            
        # Sort by score, highest first
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        # Print top 3 scored results
        print("\nTop 3 results by quality score:")
        for i, (result, score) in enumerate(scored_results[:min(3, len(scored_results))]):
            print(f"Result #{i+1} (Score: {score}):")
            print(f"  Title: {result.get('title', 'Unknown')}")
            print(f"  File info: {result.get('file_info', 'Unknown')}")
            
        # Return the highest scored result
        best_result = scored_results[0][0]
        print(f"\nSelected best result: {best_result.get('title', 'Unknown')}")
        return best_result
    
    def check_file_validity(self, filepath):
        """Check if a file appears to be valid based on its signature"""
        if not os.path.exists(filepath):
            print(f"File does not exist: {filepath}")
            return False
            
        try:
            with open(filepath, 'rb') as f:
                header = f.read(8)  # Read first 8 bytes for signature check
                
                # Check file signature
                if filepath.suffix.lower() == '.pdf' and not header.startswith(b'%PDF'):
                    print(f"Invalid PDF file: {filepath}")
                    print(f"Header: {header}")
                    return False
                elif filepath.suffix.lower() == '.epub' and not header.startswith(b'PK\x03\x04'):
                    print(f"Invalid EPUB file: {filepath}")
                    print(f"Header: {header}")
                    return False
                    
            # If we reached here, file seems valid
            return True
        except Exception as e:
            print(f"Error checking file validity: {e}")
            return False