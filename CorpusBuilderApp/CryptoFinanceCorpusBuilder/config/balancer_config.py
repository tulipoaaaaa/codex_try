# CryptoFinanceCorpusBuilder/config/balancer_config.py
"""
Configuration management for corpus balancer module.
Integrates with existing domain configuration system.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import logging

# Default balance thresholds optimized for crypto-finance corpora
DEFAULT_BALANCE_THRESHOLDS = {
    # Entropy thresholds (bits)
    'entropy_min': 2.0,  # Minimum acceptable entropy for balanced distribution
    'entropy_target': 2.5,  # Target entropy for rebalancing
    
    # Inequality thresholds
    'gini_max': 0.7,  # Maximum Gini coefficient (0 = perfect equality, 1 = maximum inequality)
    'gini_target': 0.4,  # Target Gini coefficient for rebalancing
    
    # Ratio constraints
    'ratio_max': 10.0,  # Maximum acceptable imbalance ratio (largest:smallest class)
    'ratio_target': 3.0,  # Target imbalance ratio for rebalancing
    
    # Sample size constraints
    'min_samples': 30,  # Minimum samples per class for statistical significance
    'min_samples_strict': 100,  # Minimum for high-confidence analysis
    
    # Quality thresholds
    'min_quality_ratio': 0.7,  # Minimum ratio of high-quality documents
    'low_quality_max': 0.3,  # Maximum acceptable ratio of low-quality documents
}

# Domain-specific balance requirements
DOMAIN_BALANCE_CONFIG = {
    'crypto_derivatives': {
        'priority': 'high',
        'min_documents': 100,
        'target_weight': 0.20,
        'quality_threshold': 0.8
    },
    'high_frequency_trading': {
        'priority': 'high',
        'min_documents': 80,
        'target_weight': 0.15,
        'quality_threshold': 0.85
    },
    'market_microstructure': {
        'priority': 'medium',
        'min_documents': 60,
        'target_weight': 0.15,
        'quality_threshold': 0.75
    },
    'risk_management': {
        'priority': 'high',
        'min_documents': 90,
        'target_weight': 0.15,
        'quality_threshold': 0.8
    },
    'decentralized_finance': {
        'priority': 'medium',
        'min_documents': 70,
        'target_weight': 0.12,
        'quality_threshold': 0.75
    },
    'portfolio_construction': {
        'priority': 'medium',
        'min_documents': 50,
        'target_weight': 0.10,
        'quality_threshold': 0.75
    },
    'valuation_models': {
        'priority': 'low',
        'min_documents': 40,
        'target_weight': 0.08,
        'quality_threshold': 0.7
    },
    'regulation_compliance': {
        'priority': 'medium',
        'min_documents': 30,
        'target_weight': 0.05,
        'quality_threshold': 0.9
    }
}

# File type balance preferences
FILE_TYPE_BALANCE_CONFIG = {
    'pdf': {
        'target_ratio': 0.6,  # PDFs should be majority but not overwhelming
        'max_ratio': 0.8,
        'quality_requirements': 'standard'
    },
    'html': {
        'target_ratio': 0.15,
        'min_ratio': 0.05,
        'quality_requirements': 'relaxed'  # HTML often has formatting issues
    },
    'markdown': {
        'target_ratio': 0.1,
        'min_ratio': 0.02,
        'quality_requirements': 'standard'
    },
    'python': {
        'target_ratio': 0.08,
        'min_ratio': 0.01,
        'quality_requirements': 'code_specific'
    },
    'jupyter': {
        'target_ratio': 0.05,
        'min_ratio': 0.005,
        'quality_requirements': 'code_specific'
    },
    'csv': {
        'target_ratio': 0.02,
        'min_ratio': 0.001,
        'quality_requirements': 'data_specific'
    }
}

# Quality weight configurations for different document types
QUALITY_WEIGHTS = {
    'standard': {
        'token_count': 0.25,
        'quality_flag': 0.35,
        'language_confidence': 0.2,
        'corruption_score': 0.1,
        'domain_relevance': 0.1
    },
    'academic': {
        'token_count': 0.2,
        'quality_flag': 0.3,
        'language_confidence': 0.15,
        'corruption_score': 0.05,
        'domain_relevance': 0.15,
        'citation_quality': 0.15
    },
    'code_specific': {
        'token_count': 0.15,
        'quality_flag': 0.25,
        'language_confidence': 0.1,
        'corruption_score': 0.2,  # Higher weight for code corruption detection
        'domain_relevance': 0.2,
        'code_quality': 0.1
    },
    'data_specific': {
        'token_count': 0.1,
        'quality_flag': 0.3,
        'corruption_score': 0.3,  # Critical for data files
        'structure_validity': 0.3
    }
}

# Rebalancing strategy configurations
REBALANCING_STRATEGIES = {
    'quality_weighted': {
        'description': 'Prioritize high-quality documents while maintaining balance',
        'parameters': {
            'quality_threshold': 0.7,
            'weight_by_quality': True,
            'preserve_best': True,
            'max_duplication_ratio': 3.0
        }
    },
    'stratified': {
        'description': 'Maintain proportional representation across strata',
        'parameters': {
            'stratify_by': ['domain', 'file_type'],
            'maintain_proportions': True,
            'min_stratum_size': 10
        }
    },
    'synthetic': {
        'description': 'Generate synthetic documents for underrepresented classes',
        'parameters': {
            'synthesis_methods': ['paraphrase', 'back_translate', 'template_fill'],
            'quality_check_synthetic': True,
            'max_synthetic_ratio': 0.3
        }
    },
    'temporal_aware': {
        'description': 'Balance while considering temporal distribution',
        'parameters': {
            'time_windows': ['monthly', 'quarterly'],
            'recent_weight': 1.5,
            'historical_importance': 0.8
        }
    }
}

class BalancerConfig:
    """Configuration manager for corpus balancer."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        config = {
            'balance_thresholds': DEFAULT_BALANCE_THRESHOLDS.copy(),
            'domain_balance': DOMAIN_BALANCE_CONFIG.copy(),
            'file_type_balance': FILE_TYPE_BALANCE_CONFIG.copy(),
            'quality_weights': QUALITY_WEIGHTS.copy(),
            'strategies': REBALANCING_STRATEGIES.copy()
        }
        
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                
                # Deep merge user config with defaults
                config = self._deep_merge(config, user_config)
                self.logger.info(f"Loaded configuration from {self.config_path}")
                
            except Exception as e:
                self.logger.warning(f"Error loading config from {self.config_path}: {e}")
                self.logger.info("Using default configuration")
        
        return config
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_balance_thresholds(self) -> Dict[str, float]:
        """Get balance threshold configuration."""
        return self._config['balance_thresholds']
    
    def get_domain_config(self, domain: str = None) -> Dict[str, Any]:
        """Get domain-specific configuration."""
        if domain:
            return self._config['domain_balance'].get(domain, {})
        return self._config['domain_balance']
    
    def get_file_type_config(self, file_type: str = None) -> Dict[str, Any]:
        """Get file type configuration."""
        if file_type:
            return self._config['file_type_balance'].get(file_type, {})
        return self._config['file_type_balance']
    
    def get_quality_weights(self, document_type: str = 'standard') -> Dict[str, float]:
        """Get quality weighting scheme for document type."""
        return self._config['quality_weights'].get(document_type, 
                                                  self._config['quality_weights']['standard'])
    
    def get_strategy_config(self, strategy: str) -> Dict[str, Any]:
        """Get configuration for specific rebalancing strategy."""
        return self._config['strategies'].get(strategy, {})
    
    def get_target_distribution(self) -> Dict[str, float]:
        """Calculate target distribution based on domain priorities."""
        domain_config = self._config['domain_balance']
        
        # Calculate target weights
        total_weight = sum(domain.get('target_weight', 0) for domain in domain_config.values())
        
        if total_weight == 0:
            # Equal distribution if no weights specified
            num_domains = len(domain_config)
            return {domain: 1.0/num_domains for domain in domain_config.keys()}
        
        # Normalize weights to sum to 1.0
        return {
            domain: config.get('target_weight', 0) / total_weight 
            for domain, config in domain_config.items()
        }
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check balance thresholds
        thresholds = self._config['balance_thresholds']
        if thresholds['entropy_min'] > thresholds['entropy_target']:
            issues.append("entropy_min should be <= entropy_target")
        
        if thresholds['gini_target'] > thresholds['gini_max']:
            issues.append("gini_target should be <= gini_max")
        
        # Check domain weights sum
        target_dist = self.get_target_distribution()
        weight_sum = sum(target_dist.values())
        if abs(weight_sum - 1.0) > 0.01:
            issues.append(f"Domain target weights sum to {weight_sum:.3f}, should sum to 1.0")
        
        # Check file type ratios
        file_type_config = self._config['file_type_balance']
        total_file_type_ratio = sum(
            config.get('target_ratio', 0) for config in file_type_config.values()
        )
        if abs(total_file_type_ratio - 1.0) > 0.01:
            issues.append(f"File type target ratios sum to {total_file_type_ratio:.3f}, should sum to 1.0")
        
        return issues
    
    def save_config(self, output_path: Path) -> None:
        """Save current configuration to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self._config, f, indent=2)
        
        self.logger.info(f"Configuration saved to {output_path}")

# Utility functions for working with existing codebase
def create_default_config_file(output_path: Path) -> None:
    """Create a default configuration file."""
    config = BalancerConfig()
    config.save_config(output_path)

def validate_corpus_structure(corpus_dir: Path) -> List[str]:
    """Validate that corpus directory has expected structure."""
    issues = []
    
    if not corpus_dir.exists():
        issues.append(f"Corpus directory does not exist: {corpus_dir}")
        return issues
    
    # Check for expected subdirectories
    expected_subdirs = ['_extracted', 'low_quality']
    for subdir in expected_subdirs:
        subdir_path = corpus_dir / subdir
        if not subdir_path.exists():
            issues.append(f"Missing expected subdirectory: {subdir}")
        elif not any(subdir_path.glob('*.json')):
            issues.append(f"No JSON metadata files found in {subdir}")
    
    return issues

def get_corpus_metadata_summary(corpus_dir: Path) -> Dict[str, Any]:
    """Get quick summary of corpus for configuration validation."""
    summary = {
        'total_files': 0,
        'domains_found': set(),
        'file_types_found': set(),
        'directories': {}
    }
    
    for subdir in ['_extracted', 'low_quality']:
        subdir_path = corpus_dir / subdir
        if subdir_path.exists():
            json_files = list(subdir_path.glob('*.json'))
            summary['directories'][subdir] = len(json_files)
            summary['total_files'] += len(json_files)
            
            # Sample a few files to get domains and types
            for json_file in json_files[:10]:  # Sample first 10 files
                try:
                    with open(json_file, 'r') as f:
                        metadata = json.load(f)
                    
                    if 'domain' in metadata:
                        summary['domains_found'].add(metadata['domain'])
                    if 'file_type' in metadata:
                        summary['file_types_found'].add(metadata['file_type'])
                        
                except Exception:
                    continue
    
    # Convert sets to lists for JSON serialization
    summary['domains_found'] = list(summary['domains_found'])
    summary['file_types_found'] = list(summary['file_types_found'])
    
    return summary

# Example configuration file creation script
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Corpus Balancer Configuration Manager')
    parser.add_argument('--create-default', type=str, help='Create default config file at path')
    parser.add_argument('--validate-corpus', type=str, help='Validate corpus structure at path')
    parser.add_argument('--corpus-summary', type=str, help='Generate corpus summary for path')
    
    args = parser.parse_args()
    
    if args.create_default:
        create_default_config_file(Path(args.create_default))
        print(f"Default configuration created at {args.create_default}")
    
    if args.validate_corpus:
        issues = validate_corpus_structure(Path(args.validate_corpus))
        if issues:
            print("Corpus structure issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("Corpus structure is valid")
    
    if args.corpus_summary:
        summary = get_corpus_metadata_summary(Path(args.corpus_summary))
        print("Corpus Summary:")
        print(json.dumps(summary, indent=2))