"""
Domain Utilities Module
Purpose: Provides domain classification and validation for extractors
Used by: PDF and Non-PDF extractors

This module provides a wrapper around domain configuration with fallback mechanisms.
It maintains backward compatibility while allowing for future configuration improvements.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import logging
logger = logging.getLogger(__name__)

# Try to load domains from config, else fallback
try:
    from shared_tools.config.domain_config import DOMAINS as _CONFIG_DOMAINS
except ImportError:
    _CONFIG_DOMAINS: Optional[Dict[str, Dict[str, Any]]] = None

try:
    from shared_tools.project_config import ProjectConfig
except ImportError:
    ProjectConfig = None

HARDCODED_DOMAINS = [
    "crypto_derivatives", "high_frequency_trading", "market_microstructure", "risk_management",
    "decentralized_finance", "portfolio_construction", "valuation_models", "regulation_compliance"
]

# For keyword fallback
DOMAIN_KEYWORDS = {
    "risk_management": ["risk", "var", "hedg"],
    "crypto_derivatives": ["deriv", "option", "future"],
    # Add more as needed
}

class DomainKeywordHelper:
    """Configuration wrapper for domain settings with fallback mechanisms."""
    
    def __init__(self, config_path: Optional[Union[str, Any]] = None):
        self.config_path = config_path
        self.project_config = None
        if ProjectConfig is not None and isinstance(config_path, ProjectConfig):
            self.project_config = config_path
            self.config_path = None
        self.domains = self._load_domains()
        self.keywords = self._load_keywords()
    
    def _load_domains(self) -> Dict[str, Dict[str, Any]]:
        """Load domains from config file or fallback to hardcoded."""
        # Try project config first
        if self.project_config and hasattr(self.project_config, 'domains'):
            return self.project_config.domains
        
        # Try config file
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('domains', {})
            except Exception as e:
                logger.warning(f"Warning: Could not load domains from {self.config_path}: {e}")
        
        # Fallback to module-level config
        if _CONFIG_DOMAINS is not None:
            return _CONFIG_DOMAINS
        
        # Fallback to hardcoded domains
        return {domain: {"allocation": 0.0} for domain in HARDCODED_DOMAINS}
    
    def _load_keywords(self) -> Dict[str, List[str]]:
        """Load domain keywords from config or fallback to hardcoded."""
        # Try project config first
        if self.project_config and hasattr(self.project_config, 'domain_keywords'):
            return self.project_config.domain_keywords
        
        # Try config file
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('keywords', DOMAIN_KEYWORDS)
            except Exception as e:
                logger.warning(f"Warning: Could not load keywords from {self.config_path}: {e}")
        return DOMAIN_KEYWORDS
    
    def get_valid_domains(self) -> List[str]:
        """Get list of valid domains."""
        return list(self.domains.keys())
    
    def get_domain_keywords(self) -> Dict[str, List[str]]:
        """Get domain keywords mapping."""
        return self.keywords

# Initialize default config
_domain_helper = DomainKeywordHelper()

# Keep existing functions as wrappers for backward compatibility
def get_valid_domains():
    """Get list of valid domains (backward compatible)."""
    return _domain_helper.get_valid_domains()

def get_domain_for_file(file_path, text=None, debug=False):
    """
    Robust domain assignment: parent dir, partial match, all path parts, keyword fallback. Debuggable.
    """
    valid_domains = [d.lower() for d in get_valid_domains()]
    # Normalize path
    if isinstance(file_path, Path):
        file_path_str = str(file_path)
    else:
        file_path_str = file_path
    file_path_str = os.path.normpath(file_path_str)
    if debug:
        logger.debug(f"[DEBUG] get_domain_for_file called with:")
        logger.info(f"  file_path: {file_path_str}")
        logger.info(f"  valid_domains: {valid_domains}")
    # 1. Parent directory (lowercased)
    parent_dir = os.path.basename(os.path.dirname(file_path_str)).lower()
    if debug:
        logger.info(f"  Parent directory (lowercased): {parent_dir}")
    if parent_dir in valid_domains:
        if debug:
            logger.info(f"  ✅ Domain matched from parent directory: {parent_dir}")
        assigned_domain = parent_dir
        if debug:
            logger.info(f"[FINAL] Path: {file_path_str}, Domains: {valid_domains}, Assigned: {assigned_domain}")
        assert isinstance(assigned_domain, str), "Assigned domain is not a string"
        return assigned_domain
    # 2. Partial match in parent directory
    for domain in valid_domains:
        if domain in parent_dir:
            if debug:
                logger.info(f"  ✅ Domain matched partially in parent directory: {domain}")
            assigned_domain = domain
            if debug:
                logger.info(f"[FINAL] Path: {file_path_str}, Domains: {valid_domains}, Assigned: {assigned_domain}")
            assert isinstance(assigned_domain, str), "Assigned domain is not a string"
            return assigned_domain
    # 3. All path components (lowercased)
    path_parts = file_path_str.replace('\\', '/').split('/')
    path_parts = [p.lower() for p in path_parts]
    if debug:
        logger.info(f"  Path parts: {path_parts}")
    for part in path_parts:
        if part in valid_domains:
            if debug:
                logger.info(f"  ✅ Domain matched in path part: {part}")
            assigned_domain = part
            if debug:
                logger.info(f"[FINAL] Path: {file_path_str}, Domains: {valid_domains}, Assigned: {assigned_domain}")
            assert isinstance(assigned_domain, str), "Assigned domain is not a string"
            return assigned_domain
        for domain in valid_domains:
            if domain in part:
                if debug:
                    logger.info(f"  ✅ Domain matched partially in path part: {domain} in {part}")
                assigned_domain = domain
                if debug:
                    logger.info(f"[FINAL] Path: {file_path_str}, Domains: {valid_domains}, Assigned: {assigned_domain}")
                assert isinstance(assigned_domain, str), "Assigned domain is not a string"
                return assigned_domain
    # 4. Keyword matching (filename/text)
    fname = os.path.basename(file_path_str).lower()
    for dom, keywords in _domain_helper.get_domain_keywords().items():
        for kw in keywords:
            if kw in fname:
                if debug:
                    logger.info(f"  ✅ Domain keyword match in filename: {dom} via {kw}")
                assigned_domain = dom
                if debug:
                    logger.info(f"[FINAL] Path: {file_path_str}, Domains: {valid_domains}, Assigned: {assigned_domain}")
                assert isinstance(assigned_domain, str), "Assigned domain is not a string"
                return assigned_domain
    if text:
        text_lower = text.lower()
        for dom, keywords in _domain_helper.get_domain_keywords().items():
            for kw in keywords:
                if kw in text_lower:
                    if debug:
                        logger.info(f"  ✅ Domain keyword match in text: {dom} via {kw}")
                    assigned_domain = dom
                    if debug:
                        logger.info(f"[FINAL] Path: {file_path_str}, Domains: {valid_domains}, Assigned: {assigned_domain}")
                    assert isinstance(assigned_domain, str), "Assigned domain is not a string"
                    return assigned_domain
    if debug:
        logger.warning("  ❌ No domain match found, returning 'unknown'")
        logger.info(f"[FINAL] Path: {file_path_str}, Domains: {valid_domains}, Assigned: unknown")
    assigned_domain = "unknown"
    assert isinstance(assigned_domain, str), "Assigned domain is not a string"
    return assigned_domain 
