import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

from .language_confidence_detector import detect_language_confidence
from .corruption_detector import detect_corruption
from .machine_translation_detector import detect_machine_translation

# Default thresholds
DEFAULT_THRESHOLDS = {
    'min_tokens': 100,
    'low_quality_tokens': 500,
    'chunk_size': 10000,
    'language_confidence': 0.8,
    'corruption': 0.3,
    'machine_translation': 0.7,
    'relevance': 30
}

# Scientific paper specific thresholds
SCIENTIFIC_PAPER_THRESHOLDS = {
    'min_tokens': 50,  # Lower minimum for scientific papers
    'low_quality_tokens': 50,  # Much lower threshold for scientific papers
    'chunk_size': 10000,  # Keep chunk size the same
    'quality_relaxations': {
        'reference_density': 0.3,  # Allow up to 30% references
        'citation_density': 0.2,   # Allow up to 20% citations
        'formula_density': 0.4     # Allow up to 40% formulas
    }
}

# Domain-specific thresholds
DOMAIN_THRESHOLDS = {
    'scientific_papers': SCIENTIFIC_PAPER_THRESHOLDS,
    'trading_strategies': {
        'min_tokens': 200,
        'low_quality_tokens': 1000,
        'chunk_size': 8000
    },
    'market_analysis': {
        'min_tokens': 150,
        'low_quality_tokens': 800,
        'chunk_size': 12000
    }
}

class QualityControlService:
    """Centralized service for content quality checks with domain-aware thresholds."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the quality control service.
        
        Args:
            config_path: Optional path to a JSON config file with custom thresholds
        """
        self.config = self._load_config(config_path)
        self.thresholds = self._get_thresholds()
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}
        
    def _get_thresholds(self) -> Dict[str, Any]:
        """Get thresholds from config or use defaults."""
        return self.config.get('thresholds', DEFAULT_THRESHOLDS)
        
    def detect_scientific_paper(self, text: str, metadata: Dict[str, Any]) -> bool:
        """Detect if a document is a scientific paper.
        
        Args:
            text: The document text
            metadata: Document metadata
            
        Returns:
            bool: True if document appears to be a scientific paper
        """
        indicators = [
            'doi' in metadata.get('keywords', []),
            'references' in text.lower(),
            'abstract' in text.lower(),
            'introduction' in text.lower(),
            'conclusion' in text.lower(),
            'references' in text.lower(),
            'bibliography' in text.lower()
        ]
        return sum(indicators) >= 3  # If 3 or more indicators present
        
    def check_quality(self, text: str, metadata: Dict[str, Any], domain: Optional[str] = None) -> Dict[str, Any]:
        """Run all quality checks on the content.
        
        Args:
            text: The document text
            metadata: Document metadata
            domain: Optional domain name for domain-specific thresholds
            
        Returns:
            Dict containing quality check results and flags
        """
        # Detect if this is a scientific paper
        is_scientific = self.detect_scientific_paper(text, metadata)
        
        # Get appropriate thresholds
        if is_scientific:
            thresholds = SCIENTIFIC_PAPER_THRESHOLDS
        elif domain and domain in DOMAIN_THRESHOLDS:
            thresholds = DOMAIN_THRESHOLDS[domain]
        else:
            thresholds = self.thresholds
            
        # Run quality checks
        quality_checks: Dict[str, Any] = {
            'language_confidence': detect_language_confidence(text),
            'corruption': detect_corruption(text),
            'machine_translation': detect_machine_translation(text),
            'is_scientific_paper': is_scientific,
            'thresholds_used': thresholds
        }
        
        # Add quality flags
        quality_checks['quality_flags'] = {
            'low_quality': (
                quality_checks['language_confidence'] < thresholds['language_confidence'] or
                quality_checks['corruption'] > thresholds['corruption'] or
                quality_checks['machine_translation'] > thresholds['machine_translation']
            ),
            'scientific_paper': is_scientific,
            'domain_specific': domain is not None
        }
        
        return quality_checks
        
    def save_quality_report(self, quality_checks: Dict[str, Any], output_dir: str):
        """Save quality check results to a JSON file.
        
        Args:
            quality_checks: Results from check_quality
            output_dir: Directory to save the report
        """
        output_path = Path(output_dir) / 'quality_report.json'
        with open(output_path, 'w') as f:
            json.dump(quality_checks, f, indent=2) 