# sources/specific_collectors/github_collector.py
import os
import json
import time
from pathlib import Path
from urllib.parse import quote
from typing import List, Optional, Union, Dict, Any
from CryptoFinanceCorpusBuilder.shared_tools.collectors.api_collector import ApiCollector
import re

def ascii_safe(s):
    """Make string safe for console output on any platform."""
    return str(s).encode('ascii', errors='replace').decode('ascii')

def normalize_title(title):
    # Identical to cache creation script
    return re.sub(r'[^\w\s]', '', str(title).lower()).strip()

class GitHubCollector(ApiCollector):
    """Collector for GitHub repositories"""
    
    def __init__(self, 
                 config: Union[str, 'ProjectConfig'],
                 api_key: Optional[str] = None,
                 delay_range: tuple = (2, 5),
                 existing_titles: Optional[str] = None):
        """Initialize the GitHub collector.
        
        Args:
            config: ProjectConfig instance or path to config file
            api_key: GitHub API key
            delay_range: Tuple of (min_delay, max_delay) in seconds between requests
            existing_titles: Path to file containing existing titles for deduplication
        """
        super().__init__(config, api_base_url='https://api.github.com', delay_range=delay_range)
        self.api_key = api_key  # Store for future use if needed
        self.rate_limits = {'api.github.com': {'requests': 5, 'period': 60}}  # Conservative rate limiting
        
        # Set up GitHub-specific directory based on environment
        self.github_dir = self.config.raw_data_dir / 'Github'
        self.github_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"GitHub directory set to: {self.github_dir}")
        
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
            dbg.write(f"Collector: github, Cache entries: {list(self.titles_cache)[:5]}\n\n")
            
        self._normalize_title = lambda t: re.sub(r'[^\w\s]', '', str(t).lower()).strip()
    
    def _get_output_path(self, filename: str, content_type: str = 'code') -> Path:
        """Get the correct output path for GitHub content.
        
        Args:
            filename: Name of the file to save
            content_type: Type of content (code, articles, etc.)
            
        Returns:
            Path object for the output file
        """
        # Always save in the GitHub directory
        return self.github_dir / filename
    
    def _determine_domain(self, repo_data: Dict[str, Any]) -> str:
        """Determine the domain for a repository based on its topics and description.
        
        Args:
            repo_data: Repository information dictionary
            
        Returns:
            Domain name as string
        """
        # Default to high_frequency_trading as most GitHub repos are about trading
        default_domain = 'high_frequency_trading'
        
        # Get repository info
        topics = repo_data.get('topics', [])
        description = repo_data.get('description', '').lower()
        name = repo_data.get('name', '').lower()
        
        # Check for domain-specific keywords
        if any(term in description or term in name for term in ['portfolio', 'allocation', 'weight']):
            return 'portfolio_construction'
        elif any(term in description or term in name for term in ['risk', 'uncertainty', 'volatility']):
            return 'risk_management'
        elif any(term in description or term in name for term in ['defi', 'decentralized', 'blockchain']):
            return 'decentralized_finance'
        elif any(term in description or term in name for term in ['hft', 'high frequency', 'algorithmic']):
            return 'high_frequency_trading'
        elif any(term in description or term in name for term in ['microstructure', 'order book', 'liquidity']):
            return 'market_microstructure'
        elif any(term in description or term in name for term in ['derivative', 'futures', 'options']):
            return 'crypto_derivatives'
        elif any(term in description or term in name for term in ['regulation', 'compliance', 'legal']):
            return 'regulation_compliance'
        
        return default_domain
    
    def collect(self, 
                search_terms: Optional[List[str]] = None,
                topic: Optional[str] = None,
                max_repos: int = 10) -> List[Dict[str, Any]]:
        """Collect repositories based on search terms or topics.
        
        Args:
            search_terms: List of search terms to find repositories
            topic: GitHub topic to search for
            max_repos: Maximum number of repositories to collect
            
        Returns:
            List of collected repository information
        """
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
                
                # Use the domain-based directory structure
                filename = f"{owner}_{repo_name}"
                target_dir = self._get_output_path(filename, 'code')
                
                # Clone the repository
                result = self._clone_repo(clone_url, target_dir)
                
                if result:
                    repo['local_path'] = str(target_dir)
                    repo['domain'] = self._determine_domain(repo)
                    cloned_repos.append(repo)
        
        self.logger.info(f"Cloned {len(cloned_repos)} repositories")
        return cloned_repos
    
    def _search_by_topic(self, topic: str, max_repos: int = 10) -> List[Dict[str, Any]]:
        """Search GitHub repositories by topic.
        
        Args:
            topic: GitHub topic to search for
            max_repos: Maximum number of repositories to return
            
        Returns:
            List of repository information dictionaries
        """
        endpoint = f"search/repositories?q=topic:{quote(topic)}&sort=stars&order=desc&per_page={max_repos}"
        response = self.api_request(endpoint)
        
        if not response or 'items' not in response:
            return []
            
        return response['items']
    
    def _search_by_term(self, term: str, max_repos: int = 10) -> List[Dict[str, Any]]:
        """Search GitHub repositories by term.
        
        Args:
            term: Search term to find repositories
            max_repos: Maximum number of repositories to return
            
        Returns:
            List of repository information dictionaries
        """
        endpoint = f"search/repositories?q={quote(term)}&sort=stars&order=desc&per_page={max_repos}"
        response = self.api_request(endpoint)
        
        if not response or 'items' not in response:
            return []
            
        return response['items']
    
    def _clone_repo(self, clone_url: str, target_dir: Path) -> Optional[Path]:
        """Clone a GitHub repository.
        
        Args:
            clone_url: URL to clone the repository from
            target_dir: Directory to clone the repository into
            
        Returns:
            Path to the cloned repository, or None if cloning failed
        """
        import subprocess
        
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

    def _should_skip(self, repo_name: str) -> bool:
        """Check if a repository should be skipped based on its name.
        
        Args:
            repo_name: Name of the repository
            
        Returns:
            True if the repository should be skipped, False otherwise
        """
        norm_title = normalize_title(repo_name)
        self.logger.debug(f"Normalized title: {ascii_safe(norm_title)}")
        
        log_dir = Path(self.config.log_dir)
        with open(log_dir / 'dedup_debug.log', 'a', encoding='utf-8') as dbg:
            dbg.write(f"Collector: github, Title: {norm_title}\n")
            
        return norm_title in self.titles_cache

    def _download_repo(self, 
                      repo_url: str,
                      repo_name: str,
                      domain: str = 'other',
                      content_type: str = 'articles') -> Optional[Path]:
        """Download and save a GitHub repository as a zip file.
        
        Args:
            repo_url: URL of the repository
            repo_name: Name of the repository
            domain: Domain to save the repository in
            content_type: Type of content being downloaded
            
        Returns:
            Path to the downloaded zip file, or None if download failed
        """
        # Determine output path
        filename = f"{repo_name}.zip"
        target_path = self._get_output_path(filename, content_type)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        zip_url = f"{repo_url}/archive/refs/heads/master.zip"
        self.logger.info(f"Downloading {zip_url} to {target_path}")
        try:
            response = self.session.get(zip_url, stream=True)
            response.raise_for_status()
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            self.logger.info(f"Successfully downloaded {target_path}")
            return target_path
        except Exception as e:
            self.logger.error(f"Error downloading {zip_url}: {e}")
            return None

    def collect_by_repo(self, repo_info: Union[Dict[str, str], List[Dict[str, str]]]) -> List[Dict[str, Any]]:
        """Collect specific repositories by owner and repo name.
        
        Args:
            repo_info: Dictionary with 'owner' and 'repo' keys, or list of such dictionaries
            
        Returns:
            List of collected repository information
        """
        if isinstance(repo_info, list):
            repos = repo_info
        else:
            repos = [repo_info]
            
        cloned_repos = []
        for repo in repos:
            owner = repo.get('owner')
            repo_name = repo.get('repo')
            
            if not owner or not repo_name:
                self.logger.error(f"Invalid repo info: {repo}")
                continue
                
            # Get repository data
            endpoint = f"repos/{owner}/{repo_name}"
            repo_data = self.api_request(endpoint)
            
            if not repo_data:
                self.logger.error(f"Failed to get repository data for {owner}/{repo_name}")
                continue
                
            # Clone repository
            clone_url = repo_data.get('clone_url')
            if clone_url:
                filename = f"{owner}_{repo_name}"
                target_dir = self._get_output_path(filename, 'code')
                
                result = self._clone_repo(clone_url, target_dir)
                
                if result:
                    repo_data['local_path'] = str(target_dir)
                    repo_data['domain'] = self._determine_domain(repo_data)
                    cloned_repos.append(repo_data)
        
        self.logger.info(f"Cloned {len(cloned_repos)} repositories")
        return cloned_repos

if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    import os
    
    parser = argparse.ArgumentParser(description="Collect data from GitHub")
    parser.add_argument("--config", required=True, help="Path to config file")
    parser.add_argument("--search-terms", nargs="*", help="List of search terms for GitHub repository search")
    parser.add_argument("--topic", type=str, help="GitHub topic to search for")
    parser.add_argument("--max-repos", type=int, default=10, help="Maximum number of repositories to collect")
    parser.add_argument("--existing-titles", type=str, help="Path to file with existing repo titles for deduplication")
    
    args = parser.parse_args()
    
    load_dotenv()
    api_key = os.getenv("GITHUB_TOKEN")
    
    collector = GitHubCollector(args.config, api_key=api_key, existing_titles=args.existing_titles)
    results = collector.collect(
        search_terms=args.search_terms,
        topic=args.topic,
        max_repos=args.max_repos
    )
    
    print(f"Collected {len(results)} GitHub records. Output dir: {collector.output_dir}")