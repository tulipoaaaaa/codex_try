import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the old BitMEX collector
from CryptoFinanceCorpusBuilder.cli.collectors.collect_bitmex import run_bitmex_collector

class Args:
    bitmex_clear_output_dir = True
    bitmex_keywords = ["bitcoin", "research"]
    bitmex_max_pages = 1
    existing_titles = None

class TestBitmexCollector(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.source_config = None
        self.base_dir = self.test_dir

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("CryptoFinanceCorpusBuilder.cli.collectors.collect_bitmex.requests.Session.get")
    def test_collect_bitmex_posts(self, mock_get):
        # Mock the BitMEX research page HTML
        with open(os.path.join(os.path.dirname(__file__), "mock_bitmex_research.html"), "r", encoding="utf-8") as f:
            html_content = f.read()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_get.return_value = mock_response

        args = Args()
        # Run the collector
        run_bitmex_collector(args, self.source_config, self.base_dir)

        # Check that output directory and metadata file exist
        output_dir = Path(self.base_dir) / "bitmex_research"
        metadata_file = output_dir / "bitmex_research_posts.json"
        self.assertTrue(output_dir.exists())
        self.assertTrue(metadata_file.exists())
        # Optionally, check that the metadata file contains expected data
        import json
        with open(metadata_file, "r", encoding="utf-8") as f:
            posts = json.load(f)
        self.assertIsInstance(posts, list)
        self.assertGreaterEqual(len(posts), 1)
        self.assertIn("title", posts[0])

if __name__ == "__main__":
    unittest.main() 