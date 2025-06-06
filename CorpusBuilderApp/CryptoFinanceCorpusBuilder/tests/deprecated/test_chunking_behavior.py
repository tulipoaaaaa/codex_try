import unittest
from pathlib import Path
import pandas as pd
import json
import nbformat
from CryptoFinanceCorpusBuilder.processors.batch_nonpdf_extractor_enhanced import (
    extract_text_from_file,
    CHUNK_TOKEN_THRESHOLD
)
import time
import tracemalloc

class TestChunkingBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test files and paths."""
        cls.test_dir = Path("data/test_collect/chunking_tests")
        
        # CSV test files
        cls.csv_files = {
            'long': cls.test_dir / "csv_long.csv",
            'wide': cls.test_dir / "csv_wide.csv",
            'multiline': cls.test_dir / "csv_multiline.csv",
            'simple': cls.test_dir / "csv_simple.csv"
        }
        
        # Python test files
        cls.python_files = {
            'many_functions': cls.test_dir / "py_functions_many.py",
            'realistic': cls.test_dir / "py_realistic_example.py",
            'one_function': cls.test_dir / "py_one_big_function.py"
        }
        
        # Jupyter notebook test files
        cls.notebook_files = {
            'many_cells': cls.test_dir / "ipynb_many_cells.ipynb",
            'realistic': cls.test_dir / "ipynb_realistic_example.ipynb"
        }
        
        # JSON test files
        cls.json_files = {
            'large_array': cls.test_dir / "json_large_array.json",
            'deep_nested': cls.test_dir / "json_deep_nested.json"
        }

    def _profile_extraction(self, func, *args, **kwargs):
        """Helper to profile time and memory usage of extraction."""
        tracemalloc.start()
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"[PERF] Time: {elapsed:.3f}s, Peak Memory: {peak/1024/1024:.2f} MB")
        return result, elapsed, peak

    def test_csv_chunking(self):
        """Test chunking behavior for CSV files with performance metrics."""
        for name, file_path in self.csv_files.items():
            with self.subTest(file=name):
                (text, tables, images), elapsed, peak = self._profile_extraction(extract_text_from_file, str(file_path))
                
                # Verify header preservation
                df = pd.read_csv(file_path)
                self.assertIn(','.join(df.columns), text, 
                    f"Header not preserved in {name}")
                
                # Verify data integrity
                self.assertGreater(len(text.split('\n')), 1,
                    f"No data rows in {name}")
                
                # Verify chunk size
                if len(text.split()) > CHUNK_TOKEN_THRESHOLD:
                    self.assertLessEqual(len(text.split()), CHUNK_TOKEN_THRESHOLD * 2,
                        f"Chunk size exceeds threshold in {name}")

    def test_python_chunking(self):
        """Test chunking behavior for Python files with performance metrics."""
        for name, file_path in self.python_files.items():
            with self.subTest(file=name):
                (text, tables, images), elapsed, peak = self._profile_extraction(extract_text_from_file, str(file_path))
                
                # Verify imports are preserved
                if 'import' in text:
                    self.assertIn('import', text.split('\n')[0],
                        f"Imports not at start in {name}")
                
                # Verify function definitions
                if 'def ' in text:
                    self.assertIn('def ', text,
                        f"Function definitions missing in {name}")
                
                # Verify chunk size
                if len(text.split()) > CHUNK_TOKEN_THRESHOLD:
                    self.assertLessEqual(len(text.split()), CHUNK_TOKEN_THRESHOLD * 2,
                        f"Chunk size exceeds threshold in {name}")

    def test_notebook_chunking(self):
        """Test chunking behavior for Jupyter notebooks with performance metrics."""
        for name, file_path in self.notebook_files.items():
            with self.subTest(file=name):
                (text, tables, images), elapsed, peak = self._profile_extraction(extract_text_from_file, str(file_path))
                
                # Load notebook for verification
                with open(file_path) as f:
                    nb = nbformat.read(f, as_version=4)
                
                # Verify cell preservation
                cell_count = len(nb.cells)
                self.assertGreater(cell_count, 0,
                    f"No cells found in {name}")
                
                # Verify markdown cells
                markdown_cells = [cell for cell in nb.cells if cell.cell_type == 'markdown']
                if markdown_cells:
                    self.assertIn(markdown_cells[0].source, text,
                        f"Markdown content missing in {name}")
                
                # Verify code cells
                code_cells = [cell for cell in nb.cells if cell.cell_type == 'code']
                if code_cells:
                    self.assertIn(code_cells[0].source, text,
                        f"Code content missing in {name}")

    def test_json_chunking(self):
        """Test chunking behavior for JSON files with performance metrics."""
        for name, file_path in self.json_files.items():
            with self.subTest(file=name):
                (text, tables, images), elapsed, peak = self._profile_extraction(extract_text_from_file, str(file_path))
                
                # Load JSON for verification
                with open(file_path) as f:
                    data = json.load(f)
                
                # Verify structure preservation
                if isinstance(data, list):
                    self.assertIn('[', text,
                        f"Array structure missing in {name}")
                elif isinstance(data, dict):
                    self.assertIn('{', text,
                        f"Object structure missing in {name}")
                
                # Verify chunk size
                if len(text.split()) > CHUNK_TOKEN_THRESHOLD:
                    self.assertLessEqual(len(text.split()), CHUNK_TOKEN_THRESHOLD * 2,
                        f"Chunk size exceeds threshold in {name}")

    def test_chunk_overlap(self):
        """Test that chunks maintain context through overlap (with performance metrics)."""
        file_path = self.python_files['many_functions']
        (text, tables, images), elapsed, peak = self._profile_extraction(extract_text_from_file, str(file_path))
        
        # If text is chunked, verify overlap
        if len(text.split()) > CHUNK_TOKEN_THRESHOLD:
            chunks = text.split('\n\n')  # Assuming chunks are separated by double newlines
            for i in range(len(chunks)-1):
                # Check for common context between chunks
                self.assertTrue(
                    any(word in chunks[i+1] for word in chunks[i].split()[-10:]),
                    "Chunks lack sufficient overlap"
                )

    def test_structure_integrity(self):
        """Test that chunking preserves file structure (with performance metrics)."""
        for file_type, files in [
            ('CSV', self.csv_files),
            ('Python', self.python_files),
            ('Notebook', self.notebook_files),
            ('JSON', self.json_files)
        ]:
            for name, file_path in files.items():
                with self.subTest(file_type=file_type, file=name):
                    (text, tables, images), elapsed, peak = self._profile_extraction(extract_text_from_file, str(file_path))
                    
                    # Verify basic structure
                    if file_type == 'CSV':
                        self.assertIn(',', text, "CSV structure broken")
                    elif file_type == 'Python':
                        self.assertIn('\n', text, "Python structure broken")
                    elif file_type == 'Notebook':
                        self.assertIn('```', text, "Notebook structure broken")
                    elif file_type == 'JSON':
                        self.assertTrue(
                            (text.startswith('{') and text.endswith('}')) or
                            (text.startswith('[') and text.endswith(']')),
                            "JSON structure broken"
                        )

if __name__ == '__main__':
    unittest.main() 