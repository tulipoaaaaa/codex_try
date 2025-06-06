import pytest
from pathlib import Path
import json
import os
from CryptoFinanceCorpusBuilder.shared_tools.collectors.collect_isda import ISDADocumentationCollector
from CryptoFinanceCorpusBuilder.shared_tools.project_config import ProjectConfig

@pytest.fixture
def config():
    """Provide a ProjectConfig instance for testing."""
    config_path = Path(__file__).parent.parent.parent / "config" / "test_config.yaml"
    return ProjectConfig(config_path, environment='test')

@pytest.fixture
def collector(config):
    """Provide an ISDA collector instance for testing."""
    return ISDADocumentationCollector(config)

def test_isda_collector_initialization(collector, config):
    """Test that the ISDA collector initializes correctly with ProjectConfig."""
    assert collector.config == config
    assert collector.isda_dir == config.raw_data_dir / 'ISDA'
    assert collector.isda_dir.exists()

def test_isda_collector_output_paths(collector):
    """Test that the ISDA collector uses correct output paths."""
    # Test with test config
    filename = "test_document.pdf"
    output_path = collector._get_output_path(filename)
    expected_path = collector.isda_dir / filename
    assert output_path == expected_path

def test_isda_collector_metadata(collector):
    """Test that the ISDA collector generates correct metadata."""
    # Test document collection with real ISDA document
    test_doc_id = "2021-ISDA-Defined-Terms-Supplement-1"  # Real ISDA document ID
    results = collector.collect_by_id(test_doc_id)
    
    if results:  # If any documents were collected
        doc = results[0]
        assert "document_id" in doc
        assert "title" in doc
        assert "filepath" in doc
        assert "metadata_path" in doc
        assert "domain" in doc
        
        # Check metadata file
        meta_path = Path(doc["metadata_path"])
        assert meta_path.exists()
        
        with open(meta_path, "r", encoding="utf-8") as f:
            meta_data = json.load(f)
            assert "document_id" in meta_data
            assert "title" in meta_data
            assert "url" in meta_data
            assert "download_date" in meta_data
            assert "domain" in meta_data

def test_isda_collector_file_validation(collector):
    """Test that the ISDA collector validates files correctly."""
    # Create a valid test PDF file with proper structure
    test_file = collector.isda_dir / "test.pdf"
    
    # Create a minimal valid PDF file (at least 1KB)
    pdf_content = b"%PDF-1.4\n" + b"1 0 obj\n<<>>\nendobj\n" + b"xref\n0 2\n" + b"trailer\n<<>>\nstartxref\n0\n%%EOF\n"
    # Pad to ensure file is at least 1KB
    pdf_content = pdf_content + b" " * (1024 - len(pdf_content))
    
    with open(test_file, "wb") as f:
        f.write(pdf_content)

    # Test valid file
    assert collector._check_file_validity(test_file)
    
    # Test invalid file (too small)
    small_file = collector.isda_dir / "small.pdf"
    with open(small_file, "wb") as f:
        f.write(b"%PDF-1.4\n")
    assert not collector._check_file_validity(small_file)
    
    # Test invalid file (not a PDF)
    invalid_file = collector.isda_dir / "invalid.txt"
    with open(invalid_file, "wb") as f:
        f.write(b"Not a PDF file")
    assert not collector._check_file_validity(invalid_file)
    
    # Cleanup
    test_file.unlink(missing_ok=True)
    small_file.unlink(missing_ok=True)
    invalid_file.unlink(missing_ok=True)

def test_isda_collector_projectconfig(config, collector):
    """Test ISDACollector with ProjectConfig integration and real downloads"""

    # Get search terms from ProjectConfig domains
    keywords = []
    for domain_name, domain_config in config.domain_configs.items():
        if hasattr(domain_config, 'search_terms'):
            keywords.extend(domain_config.search_terms)

    # Verify we have keywords
    assert len(keywords) > 0, "No keywords found in ProjectConfig domains"

    # Collect documents with real downloads
    results = collector.collect(
        keywords=keywords[:2],  # Limit to 2 terms for testing
        max_sources=2  # Limit results for testing
    )
    
    # Verify results
    assert len(results) > 0, "No documents were collected"
    
    # Verify file existence and metadata
    for result in results:
        assert Path(result['filepath']).exists(), f"File not found: {result['filepath']}"
        assert Path(result['metadata_path']).exists(), f"Metadata file not found: {result['metadata_path']}"
        
        # Verify metadata content
        with open(result['metadata_path'], 'r') as f:
            metadata = json.load(f)
            assert 'title' in metadata
            assert 'url' in metadata
            assert 'download_date' in metadata

@pytest.mark.integration
def test_isda_collector_by_id(config, collector):
    """Test collecting specific documents by ID"""
    document_ids = [
        "2021-ISDA-Defined-Terms-Supplement-1",
        "2021-ISDA-Defined-Terms-Supplement-2"
    ]
    
    # Collect documents by ID
    results = collector.collect_by_id(document_ids)
    
    # Verify results
    assert len(results) > 0, "No documents were collected"
    
    # Check file structure
    for result in results:
        # Verify file exists
        assert Path(result['filepath']).exists(), f"File not found: {result['filepath']}"
        
        # Verify file is in correct directory
        file_path = Path(result['filepath'])
        assert file_path.parent == collector.isda_dir, f"Invalid directory: {file_path.parent}"
        
        # Verify metadata
        assert result['document_id'] in document_ids, "Document ID mismatch"
        assert 'title' in result, "Title missing from metadata"
        assert 'filepath' in result, "Filepath missing from metadata"
        
        # Verify file size
        file_size = file_path.stat().st_size
        assert file_size > 1000, f"File too small: {file_size} bytes"
        assert file_size < 1000000, f"File too large: {file_size} bytes"

@pytest.mark.integration
def test_domain_classification(collector, config):
    """Integration test: Test domain classification of ISDA documents"""
    # Test with real document IDs
    documents = [
        {'id': '2021-ISDA-Defined-Terms-Supplement-1', 'domain': 'regulation_compliance'},
        {'id': '2021-ISDA-Defined-Terms-Supplement-2', 'domain': 'regulation_compliance'}
    ]
    
    results = collector.collect_by_id([item['id'] for item in documents])
    
    assert len(results) > 0
    for result in results:
        assert 'domain' in result
        # Verify domain is one of the configured domains
        assert result['domain'] in config.domain_configs.keys()

@pytest.mark.integration
def test_file_validation(collector):
    """Integration test: Test file validation"""
    # First collect a document by ID
    document_id = "2021-ISDA-Defined-Terms-Supplement-1"
    results = collector.collect_by_id(document_id)
    assert len(results) > 0
    
    # Test file validation
    filepath = results[0]['filepath']
    assert collector._check_file_validity(filepath)

@pytest.mark.integration
def test_metadata_generation(collector):
    """Integration test: Test metadata generation for collected documents"""
    document_id = "2021-ISDA-Defined-Terms-Supplement-1"
    results = collector.collect_by_id(document_id)
    assert len(results) > 0
    
    result = results[0]
    meta_file = Path(result['filepath']).with_suffix('.meta')
    
    assert meta_file.exists()
    assert all(key in result for key in ['document_id', 'title', 'filepath'])

def test_error_handling(collector):
    """Test error handling for invalid inputs"""
    # Test with invalid document ID
    results = collector.collect_by_id(["INVALID-ID-123"])
    assert len(results) == 0
    
    # Test with empty ID list
    results = collector.collect_by_id([])
    assert len(results) == 0

@pytest.mark.integration
def test_cleanup(collector):
    """Integration test: Test cleanup of downloaded files"""
    # Collect some documents by ID
    document_id = "2021-ISDA-Defined-Terms-Supplement-1"
    results = collector.collect_by_id(document_id)
    
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
    test_isda_collector_projectconfig()
    print("ISDA collector test completed successfully!") 