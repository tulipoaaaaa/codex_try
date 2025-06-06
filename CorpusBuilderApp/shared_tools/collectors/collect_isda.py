import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
from pathlib import Path
from .base_collector import BaseCollector

class ISDADocumentationCollector(BaseCollector):
    def __init__(self, config, sources=None):
        if isinstance(config, str):
            from shared_tools.project_config import ProjectConfig
            config = ProjectConfig(config, environment='test')
        super().__init__(config)
        self.sources = sources or []
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        # Set up ISDA-specific directory based on environment
        self.isda_dir = self.config.raw_data_dir / 'ISDA'
        self.isda_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"ISDA directory set to: {self.isda_dir}")

    def _get_output_path(self, filename, content_type='reports'):
        """Get the correct output path for ISDA content."""
        # Always save in the ISDA directory
        return self.isda_dir / filename

    def find_isda_documentation(self):
        """Find ISDA documentation pages and create a structured reference list."""
        potential_urls = [
            "https://www.isda.org/books/",
            "https://www.isda.org/documentation/",
            "https://www.isda.org/documents/",
            "https://www.isda.org/protocols/",
            "https://www.isda.org/guides/",
            "https://www.isda.org/bookstore/",
            "https://www.isda.org/books-and-protocols/",
            "https://www.isda.org/book-and-protocol-list/",
            "https://www.isda.org/legal-documentation/"
        ]
        
        self.logger.info("Checking ISDA main site navigation for documentation links")
        documentation_pages = []
        
        try:
            # Check main site navigation
            main_response = self.session.get("https://www.isda.org")
            main_response.raise_for_status()
            main_soup = BeautifulSoup(main_response.text, "html.parser")
            nav_items = main_soup.find_all("a", href=True)
            
            for item in nav_items:
                text = item.text.strip().lower()
                href = item["href"]
                if any(keyword in text for keyword in ["document", "legal", "protocol", "book", "publication"]):
                    full_url = urljoin("https://www.isda.org", href)
                    if full_url not in potential_urls:
                        potential_urls.append(full_url)
                        self.logger.info(f"Found potential documentation link in nav: {text} -> {full_url}")
        except Exception as e:
            self.logger.error(f"Error checking main site: {e}")
            
        # Check each potential URL
        for url in potential_urls:
            self.logger.info(f"Checking potential documentation URL: {url}")
            try:
                response = self.session.get(url)
                if response.status_code == 404:
                    self.logger.info(f"URL not found: {url}")
                    continue
                    
                # Save HTML for debugging
                url_filename = url.split("/")[-2] if url.endswith("/") else url.split("/")[-1]
                if not url_filename:
                    url_filename = "index"
                html_path = self.isda_dir / f"isda_{url_filename}.html"
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(response.text)
                    
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Extract document information
                doc_info = {
                    "url": url,
                    "title": soup.title.text if soup.title else url,
                    "type": self._determine_document_type(url, soup),
                    "date": self._extract_date(soup),
                    "pdf_links": [],
                    "document_sections": [],
                    "keywords": self._extract_keywords(soup),
                    "source": "direct"
                }
                
                # Find PDF links
                pdf_links = soup.find_all("a", href=lambda h: h and h.lower().endswith(".pdf"))
                if pdf_links:
                    doc_info["pdf_links_count"] = len(pdf_links)
                    for link in pdf_links:
                        pdf_url = urljoin(url, link["href"])
                        pdf_info = {
                            "url": pdf_url,
                            "title": link.text.strip() or os.path.basename(pdf_url),
                            "context": self._get_link_context(link),
                            "date": self._extract_date_from_link(link)
                        }
                        doc_info["pdf_links"].append(pdf_info)
                
                # Find document sections
                doc_sections = soup.find_all(class_=lambda c: c and "document" in str(c).lower())
                if doc_sections:
                    doc_info["document_sections_count"] = len(doc_sections)
                    for section in doc_sections:
                        section_info = {
                            "title": section.find("h2", "h3", "h4").text.strip() if section.find("h2", "h3", "h4") else "Untitled Section",
                            "content": section.text.strip()[:200] + "..." if len(section.text.strip()) > 200 else section.text.strip(),
                            "links": [urljoin(url, a["href"]) for a in section.find_all("a", href=True)]
                        }
                        doc_info["document_sections"].append(section_info)
                
                documentation_pages.append(doc_info)
                
            except Exception as e:
                self.logger.error(f"Error checking {url}: {e}")
                
        # Check search results
        try:
            search_url = "https://www.isda.org/?s=documentation+protocol"
            self.logger.info(f"Checking search page: {search_url}")
            search_response = self.session.get(search_url)
            search_soup = BeautifulSoup(search_response.text, "html.parser")
            
            # Save search results for debugging
            search_path = self.isda_dir / "isda_search_results.html"
            with open(search_path, "w", encoding="utf-8") as f:
                f.write(search_response.text)
                
            search_results = search_soup.find_all("article")
            for result in search_results[:10]:
                links = result.find_all("a", href=True)
                for link in links:
                    href = link["href"]
                    if "/document/" in href or "/protocol/" in href or "/bookstore/" in href:
                        full_url = href if href.startswith("http") else urljoin("https://www.isda.org", href)
                        doc_info = {
                            "url": full_url,
                            "title": link.text.strip(),
                            "type": self._determine_document_type(full_url, result),
                            "date": self._extract_date(result),
                            "keywords": self._extract_keywords(result),
                            "source": "search",
                            "context": self._get_link_context(link)
                        }
                        documentation_pages.append(doc_info)
                        self.logger.info(f"Found potential documentation link in search: {link.text.strip()} -> {href}")
        except Exception as e:
            self.logger.error(f"Error checking search page: {e}")
            
        # Save documentation pages list with enhanced structure
        results_path = self.isda_dir / "isda_documentation_sources.json"
        with open(results_path, "w") as f:
            json.dump({
                "metadata": {
                    "generated_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_sources": len(documentation_pages),
                    "source_types": list(set(doc["type"] for doc in documentation_pages)),
                    "document_types": {
                        "protocols": len([doc for doc in documentation_pages if doc["type"] == "protocol"]),
                        "books": len([doc for doc in documentation_pages if doc["type"] == "book"]),
                        "legal_docs": len([doc for doc in documentation_pages if doc["type"] == "legal"]),
                        "other": len([doc for doc in documentation_pages if doc["type"] == "other"])
                    }
                },
                "sources": documentation_pages
            }, f, indent=2)
            
        self.logger.info(f"Found {len(documentation_pages)} potential documentation pages, saved to {results_path}")
        return documentation_pages

    def _determine_document_type(self, url, soup):
        """Determine the type of document based on URL and content."""
        url_lower = url.lower()
        if "protocol" in url_lower:
            return "protocol"
        elif "book" in url_lower:
            return "book"
        elif "legal" in url_lower or "documentation" in url_lower:
            return "legal"
        else:
            return "other"

    def _extract_date(self, element):
        """Extract date from element content."""
        # Look for common date patterns
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'\d{4}'
        ]
        
        text = element.text
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    def _extract_date_from_link(self, link):
        """Extract date from link text or context."""
        # Check link text
        date = self._extract_date(link)
        if date:
            return date
        
        # Check parent element
        if link.parent:
            date = self._extract_date(link.parent)
            if date:
                return date
            
        return None

    def _get_link_context(self, link):
        """Get the context around a link."""
        context = []
        
        # Get parent paragraph or div
        parent = link.parent
        if parent:
            context.append(parent.text.strip())
        
        # Get sibling elements
        if parent and parent.parent:
            for sibling in parent.parent.find_all(["p", "div", "li"]):
                if sibling != parent:
                    context.append(sibling.text.strip())
                
        return " ".join(context)

    def _extract_keywords(self, element):
        """Extract relevant keywords from element content."""
        text = element.text.lower()
        keywords = set()
        
        # Common ISDA-related terms
        isda_terms = [
            "protocol", "agreement", "documentation", "legal", "derivatives",
            "swap", "credit", "default", "master", "supplement", "definitions"
        ]
        
        for term in isda_terms:
            if term in text:
                keywords.add(term)
            
        return list(keywords)

    def collect(self, max_sources=5, keywords=None):
        """Collect ISDA documentation."""
        # First find documentation pages if not provided
        if not self.sources:
            self.sources = self.find_isda_documentation()
            
        self.logger.info(f"Collecting ISDA documentation from {len(self.sources)} sources")
        documents = []
        
        for i, source in enumerate(self.sources[:max_sources]):
            url = source.get("url")
            if not url:
                continue
                
            self.logger.info(f"Processing source {i+1}/{min(max_sources, len(self.sources))}: {url}")
            try:
                response = self.session.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                pdf_links = []
                
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if href.lower().endswith(".pdf"):
                        full_url = urljoin(url, href)
                        text = a.text.strip()
                        if not text:
                            if a.parent:
                                text = a.parent.text.strip()
                        if not text:
                            text = os.path.basename(href)
                            
                        # Keyword filtering
                        include_pdf = True
                        if keywords:
                            context = (text or "")
                            if a.parent and a.parent != a:
                                context += " " + a.parent.text.strip()
                            context = context.lower()
                            if not any(kw.lower() in context for kw in keywords):
                                include_pdf = False
                                
                        if keywords and not include_pdf:
                            self.logger.info(f"Skipping PDF (no keyword match): {text} [{full_url}]")
                            continue
                        elif keywords:
                            self.logger.info(f"Including PDF (keyword match): {text} [{full_url}]")
                            
                        pdf_links.append({
                            "url": full_url,
                            "text": text
                        })
                        
                self.logger.info(f"Found {len(pdf_links)} PDF links on {url}")
                
                for pdf in pdf_links:
                    pdf_url = pdf["url"]
                    text = pdf["text"]
                    safe_text = re.sub(r'[^\w\s-]', '', text).strip().lower()
                    filename = re.sub(r'[-\s]+', '-', safe_text)
                    if len(filename) > 50:
                        filename = filename[:50]
                    if not filename.endswith(".pdf"):
                        filename += ".pdf"
                        
                    output_path = self._get_output_path(filename, 'reports')
                    self.logger.info(f"Downloading PDF: {pdf_url} -> {output_path}")
                    
                    try:
                        pdf_response = self.session.get(pdf_url, stream=True)
                        pdf_response.raise_for_status()
                        with open(output_path, "wb") as f:
                            for chunk in pdf_response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    
                        # Verify downloaded file
                        if not self._check_file_validity(output_path):
                            self.logger.error(f"Downloaded file failed validation: {output_path}")
                            os.remove(output_path)
                            continue
                                    
                        # Save metadata
                        meta_path = output_path.with_suffix(output_path.suffix + ".meta")
                        meta_data = {
                            "title": text,
                            "url": pdf_url,
                            "source_url": url,
                            "download_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "keywords": keywords if keywords else []
                        }
                        with open(meta_path, "w", encoding="utf-8") as f:
                            json.dump(meta_data, f, indent=2)
                            
                        documents.append({
                            "title": text,
                            "url": pdf_url,
                            "filepath": str(output_path),
                            "metadata_path": str(meta_path)
                        })
                        
                    except Exception as e:
                        self.logger.error(f"Error downloading PDF {pdf_url}: {e}")
                        continue
                        
            except Exception as e:
                self.logger.error(f"Error processing source {url}: {e}")
                continue
                
        return documents

    def collect_by_id(self, document_ids):
        """Collect specific ISDA documents by ID."""
        if not isinstance(document_ids, list):
            document_ids = [document_ids]
            
        documents = []
        for doc_id in document_ids:
            # Updated URL patterns for ISDA's actual document structure
            url_patterns = [
                f"https://www.isda.org/a/{doc_id}/",  # ISDA's actual URL pattern
                f"https://www.isda.org/document/{doc_id}/",
                f"https://www.isda.org/documents/{doc_id}/",
                f"https://www.isda.org/protocols/{doc_id}/"
            ]
            
            for url in url_patterns:
                try:
                    self.logger.info(f"Trying URL pattern: {url}")
                    response = self.session.get(url)
                    if response.status_code == 404:
                        self.logger.info(f"URL not found: {url}")
                        continue
                        
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # Save HTML for debugging
                    debug_path = self.isda_dir / f"debug_{doc_id}.html"
                    with open(debug_path, "w", encoding="utf-8") as f:
                        f.write(response.text)
                    
                    # Look for PDF links in multiple ways
                    pdf_links = []
                    
                    # Method 1: Direct PDF links in content
                    for a in soup.find_all("a", href=True):
                        href = a["href"]
                        if href.lower().endswith(".pdf"):
                            full_url = urljoin(url, href)
                            pdf_links.append(full_url)
                            self.logger.info(f"Found direct PDF link: {full_url}")
                    
                    # Method 2: Look for download buttons/sections
                    download_elements = soup.find_all(class_=lambda c: c and any(x in str(c).lower() for x in ["download", "document", "pdf", "button"]))
                    for element in download_elements:
                        for a in element.find_all("a", href=True):
                            href = a["href"]
                            if href.lower().endswith(".pdf"):
                                full_url = urljoin(url, href)
                                if full_url not in pdf_links:
                                    pdf_links.append(full_url)
                                    self.logger.info(f"Found PDF link in download section: {full_url}")
                    
                    # Method 3: Look for document sections
                    doc_sections = soup.find_all(class_=lambda c: c and any(x in str(c).lower() for x in ["document", "content", "article"]))
                    for section in doc_sections:
                        for a in section.find_all("a", href=True):
                            href = a["href"]
                            if href.lower().endswith(".pdf"):
                                full_url = urljoin(url, href)
                                if full_url not in pdf_links:
                                    pdf_links.append(full_url)
                                    self.logger.info(f"Found PDF link in document section: {full_url}")
                    
                    self.logger.info(f"Found {len(pdf_links)} PDF links for {doc_id}")
                    
                    for pdf_url in pdf_links:
                        try:
                            # Download and validate PDF
                            filename = f"{doc_id}_{os.path.basename(pdf_url)}"
                            output_path = self._get_output_path(filename)
                            
                            self.logger.info(f"Downloading PDF: {pdf_url} -> {output_path}")
                            pdf_response = self.session.get(pdf_url, stream=True)
                            pdf_response.raise_for_status()
                            
                            # Check content type
                            content_type = pdf_response.headers.get('content-type', '').lower()
                            if 'application/pdf' not in content_type and not pdf_url.lower().endswith('.pdf'):
                                self.logger.warning(f"Skipping non-PDF content: {content_type}")
                                continue
                            
                            with open(output_path, "wb") as f:
                                for chunk in pdf_response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                                    
                            if self._check_file_validity(output_path):
                                # Save metadata
                                meta_path = output_path.with_suffix('.meta')
                                meta_data = {
                                    "document_id": doc_id,
                                    "title": os.path.basename(pdf_url),
                                    "url": pdf_url,
                                    "download_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "domain": "regulation_compliance"
                                }
                                with open(meta_path, "w", encoding="utf-8") as f:
                                    json.dump(meta_data, f, indent=2)
                                    
                                documents.append({
                                    "document_id": doc_id,
                                    "title": os.path.basename(pdf_url),
                                    "filepath": str(output_path),
                                    "metadata_path": str(meta_path),
                                    "domain": "regulation_compliance"
                                })
                                self.logger.info(f"Successfully downloaded and validated: {filename}")
                                break  # Successfully found and downloaded document
                            else:
                                self.logger.error(f"Downloaded file failed validation: {output_path}")
                                os.remove(output_path)
                                
                        except Exception as e:
                            self.logger.error(f"Error downloading PDF {pdf_url}: {e}")
                            continue
                        
                except Exception as e:
                    self.logger.error(f"Error processing document {doc_id} at {url}: {e}")
                    continue
                    
        return documents

    def _check_file_validity(self, filepath):
        """Check if a downloaded file is valid."""
        try:
            path = Path(filepath)
            if not path.exists():
                return False
                
            # Check file size
            file_size = path.stat().st_size
            if file_size < 1000 or file_size > 1000000:  # Between 1KB and 1MB
                return False
                
            # Check if it's a valid PDF
            if path.suffix.lower() == '.pdf':
                with open(path, 'rb') as f:
                    header = f.read(5)
                    if not header.startswith(b'%PDF-'):
                        return False
                        
            return True
        except Exception as e:
            self.logger.error(f"Error validating file {filepath}: {str(e)}")
            return False

def run_isda_collector(args, source_config, base_dir):
    """Legacy entry point for backward compatibility."""
    try:
        # Find ISDA documentation pages
        documentation_pages = find_isda_documentation(base_dir)
        
        # Initialize collector
        collector = ISDADocumentationCollector(base_dir, documentation_pages)
        
        # Collect documents
        results = collector.collect(
            max_sources=getattr(args, 'isda_max_sources', 5),
            keywords=getattr(args, 'isda_keywords', None)
        )
        
        return results
        
    except Exception as e:
        logging.error(f"Error in ISDA collector: {e}")
        return []

def find_isda_documentation(base_dir):
    """Find ISDA documentation pages."""
    potential_urls = [
        "https://www.isda.org/books/",
        "https://www.isda.org/documentation/",
        "https://www.isda.org/documents/",
        "https://www.isda.org/protocols/",
        "https://www.isda.org/guides/",
        "https://www.isda.org/bookstore/",
        "https://www.isda.org/books-and-protocols/",
        "https://www.isda.org/book-and-protocol-list/",
        "https://www.isda.org/legal-documentation/"
    ]
    
    logger = logging.getLogger("ISDADocFinder")
    logger.info("Checking ISDA main site navigation for documentation links")
    
    try:
        main_response = requests.get("https://www.isda.org", headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        main_response.raise_for_status()
        main_soup = BeautifulSoup(main_response.text, "html.parser")
        nav_items = main_soup.find_all("a", href=True)
        
        for item in nav_items:
            text = item.text.strip().lower()
            href = item["href"]
            if any(keyword in text for keyword in ["document", "legal", "protocol", "book", "publication"]):
                full_url = urljoin("https://www.isda.org", href)
                if full_url not in potential_urls:
                    potential_urls.append(full_url)
                    logger.info(f"Found potential documentation link in nav: {text} -> {full_url}")
                    
    except Exception as e:
        logger.error(f"Error checking main site: {e}")
        
    documentation_pages = []
    output_dir = Path(base_dir)
    
    for url in potential_urls:
        logger.info(f"Checking potential documentation URL: {url}")
        try:
            response = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            if response.status_code == 404:
                logger.info(f"URL not found: {url}")
                continue
                
            url_filename = url.split("/")[-2] if url.endswith("/") else url.split("/")[-1]
            if not url_filename:
                url_filename = "index"
                
            html_path = output_dir / f"isda_{url_filename}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(response.text)
                
            soup = BeautifulSoup(response.text, "html.parser")
            pdf_links = soup.find_all("a", href=lambda h: h and h.lower().endswith(".pdf"))
            
            if pdf_links:
                logger.info(f"Found {len(pdf_links)} PDF links on {url}")
                documentation_pages.append({
                    "url": url,
                    "pdf_links_count": len(pdf_links),
                    "title": soup.title.text if soup.title else url
                })
            else:
                doc_sections = soup.find_all(class_=lambda c: c and "document" in str(c).lower())
                if doc_sections:
                    logger.info(f"Found {len(doc_sections)} document sections on {url}")
                    documentation_pages.append({
                        "url": url,
                        "document_sections_count": len(doc_sections),
                        "title": soup.title.text if soup.title else url
                    })
                    
        except Exception as e:
            logger.error(f"Error checking {url}: {e}")
            
    try:
        search_url = "https://www.isda.org/?s=documentation+protocol"
        logger.info(f"Checking search page: {search_url}")
        search_response = requests.get(search_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        search_soup = BeautifulSoup(search_response.text, "html.parser")
        search_path = output_dir / "isda_search_results.html"
        
        with open(search_path, "w", encoding="utf-8") as f:
            f.write(search_response.text)
            
        search_results = search_soup.find_all("article")
        for result in search_results[:10]:
            links = result.find_all("a", href=True)
            for link in links:
                href = link["href"]
                if "/document/" in href or "/protocol/" in href or "/bookstore/" in href:
                    documentation_pages.append({
                        "url": href if href.startswith("http") else urljoin("https://www.isda.org", href),
                        "source": "search",
                        "title": link.text.strip()
                    })
                    logger.info(f"Found potential documentation link in search: {link.text.strip()} -> {href}")
                    
    except Exception as e:
        logger.error(f"Error checking search page: {e}")
        
    results_path = output_dir / "isda_documentation_sources.json"
    with open(results_path, "w") as f:
        json.dump(documentation_pages, f, indent=2)
        
    logger.info(f"Found {len(documentation_pages)} potential documentation pages, saved to {results_path}")
    return documentation_pages

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Collect ISDA documentation")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--isda-keywords", nargs="*", help="Keywords to filter documents")
    parser.add_argument("--isda-max-sources", type=int, default=5, help="Maximum number of sources to process")
    args = parser.parse_args()
    
    results = run_isda_collector(args, None, args.output_dir)
    print(f"\nCollected {len(results)} documents") 