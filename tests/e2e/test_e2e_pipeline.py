import pytest
from pathlib import Path
import os
import shutil
from CorpusBuilderApp.shared_tools.processors.batch_nonpdf_extractor_enhanced import BatchNonPDFExtractorEnhanced
from CorpusBuilderApp.shared_tools.processors.batch_text_extractor_enhanced_prerefactor import BatchTextExtractorEnhancedPrerefactor

@pytest.fixture
def test_data_dir():
    """Fixture to provide test data directory"""
    return Path("G:/data/e2E")

@pytest.fixture
def output_dir():
    """Fixture to provide output directory within the test data directory"""
    output_path = Path("G:/data/e2E/output")
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path

@pytest.fixture
def pdf_processor():
    """Fixture to provide configured PDF processor instance"""
    processor = BatchTextExtractorEnhancedPrerefactor()
    processor.configure(
        max_workers=2,
        timeout=30,
        chunk_size=1000,
        chunk_overlap=100
    )
    return processor

@pytest.fixture
def nonpdf_processor():
    """Fixture to provide configured non-PDF processor instance"""
    processor = BatchNonPDFExtractorEnhanced()
    processor.configure(
        max_workers=2,
        timeout=30,
        chunk_size=1000,
        chunk_overlap=100
    )
    return processor

def test_e2e_pipeline(pdf_processor, nonpdf_processor, test_data_dir, output_dir):
    """Test the complete end-to-end processing pipeline"""
    # Create test data structure
    test_structure = {
        "pdf_files": {
            "financial_report.pdf": "Financial Report Content",
            "academic_paper.pdf": "Academic Paper Content"
        },
        "nonpdf_files": {
            "python_script.py": "def calculate_risk(): pass",
            "markdown_report.md": "# Test Report\n## Section\nContent",
            "html_report.html": "<html><body>Test</body></html>",
            "json_config.json": '{"key": "value"}',
            "csv_data.csv": "Date,Price\n2024-01-01,100"
        }
    }
    
    # Create test directories and files
    pdf_dir = test_data_dir / "pdf_files"
    nonpdf_dir = test_data_dir / "nonpdf_files"
    
    pdf_dir.mkdir(parents=True, exist_ok=True)
    nonpdf_dir.mkdir(parents=True, exist_ok=True)
    
    # Create PDF files (in a real test, these would be actual PDF files)
    for filename in test_structure["pdf_files"].keys():
        file_path = pdf_dir / filename
        file_path.touch()  # Create empty file for now
    
    # Create non-PDF files
    for filename, content in test_structure["nonpdf_files"].items():
        file_path = nonpdf_dir / filename
        file_path.write_text(content)
    
    # Process PDF files
    pdf_output_dir = output_dir / "pdf_output"
    pdf_output_dir.mkdir(parents=True, exist_ok=True)
    pdf_result = pdf_processor.process_directory(str(pdf_dir), str(pdf_output_dir))
    
    # Verify PDF processing results
    assert pdf_result is not None
    assert "processed_files" in pdf_result
    assert "errors" in pdf_result
    
    # Process non-PDF files
    nonpdf_output_dir = output_dir / "nonpdf_output"
    nonpdf_output_dir.mkdir(parents=True, exist_ok=True)
    nonpdf_result = nonpdf_processor.process_directory(str(nonpdf_dir), str(nonpdf_output_dir))
    
    # Verify non-PDF processing results
    assert nonpdf_result is not None
    assert "processed_files" in nonpdf_result
    assert "errors" in nonpdf_result
    
    # Verify that all files were processed
    for filename in test_structure["pdf_files"].keys():
        output_file = pdf_output_dir / f"{Path(filename).stem}.txt"
        assert output_file.exists()
    
    for filename in test_structure["nonpdf_files"].keys():
        output_file = nonpdf_output_dir / f"{Path(filename).stem}.txt"
        assert output_file.exists()
    
    # Verify content of processed files
    for filename, content in test_structure["nonpdf_files"].items():
        output_file = nonpdf_output_dir / f"{Path(filename).stem}.txt"
        processed_content = output_file.read_text()
        assert content in processed_content

def test_e2e_pipeline_with_errors(pdf_processor, nonpdf_processor, test_data_dir, output_dir):
    """Test the end-to-end pipeline with error handling"""
    # Create test data with invalid files
    test_structure = {
        "pdf_files": {
            "valid.pdf": "Valid PDF Content",
            "invalid.txt": "Invalid PDF Content"
        },
        "nonpdf_files": {
            "valid.py": "def test(): pass",
            "invalid.bin": "Binary Content"
        }
    }
    
    # Create test directories and files
    pdf_dir = test_data_dir / "pdf_files"
    nonpdf_dir = test_data_dir / "nonpdf_files"
    
    pdf_dir.mkdir(parents=True, exist_ok=True)
    nonpdf_dir.mkdir(parents=True, exist_ok=True)
    
    # Create files
    for filename in test_structure["pdf_files"].keys():
        file_path = pdf_dir / filename
        file_path.touch()
    
    for filename, content in test_structure["nonpdf_files"].items():
        file_path = nonpdf_dir / filename
        file_path.write_text(content)
    
    # Process PDF files
    pdf_output_dir = output_dir / "pdf_output"
    pdf_output_dir.mkdir(parents=True, exist_ok=True)
    pdf_result = pdf_processor.process_directory(str(pdf_dir), str(pdf_output_dir))
    
    # Verify PDF processing results
    assert pdf_result is not None
    assert "processed_files" in pdf_result
    assert "errors" in pdf_result
    assert len(pdf_result["errors"]) > 0  # Should have errors for invalid file
    
    # Process non-PDF files
    nonpdf_output_dir = output_dir / "nonpdf_output"
    nonpdf_output_dir.mkdir(parents=True, exist_ok=True)
    nonpdf_result = nonpdf_processor.process_directory(str(nonpdf_dir), str(nonpdf_output_dir))
    
    # Verify non-PDF processing results
    assert nonpdf_result is not None
    assert "processed_files" in nonpdf_result
    assert "errors" in nonpdf_result
    assert len(nonpdf_result["errors"]) > 0  # Should have errors for invalid file
    
    # Verify that only valid files were processed
    assert (pdf_output_dir / "valid.txt").exists()
    assert not (pdf_output_dir / "invalid.txt").exists()
    
    assert (nonpdf_output_dir / "valid.txt").exists()
    assert not (nonpdf_output_dir / "invalid.txt").exists() 