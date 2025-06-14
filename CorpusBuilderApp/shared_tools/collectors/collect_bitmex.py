import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import json
import shutil
import logging
from pathlib import Path
from .base_collector import BaseCollector
from shared_tools.utils.domain_utils import get_domain_for_file
from typing import Union
logger = logging.getLogger(__name__)

class UpdatedBitMEXCollector(BaseCollector):
    def __init__(self, config: Union[str, 'ProjectConfig'], delay_range: tuple = (2, 5)):
        """Initialize the BitMEX collector.
        
        Args:
            config: ProjectConfig instance or path to config file
            delay_range: Tuple of (min_delay, max_delay) in seconds between requests
        """
        super().__init__(config, delay_range=delay_range)
        self.base_url = 'https://blog.bitmex.com'
        
        # Use the raw_data_dir determined by BaseCollector (from the supplied config)
        # This makes the collector test-friendly because the tests can pass in a
        # lightweight DummyConfig with a temporary/raw output directory.
        self.bitmex_dir = self.raw_data_dir

        # Ensure the directory exists (e.g., when a brand-new temporary path is supplied)
        self.bitmex_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"BitMEXCollector initialized with output directory: {self.bitmex_dir}")
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        })
        self.titles_cache = set()  # Will be set externally if needed
        self._normalize_title = lambda title: re.sub(r'[^\w\s]', '', str(title).lower()).strip()

    def _get_output_path(self, filename, content_type='articles'):
        """Get the correct output path for BitMEX content."""
        # BitMEX content is primarily about crypto derivatives and market microstructure
        domain = 'crypto_derivatives'  # Default domain for BitMEX content
        path = super()._get_output_path(domain, content_type, filename)
        # Ensure the directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _download_file(self, url, filename, subfolder: str | None = None):
        """Download a file into self.bitmex_dir or an optional subfolder."""
        if subfolder is None:
            # Skip categorisation only if caller did not specify; default to root dir
            target_dir = self.bitmex_dir
        else:
            target_dir = self.bitmex_dir / subfolder
            target_dir.mkdir(parents=True, exist_ok=True)

        filepath = target_dir / filename
        try:
            self.logger.info(f"Downloading {url} to {filepath}")
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            self.logger.info(f"Successfully downloaded to {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Error downloading {url}: {e}")
            return None

    def _save_post_html(self, post):
        if 'content_html' not in post or not post['content_html']:
            return None
        title = post.get('title', 'unknown')
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().lower()
        safe_title = re.sub(r'[-\s]+', '-', safe_title)
        # Route into category subfolder if available
        category = post.get('category')
        if category is None:
            # Default to root directory if category unexpectedly missing
            target_dir = self.bitmex_dir
        else:
            target_dir = self.bitmex_dir / category
            target_dir.mkdir(parents=True, exist_ok=True)
        target_dir.mkdir(parents=True, exist_ok=True)
        html_path = target_dir / f"{safe_title}.html"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{post.get('title', 'BitMEX Research Post')}</title>
            <meta charset=\"utf-8\">
            <meta name=\"date\" content=\"{post.get('date', '')}\">
        </head>
        <body>
            <h1>{post.get('title', '')}</h1>
            <p class=\"date\">{post.get('date', '')}</p>
            <div class=\"content\">
                {post.get('content_html', '')}
            </div>
            <div class=\"metadata\">
                <p>Source: <a href=\"{post.get('url', '')}\">{post.get('url', '')}</a></p>
            </div>
        </body>
        </html>
        """
        try:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"Saved HTML to {html_path}")
            return html_path
        except Exception as e:
            self.logger.error(f"Error saving HTML: {e}")
            return None

    def _save_metadata(self, posts):
        metadata_path = self.bitmex_dir / "bitmex_research_posts.json"
        try:
            with open(metadata_path, 'w') as f:
                json.dump(posts, f, indent=2)
            self.logger.info(f"Saved metadata for {len(posts)} posts to {metadata_path}")
        except Exception as e:
            self.logger.error(f"Error saving metadata: {e}")

    def collect(self, max_pages=1, categories=None, keywords=None):
        """Collect posts.

        Args:
            max_pages (int|None): pages per start URL to crawl (None = until 404).
            categories (list[str]|None): list of category slugs (e.g. 'research') **or** full URLs.
                When omitted the collector behaves like before, starting from the homepage.
            keywords (list[str]|None): optional keyword filter inside articles.
        """

        cat_info = f"categories={categories}" if categories else "front-page only"
        self.logger.info(
            f"Collecting BitMEX blog posts ({cat_info}; max_pages={max_pages if max_pages else 'ALL'})"
        )

        all_posts = []
        seen_titles = set()  # normalize_title values to skip duplicates in same run

        try:
            # Determine starting URLs (homepage or category pages)
            if categories:
                start_urls = []
                for cat in categories:
                    if cat.startswith("http://") or cat.startswith("https://"):
                        start_urls.append(cat.rstrip("/"))
                    else:
                        start_urls.append(f"{self.base_url}/category/{cat.strip('/')}/")
            else:
                start_urls = [self.base_url]

            for base in start_urls:
                page_num = 1
                while True:
                    page_url = (
                        base if page_num == 1 else f"{base.rstrip('/')}/page/{page_num}/"
                    )
                    self.logger.info(f"Fetching page: {page_url}")
                    response = self.session.get(page_url, timeout=30)
                    if response.status_code != 200:
                        # Non-200 typically means we ran past the archive depth – stop crawling
                        self.logger.info(f"Stopping pagination at page {page_num}: HTTP {response.status_code}")
                        break

                    # persist raw html for debugging (one file per page)
                    raw_html_path = self.bitmex_dir / f"bitmex_research_page_{page_num}.html"
                    with open(raw_html_path, 'w', encoding='utf-8') as f:
                        f.write(response.text)

                    soup = BeautifulSoup(response.text, 'html.parser')

                    # 1) Grab links in the archive tables (Complete Works / Full Catalogue)
                    anchors = soup.select('table a[href]')

                    # 2) Also grab the large card-style tiles near the top (entry-title)
                    anchors += soup.select('h2.entry-title a[href]')

                    self.logger.info(f"Found {len(anchors)} candidate article links on page {page_num}")

                    for a_tag in anchors:
                        title = a_tag.get_text(strip=True)
                        norm_title = self._normalize_title(title)
                        if norm_title in seen_titles:
                            continue
                        seen_titles.add(norm_title)

                        link = a_tag['href']
                        if link and not link.startswith(('http://', 'https://')):
                            link = urljoin(self.base_url, link)

                        post = {
                            'title': title,
                            'url': link,
                            'category': ('research' if 'research' in base else 'crypto_trader_digest')
                        }
                        all_posts.append(post)
                        self.logger.debug(f"Queued article: {title}")

                    if not anchors:
                        # Nothing found on this page – stop crawling further pages for this category
                        break

                    # Move to next page or stop if max_pages reached
                    if max_pages and page_num >= max_pages:
                        self.logger.info(
                            f"Reached max_pages limit ({max_pages}) for base {base}. Stopping crawl."
                        )
                        break
                    page_num += 1

            # Additional deduplication against external titles cache
            if self.titles_cache:
                before_count = len(all_posts)
                all_posts = [
                    p
                    for p in all_posts
                    if self._normalize_title(p.get("title", "")) not in self.titles_cache
                ]
                skipped = before_count - len(all_posts)
                logger.info(
                    f"Deduplication: Skipped {skipped} results already in the existing titles cache."
                )

            self._save_metadata(all_posts)
            processed_posts = self._process_posts(all_posts, keywords=keywords)
            return processed_posts

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching BitMEX research page: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error in BitMEX collector: {e}")
            return []

    def _process_posts(self, posts, keywords=None):
        processed_posts = []
        for post in posts:
            url = post.get('url')
            if not url:
                continue
            try:
                self.logger.info(f"Fetching post: {url}")
                response = self.session.get(url, timeout=30)
                if response.status_code != 200:
                    self.logger.warning(f"Failed to fetch post: {response.status_code}")
                    continue
                soup = BeautifulSoup(response.text, 'html.parser')
                # robust content selector
                content_elem = (
                    soup.select_one('article.post div.post-content') or
                    soup.select_one('article.post') or
                    soup.select_one('div.post-content') or
                    soup.find('article')
                )
                if content_elem:
                    post['content_text'] = content_elem.get_text('\n', strip=True)
                    post['content_html'] = str(content_elem)
                    # Keyword search in content
                    if keywords:
                        found_keywords = [kw for kw in keywords if kw.lower() in post['content_text'].lower()]
                        if not found_keywords:
                            self.logger.info(f"Skipping post '{post.get('title','')}' ({url}) - no keywords found.")
                            continue
                        else:
                            logger.info(f"Keywords found in post '{post.get('title','')}' ({url}): {found_keywords}")
                    pdf_links = []
                    for link in content_elem.find_all('a', href=True):
                        href = link['href']
                        if href.lower().endswith('.pdf'):
                            full_url = urljoin(url, href)
                            pdf_links.append(full_url)
                    downloaded_pdfs = []
                    category = post.get('category')
                    if category is None:
                        # Default to root directory if category unexpectedly missing
                        target_dir = self.bitmex_dir
                    else:
                        target_dir = self.bitmex_dir / category
                        target_dir.mkdir(parents=True, exist_ok=True)
                    for i, pdf_url in enumerate(pdf_links):
                        title = post.get('title', 'unknown')
                        safe_title = re.sub(r'[^\w\s-]', '', title).strip().lower()
                        safe_title = re.sub(r'[-\s]+', '-', safe_title)
                        filename = f"{safe_title}-{i+1}.pdf"
                        filepath = self._download_file(pdf_url, filename, subfolder=category)
                        if filepath:
                            downloaded_pdfs.append({
                                'url': pdf_url,
                                'filepath': str(filepath),
                                'filename': filename
                            })
                    post['pdfs'] = downloaded_pdfs
                    html_path = self._save_post_html(post)
                    if html_path:
                        post['saved_html_path'] = str(html_path)
                processed_posts.append(post)
            except Exception as e:
                self.logger.error(f"Error processing post {url}: {e}")
                continue
        self._save_metadata(processed_posts)
        return processed_posts

def run_bitmex_collector(args, source_config, base_dir):
    # Set up output directory (test-safe, clear if exists)
    source_dir = Path(base_dir) / 'bitmex_research'
    if getattr(args, 'bitmex_clear_output_dir', False):
        if source_dir.exists():
            shutil.rmtree(source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)
    bitmex_keywords = getattr(args, 'bitmex_keywords', None)
    if bitmex_keywords:
        logger.info(f"BitMEX keyword filter enabled: {bitmex_keywords}")
    # Deduplication: load existing titles cache
    titles_cache = set()
    existing_titles_path = getattr(args, 'existing_titles', None)
    if existing_titles_path and os.path.exists(existing_titles_path):
        def normalize_title(title):
            return re.sub(r'[^\w\s]', '', str(title).lower()).strip()
        with open(existing_titles_path, 'r', encoding='utf-8') as f:
            titles_cache = {normalize_title(line.strip()) for line in f}
    def normalize_title(title):
        return re.sub(r'[^\w\s]', '', str(title).lower()).strip()
    try:
        logger.info("\nStarting updated BitMEX collector test...")
        collector = UpdatedBitMEXCollector(source_dir)
        results = collector.collect(max_pages=getattr(args, 'bitmex_max_pages', 1), keywords=bitmex_keywords)
        logger.info(f"\n===== Updated BitMEXCollector Results =====")
        logger.info(f"Collected {len(results)} research posts")
        if results:
            show_count = min(3, len(results))
            for i, post in enumerate(results[:show_count]):
                logger.info(f"\nPost #{i+1}:")
                logger.info(f"  Title: {post.get('title')}")
                logger.info(f"  URL: {post.get('url')}")
                pdfs = post.get('pdfs', [])
                logger.info(f"  PDF Count: {len(pdfs)}")
                for j, pdf in enumerate(pdfs[:2]):
                    logger.info(f"    PDF #{j+1}: {pdf.get('filename')}")
                    filepath = pdf.get('filepath', '')
                    if filepath and os.path.exists(filepath):
                        size_kb = os.path.getsize(filepath) / 1024
                        logger.info(f"    Size: {size_kb:.2f} KB")
                        logger.info(f"    Exists: Yes")
                    else:
                        logger.info(f"    Exists: No")
                html_path = post.get('saved_html_path', '')
                if html_path and os.path.exists(html_path):
                    size_kb = os.path.getsize(html_path) / 1024
                    logger.info(f"  HTML saved: Yes ({size_kb:.2f} KB)")
                else:
                    logger.info(f"  HTML saved: No")
        logger.info("\n===== Test Directory Contents =====")
        for root, dirs, files in os.walk(source_dir):
            level = root.replace(str(source_dir), '').count(os.sep)
            indent = ' ' * 4 * level
            logger.info(f"{indent}{os.path.basename(root)}/")
            sub_indent = ' ' * 4 * (level + 1)
            for f in files[:5]:
                filepath = os.path.join(root, f)
                size_kb = os.path.getsize(filepath) / 1024
                logger.info(f"{sub_indent}{f} ({size_kb:.2f} KB)")
            if len(files) > 5:
                logger.info(f"{sub_indent}...and {len(files)-5} more files")
    except Exception as e:
        logger.warning(f"Error in BitMEX collector: {e}")
        import traceback
        traceback.print_exc()
    return None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Collect BitMEX Research blog posts and PDFs")
    parser.add_argument("--output-dir", default="test_outputs/bitmex/", help="Output directory for collected data")
    parser.add_argument("--bitmex-keywords", nargs="*", help="List of keywords to filter posts (optional)")
    parser.add_argument("--bitmex-max-pages", type=int, default=1, help="Max number of pages to fetch")
    parser.add_argument("--existing-titles", help="Path to file containing existing titles for deduplication")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    keywords = args.bitmex_keywords if args.bitmex_keywords else None
    collector = UpdatedBitMEXCollector(args.output_dir)
    results = collector.collect(max_pages=args.bitmex_max_pages, keywords=keywords)
    logger.info(f"\nCollected {len(results)} BitMEX research posts. Output dir: {args.output_dir}")
    if results:
        logger.info(f"First post: {results[0].get('title','N/A')}")

BitMEXCollector = UpdatedBitMEXCollector 
