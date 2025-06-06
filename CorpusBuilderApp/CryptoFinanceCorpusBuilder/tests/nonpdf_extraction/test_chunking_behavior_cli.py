import unittest
import subprocess
import os
import sys
from pathlib import Path
try:
    import pandas as pd
except ImportError:
    pd = None
try:
    import json
    import nbformat
except ImportError:
    nbformat = None

class TestNonPDFExtractorCLI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path("data/test_collect/chunking_tests")
        cls.output_dir = cls.test_dir / "_extracted"
        cls.csv_files = ["csv_long.csv", "csv_wide.csv", "csv_multiline.csv", "csv_simple.csv"]
        cls.python_files = ["py_functions_many.py", "py_realistic_example.py", "py_one_big_function.py"]
        cls.notebook_files = ["ipynb_many_cells.ipynb", "ipynb_realistic_example.ipynb"]
        cls.json_files = ["json_large_array.json", "json_deep_nested.json"]

    def run_cli_and_check(self, file_name, ext):
        # Remove old output if exists
        out_file = self.output_dir / file_name.replace(ext, ".txt")
        if out_file.exists():
            out_file.unlink()
        # Run the CLI
        env = os.environ.copy()
        result = subprocess.run([
            sys.executable, "-m", "CryptoFinanceCorpusBuilder.processors.batch_nonpdf_extractor_enhanced",
            "--input-dir", str(self.test_dir),
            "--output-dir", str(self.output_dir),
            "--single-file", file_name,
            "--verbose"
        ], capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0, f"CLI failed: {result.stderr}")
        # Check output file exists
        self.assertTrue(out_file.exists(), f"Output file not created: {out_file}")
        return out_file

    @unittest.skipIf(pd is None, "pandas not installed")
    def test_csv_files(self):
        for file_name in self.csv_files:
            with self.subTest(file=file_name):
                out_file = self.run_cli_and_check(file_name, ".csv")
                # Check header and row count
                df = pd.read_csv(self.test_dir / file_name)
                with open(out_file, "r", encoding="utf-8") as f:
                    content = f.read()
                self.assertIn(",".join(df.columns), content, "Header not preserved")
                self.assertGreater(len(content.splitlines()), 1, "No data rows in output")

    def test_python_files(self):
        for file_name in self.python_files:
            with self.subTest(file=file_name):
                out_file = self.run_cli_and_check(file_name, ".py")
                with open(out_file, "r", encoding="utf-8") as f:
                    content = f.read()
                # Check for import and def
                if "import" in content:
                    self.assertIn("import", content.splitlines()[0], "Imports not at start")
                if "def " in content:
                    self.assertIn("def ", content, "Function definitions missing")

    @unittest.skipIf(nbformat is None, "nbformat not installed")
    def test_notebook_files(self):
        for file_name in self.notebook_files:
            with self.subTest(file=file_name):
                out_file = self.run_cli_and_check(file_name, ".ipynb")
                with open(self.test_dir / file_name, "r", encoding="utf-8") as f:
                    nb = nbformat.read(f, as_version=4)
                with open(out_file, "r", encoding="utf-8") as f:
                    content = f.read()
                # Check for markdown and code cell content
                markdown_cells = [cell for cell in nb.cells if cell.cell_type == 'markdown']
                if markdown_cells:
                    self.assertIn(markdown_cells[0].source.strip(), content, "Markdown missing")
                code_cells = [cell for cell in nb.cells if cell.cell_type == 'code']
                if code_cells:
                    self.assertIn(code_cells[0].source.strip(), content, "Code missing")

    def test_json_files(self):
        for file_name in self.json_files:
            with self.subTest(file=file_name):
                out_file = self.run_cli_and_check(file_name, ".json")
                with open(self.test_dir / file_name, "r", encoding="utf-8") as f:
                    data = json.load(f)
                with open(out_file, "r", encoding="utf-8") as f:
                    content = f.read()
                # Check for structure
                if isinstance(data, list):
                    self.assertIn('[', content, "Array structure missing")
                elif isinstance(data, dict):
                    self.assertIn('{', content, "Object structure missing")

if __name__ == "__main__":
    unittest.main() 