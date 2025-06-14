# sources/base_collector.py
import os
import logging
import random
import time
import json
import hashlib
import requests
from urllib.parse import urlparse
from pathlib import Path
from typing import Optional, Union, Any

class BaseCollector:
    """Base class for all data collectors"""

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36'
    ]

    @staticmethod
    def _get_path_attr(cfg: Any, attr_name: str, getter_name: str) -> Any:
        """Return a path-like attribute from cfg using attr or getter method."""
        if hasattr(cfg, attr_name):
            value = getattr(cfg, attr_name)
            if callable(value):
                try:
                    return value()
                except TypeError:
                    return value
            return value
        getter = getattr(cfg, getter_name, None)
        if callable(getter):
            return getter()
        elif getter is not None:
            return getter
        raise AttributeError(f"{cfg!r} has neither {attr_name!r} nor {getter_name!r}")
    
    def __init__(self, config: Union[str, 'ProjectConfig'], delay_range: tuple = (2, 5)):
        """
        Initialize BaseCollector with ProjectConfig.
        
        Args:
            config: ProjectConfig instance or path to config file
            delay_range: Tuple of (min, max) delay between requests
        """
        if isinstance(config, str):
            from shared_tools.project_config import ProjectConfig
            config = ProjectConfig(config, environment='test')
        
        self.config = config
        self.raw_data_dir = Path(self._get_path_attr(config, "raw_data_dir", "get_raw_dir"))
        self.delay_range = delay_range

        # ------------------------------------------------------------------
        # Back-compatibility shim: older collectors/processors sometimes read
        # `config.raw_data_dir` directly. Real `ProjectConfig` instances only
        # expose `get_raw_dir()`.  Add the attribute dynamically if absent so
        # those call-sites keep working without further edits.
        # ------------------------------------------------------------------
        if not hasattr(config, "raw_data_dir"):
            setattr(config, "raw_data_dir", self.raw_data_dir)

        # ------------------------------------------------------------------
        # Determine domain configurations gracefully across multiple config
        # object shapes:
        # 1. Modern callers (tests) often expose `domain_configs` directly.
        # 2. Some legacy dummy configs expose `get_processor_config()`.
        # 3. A real `ProjectConfig` stores the mapping under `domains:` in the
        #    YAML and provides a generic `.get()` accessor.
        # Fallback → {"other": {}} to guarantee the attribute exists.
        # ------------------------------------------------------------------

        if hasattr(config, "domain_configs"):
            self.domain_configs = config.domain_configs
        elif hasattr(config, "get_processor_config"):
            try:
                self.domain_configs = (
                    config.get_processor_config("domain").get("domain_configs", {})
                )
            except Exception:
                self.domain_configs = {}
        elif hasattr(config, "get"):
            # Works for ProjectConfig and any mapping-like config with a .get()
            self.domain_configs = config.get("domains", {})  # type: ignore[arg-type]
        else:
            self.domain_configs = {"other": {}}
        
        # Configure logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
            # Add file handler with UTF-8 encoding
            log_dir = Path(self._get_path_attr(config, "log_dir", "get_logs_dir"))
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_dir / f"{self.__class__.__name__.lower()}.log", encoding="utf-8")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
        self.logger.info(f"Initializing {self.__class__.__name__} with output directory: {self.raw_data_dir}")
        
        # Create directory structure
        self._setup_domain_directories()
        self.output_dir = self.raw_data_dir
        self.session = requests.Session()

        # Hash cache for optional deduplication
        self.hash_cache_path = Path(getattr(config, 'get_metadata_dir', lambda: Path(config.metadata_dir))()) / 'seen_hashes.json'
        self.hash_cache = {}
        if self.hash_cache_path.exists():
            try:
                with open(self.hash_cache_path, 'r') as f:
                    self.hash_cache = json.load(f)
            except Exception as exc:  # pragma: no cover - non-critical load failure
                self.logger.warning(f"Failed to load hash cache: {exc}")
        self.skip_known_hashes = False
    
    def _setup_domain_directories(self):
        """Create domain-based directory structure based on config."""
        self.logger.info("Setting up domain-based directory structure...")
        
        # Get domains from config
        domains = list(self.domain_configs.keys())
        if not domains:
            # Fallback to default domains if none configured
            domains = [
                'crypto_derivatives',
                'high_frequency_trading',
                'portfolio_construction',
                'risk_management',
                'market_microstructure',
                'trading_strategies',
                'other'
            ]
        
        content_types = ['papers', 'reports', 'articles']
        
        for domain in domains:
            domain_dir = self.raw_data_dir / domain
            if not domain_dir.exists():
                self.logger.debug(f"Creating domain directory: {domain_dir}")
                domain_dir.mkdir(parents=True, exist_ok=True)
            
            for content_type in content_types:
                content_dir = domain_dir / content_type
                if not content_dir.exists():
                    self.logger.debug(f"Creating content directory: {content_dir}")
                    content_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Directory structure setup complete")
    
    def _get_output_path(self, domain: str, content_type: str, filename: str) -> Path:
        """Get the correct output path based on domain and content type."""
        # Get valid domains from config
        valid_domains = list(self.domain_configs.keys())
        
        if domain not in valid_domains:
            domain = 'other'
            self.logger.debug(f"Domain '{domain}' not recognized, using 'other'")
            
        if content_type not in ['papers', 'reports', 'articles']:
            content_type = 'articles'
            self.logger.debug(f"Content type '{content_type}' not recognized, using 'articles'")
            
        output_path = self.raw_data_dir / domain / content_type / filename
        self.logger.debug(f"Generated output path: {output_path}")
        return output_path
    
    def collect(self, query, max_items=100):
        """Main collection method to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement the collect method")
    
    def download_file(self, url: str, filename: Optional[str] = None, subfolder: Optional[str] = None) -> Optional[Path]:
        """Download a file with rate limiting and random user agent"""
        # Apply rate limiting
        self._respect_rate_limits(url)
        
        # Set destination path
        target_dir = self.output_dir
        if subfolder:
            target_dir = self.output_dir / subfolder
            target_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            url_parts = urlparse(url)
            filename = os.path.basename(url_parts.path)
            if not filename:
                filename = f"download_{int(time.time())}"
        
        filepath = target_dir / filename
        
        # Download the file
        headers = {'User-Agent': self._get_random_user_agent()}
        
        for attempt in range(3):
            try:
                self.logger.info(f"Downloading {url} to {filepath}")
                response = requests.get(url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()

                if int(response.headers.get("Content-Length", 0)) > 100_000_000:
                    self.logger.warning(f"Large file: {filename}")

                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                sha256 = hashlib.sha256(filepath.read_bytes()).hexdigest()
                self.logger.info(f"SHA256 for {filepath.name}: {sha256}")

                if sha256 in self.hash_cache and self.skip_known_hashes:
                    self.logger.info(f"Known file detected by hash: {filepath}")
                    if filepath.exists():
                        filepath.unlink()
                    return None

                if sha256 not in self.hash_cache:
                    self.hash_cache[sha256] = str(filepath)
                    self._save_hash_cache()

                self.logger.info(f"Successfully downloaded {filepath}")
                return filepath
            except Exception as e:
                if attempt == 2:
                    self.logger.error(f"Download failed after 3 attempts: {e}")
                    return None
                self.logger.warning(f"Retry {attempt+1}/3 for {url}")
                time.sleep(2)
    
    def _get_random_user_agent(self) -> str:
        """Return a random user agent string"""
        return random.choice(self.USER_AGENTS)
    
    def _respect_rate_limits(self, url: str) -> None:
        """Implement rate limiting based on domain"""
        domain = urlparse(url).netloc
        delay = random.uniform(*self.delay_range)
        self.logger.debug(f"Waiting {delay:.2f}s before requesting from {domain}")
        time.sleep(delay)

    def _save_hash_cache(self) -> None:
        """Persist the global hash cache safely."""
        try:
            self.hash_cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.hash_cache_path, 'w') as f:
                json.dump(self.hash_cache, f, indent=2)
        except Exception as exc:  # pragma: no cover - non-critical save failure
            self.logger.warning(f"Failed to update hash cache: {exc}")
