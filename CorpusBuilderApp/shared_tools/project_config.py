import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Type
import yaml
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

class EnvironmentConfig(BaseModel):
    """Schema for environment-specific configuration."""
    corpus_dir: str = Field(..., description="Base directory for the corpus")
    cache_dir: Optional[str] = Field(None, description="Optional cache directory")
    log_dir: Optional[str] = Field(None, description="Optional log directory")
    raw_data_dir: Optional[str] = Field(None, description="Directory for raw documents")
    processed_dir: Optional[str] = Field(None, description="Directory for processed files")
    metadata_dir: Optional[str] = Field(None, description="Directory for metadata files")

class DomainConfig(BaseModel):
    """Schema for domain-specific configuration."""
    allocation: float = Field(..., description="Target allocation ratio for the domain")
    min_documents: int = Field(..., description="Minimum number of documents required")
    priority: str = Field(..., description="Priority level (high/medium/low)")
    quality_threshold: float = Field(..., description="Minimum quality score required")
    target_weight: float = Field(..., description="Target weight in corpus balancing")
    search_terms: List[str] = Field(..., description="Domain-specific search terms")


class GitHubCollectorConfig(BaseModel):
    """Optional schema for GitHub collector configuration."""
    enabled: bool = False
    search_terms: List[str] = Field(default_factory=list)
    topic: Optional[str] = None
    max_repos: int = 10


class ArxivCollectorConfig(BaseModel):
    """Optional schema for arXiv collector configuration."""
    enabled: bool = False
    search_terms: List[str] = Field(default_factory=list)
    max_papers: int = 50


class PDFProcessorConfig(BaseModel):
    """Optional schema for PDF processor configuration."""
    enabled: bool = False
    threads: int = 4
    enable_ocr: bool = True


class TextProcessorConfig(BaseModel):
    """Optional schema for text processor configuration."""
    enabled: bool = False
    threads: int = 4
    min_quality: int = 70


class AutoBalanceConfig(BaseModel):
    """Optional schema for Auto Balance service configuration."""

    enabled: bool = False
    dominance_ratio: float = 5.0
    min_entropy: float = 2.0
    check_interval: int = 900  # seconds
    start_balancing: bool = False


class EnvironmentSettings(BaseModel):
    """Runtime environment details."""
    active: str = Field("test", description="Active environment name")
    python_path: str = Field("", description="Path to Python interpreter")
    venv_path: str = Field("", description="Path to virtual environment")
    temp_dir: str = Field("", description="Temporary directory")


COLLECTOR_SCHEMAS: Dict[str, Type[BaseModel]] = {
    "github": GitHubCollectorConfig,
    "arxiv": ArxivCollectorConfig,
}


PROCESSOR_SCHEMAS: Dict[str, Type[BaseModel]] = {
    "pdf": PDFProcessorConfig,
    "text": TextProcessorConfig,
}


def get_collector_schema(name: str) -> Optional[Type[BaseModel]]:
    return COLLECTOR_SCHEMAS.get(name)


def get_processor_schema(name: str) -> Optional[Type[BaseModel]]:
    return PROCESSOR_SCHEMAS.get(name)

class ProjectConfigSchema(BaseModel):
    """Schema for ProjectConfig YAML files."""
    environment: EnvironmentSettings = Field(default_factory=EnvironmentSettings, description="Runtime environment settings")
    environments: Dict[str, EnvironmentConfig] = Field(..., description="Environment-specific configurations")
    domains: Dict[str, DomainConfig] = Field(
        default_factory=lambda: {
            'crypto_derivatives': {
                'allocation': 0.2,
                'min_documents': 100,
                'priority': 'high',
                'quality_threshold': 0.8,
                'target_weight': 0.2,
                'search_terms': [
                    'cryptocurrency derivatives',
                    'bitcoin futures',
                    'crypto options',
                    'perpetual swap',
                    'funding rate',
                    'basis trading',
                    'crypto derivatives pricing'
                ]
            },
            'decentralized_finance': {
                'allocation': 0.12,
                'min_documents': 70,
                'priority': 'medium',
                'quality_threshold': 0.75,
                'target_weight': 0.12,
                'search_terms': [
                    'defi protocols',
                    'automated market maker design',
                    'yield optimization strategies',
                    'liquidity mining'
                ]
            },
            'high_frequency_trading': {
                'allocation': 0.15,
                'min_documents': 80,
                'priority': 'high',
                'quality_threshold': 0.85,
                'target_weight': 0.15,
                'search_terms': [
                    'high frequency trading cryptocurrency',
                    'algorithmic crypto trading',
                    'low latency trading blockchain',
                    'market making algorithms crypto'
                ]
            },
            'market_microstructure': {
                'allocation': 0.15,
                'min_documents': 60,
                'priority': 'medium',
                'quality_threshold': 0.75,
                'target_weight': 0.15,
                'search_terms': [
                    'crypto market microstructure',
                    'order book dynamics',
                    'liquidity provision blockchain',
                    'market impact crypto'
                ]
            },
            'portfolio_construction': {
                'allocation': 0.1,
                'min_documents': 50,
                'priority': 'medium',
                'quality_threshold': 0.75,
                'target_weight': 0.1,
                'search_terms': [
                    'crypto portfolio construction',
                    'bitcoin asset allocation',
                    'digital asset correlation',
                    'crypto diversification'
                ]
            },
            'regulation_compliance': {
                'allocation': 0.05,
                'min_documents': 30,
                'priority': 'medium',
                'quality_threshold': 0.9,
                'target_weight': 0.05,
                'search_terms': [
                    'cryptocurrency regulation',
                    'crypto compliance framework',
                    'digital asset taxation',
                    'crypto KYC AML'
                ]
            },
            'risk_management': {
                'allocation': 0.15,
                'min_documents': 90,
                'priority': 'high',
                'quality_threshold': 0.8,
                'target_weight': 0.15,
                'search_terms': [
                    'cryptocurrency risk models',
                    'crypto portfolio hedging',
                    'defi risk management',
                    'crypto VaR'
                ]
            },
            'valuation_models': {
                'allocation': 0.08,
                'min_documents': 40,
                'priority': 'low',
                'quality_threshold': 0.7,
                'target_weight': 0.08,
                'search_terms': [
                    'token valuation models',
                    'cryptocurrency fundamental analysis',
                    'on-chain metrics valuation',
                    'crypto DCF'
                ]
            }
        },
        description="Domain-specific configurations"
    )
    auto_balance: AutoBalanceConfig = Field(default_factory=AutoBalanceConfig, description="Auto balance service configuration")

class ProjectConfig:
    """Project configuration manager with .env support"""
    
    def __init__(self, config_path: str, environment: Optional[str] = None):
        """Initialize configuration with .env support"""
        self.config_path = Path(config_path)
        self.environment = environment or os.getenv('ENVIRONMENT', 'test')

        self.logger = logging.getLogger(self.__class__.__name__)
        self._schema: Type[BaseModel] = ProjectConfigSchema

        # Load .env file if it exists
        env_path = self.config_path.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)

        # Load configuration
        self.config = self._load_yaml_and_env_merge()
        self.revalidate()
        # Ensure legacy attribute remains consistent
        self.environment = self.get("environment.active")
        
    def _load_yaml_and_env_merge(self) -> Dict[str, Any]:
        """Load configuration from YAML and merge environment variables."""
        config: Dict[str, Any] = {}
        
        # Load from YAML if it exists
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)

        # Convert legacy environment format
        if isinstance(config.get('environment'), str):
            config['environment'] = {
                'active': config['environment'],
                'python_path': '',
                'venv_path': '',
                'temp_dir': ''
            }
        
        # Override with environment variables
        env_config = {
            'environment': {
                'active': os.getenv('ENVIRONMENT', 'test'),
                'python_path': os.getenv('PYTHON_PATH', ''),
                'venv_path': os.getenv('VENV_PATH', ''),
                'temp_dir': os.getenv('TEMP_DIR', '')
            },
            'api_keys': {
                'github_token': os.getenv('GITHUB_TOKEN', ''),
                'aa_cookie': os.getenv('AA_COOKIE', ''),
                'fred_key': os.getenv('FRED_API_KEY', ''),
                'bitmex_key': os.getenv('BITMEX_API_KEY', ''),
                'bitmex_secret': os.getenv('BITMEX_API_SECRET', ''),
                'arxiv_email': os.getenv('ARXIV_EMAIL', '')
            },
            'processing': {
                'pdf': {
                    'threads': int(os.getenv('PDF_THREADS', '4')),
                    'enable_ocr': True,
                    'enable_formula': True,
                    'enable_tables': True
                },
                'text': {
                    'threads': int(os.getenv('TEXT_THREADS', '4')),
                    'enable_language': True,
                    'min_quality': 70,
                    'enable_deduplication': True
                },
                'advanced': {
                    'batch_size': int(os.getenv('BATCH_SIZE', '50')),
                    'max_retries': int(os.getenv('MAX_RETRIES', '3')),
                    'timeout': int(os.getenv('TIMEOUT', '300'))
                }
            }
        }
        env_dirs = {}
        if 'CORPUS_ROOT' in os.environ:
            env_dirs['corpus_root'] = os.environ['CORPUS_ROOT']
        if 'RAW_DATA_DIR' in os.environ:
            env_dirs['raw_data_dir'] = os.environ['RAW_DATA_DIR']
        if 'PROCESSED_DIR' in os.environ:
            env_dirs['processed_dir'] = os.environ['PROCESSED_DIR']
        if 'METADATA_DIR' in os.environ:
            env_dirs['metadata_dir'] = os.environ['METADATA_DIR']
        if 'LOGS_DIR' in os.environ:
            env_dirs['logs_dir'] = os.environ['LOGS_DIR']
        if env_dirs:
            env_config['directories'] = env_dirs
        
        # Deep merge configs, with env vars taking precedence
        self._deep_merge(config, env_config)

        # Map legacy directories to environment-specific section
        env_name = config.get('environment', {}).get('active', self.environment)
        dirs = config.get('directories', {})
        envs = config.setdefault('environments', {})
        env_section = envs.setdefault(env_name, {})
        defaults = {
            'corpus_root': '~/crypto_corpus',
            'raw_data_dir': '~/crypto_corpus/raw',
            'processed_dir': '~/crypto_corpus/processed',
            'metadata_dir': '~/crypto_corpus/metadata',
            'logs_dir': '~/crypto_corpus/logs',
        }
        for key, default in defaults.items():
            value = dirs.get(key)
            if value is None:
                value = env_section.get(key)
            if value is None:
                value = default
            dirs[key] = value
            env_section[key] = value
        config['directories'] = dirs
        envs[env_name] = env_section
        config['environments'] = envs

        # Validate collector and processor sections if present
        self._validate_section_schemas(config)

        return config
    
    def _validate_section_schemas(self, config: Dict[str, Any]) -> None:
        """Validate collector and processor sections using optional schemas."""
        for name, data in config.get("collectors", {}).items():
            model = get_collector_schema(name)
            if model:
                try:
                    model.parse_obj(data)
                except ValidationError as exc:  # pragma: no cover - simple log
                    self.logger.warning("Invalid collector config '%s': %s", name, exc)

        for name, data in config.get("processors", {}).items():
            model = get_processor_schema(name)
            if model:
                try:
                    model.parse_obj(data)
                except ValidationError as exc:  # pragma: no cover - simple log
                    self.logger.warning("Invalid processor config '%s': %s", name, exc)

    # Backwards compatibility
    def _load_config(self) -> Dict[str, Any]:
        return self._load_yaml_and_env_merge()

    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep merge two dictionaries"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    def set(self, dotted_key: str, value):
        parts = dotted_key.split('.')
        node = self.config
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = value
    
    def save(self) -> None:
        """Save configuration to YAML file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def reload_from_file(self) -> None:
        """Reload YAML from disk and reapply environment variables."""
        self.config = self._load_yaml_and_env_merge()
        self.revalidate()

    def revalidate(self) -> None:
        """Re-parse the current configuration using the schema."""
        self._parsed_config = self._schema.parse_obj(self.config)
        parsed_dict = getattr(self._parsed_config, "dict", lambda: {})()
        for key, value in parsed_dict.items():
            if key not in self.config:
                self.config[key] = value

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None

 # Directory helper methods
    def get_corpus_root(self) -> Path:
        env = self.get('environment.active')
        path = self.get(f'environments.{env}.corpus_root')
        if path is None:
            path = self.get('directories.corpus_root')
        return Path(path).expanduser()

    def get_corpus_dir(self) -> Path:
        return self.get_corpus_root()

    def get_raw_dir(self) -> Path:
        env = self.get('environment.active')
        path = self.get(f'environments.{env}.raw_data_dir')
        if path is None:
            path = self.get('directories.raw_data_dir')
        return Path(path).expanduser()

    def get_input_dir(self) -> Path:
        """Legacy helper for compatibility with older processors."""
        return self.get_raw_dir()

    def get_processed_dir(self) -> Path:
        env = self.get('environment.active')
        path = self.get(f'environments.{env}.processed_dir')
        if path is None:
            path = self.get('directories.processed_dir')
        return Path(path).expanduser()

    def get_metadata_dir(self) -> Path:
        env = self.get('environment.active')
        path = self.get(f'environments.{env}.metadata_dir')
        if path is None:
            path = self.get('directories.metadata_dir')
        return Path(path).expanduser()

    def get_logs_dir(self) -> Path:
        """
        Return the configured logs directory as a Path object.
        Falls back to ~/.cryptofinance/logs if not explicitly set.

        Use `str(...)` or `.as_posix()` if string form is needed (e.g. subprocess).
        """
        env = self.get('environment.active')
        path = self.get(f'environments.{env}.logs_dir')
        if path is None:
            path = self.get('directories.logs_dir', os.path.expanduser("~/.cryptofinance/logs"))
        return Path(path).expanduser()

    def get_stats_dir(self) -> Path:
        """Return directory where corpus statistics are stored."""
        default = self.get_logs_dir() / "stats"
        return Path(self.get("directories.stats_dir", str(default))).expanduser()

    @classmethod
    def from_yaml(cls, yaml_path: str, environment: Optional[str] = None) -> 'ProjectConfig':
        """Load config from YAML file with schema validation."""
        return cls(yaml_path, environment=environment)

    @classmethod
    def create_default_config_object(cls) -> Dict[str, Any]:
        """Return a basic default configuration dictionary."""
        config_dir = Path.home() / ".cryptofinance"
        return {
            "environment": {
                "active": "test",
                "python_path": "",
                "venv_path": "",
                "temp_dir": "",
            },
            "environments": {
                "test": {
                    "corpus_dir": str(config_dir / "corpus"),
                    "cache_dir": str(config_dir / "cache"),
                    "log_dir": str(config_dir / "logs"),
                    "raw_data_dir": str(config_dir / "corpus" / "raw"),
                    "processed_dir": str(config_dir / "corpus" / "processed"),
                    "metadata_dir": str(config_dir / "corpus" / "metadata"),
                },
                "production": {
                    "corpus_dir": str(Path.home() / "CryptoCorpus"),
                    "cache_dir": str(Path.home() / "CryptoCorpus" / "cache"),
                    "log_dir": str(Path.home() / "CryptoCorpus" / "logs"),
                    "raw_data_dir": str(Path.home() / "CryptoCorpus" / "raw"),
                    "processed_dir": str(Path.home() / "CryptoCorpus" / "processed"),
                    "metadata_dir": str(Path.home() / "CryptoCorpus" / "metadata"),
                },
            },
            "auto_balance": {
                "enabled": False,
                "dominance_ratio": 5.0,
                "min_entropy": 2.0,
                "check_interval": 900,
                "start_balancing": False,
            },
        }
