import pytest
from pathlib import Path
import os
import shutil
from CorpusBuilderApp.shared_tools.processors.batch_text_extractor_enhanced_prerefactor import BatchTextExtractorEnhancedPrerefactor
import logging

@pytest.fixture
def test_data_dir():
    """Fixture to provide test data directory"""
    return Path("G:/data/test_processors/pdf_processors")

@pytest.fixture
def output_dir():
    """Fixture to provide output directory within the test data directory"""
    output_path = Path("G:/data/test_processors/pdf_processors/output")
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path

@pytest.fixture
def processor():
    """Fixture to provide configured processor instance"""
    processor = BatchTextExtractorEnhancedPrerefactor()
    processor.configure(
        max_workers=2,
        timeout=30,
        chunk_size=1000,
        chunk_overlap=100
    )
    return processor

def test_process_pdf_with_tables(processor, test_data_dir, output_dir):
    """Test processing a PDF file containing tables"""
    # Create test PDF file with tables
    test_file = test_data_dir / "financial_report.pdf"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Note: In a real test, we would need to create an actual PDF file
    # For now, we'll assume the file exists and contains tables
    
    # Process the file
    result = processor.extract_file(str(test_file), str(output_dir))
    
    # Verify results
    assert result is True
    output_file = output_dir / "financial_report.txt"
    assert output_file.exists()
    
    content = output_file.read_text()
    assert "Financial Report" in content
    assert "Table" in content  # Assuming the PDF contains tables

def test_process_pdf_with_formulas(processor, test_data_dir, output_dir):
    """Test processing a PDF file containing mathematical formulas"""
    # Create test PDF file with formulas
    test_file = test_data_dir / "mathematical_paper.pdf"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Note: In a real test, we would need to create an actual PDF file
    # For now, we'll assume the file exists and contains formulas
    
    # Process the file
    result = processor.extract_file(str(test_file), str(output_dir))
    
    # Verify results
    assert result is True
    output_file = output_dir / "mathematical_paper.txt"
    assert output_file.exists()
    
    content = output_file.read_text()
    assert "Mathematical Paper" in content
    assert "Formula" in content  # Assuming the PDF contains formulas

def test_process_pdf_with_images(processor, test_data_dir, output_dir):
    """Test processing a PDF file containing images"""
    # Create test PDF file with images
    test_file = test_data_dir / "image_report.pdf"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Note: In a real test, we would need to create an actual PDF file
    # For now, we'll assume the file exists and contains images
    
    # Process the file
    result = processor.extract_file(str(test_file), str(output_dir))
    
    # Verify results
    assert result is True
    output_file = output_dir / "image_report.txt"
    assert output_file.exists()
    
    content = output_file.read_text()
    assert "Image Report" in content
    assert "Figure" in content  # Assuming the PDF contains images

def test_process_pdf_with_text_only(processor, test_data_dir, output_dir):
    """Test processing a PDF file containing only text"""
    # Create test PDF file with text only
    test_file = test_data_dir / "text_only.pdf"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Note: In a real test, we would need to create an actual PDF file
    # For now, we'll assume the file exists and contains only text
    
    # Process the file
    result = processor.extract_file(str(test_file), str(output_dir))
    
    # Verify results
    assert result is True
    output_file = output_dir / "text_only.txt"
    assert output_file.exists()
    
    content = output_file.read_text()
    assert "Text Only" in content

def test_process_directory(processor, test_data_dir, output_dir):
    """Test processing a directory with multiple PDF files"""
    # Create test PDF files
    test_files = {
        "report1.pdf": "Financial Report 1",
        "report2.pdf": "Financial Report 2",
        "paper1.pdf": "Academic Paper 1",
        "paper2.pdf": "Academic Paper 2"
    }
    
    for filename, content in test_files.items():
        file_path = test_data_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # Note: In a real test, we would need to create actual PDF files
        # For now, we'll assume the files exist
    
    # Process directory
    result = processor.process_directory(str(test_data_dir), str(output_dir))
    
    # Verify results
    assert result is not None
    assert "processed_files" in result
    assert "errors" in result
    
    # Check that all files were processed
    for filename in test_files.keys():
        output_file = output_dir / f"{Path(filename).stem}.txt"
        assert output_file.exists()

def test_error_handling(processor, test_data_dir, output_dir):
    """Test error handling for invalid files"""
    # Create invalid file
    test_file = test_data_dir / "invalid.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("This is not a PDF file")
    
    # Process the file
    result = processor.extract_file(str(test_file), str(output_dir))
    
    # Verify that the processor handles the error gracefully
    assert result is False
    assert not (output_dir / "invalid.txt").exists()

    # Keep generated files for inspection; only close log handlers.
    logging.shutdown()
    # If you want to clean up automatically, uncomment the next line.
    # shutil.rmtree(out_dir, ignore_errors=True) 