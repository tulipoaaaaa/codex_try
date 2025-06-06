import os
import sys
import pytest
import json
import shutil
from pathlib import Path
from dotenv import load_dotenv
from CryptoFinanceCorpusBuilder.shared_tools.collectors.collect_bitmex import UpdatedBitMEXCollector
from CryptoFinanceCorpusBuilder.shared_tools.project_config import ProjectConfig

# Load environment variables from .env file
load_dotenv()

@pytest.fixture
def config():
    """Fixture to provide ProjectConfig instance"""
    config_path = os.path.join(os.path.dirname(__file__), '../../config/test_config.yaml')
    return ProjectConfig(config_path, environment='test')

@pytest.fixture
def collector(config):
    """Fixture to provide UpdatedBitMEXCollector instance"""
    return UpdatedBitMEXCollector(config)

def test_bitmex_collector_initialization(config):
    """Test UpdatedBitMEXCollector initialization"""
    collector = UpdatedBitMEXCollector(config)
    assert collector.base_url == 'https://blog.bitmex.com/research/'
    assert collector.titles_cache == set()
    assert collector.session.headers['User-Agent'] is not None

def test_bitmex_collector_projectconfig(config, collector):
    """Test UpdatedBitMEXCollector with ProjectConfig integration and real downloads"""
    # Clear output directory for clean test
    if collector.output_dir.exists():
        shutil.rmtree(collector.output_dir)
    collector.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Collect research posts
    results = collector.collect(max_pages=2)  # Increased to 2 pages for better coverage
    
    # Verify results
    assert len(results) > 0, "No research posts were collected"
    print(f"\nCollected {len(results)} posts")
    
    # Check file structure
    for post in results:
        # Print post details for debugging
        print(f"\nPost: {post.get('title')}")
        print(f"URL: {post.get('url')}")
        
        # Verify HTML file exists
        assert 'saved_html_path' in post, "HTML file path missing from post"
        html_path = Path(post['saved_html_path'])
        assert html_path.exists(), f"HTML file not found: {html_path}"
        print(f"HTML saved: {html_path}")
        
        # Verify file is in correct domain directory
        assert html_path.parent.parent.name == 'crypto_derivatives', f"Invalid domain directory: {html_path.parent.parent.name}"
        
        # Verify metadata
        assert 'title' in post, "Title missing from metadata"
        assert 'url' in post, "URL missing from metadata"
        assert 'date' in post, "Date missing from metadata"
        assert 'content_text' in post, "Content text missing from metadata"
        
        # Verify file size
        file_size = html_path.stat().st_size
        assert file_size > 1000, f"File too small: {file_size} bytes"
        print(f"HTML size: {file_size/1024:.2f} KB")
        
        # Check PDFs if any
        if 'pdfs' in post:
            print(f"PDFs found: {len(post['pdfs'])}")
            for pdf in post['pdfs']:
                pdf_path = Path(pdf['filepath'])
                assert pdf_path.exists(), f"PDF file not found: {pdf_path}"
                pdf_size = pdf_path.stat().st_size
                assert pdf_size > 1000, f"PDF file too small: {pdf_size} bytes"
                print(f"PDF: {pdf['filename']} ({pdf_size/1024:.2f} KB)")
    
    # Verify metadata file
    metadata_path = collector.output_dir / "bitmex_research_posts.json"
    assert metadata_path.exists(), "Metadata file not found"
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    assert len(metadata) == len(results), "Metadata count doesn't match results count"
    print(f"\nMetadata saved: {metadata_path}")

def test_keyword_filtering(collector):
    """Test filtering posts by keywords"""
    # Test with specific keywords
    keywords = ['bitcoin', 'derivatives']
    results = collector.collect(max_pages=2, keywords=keywords)
    
    if results:
        print(f"\nFound {len(results)} posts with keywords: {keywords}")
        for post in results:
            # Verify content contains at least one keyword
            content_lower = post['content_text'].lower()
            found_keywords = [kw for kw in keywords if kw.lower() in content_lower]
            assert found_keywords, f"Post '{post['title']}' does not contain any of the keywords: {keywords}"
            print(f"Post '{post['title']}' contains keywords: {found_keywords}")

def test_metadata_generation(collector):
    """Test metadata generation for collected posts"""
    results = collector.collect(max_pages=2)
    assert len(results) > 0
    
    # Check metadata file
    metadata_path = collector.output_dir / "bitmex_research_posts.json"
    assert metadata_path.exists(), "Metadata file not found"
    
    # Verify metadata content
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    assert len(metadata) > 0, "Metadata file is empty"
    assert all('title' in post for post in metadata), "Some posts missing title in metadata"
    assert all('url' in post for post in metadata), "Some posts missing URL in metadata"
    print(f"\nMetadata contains {len(metadata)} posts")

def test_error_handling(collector):
    """Test error handling for invalid inputs"""
    # Test with invalid URL
    collector.base_url = "https://invalid-url-that-does-not-exist.com"
    try:
        results = collector.collect(max_pages=1)
        assert len(results) == 0, "Should handle invalid URL gracefully"
    except Exception as e:
        pytest.fail(f"Collector should handle invalid URL gracefully, but raised: {e}")
    
    # Test with invalid keywords
    collector.base_url = 'https://blog.bitmex.com/research/'
    results = collector.collect(max_pages=1, keywords=['invalid_keyword_123456789'])
    assert len(results) == 0, "Should handle no matching keywords gracefully"

def test_cleanup(collector):
    """Test cleanup of downloaded files"""
    # Collect some posts
    results = collector.collect(max_pages=1)
    assert len(results) > 0
    
    # Clean up
    for post in results:
        if 'saved_html_path' in post:
            html_path = Path(post['saved_html_path'])
            if html_path.exists():
                html_path.unlink()
        
        if 'pdfs' in post:
            for pdf in post['pdfs']:
                pdf_path = Path(pdf['filepath'])
                if pdf_path.exists():
                    pdf_path.unlink()
    
    # Verify cleanup
    assert not any(Path(post['saved_html_path']).exists() for post in results if 'saved_html_path' in post)
    assert not any(Path(pdf['filepath']).exists() for post in results if 'pdfs' in post for pdf in post['pdfs'])

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 