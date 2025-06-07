# DEPRECATED: This file belongs to the legacy CryptoFinanceCorpusBuilder package and should not be used in new modules.
import os
import sys
import pytest
from pathlib import Path
from shared_tools.collectors.repo_collector import RepoCollector
from shared_tools.project_config import ProjectConfig

@pytest.fixture
def config():
    """Fixture to provide ProjectConfig instance"""
    config_path = os.path.join(os.path.dirname(__file__), '../../config/test_config.yaml')
    return ProjectConfig(config_path, environment='test')

@pytest.fixture
def collector(config):
    """Fixture to provide RepoCollector instance"""
    return RepoCollector(config)

def test_repo_collector_projectconfig(config, collector):
    """Test RepoCollector with ProjectConfig integration and real downloads"""
    
    # Test search terms from config
    search_terms = []
    for domain, domain_config in config.domain_configs.items():
        search_terms.extend(domain_config.get('search_terms', []))
    
    # Collect repositories with real downloads
    results = collector.collect(
        search_terms=search_terms[:2],  # Limit to 2 terms for testing
        max_results=2  # Limit results for testing
    )
    
    # Verify results
    assert len(results) > 0, "No repositories were collected"
    
    # Check file structure
    for result in results:
        # Verify file exists
        assert Path(result['filepath']).exists(), f"File not found: {result['filepath']}"
        
        # Verify file is in correct domain directory
        file_path = Path(result['filepath'])
        assert file_path.parent.parent.name in config.domain_configs, f"Invalid domain directory: {file_path.parent.parent.name}"
        
        # Verify metadata
        assert 'repo_id' in result, "Repository ID missing from metadata"
        assert 'title' in result, "Title missing from metadata"
        assert 'filepath' in result, "Filepath missing from metadata"
        
        # Verify file size
        file_size = file_path.stat().st_size
        assert file_size > 1000, f"File too small: {file_size} bytes"
        assert file_size < 1000000, f"File too large: {file_size} bytes"

@pytest.mark.integration
def test_repo_collector_by_id(config, collector):
    """Test collecting specific repositories by ID"""
    repo_ids = [
        "R-2023-001",
        "R-2023-002"
    ]
    
    # Collect repositories by ID
    results = collector.collect_by_id(repo_ids)
    
    # Verify results
    assert len(results) > 0, "No repositories were collected"
    
    # Check file structure
    for result in results:
        # Verify file exists
        assert Path(result['filepath']).exists(), f"File not found: {result['filepath']}"
        
        # Verify file is in correct domain directory
        file_path = Path(result['filepath'])
        assert file_path.parent.parent.name in config.domain_configs, f"Invalid domain directory: {file_path.parent.parent.name}"
        
        # Verify metadata
        assert result['repo_id'] in repo_ids, "Repository ID mismatch"
        assert 'title' in result, "Title missing from metadata"
        assert 'filepath' in result, "Filepath missing from metadata"
        
        # Verify file size
        file_size = file_path.stat().st_size
        assert file_size > 1000, f"File too small: {file_size} bytes"
        assert file_size < 1000000, f"File too large: {file_size} bytes"

@pytest.mark.integration
def test_domain_classification(collector):
    """Integration test: Test domain classification of repositories"""
    # Test with known repository IDs
    repositories = [
        {'id': 'R-2023-001', 'domain': 'portfolio_construction'},
        {'id': 'R-2023-002', 'domain': 'high_frequency_trading'},
        {'id': 'R-2023-003', 'domain': 'risk_management'}
    ]
    
    results = collector.collect_by_id([item['id'] for item in repositories])
    
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
    # First collect a repository by ID
    repo_id = "R-2023-001"
    results = collector.collect_by_id(repo_id)
    assert len(results) > 0
    
    # Test file validation
    filepath = results[0]['filepath']
    assert collector._check_file_validity(filepath)

@pytest.mark.integration
def test_metadata_generation(collector):
    """Integration test: Test metadata generation for collected repositories"""
    repo_id = "R-2023-001"
    results = collector.collect_by_id(repo_id)
    assert len(results) > 0
    
    result = results[0]
    meta_file = Path(result['filepath']).with_suffix('.meta')
    
    assert meta_file.exists()
    assert all(key in result for key in ['repo_id', 'title', 'filepath'])

def test_error_handling(collector):
    """Test error handling for invalid inputs"""
    # Test with invalid repository ID
    results = collector.collect_by_id(["INVALID-ID-123"])
    assert len(results) == 0
    
    # Test with empty ID list
    results = collector.collect_by_id([])
    assert len(results) == 0

@pytest.mark.integration
def test_cleanup(collector):
    """Integration test: Test cleanup of downloaded files"""
    # Collect some repositories by ID
    repo_id = "R-2023-001"
    results = collector.collect_by_id(repo_id)
    
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