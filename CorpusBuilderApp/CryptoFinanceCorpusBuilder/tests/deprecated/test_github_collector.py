import os
import pytest
from pathlib import Path
from shared_tools.collectors.github_collector import GitHubCollector
from shared_tools.project_config import ProjectConfig

# Test configuration
TEST_CONFIG = {
    "environment": "test",
    "environments": {
        "test": {
            "corpus_dir": "data/test_output",
            "cache_dir": "data/test_output/cache",
            "log_dir": "data/test_output/logs"
        }
    }
}

@pytest.fixture
def test_config():
    """Create a test configuration"""
    config = ProjectConfig.from_dict(TEST_CONFIG)
    return config

@pytest.fixture
def collector(test_config):
    """Create a GitHub collector instance"""
    output_dir = Path(test_config.get_corpus_dir()) / "github_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    return GitHubCollector(output_dir)

def test_collect_by_topic(collector):
    """Test collecting repositories by topic"""
    topics = ["cryptocurrency", "trading-bot"]
    repos = collector.collect_by_topic(topics, max_results=2)
    
    assert len(repos) > 0
    assert all('name' in repo for repo in repos)
    assert all('description' in repo for repo in repos)
    assert all('stars' in repo for repo in repos)
    assert all('language' in repo for repo in repos)

def test_collect_by_search(collector):
    """Test collecting repositories by search terms"""
    search_terms = ["crypto trading bot python"]
    repos = collector.collect_by_search(search_terms, max_results=2)
    
    assert len(repos) > 0
    assert all('name' in repo for repo in repos)
    assert all('description' in repo for repo in repos)
    assert all('stars' in repo for repo in repos)

def test_repository_cloning(collector):
    """Test repository cloning functionality"""
    repos = collector.collect_by_topic(["cryptocurrency"], max_results=1)
    assert len(repos) > 0
    
    repo = repos[0]
    local_path = collector.clone_repository(repo['clone_url'])
    
    assert local_path.exists()
    assert (local_path / '.git').exists()
    assert (local_path / 'README.md').exists()

def test_code_extraction(collector):
    """Test code extraction from repositories"""
    repos = collector.collect_by_topic(["cryptocurrency"], max_results=1)
    assert len(repos) > 0
    
    repo = repos[0]
    local_path = collector.clone_repository(repo['clone_url'])
    
    # Extract Python files
    python_files = collector.extract_code_files(local_path, extensions=['.py'])
    assert len(python_files) > 0
    
    # Verify file contents
    for file_path in python_files:
        assert file_path.exists()
        assert file_path.suffix == '.py'
        assert file_path.stat().st_size > 0

def test_metadata_extraction(collector):
    """Test metadata extraction from repositories"""
    repos = collector.collect_by_topic(["cryptocurrency"], max_results=1)
    assert len(repos) > 0
    
    repo = repos[0]
    assert all(key in repo for key in [
        'name',
        'description',
        'stars',
        'forks',
        'language',
        'topics',
        'created_at',
        'updated_at'
    ])

def test_error_handling(collector):
    """Test error handling for invalid inputs"""
    # Test with invalid topic
    repos = collector.collect_by_topic(["invalid-topic-123"])
    assert len(repos) == 0
    
    # Test with empty search term
    repos = collector.collect_by_search([""])
    assert len(repos) == 0

def test_rate_limiting(collector):
    """Test rate limiting functionality"""
    import time
    start_time = time.time()
    
    # Collect multiple repositories to test rate limiting
    repos = collector.collect_by_topic(["cryptocurrency"], max_results=3)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Should take at least 3 seconds due to rate limiting
    assert duration >= 3
    assert len(repos) > 0

def test_cleanup(collector):
    """Test cleanup of test files"""
    # Collect and clone a repository
    repos = collector.collect_by_topic(["cryptocurrency"], max_results=1)
    assert len(repos) > 0
    
    local_path = collector.clone_repository(repos[0]['clone_url'])
    
    # Clean up
    if local_path.exists():
        import shutil
        shutil.rmtree(local_path)
    
    # Verify cleanup
    assert not local_path.exists() 