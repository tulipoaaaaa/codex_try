import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv
from app.helpers.crypto_utils import encrypt_value, decrypt_value

class EnvironmentConfig(BaseModel):
    """Schema for environment-specific configuration."""
    corpus_dir: str = Field(..., description="Base directory for the corpus")
    cache_dir: Optional[str] = Field(None, description="Optional cache directory")
    log_dir: Optional[str] = Field(None, description="Optional log directory")

class DomainConfig(BaseModel):
    """Schema for domain-specific configuration."""
    allocation: float = Field(..., description="Target allocation ratio for the domain")
    min_documents: int = Field(..., description="Minimum number of documents required")
    priority: str = Field(..., description="Priority level (high/medium/low)")
    quality_threshold: float = Field(..., description="Minimum quality score required")
    target_weight: float = Field(..., description="Target weight in corpus balancing")
    search_terms: List[str] = Field(..., description="Domain-specific search terms")

class ProjectConfigSchema(BaseModel):
    """Schema for ProjectConfig YAML files."""
    environment: str = Field(..., description="Current environment (production/test)")
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

class ProjectConfig:
    """Project configuration manager with .env support"""
    
    def __init__(self, config_path: str, environment: Optional[str] = None):
        """Initialize configuration with .env support"""
        self.config_path = Path(config_path)
        self.environment = environment or os.getenv('ENVIRONMENT', 'test')
        
        # Load .env file if it exists
        env_path = self.config_path.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        
        # Load configuration
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML and environment variables"""
        config = {}
        
        # Load from YAML if it exists
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
        
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
            },
            'directories': {
                'corpus_root': os.getenv('CORPUS_ROOT', '~/crypto_corpus'),
                'raw_data_dir': os.getenv('RAW_DATA_DIR', '~/crypto_corpus/raw'),
                'processed_dir': os.getenv('PROCESSED_DIR', '~/crypto_corpus/processed'),
                'metadata_dir': os.getenv('METADATA_DIR', '~/crypto_corpus/metadata'),
                'logs_dir': os.getenv('LOGS_DIR', '~/crypto_corpus/logs')
            }
        }
        
        # Deep merge configs, with env vars taking precedence
        self._deep_merge(config, env_config)
        return config
    
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
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def save(self) -> None:
        """Save configuration to YAML file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    @classmethod
    def from_yaml(cls, yaml_path: str, environment: Optional[str] = None) -> 'ProjectConfig':
        """Load config from YAML file with schema validation."""
        return cls(yaml_path, environment=environment) 