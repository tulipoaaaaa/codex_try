import os
import sys
import pytest
from pathlib import Path
from shared_tools.collectors.github_collector import GitHubCollector
from shared_tools.project_config import ProjectConfig

@pytest.fixture
def config():
    """Fixture to provide ProjectConfig instance"""
    config_path = os.path.join(os.path.dirname(__file__), '../../config/master_config.yaml')
    return ProjectConfig(config_path, environment='production')

@pytest.fixture
def collector(config):
    """Fixture to provide GitHubCollector instance"""
    return GitHubCollector(config)

def test_github_collector_projectconfig(config, collector):
    """Test GitHubCollector with ProjectConfig integration and real downloads"""
    
    # Test search terms from config
    search_terms = []
    for domain, domain_config in config.domain_configs.items():
        if hasattr(domain_config, 'search_terms'):
            search_terms.extend(domain_config.search_terms)
    
    # Collect repositories with real downloads
    results = collector.collect(
        search_terms=search_terms[:2],  # Limit to 2 terms for testing
        max_repos=2  # Limit results for testing
    )
    
    # Verify results
    assert len(results) > 0, "No repositories were collected"
    
    # Check file structure
    for result in results:
        # Verify repository exists
        assert Path(result['filepath']).exists(), f"Repository not found: {result['filepath']}"
        
        # Verify repository is in correct directory
        repo_path = Path(result['filepath'])
        assert repo_path.parent == Path("G:/ai_trading_dev/data/test_corpus/raw_data/Github"), f"Repository not in correct directory: {repo_path.parent}"
        
        # Verify metadata
        assert 'repo_name' in result, "Repository name missing from metadata"
        assert 'owner' in result, "Owner missing from metadata"
        assert 'filepath' in result, "Filepath missing from metadata"
        assert 'domain' in result, "Domain missing from metadata"
        
        # Verify repository size
        repo_size = sum(f.stat().st_size for f in repo_path.rglob('*') if f.is_file())
        assert repo_size > 1000, f"Repository too small: {repo_size} bytes"
        assert repo_size < 100000000, f"Repository too large: {repo_size} bytes"

@pytest.mark.integration
def test_github_collector_by_repo(config, collector):
    """Test collecting a specific repository"""
    repo_info = {
        'owner': 'example',
        'repo': 'test-repo'
    }
    
    # Collect repository
    results = collector.collect_by_repo(repo_info)
    
    # Verify results
    assert len(results) > 0, "No repository was collected"
    
    # Check file structure
    for result in results:
        # Verify repository exists
        assert Path(result['filepath']).exists(), f"Repository not found: {result['filepath']}"
        
        # Verify repository is in correct domain directory
        repo_path = Path(result['filepath'])
        assert repo_path.parent.parent.name in config.domain_configs, f"Invalid domain directory: {repo_path.parent.parent.name}"
        
        # Verify metadata
        assert result['repo_name'] == repo_info['repo'], "Repository name mismatch"
        assert result['owner'] == repo_info['owner'], "Owner mismatch"
        assert 'filepath' in result, "Filepath missing from metadata"
        
        # Verify repository size
        repo_size = sum(f.stat().st_size for f in repo_path.rglob('*') if f.is_file())
        assert repo_size > 1000, f"Repository too small: {repo_size} bytes"
        assert repo_size < 100000000, f"Repository too large: {repo_size} bytes"

@pytest.mark.integration
def test_domain_classification(collector):
    """Integration test: Test domain classification of repositories"""
    # Test with known repositories
    repos = [
        {'owner': 'example1', 'repo': 'portfolio-optimization', 'domain': 'portfolio_construction'},
        {'owner': 'example2', 'repo': 'risk-models', 'domain': 'risk_management'},
        {'owner': 'example3', 'repo': 'defi-protocols', 'domain': 'decentralized_finance'}
    ]
    
    results = collector.collect_by_repo(repos)
    
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
def test_repository_validation(collector):
    """Integration test: Test repository validation"""
    # First collect a repository
    repo_info = {'owner': 'example', 'repo': 'test-repo'}
    results = collector.collect_by_repo(repo_info)
    assert len(results) > 0
    
    # Test repository validation
    repo_path = results[0]['filepath']
    assert collector._check_repository_validity(repo_path)

@pytest.mark.integration
def test_metadata_generation(collector):
    """Integration test: Test metadata generation for collected repositories"""
    repo_info = {'owner': 'example', 'repo': 'test-repo'}
    results = collector.collect_by_repo(repo_info)
    assert len(results) > 0
    
    repo = results[0]
    meta_file = Path(repo['filepath']).with_suffix('.meta')
    
    assert meta_file.exists()
    assert all(key in repo for key in ['repo_name', 'owner', 'filepath'])

def test_error_handling(collector):
    """Test error handling for invalid inputs"""
    # Test with invalid repository
    results = collector.collect_by_repo({'owner': 'invalid', 'repo': 'invalid-repo'})
    assert len(results) == 0
    
    # Test with empty repository list
    results = collector.collect_by_repo([])
    assert len(results) == 0

@pytest.mark.integration
def test_cleanup(collector):
    """Integration test: Test cleanup of downloaded repositories"""
    # Collect some repositories
    repo_info = {'owner': 'example', 'repo': 'test-repo'}
    results = collector.collect_by_repo(repo_info)
    
    # Clean up
    for result in results:
        repo_path = Path(result['filepath'])
        if repo_path.exists():
            for file in repo_path.rglob('*'):
                if file.is_file():
                    file.unlink()
            repo_path.rmdir()
        meta_file = repo_path.with_suffix('.meta')
        if meta_file.exists():
            meta_file.unlink()
    
    # Verify cleanup
    assert not any(Path(result['filepath']).exists() for result in results)

if __name__ == "__main__":
    test_github_collector_projectconfig()
    print("GitHub collector test completed successfully!") 