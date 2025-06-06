import unittest
from pathlib import Path
import json
from CryptoFinanceCorpusBuilder.utils.extractor_utils import load_json_config

class TestQualityControlConfig(unittest.TestCase):
    def setUp(self):
        self.config_path = Path("CryptoFinanceCorpusBuilder/config/quality_control_config.json")
        self.config = load_json_config(self.config_path)
    
    def test_config_structure(self):
        """Test that the config has all required sections."""
        required_sections = [
            "language_detection",
            "corruption_detection",
            "quality_metrics",
            "domain_classification",
            "table_detection",
            "formula_detection",
            "output_validation"
        ]
        for section in required_sections:
            self.assertIn(section, self.config)
    
    def test_language_detection_config(self):
        """Test language detection configuration values."""
        config = self.config["language_detection"]
        self.assertIsInstance(config["min_confidence"], float)
        self.assertIsInstance(config["allowed_languages"], list)
        self.assertIsInstance(config["mixed_language_threshold"], float)
        
        self.assertGreater(config["min_confidence"], 0)
        self.assertLess(config["min_confidence"], 1)
        self.assertGreater(config["mixed_language_threshold"], 0)
        self.assertLess(config["mixed_language_threshold"], 1)
        self.assertIn("en", config["allowed_languages"])
    
    def test_corruption_detection_config(self):
        """Test corruption detection configuration values."""
        config = self.config["corruption_detection"]
        self.assertIsInstance(config["non_printable_ratio_threshold"], float)
        self.assertIsInstance(config["long_run_threshold"], int)
        self.assertIsInstance(config["word_diversity_threshold"], float)
        self.assertIsInstance(config["symbol_ratio_threshold"], float)
        self.assertIsInstance(config["known_corruption_markers"], list)
        
        self.assertGreater(config["non_printable_ratio_threshold"], 0)
        self.assertLess(config["non_printable_ratio_threshold"], 1)
        self.assertGreater(config["long_run_threshold"], 0)
        self.assertGreater(config["word_diversity_threshold"], 0)
        self.assertLess(config["word_diversity_threshold"], 1)
        self.assertGreater(config["symbol_ratio_threshold"], 0)
        self.assertLess(config["symbol_ratio_threshold"], 1)
    
    def test_quality_metrics_config(self):
        """Test quality metrics configuration values."""
        config = self.config["quality_metrics"]
        self.assertIsInstance(config["min_tokens"], int)
        self.assertIsInstance(config["max_tokens"], int)
        self.assertIsInstance(config["min_sentence_length"], int)
        self.assertIsInstance(config["max_sentence_length"], int)
        self.assertIsInstance(config["min_word_length"], int)
        self.assertIsInstance(config["max_word_length"], int)
        
        self.assertGreater(config["min_tokens"], 0)
        self.assertGreater(config["max_tokens"], config["min_tokens"])
        self.assertGreater(config["min_sentence_length"], 0)
        self.assertGreater(config["max_sentence_length"], config["min_sentence_length"])
        self.assertGreater(config["min_word_length"], 0)
        self.assertGreater(config["max_word_length"], config["min_word_length"])
    
    def test_domain_classification_config(self):
        """Test domain classification configuration values."""
        config = self.config["domain_classification"]
        self.assertIsInstance(config["min_confidence"], float)
        self.assertIsInstance(config["required_keywords"], list)
        self.assertIsInstance(config["optional_keywords"], list)
        
        self.assertGreater(config["min_confidence"], 0)
        self.assertLess(config["min_confidence"], 1)
        self.assertGreater(len(config["required_keywords"]), 0)
        self.assertGreater(len(config["optional_keywords"]), 0)
    
    def test_table_detection_config(self):
        """Test table detection configuration values."""
        config = self.config["table_detection"]
        self.assertIsInstance(config["min_rows"], int)
        self.assertIsInstance(config["min_columns"], int)
        self.assertIsInstance(config["max_cell_length"], int)
        self.assertIsInstance(config["table_markers"], list)
        
        self.assertGreater(config["min_rows"], 0)
        self.assertGreater(config["min_columns"], 0)
        self.assertGreater(config["max_cell_length"], 0)
        self.assertGreater(len(config["table_markers"]), 0)
    
    def test_formula_detection_config(self):
        """Test formula detection configuration values."""
        config = self.config["formula_detection"]
        self.assertIsInstance(config["formula_markers"], list)
        self.assertGreater(len(config["formula_markers"]), 0)
    
    def test_output_validation_config(self):
        """Test output validation configuration values."""
        config = self.config["output_validation"]
        self.assertIsInstance(config["required_fields"], list)
        self.assertIsInstance(config["optional_fields"], list)
        
        self.assertGreater(len(config["required_fields"]), 0)
        self.assertGreater(len(config["optional_fields"]), 0)
        
        # Check for duplicate fields
        all_fields = config["required_fields"] + config["optional_fields"]
        self.assertEqual(len(all_fields), len(set(all_fields)))

if __name__ == "__main__":
    unittest.main() 