import unittest
from pathlib import Path
import tempfile
import json
from CryptoFinanceCorpusBuilder.utils.extractor_utils import (
    safe_filename,
    count_tokens,
    extract_metadata,
    calculate_hash,
    load_json_config,
    save_metadata,
    chunk_text,
    detect_file_type,
    normalize_text,
    calculate_similarity
)

class TestExtractorUtils(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create test files
        self.test_file = self.test_dir / "test.txt"
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("This is a test file.\nIt has multiple lines.\n")
            
        self.test_json = self.test_dir / "test.json"
        with open(self.test_json, "w", encoding="utf-8") as f:
            json.dump({"test": "data"}, f)
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_safe_filename(self):
        # Test basic functionality
        self.assertEqual(safe_filename("test.txt"), "test.txt")
        # Test special characters
        self.assertEqual(safe_filename("test:file.txt"), "test_file.txt")
        # Test spaces and dots
        self.assertEqual(safe_filename(" test.file.txt "), "test_file.txt")
    
    def test_count_tokens(self):
        # Test basic functionality
        self.assertEqual(count_tokens("This is a test"), 4)
        # Test empty string
        self.assertEqual(count_tokens(""), 0)
        # Test multiple spaces
        self.assertEqual(count_tokens("  multiple   spaces  "), 2)
    
    def test_extract_metadata(self):
        metadata = extract_metadata(self.test_file)
        self.assertEqual(metadata["filename"], "test.txt")
        self.assertEqual(metadata["file_type"], ".txt")
        self.assertIn("file_size", metadata)
        self.assertIn("created_date", metadata)
        self.assertIn("modified_date", metadata)
    
    def test_calculate_hash(self):
        # Test basic functionality
        text = "test text"
        hash1 = calculate_hash(text)
        hash2 = calculate_hash(text)
        self.assertEqual(hash1, hash2)
        # Test different texts
        hash3 = calculate_hash("different text")
        self.assertNotEqual(hash1, hash3)
    
    def test_load_json_config(self):
        # Test valid JSON
        config = load_json_config(self.test_json)
        self.assertEqual(config, {"test": "data"})
        # Test non-existent file
        with self.assertRaises(FileNotFoundError):
            load_json_config(self.test_dir / "nonexistent.json")
    
    def test_save_metadata(self):
        metadata = {"test": "data"}
        output_path = self.test_dir / "metadata.json"
        save_metadata(metadata, output_path)
        self.assertTrue(output_path.exists())
        with open(output_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data, metadata)
    
    def test_chunk_text(self):
        text = "This is a test. It has multiple sentences. This is another sentence."
        chunks = chunk_text(text, chunk_size=20, overlap=5)
        self.assertGreater(len(chunks), 1)
        # Check that chunks overlap
        self.assertIn(chunks[0][-5:], chunks[1])
    
    def test_detect_file_type(self):
        # Test known extensions
        self.assertEqual(detect_file_type(Path("test.pdf")), "pdf")
        self.assertEqual(detect_file_type(Path("test.md")), "markdown")
        # Test unknown extension
        self.assertEqual(detect_file_type(Path("test.xyz")), "unknown")
    
    def test_normalize_text(self):
        # Test basic functionality
        text = "  This is a TEST!  "
        normalized = normalize_text(text)
        self.assertEqual(normalized, "this is a test")
        # Test multiple spaces and punctuation
        text = "  Multiple   spaces...  and  punctuation!!!  "
        normalized = normalize_text(text)
        self.assertEqual(normalized, "multiple spaces and punctuation")
    
    def test_calculate_similarity(self):
        # Test identical texts
        text1 = "This is a test"
        text2 = "This is a test"
        self.assertEqual(calculate_similarity(text1, text2), 1.0)
        # Test different texts
        text3 = "This is different"
        similarity = calculate_similarity(text1, text3)
        self.assertGreater(similarity, 0)
        self.assertLess(similarity, 1.0)
        # Test empty texts
        self.assertEqual(calculate_similarity("", ""), 0.0)

if __name__ == "__main__":
    unittest.main() 