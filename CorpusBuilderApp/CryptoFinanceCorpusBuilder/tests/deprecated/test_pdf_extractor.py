import unittest
from pathlib import Path
import tempfile
import json
import shutil
from CryptoFinanceCorpusBuilder.processors.pdf_extractor import PDFExtractor
from shared_tools.models.quality_config import QualityConfig

class TestPDFExtractor(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create test directories
        self.input_dir = self.test_dir / "input"
        self.output_dir = self.test_dir / "output"
        self.input_dir.mkdir()
        self.output_dir.mkdir()
        
        # Copy test PDFs
        self.test_pdfs = [
            "crypto_derivatives_Deep_learning_and_decision_making.pdf",
            "crypto_derivatives_Deep_learning_and_decision_making_2.pdf",
            "crypto_derivatives_Deep_learning_and_decision_making_3.pdf"
        ]
        
        for pdf in self.test_pdfs:
            src = Path("CryptoFinanceCorpusBuilder/tests/pdf_extraction/test_pdfs") / pdf
            dst = self.input_dir / pdf
            shutil.copy2(src, dst)
        
        # Create test config
        self.config_file = self.test_dir / "test_config.json"
        config = QualityConfig().dict()
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f)
        
        # Initialize extractor
        self.extractor = PDFExtractor(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            quality_config=self.config_file
        )
    
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    def test_extraction_pipeline(self):
        """Test the complete PDF extraction pipeline."""
        # Run extraction
        results = self.extractor.run()
        
        # Check results structure
        self.assertIn('successful', results)
        self.assertIn('failed', results)
        self.assertEqual(len(results['successful']), len(self.test_pdfs))
        self.assertEqual(len(results['failed']), 0)
        
        # Check output files
        for pdf in self.test_pdfs:
            base_name = Path(pdf).stem
            text_file = self.extractor.extracted_dir / f"{base_name}.txt"
            metadata_file = self.extractor.extracted_dir / f"{base_name}.json"
            
            self.assertTrue(text_file.exists())
            self.assertTrue(metadata_file.exists())
            
            # Check text content
            with open(text_file, "r", encoding="utf-8") as f:
                text = f.read()
            self.assertTrue(len(text) > 0)
            
            # Check metadata content
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            # Verify metadata schema
            self.assertIn('extraction_methods', metadata)
            self.assertIn('tables', metadata)
            self.assertIn('formulas', metadata)
            self.assertIn('table_count', metadata)
            self.assertIn('formula_count', metadata)
            self.assertIn('quality_metrics', metadata)
            self.assertIn('language_detection', metadata)
            self.assertIn('corruption_detection', metadata)
            self.assertIn('domain_classification', metadata)
    
    def test_table_extraction(self):
        """Test table extraction functionality."""
        # Process a single file
        pdf_path = self.input_dir / self.test_pdfs[0]
        result = self.extractor.process_file(pdf_path)
        
        self.assertIsNotNone(result)
        self.assertIn('tables', result)
        self.assertIn('table_count', result)
        
        # Check table structure
        for table in result['tables']:
            self.assertIn('table_id', table)
            self.assertIn('page', table)
            self.assertIn('accuracy', table)
            self.assertIn('whitespace', table)
            self.assertIn('order', table)
            self.assertIn('data', table)
            self.assertIn('shape', table)
            self.assertIn('extraction_method', table)
    
    def test_formula_extraction(self):
        """Test formula extraction functionality."""
        # Process a single file
        pdf_path = self.input_dir / self.test_pdfs[0]
        result = self.extractor.process_file(pdf_path)
        
        self.assertIsNotNone(result)
        self.assertIn('formulas', result)
        self.assertIn('formula_count', result)
        
        # Check formula structure
        for formula in result['formulas']:
            self.assertIn('formula_id', formula)
            self.assertIn('type', formula)
            self.assertIn('content', formula)
            self.assertIn('position', formula)
            self.assertIn('order', formula)
    
    def test_quality_control(self):
        """Test quality control integration."""
        # Process a single file
        pdf_path = self.input_dir / self.test_pdfs[0]
        result = self.extractor.process_file(pdf_path)
        
        self.assertIsNotNone(result)
        self.assertIn('quality_metrics', result)
        self.assertIn('language_detection', result)
        self.assertIn('corruption_detection', result)
        
        # Check quality metrics
        metrics = result['quality_metrics']
        self.assertIn('token_count', metrics)
        self.assertIn('sentence_count', metrics)
        self.assertIn('word_count', metrics)
        self.assertIn('quality_score', metrics)
        
        # Check language detection
        lang = result['language_detection']
        self.assertIn('language', lang)
        self.assertIn('confidence', lang)
        self.assertIn('mixed_language', lang)
        
        # Check corruption detection
        corruption = result['corruption_detection']
        self.assertIn('corruption_score', corruption)
        self.assertIn('corruption_flags', corruption)
    
    def test_domain_classification(self):
        """Test domain classification integration."""
        # Process a single file
        pdf_path = self.input_dir / self.test_pdfs[0]
        result = self.extractor.process_file(pdf_path)
        
        self.assertIsNotNone(result)
        self.assertIn('domain_classification', result)
        
        # Check domain classification structure
        domain = result['domain_classification']
        self.assertIn('domain', domain)
        self.assertIn('confidence', domain)
        self.assertIn('keywords', domain)

if __name__ == "__main__":
    unittest.main() 