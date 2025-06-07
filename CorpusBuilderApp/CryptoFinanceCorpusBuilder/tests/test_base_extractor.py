import unittest
from pathlib import Path
import tempfile
import json
from typing import Dict, Any, Tuple
from CryptoFinanceCorpusBuilder.processors.base_extractor import BaseExtractor, ExtractionError
from shared_tools.models.quality_config import QualityConfig

class TestExtractor(BaseExtractor):
    """Test implementation of BaseExtractor."""
    
    def extract_text(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Test implementation of extract_text."""
        if not file_path.exists():
            raise ExtractionError(f"File not found: {file_path}")
        
        text = file_path.read_text(encoding='utf-8')
        metadata = {
            'test_metadata': 'test_value'
        }
        return text, metadata

class TestBaseExtractor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create test files
        self.input_dir = self.test_dir / "input"
        self.output_dir = self.test_dir / "output"
        self.input_dir.mkdir()
        self.output_dir.mkdir()
        
        self.test_file = self.input_dir / "test.txt"
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("This is a test file.\nIt has multiple lines.\n")
        
        # Create test config
        self.config_file = self.test_dir / "test_config.json"
        config = QualityConfig().dict()
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f)
        
        # Initialize extractor
        self.extractor = TestExtractor(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            quality_config=self.config_file
        )
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_initialization(self):
        """Test extractor initialization."""
        self.assertEqual(self.extractor.input_dir, self.input_dir)
        self.assertEqual(self.extractor.output_dir, self.output_dir)
        self.assertIsInstance(self.extractor.quality_config, QualityConfig)
    
    def test_process_file(self):
        """Test processing a single file."""
        result = self.extractor.process_file(self.test_file)
        self.assertIsNotNone(result)
        self.assertIn('test_metadata', result)
        self.assertIn('source_file', result)
        self.assertIn('extraction_date', result)
        self.assertIn('extractor', result)
        self.assertIn('file_type', result)
        self.assertIn('text_hash', result)
        
        # Check output files
        text_file = self.extractor.extracted_dir / "test.txt"
        metadata_file = self.extractor.extracted_dir / "test.json"
        self.assertTrue(text_file.exists())
        self.assertTrue(metadata_file.exists())
        
        # Check text content
        with open(text_file, "r", encoding="utf-8") as f:
            text = f.read()
        self.assertEqual(text, "This is a test file.\nIt has multiple lines.\n")
        
        # Check metadata content
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        self.assertEqual(metadata['test_metadata'], 'test_value')
    
    def test_process_nonexistent_file(self):
        """Test processing a nonexistent file."""
        nonexistent_file = self.input_dir / "nonexistent.txt"
        result = self.extractor.process_file(nonexistent_file)
        self.assertIsNone(result)
    
    def test_process_batch(self):
        """Test processing multiple files."""
        # Create additional test files
        test_file2 = self.input_dir / "test2.txt"
        with open(test_file2, "w", encoding="utf-8") as f:
            f.write("Another test file.")
        
        test_file3 = self.input_dir / "test3.txt"
        with open(test_file3, "w", encoding="utf-8") as f:
            f.write("Third test file.")
        
        results = self.extractor.process_batch([self.test_file, test_file2, test_file3])
        
        self.assertIn('successful', results)
        self.assertIn('failed', results)
        self.assertEqual(len(results['successful']), 3)
        self.assertEqual(len(results['failed']), 0)
    
    def test_run(self):
        """Test running the extractor on all files."""
        # Create additional test files
        test_file2 = self.input_dir / "test2.txt"
        with open(test_file2, "w", encoding="utf-8") as f:
            f.write("Another test file.")
        
        test_file3 = self.input_dir / "test3.txt"
        with open(test_file3, "w", encoding="utf-8") as f:
            f.write("Third test file.")
        
        results = self.extractor.run()
        
        self.assertIn('successful', results)
        self.assertIn('failed', results)
        self.assertEqual(len(results['successful']), 3)
        self.assertEqual(len(results['failed']), 0)
    
    def test_safe_filename(self):
        """Test handling of filenames with special characters."""
        special_file = self.input_dir / "test:file.txt"
        with open(special_file, "w", encoding="utf-8") as f:
            f.write("File with special characters.")
        
        result = self.extractor.process_file(special_file)
        self.assertIsNotNone(result)
        
        # Check that output files use safe filenames
        text_file = self.extractor.extracted_dir / "test_file.txt"
        metadata_file = self.extractor.extracted_dir / "test_file.json"
        self.assertTrue(text_file.exists())
        self.assertTrue(metadata_file.exists())

if __name__ == "__main__":
    unittest.main() 