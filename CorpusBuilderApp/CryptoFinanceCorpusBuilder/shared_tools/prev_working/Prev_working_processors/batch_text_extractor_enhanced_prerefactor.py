import os
import sys
import tempfile
import uuid
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import logging
import time
import multiprocessing

# ===== CRITICAL: Set Ghostscript environment FIRST, before any imports =====
def setup_ghostscript_environment():
    """Setup Ghostscript environment for parallel processing."""
    gs_bin = r"C:\Program Files\gs\gs10.05.1\bin"
    gs_executable = os.path.join(gs_bin, "gswin64c.exe")
    if not os.path.exists(gs_executable):
        raise RuntimeError(f"Ghostscript not found at {gs_executable}")
    os.environ["GHOSTSCRIPT_PATH"] = gs_executable
    current_path = os.environ.get("PATH", "")
    if gs_bin not in current_path:
        os.environ["PATH"] = gs_bin + os.pathsep + current_path
    print(f"Ghostscript setup: {gs_executable}")

# Setup Ghostscript FIRST
setup_ghostscript_environment()

# Now safe to import PDF processing libraries
import PyPDF2
import fitz  # PyMuPDF
from pdfminer.high_level import extract_text as pdfminer_extract_text
import camelot
import pytesseract
from PIL import Image
import json
import argparse
import time
from datetime import datetime, timezone
import hashlib
from tqdm import tqdm

# Thread-local storage for unique temp directories
thread_local = threading.local()

def get_worker_temp_dir():
    """Get unique temp directory for this worker thread."""
    if not hasattr(thread_local, 'temp_dir'):
        base_temp = tempfile.gettempdir()
        thread_id = threading.get_ident()
        worker_id = f"pdf_worker_{thread_id}_{uuid.uuid4().hex[:8]}"
        unique_dir = os.path.join(base_temp, worker_id)
        os.makedirs(unique_dir, exist_ok=True)
        thread_local.temp_dir = unique_dir
        thread_local.worker_id = worker_id
        os.environ['TEMP'] = unique_dir
        os.environ['TMP'] = unique_dir
        print(f"Worker {worker_id} using temp dir: {unique_dir}")
    return thread_local.temp_dir

def worker_initializer():
    """Initialize each worker process with proper Ghostscript environment."""
    import os
    import tempfile
    import uuid
    gs_bin = r"C:\Program Files\gs\gs10.05.1\bin"
    gs_executable = os.path.join(gs_bin, "gswin64c.exe")
    os.environ["GHOSTSCRIPT_PATH"] = gs_executable
    current_path = os.environ.get("PATH", "")
    if gs_bin not in current_path:
        os.environ["PATH"] = gs_bin + os.pathsep + current_path
    worker_pid = os.getpid()
    unique_temp = os.path.join(tempfile.gettempdir(), f"pdf_worker_{worker_pid}_{uuid.uuid4().hex[:8]}")
    os.makedirs(unique_temp, exist_ok=True)
    os.environ['TEMP'] = unique_temp
    os.environ['TMP'] = unique_temp
    print(f"Worker {worker_pid} initialized with Ghostscript and temp: {unique_temp}")

GS_PATH = r"C:\Program Files\gs\gs10.05.1\bin\gswin64c.exe"  # adjust if needed
os.environ["GHOSTSCRIPT_PATH"] = GS_PATH
os.environ["PATH"] = os.path.dirname(GS_PATH) + os.pathsep + os.environ["PATH"]
import tempfile
import uuid
from concurrent.futures import ProcessPoolExecutor
import camelot
import sys
import json
import re
import shutil
import argparse
import logging
import time
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import math
from typing import Optional, List, Dict, Any, Tuple
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import warnings
import hashlib
from contextlib import contextmanager
import concurrent.futures

import PyPDF2
import fitz  # PyMuPDF
from pdfminer.high_level import extract_text as pdfminer_extract_text
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTFigure, LTImage
import camelot
import pytesseract
from PIL import Image
import numpy as np
from langdetect import detect, LangDetectException
import yaml
from tqdm import tqdm

from CryptoFinanceCorpusBuilder.processors.corruption_detector import detect_corruption
from CryptoFinanceCorpusBuilder.processors.language_confidence_detector import detect_language_confidence
from CryptoFinanceCorpusBuilder.processors.machine_translation_detector import detect_machine_translation
from CryptoFinanceCorpusBuilder.utils.domain_utils import get_domain_for_file
from CryptoFinanceCorpusBuilder.processors.domain_classifier import DomainClassifier
from CryptoFinanceCorpusBuilder.utils.pdf_safe_open import safe_open_pdf
from CryptoFinanceCorpusBuilder.processors.formula_extractor import FormulaExtractor
from CryptoFinanceCorpusBuilder.processors.chart_image_extractor import ChartImageExtractor
from CryptoFinanceCorpusBuilder.processors.finacial_symbol_processor import FinancialSymbolProcessor, AcademicPaperProcessor, MemoryOptimizer

# --- Config ---
MIN_TOKEN_THRESHOLD = 100
LOW_QUALITY_TOKEN_THRESHOLD = 500
CHUNK_TOKEN_THRESHOLD = 10000
SUPPORTED_EXTENSIONS = {'.pdf'}
DEFAULT_TIMEOUT = 300
MAX_RETRIES = 2
BATCH_SIZE = 20

# Domain-specific thresholds
DOMAIN_THRESHOLDS = {
    'crypto_derivatives': {
        'min_tokens': 200,
        'quality_threshold': 0.8,
        'table_threshold': 0.6,
        'formula_threshold': 0.7
    },
    'high_frequency_trading': {
        'min_tokens': 200,
        'quality_threshold': 0.8,
        'table_threshold': 0.7,
        'formula_threshold': 0.8
    },
    # Add other domains as needed
}

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Silence pdfminer warnings
pdfminer_logger = logging.getLogger('pdfminer')
pdfminer_logger.setLevel(logging.ERROR)

# Silence PyPDF2 warnings
pypdf_logger = logging.getLogger('pypdf')
pypdf_logger.setLevel(logging.ERROR)

# --- Helpers ---
def safe_filename(s):
    return re.sub(r'[^a-zA-Z0-9_\-\.]+', '_', s)[:128]

def count_tokens(text):
    return len(text.split())

def quality_flag(text):
    tokens = count_tokens(text)
    if tokens < MIN_TOKEN_THRESHOLD:
        return 'low_quality'
    elif tokens < LOW_QUALITY_TOKEN_THRESHOLD:
        return 'flagged'
    else:
        return 'ok'

def write_outputs(base_dir, rel_path, text, meta, quality, tables=None, formulas=None):
    out_dir = Path(base_dir) / ('low_quality' if quality == 'low_quality' else '_extracted')
    out_dir.mkdir(parents=True, exist_ok=True)
    base = safe_filename(rel_path.name)
    txt_path = out_dir / f"{base}.txt"
    json_path = out_dir / f"{base}.json"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(text)
    output_json = dict(meta)
    if tables is not None:
        output_json['tables'] = tables
    if formulas is not None:
        output_json['formulas'] = formulas
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)
    return txt_path, json_path

# --- Extraction Classes ---
class ExtractionResult:
    def __init__(self, text: str, metadata: Dict[str, Any], tables: List[Dict], formulas: List[Dict], 
                 quality_metrics: Dict[str, Any], errors: List[str], warnings: List[str]):
        self.text = text
        self.metadata = metadata
        self.tables = tables
        self.formulas = formulas
        self.quality_metrics = quality_metrics
        self.errors = errors
        self.warnings = warnings

# --- Timeout Context ---
class timeout_context:
    def __init__(self, timeout_seconds):
        self.timeout_seconds = timeout_seconds
        self.timer = None

    def __enter__(self):
        self.timer = threading.Timer(self.timeout_seconds, self.raise_timeout)
        self.timer.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer:
            self.timer.cancel()

    def raise_timeout(self):
        raise TimeoutError(f"Operation timed out after {self.timeout_seconds} seconds")

# --- Extraction Methods ---
def extract_text_with_pypdf2(pdf_path: str) -> str:
    text = ""
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        logger.warning(f"PyPDF2 extraction failed: {str(e)}")
    return text

def extract_text_with_pymupdf(pdf_path: str) -> str:
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text() + "\n"
    except Exception as e:
        logger.warning(f"PyMuPDF extraction failed: {str(e)}")
    return text

def extract_text_with_pdfminer(pdf_path: str) -> str:
    text = ""
    try:
        text = pdfminer_extract_text(pdf_path)
    except Exception as e:
        logger.warning(f"PDFMiner extraction failed: {str(e)}")
    return text

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text using multiple methods and return the best result"""
    methods = [
        extract_text_with_pypdf2,
        extract_text_with_pymupdf,
        extract_text_with_pdfminer
    ]
    
    best_text = ""
    best_score = 0
    
    for method in methods:
        try:
            text = method(pdf_path)
            if not text:
                continue
                
            # Score based on text length and quality
            score = len(text.split())
            if score > best_score:
                best_text = text
                best_score = score
        except Exception as e:
            logger.warning(f"Text extraction method failed: {str(e)}")
            continue
    
    return best_text

def extract_tables_from_pdf(pdf_path: str, timeout_seconds: int = 30, verbose: bool = False) -> list:
    """Extract tables from PDF with robust Ghostscript handling and worker isolation."""
    worker_temp = get_worker_temp_dir()
    worker_id = getattr(thread_local, 'worker_id', 'unknown')
    tables = []
    max_retries = 2
    import fitz
    import camelot
    try:
        with fitz.open(pdf_path) as doc:
            total_pages = len(doc)
            if verbose:
                print(f"[{worker_id}] Processing {total_pages} pages from {os.path.basename(pdf_path)}")
            for batch_start in range(0, total_pages, 3):
                batch_end = min(batch_start + 3, total_pages)
                page_range = f"{batch_start + 1}-{batch_end}"
                for attempt in range(max_retries):
                    try:
                        if attempt > 0:
                            time.sleep(0.5 * attempt)
                            if verbose:
                                print(f"[{worker_id}] Retry {attempt} for pages {page_range}")
                        batch_tables = camelot.read_pdf(
                            pdf_path,
                            pages=page_range,
                            flavor='lattice',
                            strip_text='\n',
                            layout_kwargs={
                                'detect_vertical': True,
                                'line_margin': 0.5,
                                'char_margin': 2.0
                            }
                        )
                        for table in batch_tables:
                            if table.accuracy > 0.5:
                                tables.append({
                                    'table_id': f"table_{len(tables) + 1}",
                                    'page': table.page,
                                    'accuracy': float(table.accuracy),
                                    'whitespace': float(table.whitespace),
                                    'order': len(tables) + 1,
                                    'data': table.df.to_dict(orient='records'),
                                    'shape': table.df.shape,
                                    'extraction_method': 'camelot_lattice',
                                    'worker_id': worker_id,
                                    'temp_dir': worker_temp
                                })
                                if verbose:
                                    print(f"[{worker_id}] Page {table.page}: Table extracted with accuracy {table.accuracy:.2f}")
                        break
                    except Exception as e:
                        error_msg = str(e).lower()
                        if 'ghostscript' in error_msg or 'image conversion' in error_msg:
                            if attempt < max_retries - 1:
                                if verbose:
                                    print(f"[{worker_id}] Ghostscript error on pages {page_range}, attempt {attempt + 1}: {str(e)}")
                                continue
                            else:
                                print(f"[{worker_id}] Ghostscript error on pages {page_range} after {max_retries} attempts: {str(e)}")
                        else:
                            if verbose:
                                print(f"[{worker_id}] Table extraction error on pages {page_range}: {str(e)}")
                            break
    except Exception as e:
        print(f"[{worker_id}] Error processing PDF {os.path.basename(pdf_path)}: {str(e)}")
    if verbose:
        print(f"[{worker_id}] Total tables extracted from {os.path.basename(pdf_path)}: {len(tables)}")
    return tables

def extract_formulas_from_text(text: str) -> List[Dict]:
    """Extract mathematical formulas from text"""
    formulas = []
    # Look for LaTeX-style formulas
    latex_patterns = [
        r'\$[^$]+\$',  # Inline math
        r'\$\$[^$]+\$\$',  # Display math
        r'\\begin{equation}[^}]+\\end{equation}',  # Equation environment
        r'\\begin{align}[^}]+\\end{align}'  # Align environment
    ]
    
    for pattern in latex_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            formulas.append({
                'formula': match.group(),
                'type': 'latex',
                'position': match.start()
            })
    
    return formulas

def extract_pdf_chunks(pdf_path: str, token_threshold: int = CHUNK_TOKEN_THRESHOLD) -> List[str]:
    """Split large PDFs into manageable chunks"""
    text = extract_text_from_pdf(pdf_path)
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for line in text.splitlines():
        tokens = len(line.split())
        if current_tokens + tokens > token_threshold and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [current_chunk[-1]]  # Overlap
            current_tokens = len(current_chunk[-1].split())
        current_chunk.append(line)
        current_tokens += tokens
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    return chunks

def get_domain_for_pdf(file_path: str) -> Optional[str]:
    """Get domain classification for PDF"""
    domain = get_domain_for_file(file_path)
    if not domain:
        # Try content-based classification
        text = extract_text_from_pdf(file_path)
        domain_classifier = DomainClassifier()
        domain_info = domain_classifier.classify(text)
        domain = domain_info.get('domain')
    return domain

def detect_scientific_paper(text: str, metadata: Optional[Dict] = None) -> bool:
    """Detect if a document is a scientific paper based on content and metadata."""
    try:
        # Check metadata first
        if metadata:
            # Check for DOI
            if 'doi' in str(metadata).lower():
                return True
            # Check for academic keywords
            academic_keywords = ['abstract', 'introduction', 'methodology', 'conclusion', 'references']
            if any(keyword in str(metadata).lower() for keyword in academic_keywords):
                return True
        
        # Check text content
        text_lower = text.lower()
        
        # Look for common scientific paper sections
        section_indicators = [
            'abstract',
            'introduction',
            'methodology',
            'methods',
            'results',
            'discussion',
            'conclusion',
            'references',
            'bibliography',
            'acknowledgments',
            'appendix'
        ]
        
        # Count how many section indicators are present
        section_count = sum(1 for section in section_indicators if section in text_lower)
        
        # Look for academic patterns
        academic_patterns = [
            r'\bdoi:\s*[\d\.]+\/[\w\-\.]+',  # DOI pattern
            r'\bissn:\s*[\d\-]+',  # ISSN pattern
            r'\bvolume\s+\d+',  # Volume number
            r'\bissue\s+\d+',  # Issue number
            r'\bpages?\s+\d+',  # Page numbers
            r'\bjournal\s+of\b',  # Journal of...
            r'\bproceedings\b',  # Conference proceedings
            r'\bconference\b',  # Conference paper
            r'\buniversity\b',  # University affiliation
            r'\buniversity\s+of\b'  # University of...
        ]
        
        # Count academic patterns
        pattern_count = sum(1 for pattern in academic_patterns if re.search(pattern, text_lower))
        
        # Check for citation patterns
        citation_patterns = [
            r'\(\d{4}\)',  # (2023)
            r'\[\d+\]',  # [1]
            r'et al\.',  # et al.
            r'pp\.\s+\d+',  # pp. 123
            r'vol\.\s+\d+'  # vol. 1
        ]
        
        # Count citation patterns
        citation_count = sum(1 for pattern in citation_patterns if re.search(pattern, text_lower))
        
        # Determine if it's a scientific paper
        # Need at least 3 section indicators or 2 academic patterns + 1 citation pattern
        return section_count >= 3 or (pattern_count >= 2 and citation_count >= 1)
        
    except Exception as e:
        logger.warning(f"Error detecting scientific paper: {e}")
        return False

def process_pdf_file_enhanced(file_path: str, args: argparse.Namespace) -> Optional[ExtractionResult]:
    worker_temp = get_worker_temp_dir()
    worker_id = getattr(thread_local, 'worker_id', 'unknown')
    try:
        if getattr(args, 'verbose', False):
            print(f"[{worker_id}] Starting processing: {os.path.basename(file_path)}")
        # Extract text
        text = extract_text_from_pdf(file_path)
        if not text or len(text.strip()) < MIN_TOKEN_THRESHOLD:
            print(f"[{worker_id}] Extracted text too short: {len(text.strip())} tokens")
            return None
        
        # Get domain classification
        domain = get_domain_for_pdf(file_path)
        domain_thresholds = DOMAIN_THRESHOLDS.get(domain, {})

        # === NEW ENHANCEMENTS START HERE ===
        formula_extractor = FormulaExtractor()
        chart_extractor = ChartImageExtractor()
        symbol_processor = FinancialSymbolProcessor()
        academic_processor = AcademicPaperProcessor()
        # MemoryOptimizer can be used for chunked processing if needed

        pdf_output_dir = Path(args.output_dir) / 'extracted' / Path(file_path).stem
        pdf_output_dir.mkdir(parents=True, exist_ok=True)

        formula_results = formula_extractor.extract_comprehensive(file_path, text)
        image_results = chart_extractor.extract_from_pdf(file_path, str(pdf_output_dir))
        symbol_results = symbol_processor.extract_symbols(text)
        symbol_glossary = symbol_processor.generate_symbol_glossary(symbol_results)
        academic_analysis = academic_processor.detect_academic_paper(text, {})
        if academic_analysis['is_academic_paper']:
            domain_thresholds.update(academic_processor.academic_thresholds)
            logger.info(f"Detected academic paper: {file_path}")
        content_validation = academic_processor.validate_academic_content(text, {
            'formulas': formula_results,
            'images': image_results,
            'symbols': symbol_results
        })
        # === EXISTING CODE CONTINUES ===
        tables = []
        if not getattr(args, 'disable_tables', False):
            tables = extract_tables_from_pdf(file_path, timeout_seconds=getattr(args, 'timeout', 30), verbose=getattr(args, 'verbose', False))
        # Quality checks (existing + enhancements)
        quality_checks = {
            'language_confidence': detect_language_confidence(text, mixed_lang_ratio=args.mixed_lang_ratio),
            'corruption': detect_corruption(text, file_type='.pdf', thresholds=args.corruption_thresholds),
            'machine_translation': detect_machine_translation(text, config_path=args.mt_config, file_type='.pdf', domain=domain),
            'academic_analysis': academic_analysis,
            'content_validation': content_validation,
            'symbol_richness': {
                'total_symbols': symbol_results['statistics']['total_symbols'],
                'unique_symbols': symbol_results['statistics']['unique_symbols'],
                'financial_symbols': len([s for s in symbol_results['symbols_by_position'] if 'financial' in s['type']])
            }
        }
        quality_metrics = {
            **quality_checks,
            **domain_thresholds,
            'extraction_quality': {
                'tables_detected': len(tables) > 0,
                'formulas_detected': formula_results['statistics']['total_formulas'] > 0,
                'charts_detected': len([img for img in image_results if img['is_chart']]) > 0,
                'symbols_detected': symbol_results['statistics']['total_symbols'] > 0,
                'token_count': count_tokens(text),
                'quality_flag': quality_flag(text),
                'is_academic_paper': academic_analysis['is_academic_paper'],
                'academic_confidence': academic_analysis['confidence']
            }
        }
        # Extract metadata (existing code)
        metadata = {}
        try:
            with open(file_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                info = pdf.metadata
                if info:
                    metadata.update({
                        'title': info.get('/Title', ''),
                        'author': info.get('/Author', ''),
                        'subject': info.get('/Subject', ''),
                        'creator': info.get('/Creator', ''),
                        'producer': info.get('/Producer', ''),
                        'creation_date': info.get('/CreationDate', ''),
                        'modification_date': info.get('/ModDate', '')
                    })
        except Exception as e:
            logger.warning(f"Metadata extraction failed: {str(e)}")
        metadata.update({
            'domain': domain,
            'quality_metrics': quality_metrics,
            'is_scientific_paper': detect_scientific_paper(text, metadata),
            'content_hash': hashlib.md5(text.encode('utf-8')).hexdigest(),
            'file_size': os.path.getsize(file_path),
            'extraction_date': datetime.now(timezone.utc).isoformat(),
            'enhancement_results': {
                'formulas': formula_results,
                'images': image_results,
                'symbols': symbol_results,
                'symbol_glossary': symbol_glossary,
                'academic_analysis': academic_analysis
            }
        })
        result = ExtractionResult(
            text=text,
            metadata=metadata,
            tables=tables,
            formulas=formula_results['formulas'],
            quality_metrics=quality_metrics,
            errors=[],
            warnings=[]
        )
        quality = quality_flag(text)
        txt_path, json_path = write_outputs(args.output_dir, Path(file_path), text, metadata, quality, tables=tables, formulas=formula_results['formulas'])
        return result
    except Exception as e:
        print(f"[{worker_id}] Error processing {os.path.basename(file_path)}: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Enhanced PDF text extraction with quality control')
    parser.add_argument('--input-dir', required=True, help='Input directory containing PDFs')
    parser.add_argument('--output-dir', required=True, help='Output directory for extracted text')
    parser.add_argument('--single-file', help='Process only this specific file')
    parser.add_argument('--disable-tables', action='store_true', help='Disable table extraction')
    parser.add_argument('--disable-formulas', action='store_true', help='Disable formula extraction')
    parser.add_argument('--mixed-lang-ratio', type=float, default=0.30, help='Mixed language ratio threshold')
    parser.add_argument('--corruption-thresholds', type=str, help='Path to corruption thresholds config')
    parser.add_argument('--mt-config', type=str, help='Path to machine translation config')
    parser.add_argument('--num-workers', type=int, default=os.cpu_count(), help='Number of worker processes')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, help='Batch size for processing')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT, help='Timeout in seconds')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--auto-normalize', dest='auto_normalize', action='store_true', help='Automatically normalize metadata after extraction (default: on)')
    parser.add_argument('--no-auto-normalize', dest='auto_normalize', action='store_false', help='Do not normalize metadata after extraction')
    parser.set_defaults(auto_normalize=True)
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Process single file if specified
    if args.single_file:
        file_path = os.path.join(args.input_dir, args.single_file)
        logger.info(f"Processing single file: {file_path}")
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return
        if not file_path.lower().endswith('.pdf'):
            logger.error(f"Not a PDF file: {file_path}")
            return
        process_pdf_file_enhanced(file_path, args)
        return
    
    # Get list of PDF files for batch processing
    pdf_files = []
    for root, _, files in os.walk(args.input_dir):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    
    if not pdf_files:
        logger.error(f"No PDF files found in {args.input_dir}")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # At the start of main(), add:
    failed_files = []
    successful_files = []
    
    # Use optimal worker count
    args.num_workers = min(args.num_workers, multiprocessing.cpu_count() - 1, 8)
    with ProcessPoolExecutor(max_workers=args.num_workers, initializer=worker_initializer) as executor:
        futures = {}
        for pdf_file in pdf_files:
            future = executor.submit(process_pdf_file_enhanced, pdf_file, args)
            futures[future] = pdf_file
        
        completed = 0
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
            completed += 1
            pdf_file = futures[future]
            result = future.result()
            if result:
                successful_files.append(pdf_file)
            else:
                failed_files.append((pdf_file, 'Failed to process (see logs for details)'))
            logger.info(f"Progress: {completed}/{len(pdf_files)} files processed ({len(successful_files)} successful)")
    
    logger.info(f"Processing complete. {len(successful_files)}/{len(pdf_files)} files processed successfully")

    # At the end of main(), after all files are processed:
    print("\n=== Extraction Summary ===")
    print(f"Successful files: {len(successful_files)}")
    for f in successful_files:
        print(f"  ✓ {f}")
    print(f"Failed files: {len(failed_files)}")
    for f, reason in failed_files:
        print(f"  × {f} -- {reason}")

    # Auto-normalize metadata if enabled
    if getattr(args, 'auto_normalize', False):
        print("[INFO] Running metadata normalization on output directory...")
        from CryptoFinanceCorpusBuilder.utils.metadata_normalizer import main as normalize_directory
        normalize_directory(args.output_dir)

    # Ensure all file handles are closed before temp file deletion (handled by context managers in extraction code)

if __name__ == '__main__':
    main()

# ===== CLEANUP FUNCTION =====
def cleanup_worker_temp_dirs():
    """Clean up temporary directories created by workers."""
    try:
        base_temp = tempfile.gettempdir()
        import glob
        worker_dirs = glob.glob(os.path.join(base_temp, "pdf_worker_*"))
        for worker_dir in worker_dirs:
            try:
                import shutil
                shutil.rmtree(worker_dir, ignore_errors=True)
                print(f"Cleaned up temp dir: {worker_dir}")
            except Exception:
                pass
    except Exception as e:
        print(f"Cleanup warning: {str(e)}") 