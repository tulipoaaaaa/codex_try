import pytest
from pathlib import Path
import os
import shutil
from CorpusBuilderApp.shared_tools.processors.batch_nonpdf_extractor_enhanced import BatchNonPDFExtractorEnhanced

@pytest.fixture
def test_data_dir():
    """Fixture to provide test data directory"""
    return Path("G:/data/test_processors/nonpdf_processors")

@pytest.fixture
def output_dir():
    """Fixture to provide output directory within the test data directory"""
    output_path = Path("G:/data/test_processors/nonpdf_processors/output")
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path

@pytest.fixture
def processor():
    """Fixture to provide configured processor instance"""
    processor = BatchNonPDFExtractorEnhanced()
    processor.configure(
        max_workers=2,
        timeout=30,
        chunk_size=1000,
        chunk_overlap=100
    )
    return processor

def test_process_python_file(processor, test_data_dir, output_dir):
    """Test processing a Python file"""
    # Create test Python file
    test_file = test_data_dir / "test_script.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    test_code = """
def calculate_risk(portfolio):
    \"\"\"Calculate portfolio risk using VaR\"\"\"
    var_95 = portfolio.quantile(0.95)
    return var_95

class RiskManager:
    def __init__(self):
        self.threshold = 0.05
    
    def check_risk(self, value):
        return value < self.threshold
"""
    test_file.write_text(test_code)
    
    # Process the file
    result = processor.extract_file(str(test_file), str(output_dir))
    
    # Verify results
    assert result is True
    output_file = output_dir / "test_script.txt"
    assert output_file.exists()
    
    content = output_file.read_text()
    assert "calculate_risk" in content
    assert "RiskManager" in content
    assert "VaR" in content

def test_process_markdown_file(processor, test_data_dir, output_dir):
    """Test processing a Markdown file"""
    # Create test Markdown file
    test_file = test_data_dir / "test_doc.md"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    test_content = """
# Financial Analysis Report

## Risk Assessment
- VaR at 95% confidence: 2.5%
- Expected Shortfall: 3.1%

## Portfolio Metrics
| Metric | Value |
|--------|-------|
| Sharpe Ratio | 1.8 |
| Sortino Ratio | 2.1 |
"""
    test_file.write_text(test_content)
    
    # Process the file
    result = processor.extract_file(str(test_file), str(output_dir))
    
    # Verify results
    assert result is True
    output_file = output_dir / "test_doc.txt"
    assert output_file.exists()
    
    content = output_file.read_text()
    assert "Financial Analysis Report" in content
    assert "Risk Assessment" in content
    assert "Portfolio Metrics" in content

def test_process_html_file(processor, test_data_dir, output_dir):
    """Test processing an HTML file"""
    # Create test HTML file
    test_file = test_data_dir / "test_report.html"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    test_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Market Analysis</title>
</head>
<body>
    <h1>Market Analysis Report</h1>
    <div class="content">
        <h2>Key Findings</h2>
        <p>Market volatility increased by 15% in Q3.</p>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Volatility</td><td>15%</td></tr>
        </table>
    </div>
</body>
</html>
"""
    test_file.write_text(test_content)
    
    # Process the file
    result = processor.extract_file(str(test_file), str(output_dir))
    
    # Verify results
    assert result is True
    output_file = output_dir / "test_report.txt"
    assert output_file.exists()
    
    content = output_file.read_text()
    assert "Market Analysis Report" in content
    assert "Key Findings" in content
    assert "Market volatility" in content

def test_process_json_file(processor, test_data_dir, output_dir):
    """Test processing a JSON file"""
    # Create test JSON file
    test_file = test_data_dir / "test_data.json"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    test_content = """
{
    "portfolio": {
        "name": "High Frequency Trading",
        "metrics": {
            "sharpe_ratio": 2.1,
            "sortino_ratio": 2.5,
            "var_95": 0.02
        },
        "positions": [
            {"symbol": "AAPL", "weight": 0.3},
            {"symbol": "MSFT", "weight": 0.7}
        ]
    }
}
"""
    test_file.write_text(test_content)
    
    # Process the file
    result = processor.extract_file(str(test_file), str(output_dir))
    
    # Verify results
    assert result is True
    output_file = output_dir / "test_data.txt"
    assert output_file.exists()
    
    content = output_file.read_text()
    assert "High Frequency Trading" in content
    assert "sharpe_ratio" in content
    assert "AAPL" in content

def test_process_csv_file(processor, test_data_dir, output_dir):
    """Test processing a CSV file"""
    # Create test CSV file
    test_file = test_data_dir / "test_data.csv"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    test_content = """Date,Symbol,Price,Volume
2024-01-01,AAPL,150.25,1000000
2024-01-01,MSFT,280.50,500000
2024-01-02,AAPL,151.75,1200000
2024-01-02,MSFT,281.25,600000"""
    test_file.write_text(test_content)
    
    # Process the file
    result = processor.extract_file(str(test_file), str(output_dir))
    
    # Verify results
    assert result is True
    output_file = output_dir / "test_data.txt"
    assert output_file.exists()
    
    content = output_file.read_text()
    assert "AAPL" in content
    assert "MSFT" in content
    assert "150.25" in content

def test_process_directory(processor, test_data_dir, output_dir):
    """Test processing a directory with multiple file types"""
    # Create test files
    test_files = {
        "script.py": "def calculate_risk(): pass",
        "report.md": "# Test Report\n## Section\nContent",
        "data.html": "<html><body>Test</body></html>",
        "config.json": '{"key": "value"}',
        "prices.csv": "Date,Price\n2024-01-01,100"
    }
    
    for filename, content in test_files.items():
        file_path = test_data_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
    
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
    test_file.write_text("This is not a supported file type")
    
    # Process the file
    result = processor.extract_file(str(test_file), str(output_dir))
    
    # Verify that the processor handles the error gracefully
    assert result is False
    assert not (output_dir / "invalid.txt").exists() 