from pathlib import Path
from typing import Dict, Any, Tuple, List
import logging
import PyPDF2
import fitz  # PyMuPDF
from pdfminer.high_level import extract_text as pdfminer_extract
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTFigure
import concurrent.futures
import time

from .base_extractor import BaseExtractor, ExtractionError
from .mixins.table_mixin import TableMixin
from .mixins.formula_mixin import FormulaMixin

class PDFExtractor(BaseExtractor, TableMixin, FormulaMixin):
    """PDF text extractor with table and formula detection."""
    
    def __init__(self, 
                 input_dir: str,
                 output_dir: str,
                 num_workers: int = 4,
                 quality_config: str = None,
                 domain_config: str = None,
                 table_timeout: int = 30):
        """Initialize the PDF extractor.
        
        Args:
            input_dir: Directory containing PDF files
            output_dir: Directory to save extracted text and metadata
            num_workers: Number of worker processes
            quality_config: Path to quality control configuration
            domain_config: Path to domain classification configuration
            table_timeout: Timeout in seconds for table extraction
        """
        BaseExtractor.__init__(self, input_dir, output_dir, num_workers, quality_config, domain_config)
        TableMixin.__init__(self, table_timeout)
        FormulaMixin.__init__(self)
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def extract_text(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract text and metadata from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Tuple of (extracted_text, metadata_dict)
            
        Raises:
            ExtractionError: If extraction fails
        """
        if not file_path.exists():
            raise ExtractionError(f"File not found: {file_path}")
        
        try:
            # Extract text using multiple methods
            text_pypdf2 = self._extract_with_pypdf2(file_path)
            text_pymupdf = self._extract_with_pymupdf(file_path)
            text_pdfminer = self._extract_with_pdfminer(file_path)
            
            # Combine results
            text = self._combine_extracted_text(text_pypdf2, text_pymupdf, text_pdfminer)
            
            # Extract tables
            tables = self.extract_tables(file_path)
            
            # Extract formulas
            formulas = self.extract_formulas(text)
            
            # Prepare metadata
            metadata = {
                'extraction_methods': {
                    'pypdf2': bool(text_pypdf2),
                    'pymupdf': bool(text_pymupdf),
                    'pdfminer': bool(text_pdfminer)
                },
                'tables': tables,
                'formulas': formulas,
                'table_count': len(tables),
                'formula_count': len(formulas)
            }
            
            return text, metadata
            
        except Exception as e:
            raise ExtractionError(f"Error extracting text from {file_path}: {str(e)}")
    
    def _extract_with_pypdf2(self, file_path: Path) -> str:
        """Extract text using PyPDF2."""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            self.logger.warning(f"PyPDF2 extraction failed for {file_path}: {str(e)}")
            return ""
    
    def _extract_with_pymupdf(self, file_path: Path) -> str:
        """Extract text using PyMuPDF."""
        try:
            text = ""
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            return text
        except Exception as e:
            self.logger.warning(f"PyMuPDF extraction failed for {file_path}: {str(e)}")
            return ""
    
    def _extract_with_pdfminer(self, file_path: Path) -> str:
        """Extract text using pdfminer."""
        try:
            text = ""
            for page_layout in extract_pages(file_path):
                for element in page_layout:
                    if isinstance(element, LTTextContainer):
                        text += element.get_text() + "\n"
            return text
        except Exception as e:
            self.logger.warning(f"pdfminer extraction failed for {file_path}: {str(e)}")
            return ""
    
    def _combine_extracted_text(self, text1: str, text2: str, text3: str) -> str:
        """Combine text from multiple extraction methods."""
        # Use the longest non-empty text
        texts = [text1, text2, text3]
        valid_texts = [t for t in texts if t.strip()]
        if not valid_texts:
            return ""
        return max(valid_texts, key=len) 