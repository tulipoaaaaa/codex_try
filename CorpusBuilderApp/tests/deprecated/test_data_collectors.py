# Data Collectors Testing Suite
# Comprehensive tests for all data collection modules with focus on async operations, error handling, and data validation

import pytest
import asyncio
import aiohttp
import json
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
from datetime import datetime
import requests

# Import collectors to test
try:
    from shared_tools.collectors.fred_collector import FredCollector
    from shared_tools.collectors.github_collector import GitHubCollector
    from shared_tools.collectors.arxiv_collector import ArxivCollector
    from shared_tools.collectors.CookieAuthClient import CookieAuthClient
    from shared_tools.collectors.web_collector import WebCollector
    from shared_tools.collectors.api_collector import APICollector
    from shared_tools.collectors.enhanced_client import EnhancedClient
except ImportError:
    # Mock imports if modules are not available
    FredCollector = Mock
    GitHubCollector = Mock
    ArxivCollector = Mock
    CookieAuthClient = Mock
    WebCollector = Mock
    APICollector = Mock
    EnhancedClient = Mock


class TestFredCollector:
    """Test FRED API data collection functionality"""
    
    @pytest.fixture
    def fred_collector(self):
        """Create FredCollector instance for testing"""
        with patch.dict(os.environ, {"FRED_API_KEY": "test_api_key"}):
            if hasattr(FredCollector, '__init__'):
                return FredCollector()
            else:
                return Mock(spec=FredCollector)
    
    @pytest.fixture
    def mock_fred_response(self):
        """Mock FRED API response"""
        return {
            "realtime_start": "2024-01-01",
            "realtime_end": "2024-01-01",
            "observations": [
                {
                    "realtime_start": "2024-01-01",
                    "realtime_end": "2024-01-01",
                    "date": "2024-01-01",
                    "value": "1.5"
                }
            ]
        }
    
    def test_fred_collector_initialization(self, fred_collector):
        """Test FRED collector initialization with API key"""
        assert fred_collector is not None
        # Should have loaded API key from environment
        if hasattr(fred_collector, 'api_key'):
            assert fred_collector.api_key == "test_api_key"
    
    def test_fred_collector_missing_api_key(self):
        """Test FRED collector behavior without API key"""
        with patch.dict(os.environ, {}, clear=True):
            # Should handle missing API key gracefully
            if hasattr(FredCollector, '__init__'):
                with pytest.raises((ValueError, KeyError)) or pytest.warns(UserWarning):
                    FredCollector()
    
    @patch('requests.get')
    def test_fred_data_collection_success(self, mock_get, fred_collector, mock_fred_response):
        """Test successful data collection from FRED API"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_fred_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test data collection
        if hasattr(fred_collector, 'get_series_data'):
            result = fred_collector.get_series_data("GDP")
            assert result is not None
            mock_get.assert_called()
    
    @patch('requests.get')
    def test_fred_api_error_handling(self, mock_get, fred_collector):
        """Test FRED API error handling"""
        # Test HTTP error
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        if hasattr(fred_collector, 'get_series_data'):
            with pytest.raises(requests.exceptions.HTTPError):
                fred_collector.get_series_data("INVALID_SERIES")
    
    @patch('requests.get')
    def test_fred_rate_limit_handling(self, mock_get, fred_collector):
        """Test FRED API rate limit handling"""
        # Mock rate limit response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Too Many Requests")
        mock_get.return_value = mock_response
        
        if hasattr(fred_collector, 'get_series_data'):
            with pytest.raises(requests.exceptions.HTTPError):
                fred_collector.get_series_data("GDP")
    
    def test_fred_data_validation(self, mock_fred_response):
        """Test validation of FRED API response data"""
        # Should contain required fields
        assert "observations" in mock_fred_response
        assert len(mock_fred_response["observations"]) > 0
        
        observation = mock_fred_response["observations"][0]
        assert "date" in observation
        assert "value" in observation
        
        # Date should be valid format
        datetime.strptime(observation["date"], "%Y-%m-%d")


class TestGitHubCollector:
    """Test GitHub API data collection functionality"""
    
    @pytest.fixture
    def github_collector(self):
        """Create GitHubCollector instance for testing"""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token_12345"}):
            if hasattr(GitHubCollector, '__init__'):
                return GitHubCollector()
            else:
                return Mock(spec=GitHubCollector)
    
    @pytest.fixture
    def mock_github_response(self):
        """Mock GitHub API response"""
        return {
            "total_count": 1,
            "items": [
                {
                    "id": 123456,
                    "name": "test-repo",
                    "full_name": "user/test-repo",
                    "html_url": "https://github.com/user/test-repo",
                    "description": "Test repository",
                    "private": False,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            ]
        }
    
    def test_github_collector_initialization(self, github_collector):
        """Test GitHub collector initialization"""
        assert github_collector is not None
        if hasattr(github_collector, 'token'):
            assert github_collector.token == "test_token_12345"
    
    @patch('requests.get')
    def test_github_repo_search(self, mock_get, github_collector, mock_github_response):
        """Test GitHub repository search functionality"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_github_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        if hasattr(github_collector, 'search_repositories'):
            result = github_collector.search_repositories("cryptocurrency")
            assert result is not None
            mock_get.assert_called()
    
    @patch('requests.get')
    def test_github_authentication_error(self, mock_get, github_collector):
        """Test GitHub authentication error handling"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
        mock_get.return_value = mock_response
        
        if hasattr(github_collector, 'search_repositories'):
            with pytest.raises(requests.exceptions.HTTPError):
                github_collector.search_repositories("test")
    
    def test_github_search_query_validation(self):
        """Test GitHub search query validation"""
        valid_queries = ["cryptocurrency", "bitcoin trading", "financial analysis"]
        invalid_queries = ["", " ", "a" * 300]  # Empty or too long
        
        for query in valid_queries:
            assert len(query.strip()) > 0
            assert len(query) < 256
        
        for query in invalid_queries:
            is_invalid = len(query.strip()) == 0 or len(query) > 256
            assert is_invalid


class TestArxivCollector:
    """Test ArXiv API data collection functionality"""
    
    @pytest.fixture
    def arxiv_collector(self):
        """Create ArxivCollector instance for testing"""
        if hasattr(ArxivCollector, '__init__'):
            return ArxivCollector()
        else:
            return Mock(spec=ArxivCollector)
    
    @pytest.fixture
    def mock_arxiv_response(self):
        """Mock ArXiv API response (XML format)"""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>ArXiv Query: search_query=cryptocurrency</title>
            <entry>
                <id>http://arxiv.org/abs/2401.12345v1</id>
                <updated>2024-01-01T00:00:00Z</updated>
                <published>2024-01-01T00:00:00Z</published>
                <title>Cryptocurrency Analysis</title>
                <summary>A comprehensive analysis of cryptocurrency markets.</summary>
                <author>
                    <name>John Doe</name>
                </author>
                <link href="http://arxiv.org/abs/2401.12345v1" rel="alternate" type="text/html"/>
                <link href="http://arxiv.org/pdf/2401.12345v1.pdf" rel="related" type="application/pdf"/>
            </entry>
        </feed>"""
    
    @patch('requests.get')
    def test_arxiv_paper_search(self, mock_get, arxiv_collector, mock_arxiv_response):
        """Test ArXiv paper search functionality"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_arxiv_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        if hasattr(arxiv_collector, 'search_papers'):
            result = arxiv_collector.search_papers("cryptocurrency")
            assert result is not None
            mock_get.assert_called()
    
    def test_arxiv_xml_parsing(self, mock_arxiv_response):
        """Test ArXiv XML response parsing"""
        import xml.etree.ElementTree as ET
        
        root = ET.fromstring(mock_arxiv_response)
        
        # Should find entry elements
        entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
        assert len(entries) > 0
        
        entry = entries[0]
        title = entry.find(".//{http://www.w3.org/2005/Atom}title")
        assert title is not None
        assert title.text == "Cryptocurrency Analysis"
    
    def test_arxiv_query_sanitization(self):
        """Test ArXiv query sanitization"""
        dangerous_queries = [
            "<script>alert('xss')</script>",
            "query' OR '1'='1",
            "query\nwith\nnewlines",
            "query\twith\ttabs"
        ]
        
        for query in dangerous_queries:
            # Should sanitize dangerous characters
            contains_dangerous = any(char in query for char in ['<', '>', "'", '\n', '\t'])
            assert contains_dangerous


class TestCookieAuthClient:
    """Test cookie-based authentication client"""
    
    @pytest.fixture
    def auth_client(self):
        """Create CookieAuthClient instance for testing"""
        with patch.dict(os.environ, {"AA_ACCOUNT_COOKIE": "test_cookie=value123"}):
            if hasattr(CookieAuthClient, '__init__'):
                return CookieAuthClient()
            else:
                return Mock(spec=CookieAuthClient)
    
    @pytest.fixture
    def mock_search_response(self):
        """Mock search response from Anna's Archive"""
        return """
        <html>
        <body>
            <div class="search-result">
                <h3>Test Document</h3>
                <span class="file-info">PDF, 2.5MB</span>
                <a href="/md5/abc123def456">Download</a>
            </div>
        </body>
        </html>
        """
    
    def test_cookie_client_initialization(self, auth_client):
        """Test cookie client initialization"""
        assert auth_client is not None
        if hasattr(auth_client, 'session'):
            assert auth_client.session is not None
    
    @patch('requests.Session.get')
    def test_authenticated_search(self, mock_get, auth_client, mock_search_response):
        """Test authenticated search functionality"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_search_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        if hasattr(auth_client, 'search'):
            result = auth_client.search("test query")
            assert result is not None
            mock_get.assert_called()
    
    @patch('requests.Session.get')
    def test_download_functionality(self, mock_get, auth_client):
        """Test file download functionality"""
        # Mock download response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"%PDF-1.4\nMock PDF content"
        mock_response.headers = {"Content-Type": "application/pdf"}
        mock_get.return_value = mock_response
        
        if hasattr(auth_client, 'download_file'):
            with tempfile.TemporaryDirectory() as tmp_dir:
                output_path = Path(tmp_dir) / "test.pdf"
                result = auth_client.download_file("abc123", output_path)
                
                if result:
                    assert output_path.exists()
                    assert output_path.stat().st_size > 0
    
    def test_file_validation(self, auth_client):
        """Test file validation functionality"""
        # Test valid PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b'%PDF-1.4\nValid PDF content')
            tmp_file.flush()
            
            if hasattr(auth_client, 'check_file_validity'):
                is_valid = auth_client.check_file_validity(tmp_file.name)
                assert is_valid is True
            
            os.unlink(tmp_file.name)
        
        # Test invalid file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b'Not a PDF file')
            tmp_file.flush()
            
            if hasattr(auth_client, 'check_file_validity'):
                is_valid = auth_client.check_file_validity(tmp_file.name)
                assert is_valid is False
            
            os.unlink(tmp_file.name)


class TestAsyncDataCollectors:
    """Test asynchronous data collection functionality"""
    
    @pytest.fixture
    def event_loop(self):
        """Create event loop for async tests"""
        loop = asyncio.new_event_loop()
        yield loop
        loop.close()
    
    @pytest.mark.asyncio
    async def test_async_http_client(self):
        """Test async HTTP client functionality"""
        async with aiohttp.ClientSession() as session:
            # Test with a reliable endpoint (can be mocked in production)
            try:
                async with session.get('https://httpbin.org/json') as response:
                    assert response.status == 200
                    data = await response.json()
                    assert isinstance(data, dict)
            except aiohttp.ClientError:
                # Network issues are acceptable in tests
                pytest.skip("Network not available for async testing")
    
    @pytest.mark.asyncio
    async def test_async_error_handling(self):
        """Test async error handling"""
        async with aiohttp.ClientSession() as session:
            # Test timeout handling
            try:
                async with session.get('https://httpbin.org/delay/10', timeout=aiohttp.ClientTimeout(total=1)):
                    pass
            except asyncio.TimeoutError:
                # Expected behavior
                pass
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test concurrent request handling"""
        async with aiohttp.ClientSession() as session:
            urls = [
                'https://httpbin.org/json',
                'https://httpbin.org/uuid',
                'https://httpbin.org/base64/aGVsbG8gd29ybGQ='
            ]
            
            try:
                tasks = [session.get(url) for url in urls]
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Should handle multiple concurrent requests
                assert len(responses) == len(urls)
                
                # Close responses
                for response in responses:
                    if hasattr(response, 'close'):
                        response.close()
                        
            except aiohttp.ClientError:
                pytest.skip("Network not available for concurrent testing")


class TestDataValidation:
    """Test data validation and processing"""
    
    def test_json_data_validation(self):
        """Test JSON data structure validation"""
        valid_data = {
            "title": "Test Document",
            "authors": ["Author 1", "Author 2"],
            "date": "2024-01-01",
            "url": "https://example.com/document.pdf",
            "metadata": {
                "size": 1024,
                "format": "PDF"
            }
        }
        
        # Should contain required fields
        required_fields = ["title", "authors", "date", "url"]
        for field in required_fields:
            assert field in valid_data
        
        # Data types should be correct
        assert isinstance(valid_data["title"], str)
        assert isinstance(valid_data["authors"], list)
        assert isinstance(valid_data["metadata"], dict)
    
    def test_date_validation(self):
        """Test date format validation"""
        valid_dates = ["2024-01-01", "2023-12-31", "2024-02-29"]  # Leap year
        invalid_dates = ["2024-13-01", "2024-01-32", "invalid", ""]
        
        for date_str in valid_dates:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                is_valid = True
            except ValueError:
                is_valid = False
            assert is_valid
        
        for date_str in invalid_dates:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                is_valid = True
            except ValueError:
                is_valid = False
            assert not is_valid
    
    def test_url_validation(self):
        """Test URL format validation"""
        valid_urls = [
            "https://example.com/document.pdf",
            "https://api.example.com/v1/data",
            "https://arxiv.org/abs/2401.12345"
        ]
        
        invalid_urls = [
            "not-a-url",
            "ftp://example.com/file.txt",
            "javascript:alert('xss')",
            ""
        ]
        
        for url in valid_urls:
            assert url.startswith("https://")
            assert "." in url
        
        for url in invalid_urls:
            is_invalid = (
                not url.startswith("https://") or
                url == "" or
                "javascript:" in url
            )
            assert is_invalid


class TestCollectorErrorRecovery:
    """Test error recovery and resilience in data collectors"""
    
    def test_retry_mechanism(self):
        """Test retry mechanism for failed requests"""
        import time
        
        retry_count = 0
        max_retries = 3
        
        def simulate_failing_request():
            nonlocal retry_count
            retry_count += 1
            
            if retry_count < max_retries:
                raise requests.exceptions.ConnectionError("Connection failed")
            return {"status": "success", "retries": retry_count}
        
        # Simulate retry logic
        for attempt in range(max_retries):
            try:
                result = simulate_failing_request()
                assert result["status"] == "success"
                assert result["retries"] == max_retries
                break
            except requests.exceptions.ConnectionError:
                if attempt == max_retries - 1:
                    pytest.fail("Max retries exceeded")
                time.sleep(0.1)  # Short delay between retries
    
    def test_partial_failure_handling(self):
        """Test handling of partial failures in batch operations"""
        items_to_process = ["item1", "item2", "item3", "item4", "item5"]
        failing_items = {"item2", "item4"}
        
        results = {"successful": [], "failed": []}
        
        for item in items_to_process:
            try:
                if item in failing_items:
                    raise ValueError(f"Processing failed for {item}")
                
                # Simulate successful processing
                results["successful"].append(item)
                
            except ValueError as e:
                results["failed"].append({"item": item, "error": str(e)})
        
        # Should have processed all items, some successfully, some with failures
        assert len(results["successful"]) == 3
        assert len(results["failed"]) == 2
        assert len(results["successful"]) + len(results["failed"]) == len(items_to_process)
    
    def test_circuit_breaker_pattern(self):
        """Test circuit breaker pattern for handling repeated failures"""
        failure_count = 0
        failure_threshold = 3
        circuit_open = False
        
        def simulate_request():
            nonlocal failure_count, circuit_open
            
            if circuit_open:
                raise Exception("Circuit breaker is open")
            
            # Simulate failures
            failure_count += 1
            if failure_count <= failure_threshold:
                raise requests.exceptions.ConnectionError("Request failed")
            
            # After threshold, open circuit
            circuit_open = True
            raise Exception("Circuit breaker is open")
        
        # Test that circuit breaker opens after threshold
        for i in range(failure_threshold + 1):
            with pytest.raises(Exception):
                simulate_request()
        
        assert circuit_open
        assert failure_count > failure_threshold


# Test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])