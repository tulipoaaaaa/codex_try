# DEPRECATED: This file belongs to the legacy CryptoFinanceCorpusBuilder package and should not be used in new modules.
import unittest
import tempfile
import shutil
import os
import json
from pathlib import Path

from processors.text_extractor import TextExtractor
from processors.domain_classifier import DomainClassifier

class TestTextExtractor(unittest.TestCase):
    """Test text extraction functionality"""
    
    def setUp(self):
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp()
        # Create test files
        self.create_test_files()
        # Initialize extractor
        self.extractor = TextExtractor()
    
    def tearDown(self):
        # Clean up
        shutil.rmtree(self.test_dir)
    
    def create_test_files(self):
        """Create test files for extraction"""
        # Create a text file
        with open(os.path.join(self.test_dir, "test.txt"), "w") as f:
            f.write("This is a test document.\nIt has multiple lines.\nAnd contains crypto trading content.")
        
        # Create a markdown file
        with open(os.path.join(self.test_dir, "test.md"), "w") as f:
            f.write("# Test Document\n\nThis is a *markdown* document about **cryptocurrency trading**.")
        
        # Create a simple JSON file that simulates a notebook
        notebook = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "source": ["# Notebook Title", "This is a test notebook."]
                },
                {
                    "cell_type": "code",
                    "source": ["import pandas as pd", "# Analysis code"]
                }
            ],
            "metadata": {"kernelspec": {"language": "python"}}
        }
        with open(os.path.join(self.test_dir, "test.ipynb"), "w") as f:
            json.dump(notebook, f)
    
    def test_extract_text(self):
        """Test extraction from text file"""
        result = self.extractor.extract(os.path.join(self.test_dir, "test.txt"))
        self.assertIsNotNone(result)
        self.assertIn("text", result)
        self.assertEqual(result["file_type"], "text")
        self.assertIn("crypto trading", result["text"])
    
    def test_extract_markdown(self):
        """Test extraction from markdown file"""
        result = self.extractor.extract(os.path.join(self.test_dir, "test.md"))
        self.assertIsNotNone(result)
        self.assertIn("text", result)
        self.assertEqual(result["file_type"], "markdown")
        self.assertIn("cryptocurrency trading", result["text"])
    
    def test_extract_notebook(self):
        """Test extraction from notebook file"""
        result = self.extractor.extract(os.path.join(self.test_dir, "test.ipynb"))
        self.assertIsNotNone(result)
        self.assertIn("text", result)
        self.assertEqual(result["file_type"], "notebook")
        self.assertIn("Notebook Title", result["text"])
        self.assertIn("import pandas", result["text"])

class TestDomainClassifier(unittest.TestCase):
    """Test domain classification functionality"""
    
    def setUp(self):
        # Create test domain config
        self.test_domains = {
            "crypto_derivatives": {
                "search_terms": ["cryptocurrency derivatives", "bitcoin futures"]
            },
            "high_frequency_trading": {
                "search_terms": ["high frequency trading", "algorithmic trading"]
            }
        }
        # Initialize classifier with test domains
        self.classifier = DomainClassifier(self.test_domains)
    
    def test_domain_classification(self):
        """Test basic classification"""
        # Text clearly about crypto derivatives
        text = "Bitcoin futures contracts are derivative products that allow trading bitcoin price movements."
        result = self.classifier.classify(text)
        self.assertEqual(result["domain"], "crypto_derivatives")
        
        # Text clearly about high frequency trading
        text = "High frequency trading algorithms execute thousands of orders per second."
        result = self.classifier.classify(text)
        self.assertEqual(result["domain"], "high_frequency_trading")
        
        # Text without clear domain indicators
        text = "Financial markets operate based on supply and demand principles."
        result = self.classifier.classify(text)
        # We don't assert the exact domain here, just that there is one
        self.assertIn("domain", result)
        
    def test_title_weighting(self):
        """Test that title is weighted higher in classification"""
        # Text about HFT but title about derivatives
        text = "Algorithms execute trades at high speeds in milliseconds."
        title = "Bitcoin Futures Trading Guide"
        result = self.classifier.classify(text, title)
        self.assertEqual(result["domain"], "crypto_derivatives")

# Run tests if script is executed directly
if __name__ == "__main__":
    unittest.main() 