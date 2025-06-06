import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from pydantic import BaseModel, Field, validator

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
    """
    Manages and enforces the standard folder structure for a corpus project.
    Auto-creates all required directories on initialization.
    Supports multiple environments (production/test) with environment-specific settings.
    """
    def __init__(self, config_path: str, environment: Optional[str] = None, create_dirs: bool = True):
        # Load and validate config
        self.config_data = self._load_config(config_path)
        self.schema = ProjectConfigSchema(**self.config_data)
        
        # Set environment
        self.environment = environment or self.schema.environment
        if self.environment not in self.schema.environments:
            raise ValueError(f"Environment '{self.environment}' not found in config")
        
        # Get environment-specific config
        env_config = self.schema.environments[self.environment]
        
        # Set up paths
        self.corpus_dir = Path(env_config.corpus_dir)
        self.cache_dir = Path(env_config.cache_dir) if env_config.cache_dir else None
        self.log_dir = Path(env_config.log_dir) if env_config.log_dir else None
        
        # Standard subfolders
        self.raw_data_dir = self.corpus_dir / 'raw_data'
        self.extracted_dir = self.corpus_dir / 'extracted'
        self.pdf_extracted_dir = self.corpus_dir / 'pdf_extracted'
        self.nonpdf_extracted_dir = self.corpus_dir / 'nonpdf_extracted'
        self.balance_reports_dir = self.corpus_dir / 'balance_reports'
        self.processed_dir = self.corpus_dir / 'processed'
        self.reports_dir = self.corpus_dir / 'reports'
        self.config_dir = self.corpus_dir / 'config'
        self.cache_data_dir = self.cache_dir / 'corpus_cache' if self.cache_dir else None
        
        # Store domain configs
        self.domain_configs = self.schema.domains
        
        if create_dirs:
            self._validate_and_create_dirs()

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _validate_and_create_dirs(self):
        """Validate and create required directories."""
        # Create base directories
        for dir_path in [
            self.raw_data_dir, self.extracted_dir, self.pdf_extracted_dir,
            self.nonpdf_extracted_dir, self.balance_reports_dir, self.processed_dir,
            self.reports_dir, self.log_dir, self.config_dir
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create domain-specific directories
        for domain in self.domain_configs:
            domain_dir = self.raw_data_dir / domain
            for content_type in ['papers', 'reports', 'articles']:
                (domain_dir / content_type).mkdir(parents=True, exist_ok=True)

    def set_cache_dir(self, cache_dir: str):
        """Update cache directory path."""
        self.cache_dir = Path(cache_dir)
        self.cache_data_dir = self.cache_dir / 'corpus_cache'
        self.cache_data_dir.mkdir(parents=True, exist_ok=True)

    def to_yaml(self, yaml_path: str) -> None:
        """Save config to YAML file."""
        config_data = {
            'environment': self.environment,
            'environments': {
                env: {
                    'corpus_dir': str(config.corpus_dir),
                    'cache_dir': str(config.cache_dir) if config.cache_dir else None,
                    'log_dir': str(config.log_dir) if config.log_dir else None
                }
                for env, config in self.schema.environments.items()
            },
            'domains': self.domain_configs
        }
        
        with open(yaml_path, 'w') as f:
            yaml.safe_dump(config_data, f, default_flow_style=False)

    @classmethod
    def from_yaml(cls, yaml_path: str, environment: Optional[str] = None) -> 'ProjectConfig':
        """Load config from YAML file with schema validation."""
        return cls(yaml_path, environment=environment) 