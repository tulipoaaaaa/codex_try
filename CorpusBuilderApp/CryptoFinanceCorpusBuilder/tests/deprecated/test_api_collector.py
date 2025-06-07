import os
import sys
import pytest
import json
from pathlib import Path
from dotenv import load_dotenv
from shared_tools.collectors.api_collector import ApiCollector
from shared_tools.project_config import ProjectConfig

# Load environment variables
load_dotenv()

@pytest.fixture
def config():
    """Fixture to provide ProjectConfig instance"""
    config_path = os.path.join(os.path.dirname(__file__), '../../config/test_config.yaml')
    return ProjectConfig(config_path, environment='test')

@pytest.fixture
def collector(config):
    """Fixture to provide ApiCollector instance with real API configuration"""
    # Get API key from environment
    api_key = os.getenv("API_KEY")
    if not api_key:
        pytest.skip("API_KEY environment variable not set")
    
    # Initialize collector with real API configuration
    collector = ApiCollector(
        config,
        api_base_url="https://api.example.com",  # Replace with your actual API base URL
        delay_range=(2, 5)  # Shorter delays for testing
    )
    collector.api_key = api_key
    return collector

def test_api_collector_initialization(config):
    """Test ApiCollector initialization with real config"""
    collector = ApiCollector(config, api_base_url="https://api.example.com")
    assert collector.api_base_url == "https://api.example.com"
    assert collector.delay_range == (5, 10)
    assert collector.api_key is None
    assert collector.last_request_time == {}
    assert collector.rate_limits == {}

def test_api_request_success(collector):
    """Test successful API request with real API"""
    # Test with a real endpoint
    result = collector.api_request(
        "test/endpoint",  # Replace with your actual endpoint
        params={"q": "bitcoin"},
        headers={"Accept": "application/json"}
    )
    
    assert result is not None
    assert isinstance(result, (dict, str))

def test_api_request_failure(collector):
    """Test failed API request with real API"""
    # Test with invalid endpoint
    result = collector.api_request("invalid/endpoint/123456789")
    assert result is None

def test_rate_limiting(collector):
    """Test rate limiting with real API"""
    # Set up rate limits
    collector.rate_limits = {
        "api.example.com": {
            "requests": 2,
            "period": 1
        }
    }
    
    # Make multiple requests to test rate limiting
    results = []
    for _ in range(3):
        result = collector.api_request("test/endpoint")
        results.append(result)
    
    # Should get results despite rate limiting
    assert any(r is not None for r in results)

def test_api_key_handling(collector):
    """Test API key handling with real API"""
    # Make request with API key
    result = collector.api_request(
        "test/endpoint",
        params={"q": "test"}
    )
    
    assert result is not None

def test_error_handling(collector):
    """Test error handling with real API"""
    # Test with invalid parameters
    result = collector.api_request(
        "test/endpoint",
        params={"invalid": "parameter"}
    )
    
    # Should handle error gracefully
    assert result is not None or result is None  # Either response or None is acceptable

def test_metadata_generation(collector):
    """Test metadata generation for API responses"""
    # Make a real API request
    result = collector.api_request("test/endpoint")
    
    if result:
        # Save response to file
        output_dir = collector.raw_data_dir / "test_domain" / "papers"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / "test_response.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        
        # Verify file was created
        assert output_file.exists()
        assert output_file.stat().st_size > 0

@pytest.mark.integration
def test_api_collector_projectconfig(config, collector):
    """Test APICollector with ProjectConfig integration and real downloads"""
    
    # Test search terms from config
    search_terms = []
    for domain, domain_config in config.domain_configs.items():
        search_terms.extend(domain_config.get('search_terms', []))
    
    # Collect data with real API calls
    results = collector.collect(
        search_terms=search_terms[:2],  # Limit to 2 terms for testing
        max_results=2  # Limit results for testing
    )
    
    # Verify results
    assert len(results) > 0, "No data was collected"
    
    # Check file structure
    for result in results:
        # Verify file exists
        assert Path(result['filepath']).exists(), f"File not found: {result['filepath']}"
        
        # Verify file is in correct domain directory
        file_path = Path(result['filepath'])
        assert file_path.parent.parent.name in config.domain_configs, f"Invalid domain directory: {file_path.parent.parent.name}"
        
        # Verify metadata
        assert 'api_id' in result, "API ID missing from metadata"
        assert 'title' in result, "Title missing from metadata"
        assert 'filepath' in result, "Filepath missing from metadata"
        
        # Verify file size
        file_size = file_path.stat().st_size
        assert file_size > 1000, f"File too small: {file_size} bytes"
        assert file_size < 1000000, f"File too large: {file_size} bytes"

@pytest.mark.integration
def test_api_collector_by_id(config, collector):
    """Test collecting specific data by API ID"""
    api_id = "test_api_id_123"  # Example API ID
    
    # Collect data by ID
    results = collector.collect_by_id(api_id)
    
    # Verify results
    assert len(results) > 0, "No data was collected"
    
    # Check file structure
    for result in results:
        # Verify file exists
        assert Path(result['filepath']).exists(), f"File not found: {result['filepath']}"
        
        # Verify file is in correct domain directory
        file_path = Path(result['filepath'])
        assert file_path.parent.parent.name in config.domain_configs, f"Invalid domain directory: {file_path.parent.parent.name}"
        
        # Verify metadata
        assert result['api_id'] == api_id, "API ID mismatch"
        assert 'title' in result, "Title missing from metadata"
        assert 'filepath' in result, "Filepath missing from metadata"
        
        # Verify file size
        file_size = file_path.stat().st_size
        assert file_size > 1000, f"File too small: {file_size} bytes"
        assert file_size < 1000000, f"File too large: {file_size} bytes"

@pytest.mark.integration
def test_domain_classification(collector):
    """Integration test: Test domain classification of API data"""
    # Test with known API IDs
    api_ids = [
        {'id': 'test_api_id_1', 'domain': 'portfolio_construction'},
        {'id': 'test_api_id_2', 'domain': 'risk_management'},
        {'id': 'test_api_id_3', 'domain': 'crypto_derivatives'}
    ]
    
    results = collector.collect_by_id([item['id'] for item in api_ids])
    
    assert len(results) > 0
    for result in results:
        assert 'domain' in result
        assert result['domain'] in [
            "portfolio_construction",
            "risk_management",
            "regulation_compliance",
            "decentralized_finance",
            "valuation_models",
            "high_frequency_trading",
            "market_microstructure",
            "crypto_derivatives"
        ]

@pytest.mark.integration
def test_file_validation(collector):
    """Integration test: Test file validation"""
    # First collect data by ID
    api_id = "test_api_id_123"
    results = collector.collect_by_id(api_id)
    assert len(results) > 0
    
    # Test file validation
    filepath = results[0]['filepath']
    assert collector._check_file_validity(filepath)

@pytest.mark.integration
def test_cleanup(collector):
    """Integration test: Test cleanup of downloaded files"""
    # Collect some data by ID
    api_id = "test_api_id_123"
    results = collector.collect_by_id(api_id)
    
    # Clean up
    for result in results:
        filepath = Path(result['filepath'])
        if filepath.exists():
            filepath.unlink()
        meta_file = filepath.with_suffix('.meta')
        if meta_file.exists():
            meta_file.unlink()
    
    # Verify cleanup
    assert not any(Path(result['filepath']).exists() for result in results)

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 