import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
from pathlib import Path

def run_isda_collector(args, source_config, base_dir):
    # Set up output directory (test-safe, clear if exists)
    source_dir = Path(base_dir) / 'isda'
    if getattr(args, 'isda_clear_output_dir', False):
        if source_dir.exists():
            import shutil
            shutil.rmtree(source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)
    output_dir = source_dir
    # Set up logging
    isda_logger = logging.getLogger("ISDADocFinder")
    isda_logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    if not isda_logger.handlers:
        isda_logger.addHandler(handler)
    # Step 1: Find ISDA documentation pages
    def find_isda_documentation():
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
        isda_logger.info("Checking ISDA main site navigation for documentation links")
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
                        isda_logger.info(f"Found potential documentation link in nav: {text} -> {full_url}")
        except Exception as e:
            isda_logger.error(f"Error checking main site: {e}")
        documentation_pages = []
        for url in potential_urls:
            isda_logger.info(f"Checking potential documentation URL: {url}")
            try:
                response = requests.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                })
                if response.status_code == 404:
                    isda_logger.info(f"URL not found: {url}")
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
                    isda_logger.info(f"Found {len(pdf_links)} PDF links on {url}")
                    documentation_pages.append({
                        "url": url,
                        "pdf_links_count": len(pdf_links),
                        "title": soup.title.text if soup.title else url
                    })
                else:
                    doc_sections = soup.find_all(class_=lambda c: c and "document" in str(c).lower())
                    if doc_sections:
                        isda_logger.info(f"Found {len(doc_sections)} document sections on {url}")
                        documentation_pages.append({
                            "url": url,
                            "document_sections_count": len(doc_sections),
                            "title": soup.title.text if soup.title else url
                        })
            except Exception as e:
                isda_logger.error(f"Error checking {url}: {e}")
        try:
            search_url = "https://www.isda.org/?s=documentation+protocol"
            isda_logger.info(f"Checking search page: {search_url}")
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
                        isda_logger.info(f"Found potential documentation link in search: {link.text.strip()} -> {href}")
        except Exception as e:
            isda_logger.error(f"Error checking search page: {e}")
        results_path = output_dir / "isda_documentation_sources.json"
        with open(results_path, "w") as f:
            json.dump(documentation_pages, f, indent=2)
        isda_logger.info(f"Found {len(documentation_pages)} potential documentation pages, saved to {results_path}")
        return documentation_pages
    documentation_pages = find_isda_documentation()
    # Step 2: Download PDFs from documentation pages
    isda_keywords = getattr(args, 'isda_keywords', None)
    class ISDADocumentationCollector:
        def __init__(self, output_dir, sources=None):
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(exist_ok=True, parents=True)
            self.sources = sources or []
            self.logger = logging.getLogger("ISDADocCollector")
            self.logger.setLevel(logging.INFO)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
                self.logger.addHandler(handler)
        def collect(self, max_sources=5):
            self.logger.info(f"Collecting ISDA documentation from {len(self.sources)} sources")
            documents = []
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            for i, source in enumerate(self.sources[:max_sources]):
                url = source.get("url")
                if not url:
                    continue
                self.logger.info(f"Processing source {i+1}/{min(max_sources, len(self.sources))}: {url}")
                try:
                    response = session.get(url)
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
                            # ISDA keyword filtering
                            include_pdf = True
                            if isda_keywords:
                                context = (text or "")
                                # Also check nearby HTML (parent text)
                                if a.parent and a.parent != a:
                                    context += " " + a.parent.text.strip()
                                context = context.lower()
                                if not any(kw.lower() in context for kw in isda_keywords):
                                    include_pdf = False
                            if isda_keywords and not include_pdf:
                                print(f"Skipping PDF (no keyword match): {text} [{full_url}]")
                                continue
                            elif isda_keywords:
                                print(f"Including PDF (keyword match): {text} [{full_url}]")
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
                        output_path = self.output_dir / filename
                        self.logger.info(f"Downloading PDF: {pdf_url} -> {output_path}")
                        try:
                            pdf_response = session.get(pdf_url, stream=True)
                            pdf_response.raise_for_status()
                            with open(output_path, "wb") as f:
                                for chunk in pdf_response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                            self.logger.info(f"Successfully downloaded: {output_path}")
                            documents.append({
                                "title": text,
                                "url": pdf_url,
                                "source_url": url,
                                "local_path": str(output_path),
                                "file_size": os.path.getsize(output_path)
                            })
                        except Exception as e:
                            self.logger.error(f"Error downloading PDF {pdf_url}: {e}")
                    if i < len(self.sources) - 1:
                        time.sleep(3)
                except Exception as e:
                    self.logger.error(f"Error processing source {url}: {e}")
            metadata_path = self.output_dir / "isda_documents_metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(documents, f, indent=2)
            self.logger.info(f"Collected {len(documents)} documents, metadata saved to {metadata_path}")
            return documents
    collector = ISDADocumentationCollector(output_dir, documentation_pages)
    max_sources = getattr(args, 'isda_max_sources', 5)
    documents = collector.collect(max_sources=max_sources)
    print(f"Downloaded {len(documents)} ISDA documentation files")
    print("\n===== Test Directory Contents =====")
    for root, dirs, files in os.walk(output_dir):
        level = root.replace(str(output_dir), '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for f in files[:5]:
            filepath = os.path.join(root, f)
            size_kb = os.path.getsize(filepath) / 1024
            print(f"{sub_indent}{f} ({size_kb:.2f} KB)")
        if len(files) > 5:
            print(f"{sub_indent}... and {len(files)-5} more files")
    return None

if __name__ == "__main__":
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description="Collect ISDA documentation and PDFs")
    parser.add_argument("--output-dir", required=True, help="Output directory for collected data")
    parser.add_argument("--isda-keywords", nargs="*", help="List of keywords to filter PDFs (optional)")
    parser.add_argument("--isda-max-sources", type=int, default=5, help="Maximum number of documentation sources to process")
    parser.add_argument("--isda-clear-output-dir", action="store_true", help="Clear the output directory before collecting")
    args = parser.parse_args()
    base_dir = Path(args.output_dir).parent
    source_config = None
    print(f"[DEBUG] CLI args: {args}")
    run_isda_collector(args, source_config, base_dir)
    print(f"ISDA collection complete. Output dir: {args.output_dir}") 