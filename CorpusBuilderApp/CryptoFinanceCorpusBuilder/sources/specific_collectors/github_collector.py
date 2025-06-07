# DEPRECATED: This file belongs to the legacy CryptoFinanceCorpusBuilder package and should not be used in new modules.
# sources/specific_collectors/github_collector.py
import os
import json
import time
from pathlib import Path
from urllib.parse import quote
from CryptoFinanceCorpusBuilder.sources.api_collector import ApiCollector
import re

def ascii_safe(s):
    """Make string safe for console output on any platform."""
    return str(s).encode('ascii', errors='replace').decode('ascii')

def normalize_title(title):
    # Identical to cache creation script
    return re.sub(r'[^\w\s]', '', str(title).lower()).strip()

class GitHubCollector(ApiCollector):
    """Collector for GitHub repositories"""
    
    def __init__(self, output_dir, api_key=None, delay_range=(2, 5), existing_titles=None):
        super().__init__(output_dir, api_key=api_key, api_base_url='https://api.github.com', delay_range=delay_range)
        self.rate_limits = {'api.github.com': {'requests': 5, 'period': 60}}  # Conservative rate limiting
        # Deduplication: load existing titles cache
        self.titles_cache = set()
        if existing_titles and os.path.exists(existing_titles):
            with open(existing_titles, 'r', encoding='utf-8') as f:
                self.titles_cache = {line.strip() for line in f}
        print(f"DEBUG: Cache size: {len(self.titles_cache)}")
        print(f"DEBUG: First 5 cache entries: {[ascii_safe(x) for x in list(self.titles_cache)[:5]]}")
        with open('dedup_debug.log', 'a', encoding='utf-8') as dbg:
            dbg.write(f"Collector: github, Cache entries: {list(self.titles_cache)[:5]}\n\n")
        self._normalize_title = lambda t: re.sub(r'[^\w\s]', '', str(t).lower()).strip()
    
    def collect(self, search_terms=None, topic=None, max_repos=10):
        """Collect repositories based on search terms or topics"""
        if search_terms is None and topic is None:
            self.logger.error("Either search_terms or topic must be provided")
            return []
        
        # Get repository data
        repos = []
        
        if topic:
            repos = self._search_by_topic(topic, max_repos)
        elif search_terms:
            for term in search_terms:
                results = self._search_by_term(term, max_repos // len(search_terms))
                repos.extend(results)
        
        # Deduplication: filter out repos whose normalized name is in the cache
        if self.titles_cache:
            before_count = len(repos)
            repos = [r for r in repos if not self._should_skip(r.get('name', ''))]
            skipped = before_count - len(repos)
            self.logger.info(f"Deduplication: Skipped {skipped} results already in the existing titles cache.")
        
        # Clone repositories
        cloned_repos = []
        for repo in repos:
            clone_url = repo.get('clone_url')
            if clone_url:
                # Clone to a directory named after the repo
                repo_name = repo.get('name', 'unknown')
                owner = repo.get('owner', {}).get('login', 'unknown')
                
                target_dir = self.output_dir / f"{owner}_{repo_name}"
                
                # Clone the repository
                result = self._clone_repo(clone_url, target_dir)
                
                if result:
                    repo['local_path'] = str(target_dir)
                    cloned_repos.append(repo)
        
        self.logger.info(f"Cloned {len(cloned_repos)} repositories")
        return cloned_repos
    
    def _search_by_topic(self, topic, max_repos=10):
        """Search GitHub repositories by topic"""
        endpoint = f"search/repositories?q=topic:{quote(topic)}&sort=stars&order=desc&per_page={max_repos}"
        response = self.api_request(endpoint)
        
        if not response or 'items' not in response:
            return []
            
        return response['items']
    
    def _search_by_term(self, term, max_repos=10):
        """Search GitHub repositories by term"""
        endpoint = f"search/repositories?q={quote(term)}&sort=stars&order=desc&per_page={max_repos}"
        response = self.api_request(endpoint)
        
        if not response or 'items' not in response:
            return []
            
        return response['items']
    
    def _clone_repo(self, clone_url, target_dir):
        """Clone a GitHub repository"""
        import subprocess
        
        target_dir = Path(target_dir)
        
        # Skip if already exists
        if target_dir.exists():
            self.logger.info(f"Repository already exists at {target_dir}")
            return target_dir
            
        try:
            # Create parent directory if it doesn't exist
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            
            # Clone with depth 1 to save bandwidth and time
            self.logger.info(f"Cloning repository: {clone_url}")
            cmd = ['git', 'clone', '--depth', '1', clone_url, str(target_dir)]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info(f"Successfully cloned repository to {target_dir}")
            
            return target_dir
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error cloning repository {clone_url}: {e}")
            self.logger.error(f"STDERR: {e.stderr}")
            return None

    def _should_skip(self, repo_name):
        norm_title = normalize_title(repo_name)
        print(f"DEBUG: Normalized title: {ascii_safe(norm_title)}")
        with open('dedup_debug.log', 'a', encoding='utf-8') as dbg:
            dbg.write(f"Collector: github, Title: {norm_title}\n")
        return norm_title in self.titles_cache