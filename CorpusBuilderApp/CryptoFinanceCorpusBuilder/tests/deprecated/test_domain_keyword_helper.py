"""
Test suite for domain configuration wrapper.
Tests both the DomainKeywordHelper class and backward compatibility functions.
"""
# DEPRECATED: This file belongs to the legacy CryptoFinanceCorpusBuilder package and should not be used in new modules.

import os
import sys
import unittest
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from CryptoFinanceCorpusBuilder.utils.domain_utils import (
    DomainKeywordHelper,
    get_valid_domains,
    get_domain_for_file
)

class TestDomainKeywordHelper(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.test_corpus_dir = Path(project_root) / "data" / "test_corpus_sample"
        self._create_test_corpus()
        
    def tearDown(self):
        """Clean up test environment."""
        if self.test_corpus_dir.exists():
            for file in self.test_corpus_dir.rglob("*"):
                if file.is_file():
                    file.unlink()
            for dir in reversed(list(self.test_corpus_dir.rglob("*"))):
                if dir.is_dir():
                    dir.rmdir()
            self.test_corpus_dir.rmdir()

    def _create_test_corpus(self):
        """Create test corpus structure."""
        domains = ["crypto_derivatives", "high_frequency_trading", "market_microstructure"]
        for domain in domains:
            domain_dir = self.test_corpus_dir / domain
            domain_dir.mkdir(parents=True, exist_ok=True)
            test_file = domain_dir / "test_file.txt"
            test_file.write_text(f"Test content for {domain}")

    def test_default_config(self):
        """Test default configuration loading."""
        config = DomainKeywordHelper()
        domains = config.get_valid_domains()
        self.assertIsInstance(domains, list)
        self.assertTrue(len(domains) > 0)
        self.assertTrue(all(isinstance(d, str) for d in domains))

    def test_backward_compatibility(self):
        """Test backward compatibility functions."""
        # Test get_valid_domains
        domains = get_valid_domains()
        self.assertIsInstance(domains, list)
        self.assertTrue(len(domains) > 0)

        # Test get_domain_for_file with parent directory
        test_file = self.test_corpus_dir / "crypto_derivatives" / "test_file.txt"
        domain = get_domain_for_file(test_file)
        self.assertEqual(domain, "crypto_derivatives")

        # Test get_domain_for_file with partial match
        test_file = self.test_corpus_dir / "high_frequency_trading" / "test_file.txt"
        domain = get_domain_for_file(test_file)
        self.assertEqual(domain, "high_frequency_trading")

    def test_domain_keywords(self):
        """Test domain keyword functionality."""
        config = DomainKeywordHelper()
        keywords = config.get_domain_keywords()
        self.assertIsInstance(keywords, dict)
        self.assertTrue(len(keywords) > 0)

    def test_file_domain_detection(self):
        """Test domain detection from file paths."""
        # Test exact match
        test_file = self.test_corpus_dir / "market_microstructure" / "test_file.txt"
        domain = get_domain_for_file(test_file)
        self.assertEqual(domain, "market_microstructure")

        # Test unknown domain
        test_file = self.test_corpus_dir / "unknown_domain" / "test_file.txt"
        domain = get_domain_for_file(test_file)
        self.assertEqual(domain, "unknown")

if __name__ == "__main__":
    unittest.main() 