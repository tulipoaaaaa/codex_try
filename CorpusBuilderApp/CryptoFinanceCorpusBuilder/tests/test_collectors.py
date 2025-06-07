# DEPRECATED: This file belongs to the legacy CryptoFinanceCorpusBuilder package and should not be used in new modules.
import unittest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import collectors
from sources.api_collector import ApiCollector
from sources.web_collector import WebCollector
from sources.repo_collector import RepoCollector
from sources.specific_collectors.arxiv_collector import ArxivCollector

class TestBaseCollectors(unittest.TestCase):
    """Test basic collector functionality"""
    
    def setUp(self):
        # Create temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_api_collector_initialization(self):
        """Test API collector initialization"""
        collector = ApiCollector(self.test_dir, api_key="test_key", api_base_url="https://api.example.com")
        self.assertEqual(collector.api_key, "test_key")
        self.assertEqual(collector.api_base_url, "https://api.example.com")
        self.assertTrue(Path(self.test_dir).exists())
    
    @patch('sources.api_collector.ApiCollector.api_request')
    def test_api_request(self, mock_request):
        """Test API request method"""
        mock_request.return_value = {"key": "value"}
        
        collector = ApiCollector(self.test_dir, api_key="test_key", api_base_url="https://api.example.com")
        result = collector.api_request("test_endpoint")
        
        mock_request.assert_called_once()
        self.assertEqual(result, {"key": "value"})
    
    @patch('sources.web_collector.WebCollector.fetch_page')
    def test_web_collector_get_soup(self, mock_fetch):
        """Test web collector soup generation"""
        mock_fetch.return_value = "<html><body><h1>Test Page</h1></body></html>"
        
        collector = WebCollector(self.test_dir, base_url="https://example.com")
        soup = collector.get_soup("https://example.com/page")
        
        mock_fetch.assert_called_once()
        self.assertIsNotNone(soup)
        self.assertEqual(soup.h1.text, "Test Page")

class TestArxivCollector(unittest.TestCase):
    """Test ArxivCollector functionality"""
    
    def setUp(self):
        # Create temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        # Create a collector instance
        self.collector = ArxivCollector(self.test_dir)
    
    def tearDown(self):
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    @patch('sources.specific_collectors.arxiv_collector.ArxivCollector._execute_search')
    def test_search_by_term(self, mock_execute):
        """Test search by term"""
        mock_execute.return_value = [{"title": "Test Paper", "arxiv_id": "1234.5678"}]
        
        results = self.collector._search_by_term("cryptocurrency trading")
        
        mock_execute.assert_called_once()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Test Paper")
    
    @patch('sources.specific_collectors.arxiv_collector.ArxivCollector._parse_response')
    @patch('sources.api_collector.ApiCollector.api_request')
    def test_execute_search(self, mock_request, mock_parse):
        """Test execute search"""
        mock_request.return_value = "XML response"
        mock_parse.return_value = [{"title": "Test Paper"}]
        
        results = self.collector._execute_search("q-fin.CP")
        
        mock_request.assert_called_once()
        mock_parse.assert_called_once_with("XML response")
        self.assertEqual(results, [{"title": "Test Paper"}]) 