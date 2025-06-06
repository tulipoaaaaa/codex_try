# sources/specific_collectors/arxiv_collector.py (API based)
import xml.etree.ElementTree as ET
import urllib.parse
import time
import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Union
from CryptoFinanceCorpusBuilder.shared_tools.collectors.api_collector import ApiCollector
import logging
import argparse
import requests
import json

def ascii_safe(s):
    """Make string safe for console output on any platform."""
    return str(s).encode('ascii', errors='replace').decode('ascii')

def normalize_title(title):
    # Identical to cache creation script
    return re.sub(r'[^\w\s]', '', str(title).lower()).strip()

class ArxivCollector(ApiCollector):
    """Collector for arXiv quantitative finance papers"""
    
    def __init__(self, 
                 config: Union[str, 'ProjectConfig'],
                 delay_range: tuple = (5, 10),
                 clear_output_dir: bool = False,
                 existing_titles: Optional[str] = None):
        """Initialize the arXiv collector.
        
        Args:
            config: ProjectConfig instance or path to config file
            delay_range: Tuple of (min_delay, max_delay) in seconds between requests
            clear_output_dir: Whether to clear the output directory before starting
            existing_titles: Path to file containing existing titles for deduplication
        """
        if isinstance(config, str):
            from shared_tools.project_config import ProjectConfig
            config = ProjectConfig(config, environment='test')
        
        super().__init__(config, api_base_url='http://export.arxiv.org/api/query', delay_range=delay_range)
        
        self.categories = ['q-fin.CP', 'q-fin.PM', 'q-fin.RM', 'q-fin.ST', 'q-fin.TR']
        self.rate_limits = {'export.arxiv.org': {'requests': 1, 'period': 3}}  # Max 1 request per 3 seconds
        self.logger.setLevel(logging.DEBUG)
        
        if clear_output_dir:
            import shutil
            if Path(self.output_dir).exists():
                shutil.rmtree(self.output_dir)
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            
        # Deduplication: load existing titles cache
        self.titles_cache = set()
        if existing_titles and os.path.exists(existing_titles):
            with open(existing_titles, 'r', encoding='utf-8') as f:
                self.titles_cache = {line.strip() for line in f}
        self.logger.info(f"Cache size: {len(self.titles_cache)}")
        self.logger.info(f"First 5 cache entries: {[ascii_safe(x) for x in list(self.titles_cache)[:5]]}")
        
        log_dir = Path(config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_dir / 'dedup_debug.log', 'a', encoding='utf-8') as dbg:
            dbg.write(f"Collector: arxiv, Cache entries: {list(self.titles_cache)[:5]}\n\n")
            
        self._normalize_title = lambda t: re.sub(r'[^\w\s]', '', str(t).lower()).strip()
        
        # Category to domain mapping
        self.category_domain_map = {
            'q-fin.CP': 'crypto_derivatives',  # Computational Finance
            'q-fin.PM': 'portfolio_construction',  # Portfolio Management
            'q-fin.RM': 'risk_management',  # Risk Management
            'q-fin.ST': 'market_microstructure',  # Statistical Finance
            'q-fin.TR': 'high_frequency_trading'  # Trading and Market Microstructure
        }
    
    def _get_output_path(self, filename, content_type='papers'):
        """Get the correct output path for arXiv content."""
        # Determine domain based on paper category
        domain = self._determine_domain()
        return super()._get_output_path(domain, content_type, filename)
    
    def _determine_domain(self, category=None):
        """Determine the domain for a paper based on its category."""
        if category is None:
            category = getattr(self, 'current_category', None)
        # Default to unknown if no category is set or category is not recognized
        if not category or category not in self.category_domain_map:
            return 'unknown'
        return self.category_domain_map.get(category, 'unknown')
    
    def collect(self, search_terms=None, max_results=100, start_index=0, clear_output_dir=False):
        """Collect papers from arXiv q-fin category"""
        if clear_output_dir:
            import shutil
            if Path(self.output_dir).exists():
                shutil.rmtree(self.output_dir)
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        if search_terms is None:
            search_terms = []
        all_results = []
        if not search_terms:
            for category in self.categories:
                self.current_category = category
                results = self._search_by_category(category, max_results, start_index)
                all_results.extend(results)
                time.sleep(5)
        else:
            for term in search_terms:
                results = self._search_by_term(term, max_results, start_index)
                all_results.extend(results)
                time.sleep(5)
        # Deduplication: filter out papers whose normalized title is in the cache
        if self.titles_cache:
            before_count = len(all_results)
            all_results = [p for p in all_results if self._should_skip(p.get('title', ''))]
            skipped = before_count - len(all_results)
            self.logger.info(f"Deduplication: Skipped {skipped} results already in the existing titles cache.")
        downloaded_papers = self._download_papers(all_results)
        # Detailed results analysis (match notebook)
        valid_papers = 0
        for i, paper in enumerate(downloaded_papers):
            self.logger.debug(f"\nPaper #{i+1}:")
            self.logger.debug(f"  Title: {paper.get('title')}")
            self.logger.debug(f"  Authors: {', '.join(paper.get('authors', []))}")
            self.logger.debug(f"  ArXiv ID: {paper.get('arxiv_id')}")
            self.logger.debug(f"  Category: {paper.get('primary_category')}")
            pdf_link = paper.get('pdf_link')
            self.logger.debug(f"  PDF Link: {pdf_link}")
            filepath = paper.get('filepath')
            if filepath and os.path.exists(filepath):
                size_kb = os.path.getsize(filepath) / 1024
                self.logger.debug(f"  File: {filepath}")
                self.logger.debug(f"  File size: {size_kb:.2f} KB")
                self.logger.debug(f"  File exists: Yes")
                valid_papers += 1
            else:
                self.logger.debug(f"  File: {filepath}")
                self.logger.debug(f"  File exists: No")
        self.logger.info(f"Summary: {valid_papers} out of {len(downloaded_papers)} papers have valid files")
        return downloaded_papers
    
    def _search_by_category(self, category, max_results=100, start_index=0):
        """Search arXiv by category"""
        query = f"cat:{category}"
        return self._execute_search(query, max_results, start_index)
    
    def _search_by_term(self, term, max_results=100, start_index=0):
        """Search arXiv by term"""
        # Limit to q-fin category and search term
        categories_query = " OR ".join([f"cat:{cat}" for cat in self.categories])
        query = f"({categories_query}) AND {term}"
        return self._execute_search(query, max_results, start_index)
    
    def _execute_search(self, query, max_results=100, start_index=0):
        """Execute an arXiv API search"""
        # URL encode the query
        encoded_query = urllib.parse.quote(query)
        
        # Build the API endpoint
        endpoint = f"?search_query={encoded_query}&start={start_index}&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        
        # Make the request
        response = self.api_request(endpoint, domain='export.arxiv.org')
        
        if not response:
            return []
        
        # Parse the XML response
        return self._parse_response(response)
    
    def _parse_response(self, response_text):
        """Parse arXiv API XML response"""
        try:
            root = ET.fromstring(response_text)
            
            # Extract entries
            results = []
            
            # Define namespaces
            ns = {'atom': 'http://www.w3.org/2005/Atom', 
                  'arxiv': 'http://arxiv.org/schemas/atom'}
            
            # Process each entry
            for entry in root.findall('.//atom:entry', ns):
                # Extract basic metadata
                title = entry.find('atom:title', ns).text.strip()
                authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
                published = entry.find('atom:published', ns).text
                summary = entry.find('atom:summary', ns).text.strip()
                
                # Extract arXiv specific metadata
                arxiv_id = entry.find('.//arxiv:id', ns)
                arxiv_id = arxiv_id.text if arxiv_id is not None else None
                
                primary_category = entry.find('.//arxiv:primary_category', ns)
                primary_category = primary_category.get('term') if primary_category is not None else None
                
                # Extract PDF link
                pdf_link = None
                for link in entry.findall('atom:link', ns):
                    if link.get('title') == 'pdf':
                        pdf_link = link.get('href')
                        break
                
                # Create clean record
                paper = {
                    'title': title,
                    'authors': authors,
                    'published': published,
                    'summary': summary,
                    'arxiv_id': arxiv_id,
                    'primary_category': primary_category,
                    'pdf_link': pdf_link,
                    'source': 'arxiv',
                    'domain': self._determine_domain(primary_category)  # Set domain based on category
                }
                
                results.append(paper)
                
            self.logger.info(f"Found {len(results)} papers")
            return results
            
        except Exception as e:
            self.logger.error(f"Error parsing arXiv response: {e}")
            return []
    
    def _download_papers(self, papers):
        """Download PDF files for papers"""
        downloaded = []
        
        for paper in papers:
            pdf_link = paper.get('pdf_link')
            if not pdf_link:
                continue
                
            # Create filename from ID
            arxiv_id = paper.get('arxiv_id', '')
            if arxiv_id:
                arxiv_id = re.sub(r'[^\w\.]', '_', arxiv_id)
                filename = f"{arxiv_id}.pdf"
            else:
                # Clean title for filename
                title = paper.get('title', 'unknown')
                filename = re.sub(r'[^\w\s-]', '', title).strip().lower()
                filename = re.sub(r'[-\s]+', '-', filename)
                filename = f"{filename}.pdf"
            
            # Set current category for domain determination
            self.current_category = paper.get('primary_category')
            
            # Get output path using domain-based structure
            output_path = self._get_output_path(filename, 'papers')
            
            # Download the PDF
            try:
                response = self.session.get(pdf_link, stream=True)
                response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Save metadata
                meta_path = output_path.with_suffix(output_path.suffix + ".meta")
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'title': paper.get('title'),
                        'authors': paper.get('authors'),
                        'published': paper.get('published'),
                        'summary': paper.get('summary'),
                        'arxiv_id': paper.get('arxiv_id'),
                        'primary_category': paper.get('primary_category'),
                        'pdf_link': pdf_link,
                        'source': 'arxiv',
                        'domain': self._determine_domain(),
                        'download_date': time.strftime('%Y-%m-%d %H:%M:%S')
                    }, f, indent=2)
                
                paper['filepath'] = str(output_path)
                paper['metadata_path'] = str(meta_path)
                downloaded.append(paper)
                
                self.logger.info(f"Downloaded: {output_path}")
                
            except Exception as e:
                self.logger.error(f"Error downloading {pdf_link}: {e}")
                continue
        
        return downloaded

    def _should_skip(self, title):
        """Check if a paper should be skipped based on title cache."""
        norm_title = normalize_title(title)
        self.logger.debug(f"Normalized title: {ascii_safe(norm_title)}")
        with open('dedup_debug.log', 'a', encoding='utf-8') as dbg:
            dbg.write(f"Collector: arxiv, Title: {norm_title}\n")
        return norm_title in self.titles_cache

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect papers from arXiv")
    parser.add_argument("--output-dir", required=True, help="Output directory for collected papers")
    parser.add_argument("--search-terms", nargs="*", help="List of search terms")
    parser.add_argument("--max-results", type=int, default=100, help="Maximum number of results per search")
    parser.add_argument("--existing-titles", type=str, help="Path to file with existing paper titles for deduplication")
    args = parser.parse_args()

    collector = ArxivCollector(args.output_dir, existing_titles=args.existing_titles)
    results = collector.collect(
        search_terms=args.search_terms,
        max_results=args.max_results
    )
    print(f"Collected {len(results)} papers. Output dir: {args.output_dir}")