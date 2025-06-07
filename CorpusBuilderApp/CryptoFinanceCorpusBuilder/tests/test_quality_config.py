# DEPRECATED: This file belongs to the legacy CryptoFinanceCorpusBuilder package and should not be used in new modules.
import unittest
from pathlib import Path
import json
from shared_tools.models.quality_config import (
    QualityConfig,
    LanguageDetectionConfig,
    CorruptionDetectionConfig,
    QualityMetricsConfig,
    DomainClassificationConfig,
    TableDetectionConfig,
    FormulaDetectionConfig,
    OutputValidationConfig
)

class TestQualityConfig(unittest.TestCase):
    def setUp(self):
        self.config_path = Path("CryptoFinanceCorpusBuilder/config/quality_control_config.json")
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config_data = json.load(f)
    
    def test_load_from_json(self):
        """Test loading configuration from JSON."""
        config = QualityConfig.parse_obj(self.config_data)
        self.assertIsInstance(config, QualityConfig)
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        config = QualityConfig()
        self.assertEqual(config.language_detection.min_confidence, 0.8)
        self.assertEqual(config.language_detection.allowed_languages, ["en"])
        self.assertEqual(config.language_detection.mixed_language_threshold, 0.2)
    
    def test_validation_rules(self):
        """Test validation rules for configuration values."""
        # Test invalid min_confidence
        with self.assertRaises(ValueError):
            LanguageDetectionConfig(min_confidence=1.5)
        
        # Test invalid max_tokens
        with self.assertRaises(ValueError):
            QualityMetricsConfig(min_tokens=1000, max_tokens=100)
        
        # Test invalid field names
        with self.assertRaises(ValueError):
            OutputValidationConfig(
                required_fields=["valid_field", "invalid-field"],
                optional_fields=["another_field"]
            )
        
        # Test duplicate fields
        with self.assertRaises(ValueError):
            OutputValidationConfig(
                required_fields=["field1", "field2"],
                optional_fields=["field2", "field3"]
            )
    
    def test_nested_validation(self):
        """Test validation of nested configuration objects."""
        config = QualityConfig(
            language_detection=LanguageDetectionConfig(
                min_confidence=0.9,
                allowed_languages=["en", "es"],
                mixed_language_threshold=0.1
            ),
            quality_metrics=QualityMetricsConfig(
                min_tokens=100,
                max_tokens=1000,
                min_sentence_length=5,
                max_sentence_length=50,
                min_word_length=2,
                max_word_length=20
            )
        )
        self.assertEqual(config.language_detection.min_confidence, 0.9)
        self.assertEqual(config.quality_metrics.max_tokens, 1000)
    
    def test_corruption_detection_config(self):
        """Test corruption detection configuration."""
        config = CorruptionDetectionConfig()
        self.assertGreater(config.non_printable_ratio_threshold, 0)
        self.assertLess(config.non_printable_ratio_threshold, 1)
        self.assertGreater(config.long_run_threshold, 0)
        self.assertGreater(len(config.known_corruption_markers), 0)
    
    def test_domain_classification_config(self):
        """Test domain classification configuration."""
        config = DomainClassificationConfig()
        self.assertGreater(config.min_confidence, 0)
        self.assertLess(config.min_confidence, 1)
        self.assertGreater(len(config.required_keywords), 0)
        self.assertGreater(len(config.optional_keywords), 0)
    
    def test_table_detection_config(self):
        """Test table detection configuration."""
        config = TableDetectionConfig()
        self.assertGreater(config.min_rows, 0)
        self.assertGreater(config.min_columns, 0)
        self.assertGreater(config.max_cell_length, 0)
        self.assertGreater(len(config.table_markers), 0)
    
    def test_formula_detection_config(self):
        """Test formula detection configuration."""
        config = FormulaDetectionConfig()
        self.assertGreater(len(config.formula_markers), 0)
    
    def test_output_validation_config(self):
        """Test output validation configuration."""
        config = OutputValidationConfig()
        self.assertGreater(len(config.required_fields), 0)
        self.assertGreater(len(config.optional_fields), 0)
        
        # Check for duplicate fields
        all_fields = config.required_fields + config.optional_fields
        self.assertEqual(len(all_fields), len(set(all_fields)))

if __name__ == "__main__":
    unittest.main() 