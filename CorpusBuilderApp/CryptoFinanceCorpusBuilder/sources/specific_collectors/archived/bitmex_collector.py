# sources/specific_collectors/bitmex_collector.py
from CryptoFinanceCorpusBuilder.sources.web_collector import WebCollector
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import json
import time
from pathlib import Path
import logging

class BitMEXResearchCollector(WebCollector):
    """Collector for BitMEX Research blog posts (robust to structure changes, robots.txt is always bypassed)"""
    
    def __init__(self, output_dir, delay_range=(3, 7)):
        super().__init__(output_dir, base_url='https://blog.bitmex.com/research/', delay_range=delay_range)
        self.respect_robots_txt = False
        self.logger = logging.getLogger('BitMEXResearchCollector')
        self.logger.warning("⚠️ BitMEXResearchCollector always bypasses robots.txt! ⚠️")
        self.logger.warning("⚠️ FOR PRODUCTION, REVIEW ETHICAL AND LEGAL CONSIDERATIONS ⚠️")
        self.session = self._get_session()

    def _get_session(self):
        import requests
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        })
        return session

    def _can_fetch(self, url):
        self.logger.warning("Bypassing robots.txt check for BitMEXResearchCollector (always returns True)")
        return True

    def collect(self, max_pages=1):
        """Collect research blog posts from BitMEX with updated HTML parsing"""
        self.logger.info(f"Collecting BitMEX Research blog posts (max {max_pages} pages)")
        all_posts = []
        # Fetch the main research page
        self.logger.info(f"Fetching page: {self.base_url}")
        response = self.session.get(self.base_url, timeout=30)
        if response.status_code != 200:
            self.logger.error(f"Failed to fetch page: {response.status_code}")
            return all_posts
        # Save the raw HTML for inspection if needed
        raw_html_path = Path(self.output_dir) / "bitmex_research.html"
        with open(raw_html_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Try to find post containers by class name patterns
        post_containers = soup.find_all("div", class_=lambda c: c and ('post' in c.lower() or 'entry' in c.lower() or 'article' in c.lower()))
        self.logger.info(f"Found {len(post_containers)} potential post containers")
        posts_found = 0
        for container in post_containers[:10]:  # Limit to first 10 for safety
            heading = container.find(['h1', 'h2', 'h3', 'h4'])
            if not heading:
                continue
            posts_found += 1
            title = heading.text.strip()
            link = None
            if heading.find('a'):
                link = heading.find('a')['href']
                if link and not link.startswith(('http://', 'https://')):
                    link = urljoin(self.base_url, link)
            date = None
            date_elem = container.find(class_=lambda c: c and ('date' in c.lower() or 'time' in c.lower()))
            if date_elem:
                date = date_elem.text.strip()
            content_preview = None
            content_elem = container.find(['p', 'div'], class_=lambda c: c and ('content' in c.lower() or 'excerpt' in c.lower() or 'summary' in c.lower()))
            if content_elem:
                content_preview = content_elem.text.strip()
            post = {
                'title': title,
                'url': link,
                'date': date,
                'excerpt': content_preview,
                'container_classes': container.get('class', [])
            }
            all_posts.append(post)
            self.logger.info(f"Found post: {title}")
        # Fallback: look for headings if no posts found
        if not all_posts:
            self.logger.info("No posts found with container approach, trying fallback method")
            headings = soup.find_all(['h1', 'h2', 'h3'])
            for heading in headings[:10]:
                parent_classes = ' '.join(parent.get('class', []) for parent in heading.parents if parent.get('class'))
                if any(x in parent_classes.lower() for x in ['nav', 'sidebar', 'menu', 'footer', 'header']):
                    continue
                title = heading.text.strip()
                link = None
                if heading.find('a'):
                    link = heading.find('a')['href']
                    if link and not link.startswith(('http://', 'https://')):
                        link = urljoin(self.base_url, link)
                elif heading.parent and heading.parent.name == 'a':
                    link = heading.parent['href']
                    if link and not link.startswith(('http://', 'https://')):
                        link = urljoin(self.base_url, link)
                post = {
                    'title': title,
                    'url': link,
                    'source': 'fallback_method'
                }
                all_posts.append(post)
                self.logger.info(f"Found post (fallback): {title}")
        self._save_metadata(all_posts)
        processed_posts = self._process_posts(all_posts)
        return processed_posts
    
    def _process_posts(self, posts):
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
                content_elem = soup.find(['div', 'article'], class_=lambda c: c and ('content' in c.lower() or 'entry' in c.lower() or 'article' in c.lower()))
                if content_elem:
                    post['content_text'] = content_elem.get_text('\n', strip=True)
                    post['content_html'] = str(content_elem)
                    pdf_links = []
                    for link in content_elem.find_all('a', href=True):
                        href = link['href']
                        if href.lower().endswith('.pdf'):
                            full_url = urljoin(url, href)
                            pdf_links.append(full_url)
                    downloaded_pdfs = []
                    for i, pdf_url in enumerate(pdf_links):
                        title = post.get('title', 'unknown')
                        safe_title = re.sub(r'[^\w\s-]', '', title).strip().lower()
                        safe_title = re.sub(r'[-\s]+', '-', safe_title)
                        filename = f"{safe_title}-{i+1}.pdf"
                        filepath = self._download_file(pdf_url, filename)
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

    def _download_file(self, url, filename):
        filepath = Path(self.output_dir) / filename
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
        html_path = Path(self.output_dir) / f"{safe_title}.html"
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
        metadata_path = Path(self.output_dir) / "bitmex_research_posts.json"
        try:
            with open(metadata_path, 'w') as f:
                json.dump(posts, f, indent=2)
            self.logger.info(f"Saved metadata for {len(posts)} posts to {metadata_path}")
        except Exception as e:
            self.logger.error(f"Error saving metadata: {e}")