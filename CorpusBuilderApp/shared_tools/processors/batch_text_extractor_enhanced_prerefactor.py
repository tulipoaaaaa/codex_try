"""
Module: batch_text_extractor_enhanced_prerefactor
Purpose: Provides enhanced batch text extraction for PDFs.
"""

import os
import sys
import platform
import glob
import shutil
import tempfile
import uuid
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import logging
import time
import multiprocessing
import types
from typing import Optional, List, Dict, Any, Tuple, Union

logger = logging.getLogger(__name__)

def find_ghostscript_executable():
    """Smart Ghostscript executable detection with version-agnostic search."""
    # 1. Check GHOSTSCRIPT_PATH environment variable first
    env_path = os.environ.get('GHOSTSCRIPT_PATH')
    if env_path:
        if os.path.isfile(env_path) and os.access(env_path, os.X_OK):
            logger.info(f"Using Ghostscript from GHOSTSCRIPT_PATH: {env_path}")
            return env_path
        elif os.path.isdir(env_path):
            # If directory provided, look for executable inside
            system = platform.system().lower()
            if system == 'windows':
                for exe in ['gswin64c.exe', 'gswin32c.exe', 'gs.exe']:
                    full_path = os.path.join(env_path, exe)
                    if os.path.exists(full_path):
                        logger.info(f"Found Ghostscript executable in GHOSTSCRIPT_PATH dir: {full_path}")
                        return full_path
            else:
                gs_exe = os.path.join(env_path, 'gs')
                if os.path.exists(gs_exe) and os.access(gs_exe, os.X_OK):
                    logger.info(f"Found Ghostscript executable in GHOSTSCRIPT_PATH dir: {gs_exe}")
                    return gs_exe
        logger.warning(f"GHOSTSCRIPT_PATH set but invalid: {env_path}")
    
    # 2. OS-specific auto-detection with version-agnostic patterns
    system = platform.system().lower()
    
    if system == 'windows':
        # Search for any Ghostscript version using glob patterns
        search_patterns = [
            r"C:\Program Files\gs\gs*\bin\gswin64c.exe",
            r"C:\Program Files\gs\gs*\bin\gswin32c.exe", 
            r"C:\Program Files (x86)\gs\gs*\bin\gswin64c.exe",
            r"C:\Program Files (x86)\gs\gs*\bin\gswin32c.exe",
            r"C:\Program Files\gs\gs*\bin\gs.exe",
            r"C:\Program Files (x86)\gs\gs*\bin\gs.exe"
        ]
        
        found_executables = []
        for pattern in search_patterns:
            matches = glob.glob(pattern)
            found_executables.extend(matches)
        
        if found_executables:
            # Sort to get newest version (assumes version in path)
            found_executables.sort(reverse=True)
            selected = found_executables[0]
            logger.info(f"Auto-detected Ghostscript (Windows): {selected}")
            return selected
    
    elif system == 'darwin':  # macOS
        # Common macOS paths with priority order
        search_paths = [
            '/opt/homebrew/bin/gs',      # Apple Silicon Homebrew
            '/usr/local/bin/gs',         # Intel Homebrew
            '/opt/local/bin/gs',         # MacPorts
            '/usr/bin/gs'                # System
        ]
        
        for path in search_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                logger.info(f"Auto-detected Ghostscript (macOS): {path}")
                return path
    
    else:  # Linux and other Unix-like systems
        # Common Linux paths
        search_paths = [
            '/usr/bin/gs',               # System package
            '/usr/local/bin/gs',         # Manual install
            '/opt/ghostscript/bin/gs',   # Custom install
            '/snap/bin/ghostscript.gs'   # Snap package
        ]
        
        for path in search_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                logger.info(f"Auto-detected Ghostscript (Linux): {path}")
                return path
    
    # 3. Final fallback: search system PATH
    gs_in_path = shutil.which('gs')
    if gs_in_path:
        logger.info(f"Found Ghostscript in system PATH: {gs_in_path}")
        return gs_in_path
    
    # 4. Windows-specific PATH search for gswin executables
    if system == 'windows':
        for exe in ['gswin64c', 'gswin32c']:
            gs_win_path = shutil.which(exe)
            if gs_win_path:
                logger.info(f"Found Ghostscript Windows executable in PATH: {gs_win_path}")
                return gs_win_path
    
    # 5. Not found - provide helpful error
    error_msg = f"Ghostscript not found on {system}. "
    if system == 'windows':
        error_msg += "Install from https://www.ghostscript.com/download/gsdnld.html or set GHOSTSCRIPT_PATH environment variable."
    elif system == 'darwin':
        error_msg += "Install with: brew install ghostscript"
    else:
        error_msg += "Install with your package manager (e.g., apt install ghostscript) or set GHOSTSCRIPT_PATH."
    
    raise RuntimeError(error_msg)

def get_ghostscript_bin_dir():
    """Get Ghostscript binary directory."""
    gs_executable = find_ghostscript_executable()
    return os.path.dirname(gs_executable)

def get_ghostscript_executable():
    """Get Ghostscript executable path (alias for find_ghostscript_executable)."""
    return find_ghostscript_executable()

# ===== CRITICAL: Set Ghostscript environment FIRST, before any imports =====
def setup_ghostscript_environment():
    """Setup Ghostscript environment for parallel processing."""
    gs_bin = get_ghostscript_bin_dir()
    gs_executable = get_ghostscript_executable()
    # gs_executable is now guaranteed to exist from find_ghostscript_executable()
    os.environ["GHOSTSCRIPT_PATH"] = gs_executable
    current_path = os.environ.get("PATH", "")
    if gs_bin not in current_path:
        os.environ["PATH"] = gs_bin + os.pathsep + current_path
    logger.info(f"Ghostscript setup: {gs_executable}")

# Setup Ghostscript FIRST
setup_ghostscript_environment()

# Now safe to import PDF processing libraries
import PyPDF2
import fitz  # type: ignore
from pdfminer.high_level import extract_text as pdfminer_extract_text  # type: ignore
import camelot  # type: ignore
import pytesseract  # type: ignore
from PIL import Image  # type: ignore
import json
import argparse
import time
from datetime import datetime, timezone
import hashlib
from tqdm import tqdm  # type: ignore
import yaml  # type: ignore

# Thread-local storage for unique temp directories
thread_local = threading.local()

def get_worker_temp_dir():
    """Get unique temp directory for this worker thread."""
    if not hasattr(thread_local, 'temp_dir'):
        env_temp = _PROJECT.get('environment.temp_dir', tempfile.gettempdir())
        base_temp = Path(env_temp) / 'temp_workers'
        thread_id = threading.get_ident()
        worker_id = f"pdf_worker_{thread_id}_{uuid.uuid4().hex[:8]}"
        unique_dir = os.path.join(base_temp, worker_id)
        os.makedirs(unique_dir, exist_ok=True)
        thread_local.temp_dir = unique_dir
        thread_local.worker_id = worker_id
        os.environ['TEMP'] = unique_dir
        os.environ['TMP'] = unique_dir
        logger.info(f"Worker {worker_id} using temp dir: {unique_dir}")
    return thread_local.temp_dir

def worker_initializer():
    """Initialize each worker process with proper Ghostscript environment."""
    import os
    import uuid
    import atexit
    import shutil
    gs_bin = get_ghostscript_bin_dir()
    gs_executable = get_ghostscript_executable()
    os.environ["GHOSTSCRIPT_PATH"] = gs_executable
    current_path = os.environ.get("PATH", "")
    if gs_bin not in current_path:
        os.environ["PATH"] = gs_bin + os.pathsep + current_path
    worker_pid = os.getpid()
    env_temp = _PROJECT.get('environment.temp_dir', tempfile.gettempdir())
    base_temp = Path(env_temp) / 'temp_workers'
    unique_temp = os.path.join(base_temp, f"pdf_worker_{worker_pid}_{uuid.uuid4().hex[:8]}")
    os.makedirs(unique_temp, exist_ok=True)
    os.environ['TEMP'] = unique_temp
    os.environ['TMP'] = unique_temp
    logger.info(f"Worker {worker_pid} initialized with Ghostscript and temp: {unique_temp}")

    def cleanup_temp():
        try:
            # Wait a short time to ensure files are closed
            import time
            time.sleep(0.5)
            if os.path.exists(unique_temp):
                shutil.rmtree(unique_temp, ignore_errors=True)
                logger.info(f"Cleaned up temp dir: {unique_temp}")
        except Exception as e:
            logger.info(f"Cleanup warning for {unique_temp}: {str(e)}")

    atexit.register(cleanup_temp)

# Additional imports for the enhanced functionality
import re
import warnings
import numpy as np  # type: ignore
from collections import Counter
import math
from contextlib import contextmanager
import concurrent.futures
from langdetect import detect, LangDetectException  # type: ignore
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTFigure, LTImage  # type: ignore

from .formula_extractor import FormulaExtractor
from .chart_image_extractor import ChartImageExtractor
from .financial_symbol_processor import FinancialSymbolProcessor, AcademicPaperProcessor, MemoryOptimizer
from ..utils.domain_utils import get_domain_for_file
from ..utils.pdf_safe_open import safe_open_pdf
from shared_tools.processors.domain_classifier import DomainClassifier
from .corruption_detector import detect_corruption
from .language_confidence_detector import detect_language_confidence
from .machine_translation_detector import detect_machine_translation
from shared_tools.project_config import ProjectConfig

_DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "configs" / "quick_test.yaml"
_PROJECT = ProjectConfig(os.environ.get("PROJECT_CONFIG", str(_DEFAULT_CONFIG)))

# Initialize Ghostscript path for camelot and other libraries
GS_PATH = find_ghostscript_executable()  # Smart auto-detection with GHOSTSCRIPT_PATH fallback
os.environ["GHOSTSCRIPT_PATH"] = GS_PATH
os.environ["PATH"] = os.path.dirname(GS_PATH) + os.pathsep + os.environ["PATH"]

# --- Config ---
MIN_TOKEN_THRESHOLD = 50
LOW_QUALITY_TOKEN_THRESHOLD = 200
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
log_dir = _PROJECT.get_logs_dir()
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "batch_text_extractor_enhanced_prerefactor.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Silence pdfminer warnings
pdfminer_logger = logging.getLogger('pdfminer')
pdfminer_logger.setLevel(logging.ERROR)

# Silence PyPDF2 warnings
pypdf_logger = logging.getLogger('pypdf')
pypdf_logger.setLevel(logging.ERROR)

# --- OCR fallback parameters ---
OCR_DPI = 300  # Rendering resolution for OCR fallback
OCR_MAX_PAGES = None  # Set to an int to cap pages processed; None = all

# --- Helpers ---
def safe_filename(s, max_length=128):
    return re.sub(r'[^a-zA-Z0-9_\-\.]+', '_', s)[:max_length]

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
    base = safe_filename(rel_path.name, 128)
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

# --- NEW: OCR fallback ---
def extract_text_with_ocr(pdf_path: str, dpi: int = OCR_DPI, max_pages: Optional[int] = OCR_MAX_PAGES) -> str:
    """Render pages to images and run pytesseract OCR."""
    try:
        import fitz  # local import to avoid unnecessary dependency if OCR disabled
        text = ""
        doc = fitz.open(pdf_path)
        matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        for page_index, page in enumerate(doc):
            if max_pages is not None and page_index >= max_pages:
                break
            pix = page.get_pixmap(matrix=matrix)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            page_text = pytesseract.image_to_string(img, config='--psm 6')
            text += page_text + "\n"
        return text
    except Exception as exc:
        logger.warning(f"OCR fallback failed for {pdf_path}: {exc}")
        return ""

def extract_text_from_pdf(pdf_path: str) -> str:
    logger.debug(f"[DEBUG] Entering extract_text_from_pdf for: {pdf_path}")
    methods = [
        extract_text_with_pypdf2,
        extract_text_with_pymupdf,
        extract_text_with_pdfminer
    ]
    best_text = ""
    best_score = 0
    for method in methods:
        try:
            logger.debug(f"[DEBUG] Trying method: {method.__name__}")
            text = method(pdf_path)
            logger.debug(f"[DEBUG] Method {method.__name__} returned {len(text) if text else 0} characters")
            if not text:
                continue
            score = len(text.split())
            if score > best_score:
                best_text = text
                best_score = score
        except Exception as e:
            logger.debug(f"[DEBUG] Exception in {method.__name__}: {e}")
            logger.warning(f"Text extraction method failed: {str(e)}")
            continue

    # If no method produced enough text, attempt OCR fallback unless disabled
    try_ocr = best_score < MIN_TOKEN_THRESHOLD and os.environ.get("DISABLE_OCR_FALLBACK", "0") != "1"
    if try_ocr:
        logger.info(f"Attempting OCR fallback for {pdf_path} – current tokens: {best_score}")
        ocr_text = extract_text_with_ocr(pdf_path)
        ocr_score = len(ocr_text.split())
        if ocr_score > best_score:
            logger.info(f"OCR fallback succeeded, tokens: {ocr_score}")
            best_text = ocr_text
            best_score = ocr_score
        else:
            logger.info("OCR fallback did not improve extraction result")

    logger.debug(f"[DEBUG] extract_text_from_pdf returning {len(best_text) if best_text else 0} characters")
    return best_text

def extract_tables_from_pdf(pdf_path: str, timeout_seconds: int = 30, verbose: bool = False) -> list:
    """Extract tables from PDF with robust Ghostscript handling and worker isolation."""
    worker_temp = get_worker_temp_dir()
    worker_id = getattr(thread_local, 'worker_id', 'unknown')
    tables = []
    max_retries = 2
    import fitz
    import camelot
    doc = None
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        if verbose:
            logger.info(f"[{worker_id}] Processing {total_pages} pages from {os.path.basename(pdf_path)}")
        for batch_start in range(0, total_pages, 3):
            batch_end = min(batch_start + 3, total_pages)
            page_range = f"{batch_start + 1}-{batch_end}"
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        time.sleep(0.5 * attempt)
                        if verbose:
                            logger.info(f"[{worker_id}] Retry {attempt} for pages {page_range}")
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
                                logger.info(f"[{worker_id}] Page {table.page}: Table extracted with accuracy {table.accuracy:.2f}")
                    break
                except Exception as e:
                    error_msg = str(e).lower()
                    if 'ghostscript' in error_msg or 'image conversion' in error_msg:
                        if attempt < max_retries - 1:
                            if verbose:
                                logger.info(f"[{worker_id}] Ghostscript error on pages {page_range}, attempt {attempt + 1}: {str(e)}")
                            continue
                        else:
                            logger.info(f"[{worker_id}] Ghostscript error on pages {page_range} after {max_retries} attempts: {str(e)}")
                    else:
                        if verbose:
                            logger.info(f"[{worker_id}] Table extraction error on pages {page_range}: {str(e)}")
                        break
    except Exception as e:
        logger.warning(f"[{worker_id}] Error processing PDF {os.path.basename(pdf_path)}: {str(e)}")
    if verbose:
        logger.info(f"[{worker_id}] Total tables extracted from {os.path.basename(pdf_path)}: {len(tables)}")

    # If Camelot found nothing and image-table OCR is enabled, try fallback
    if not tables and os.environ.get("DISABLE_IMAGE_TABLE_OCR", "0") != "1":
        try:
            from shared_tools.processors.image_table_extractor import extract_tables_from_pixmap
            for page_num in range(total_pages):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                img_tables = extract_tables_from_pixmap(pix, page_num + 1)
                tables.extend(img_tables)
            if verbose and tables:
                logger.info(
                    f"[{worker_id}] Image-based OCR extracted {len(tables)} tables from {os.path.basename(pdf_path)}"
                )
        except Exception as ocr_exc:
            logger.warning(
                f"[{worker_id}] Image-table OCR failed for {os.path.basename(pdf_path)}: {ocr_exc}"
            )

    if verbose:
        logger.info(f"[{worker_id}] Total tables extracted from {os.path.basename(pdf_path)}: {len(tables)}")

    if doc is not None:
        try:
            doc.close()
        except Exception:
            pass
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

def convert_pdf_date(pdf_date_str):
    """Convert PDF date string to ISO format."""
    if not pdf_date_str:
        return None
    try:
        # Remove PDF date prefix if present
        if pdf_date_str.startswith('D:'):
            pdf_date_str = pdf_date_str[2:]
        # Parse the date components
        year = int(pdf_date_str[:4])
        month = int(pdf_date_str[4:6])
        day = int(pdf_date_str[6:8])
        hour = int(pdf_date_str[8:10]) if len(pdf_date_str) > 8 else 0
        minute = int(pdf_date_str[10:12]) if len(pdf_date_str) > 10 else 0
        second = int(pdf_date_str[12:14]) if len(pdf_date_str) > 12 else 0
        # Create datetime object
        from datetime import datetime
        dt = datetime(year, month, day, hour, minute, second)
        return dt.isoformat()
    except (ValueError, IndexError):
        return str(pdf_date_str)

def resolve_indirect_object(obj, _seen: Optional[set] = None, _depth: int = 0):
    """Recursively resolve PyPDF2 IndirectObjects while guarding against cycles.

    Args:
        obj: Any PDF object (could be primitive, list, dict, or IndirectObject).
        _seen: Internal set of ``id(obj)`` already visited to detect self-references.
        _depth: Current recursion depth – hard-capped to avoid runaway loops.

    Returns:
        A JSON-serialisable structure with the same shape as the original object,
        but with all ``IndirectObject`` instances replaced by their resolved value
        (or a string fallback when resolution fails).
    """
    MAX_DEPTH = 20
    if _seen is None:
        _seen = set()

    # Depth / cycle guards ---------------------------------------------------
    obj_id = id(obj)
    if _depth > MAX_DEPTH or obj_id in _seen:
        return str(obj)
    _seen.add(obj_id)

    # Resolution logic -------------------------------------------------------
    try:
        if hasattr(obj, 'get_object'):
            # PyPDF2 IndirectObject
            try:
                resolved = obj.get_object()
                return resolve_indirect_object(resolved, _seen, _depth + 1)
            except Exception:
                return str(obj)
        if isinstance(obj, dict):
            return {k: resolve_indirect_object(v, _seen, _depth + 1) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [resolve_indirect_object(item, _seen, _depth + 1) for item in obj]
        if isinstance(obj, (int, float, bool, str)):
            return obj
        # Fallback to string representation for any unhandled type
        return str(obj)
    except Exception as exc:
        logger.debug("resolve_indirect_object failed at depth %s: %s", _depth, exc)
        return str(obj)

def process_pdf_file_enhanced(file_path: str, args: argparse.Namespace) -> Optional[ExtractionResult]:
    worker_temp = get_worker_temp_dir()
    worker_id = getattr(thread_local, 'worker_id', 'unknown')
    try:
        logger.debug(f"[DEBUG] process_pdf_file_enhanced: Starting for {file_path}")
        if getattr(args, 'verbose', False):
            logger.info(f"[{worker_id}] Starting processing: {os.path.basename(file_path)}")
        
        # Extract text
        text = extract_text_from_pdf(file_path)
        logger.debug(f"[DEBUG] process_pdf_file_enhanced: Extracted text length: {len(text) if text else 0}")
        
        if not text or len(text.strip()) < MIN_TOKEN_THRESHOLD:
            logger.info(f"[{worker_id}] Extracted text too short: {len(text.strip()) if text else 0} tokens (threshold: {MIN_TOKEN_THRESHOLD})")
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
            'corruption': detect_corruption(text, config=args.corruption_thresholds),
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
        # Extract metadata with proper type preservation
        metadata = {}
        try:
            with open(file_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                info = pdf.metadata
                if info:
                    # First resolve any IndirectObjects
                    resolved_info = resolve_indirect_object(info)

                    # Some PDFs return a plain string or other non-mapping; guard for that
                    if isinstance(resolved_info, dict):
                        # Handle each field with proper type conversion
                        metadata.update({
                            'title': resolved_info.get('/Title', ''),
                            'author': resolved_info.get('/Author', ''),
                            'subject': resolved_info.get('/Subject', ''),
                            'creator': resolved_info.get('/Creator', ''),
                            'producer': resolved_info.get('/Producer', ''),
                            'creation_date': convert_pdf_date(resolved_info.get('/CreationDate')),
                            'modification_date': convert_pdf_date(resolved_info.get('/ModDate'))
                        })

                        # Add any additional metadata fields
                        for key, value in resolved_info.items():
                            if key not in metadata and not key.startswith('/'):
                                metadata[key] = value
                    else:
                        metadata['raw_pdf_metadata'] = str(resolved_info)
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
        logger.warning(f"[{worker_id}] Error processing {os.path.basename(file_path)}: {str(e)}")
        return None

def run_with_project_config(
    project: Union[str, ProjectConfig],
    chunking_mode: str = 'page',
    chunk_overlap: int = 1,
    verbose: bool = False,
    auto_normalize: bool = True
) -> dict:
    """Run text extraction with project configuration
    
    Args:
        project: ProjectConfig instance or path to config file
        chunking_mode: How to chunk the text ('page' or 'token')
        chunk_overlap: Number of pages/tokens to overlap between chunks
        verbose: Enable verbose output
        auto_normalize: Whether to normalize metadata after extraction
        
    Returns:
        dict: Extraction results
    """
    if isinstance(project, str):
        project = ProjectConfig(project)
    
    # Get paths from project config
    input_dir = project.raw_data_dir
    output_dir = project.processed_dir
    
    # Get processor config if available
    processor_config = None
    if hasattr(project, 'processors') and 'text_extractor' in project.processors:
        processor_config = project.processors['text_extractor']
    
    return run_with_paths(
        input_dir=input_dir,
        output_dir=output_dir,
        chunking_mode=chunking_mode,
        chunk_overlap=chunk_overlap,
        verbose=verbose,
        auto_normalize=auto_normalize,
        processor_config=processor_config
    )

def run_with_paths(
    input_dir,
    output_dir,
    chunking_mode: str = 'page',
    chunk_overlap: int = 1,
    verbose: bool = False,
    auto_normalize: bool = True,
    processor_config: Optional[Dict] = None
) -> dict:
    """Run text extraction with explicit paths
    
    Args:
        input_dir: Input directory containing PDFs
        output_dir: Output directory for extracted text
        chunking_mode: How to chunk the text ('page' or 'token')
        chunk_overlap: Number of pages/tokens to overlap between chunks
        verbose: Enable verbose output
        auto_normalize: Whether to normalize metadata after extraction
        processor_config: Optional processor configuration
        
    Returns:
        dict: Extraction results
    """
    # Use processor config if provided
    if processor_config:
        global MIN_TOKEN_THRESHOLD, LOW_QUALITY_TOKEN_THRESHOLD, CHUNK_TOKEN_THRESHOLD
        MIN_TOKEN_THRESHOLD = processor_config.get('min_token_threshold', MIN_TOKEN_THRESHOLD)
        LOW_QUALITY_TOKEN_THRESHOLD = processor_config.get('low_quality_token_threshold', LOW_QUALITY_TOKEN_THRESHOLD)
        CHUNK_TOKEN_THRESHOLD = processor_config.get('chunk_token_threshold', CHUNK_TOKEN_THRESHOLD)
    
    # --- NEW IMPLEMENTATION START ---
    logger = logging.getLogger(__name__)
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.exists():
        raise ValueError(f"Input directory does not exist: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Respect verbose flag
    if verbose:
        logger.setLevel(logging.DEBUG)

    # Collect PDF files recursively
    files_to_process: List[str] = []
    for root, _dirs, files in os.walk(input_dir):
        for fname in files:
            if fname.lower().endswith('.pdf'):
                files_to_process.append(os.path.join(root, fname))

    if not files_to_process:
        logger.error("No PDF files found in %s", input_dir)
        return {
            'success': False,
            'files_processed': 0,
            'successful': 0,
            'failed': 0,
            'low_quality': 0,
            'error': f'No PDF files found in {input_dir}'
        }

    logger.info("Found %d PDF files to process", len(files_to_process))

    failed_files: List[str] = []
    successful_files: List[str] = []

    # Determine worker count (leave 1 CPU free, cap at 8 to avoid oversubscription)
    num_workers = min(max(1, multiprocessing.cpu_count() - 1), 8)

    # Build immutable namespace for worker arguments (pickle-safe)
    worker_args = types.SimpleNamespace(
        output_dir=str(output_dir),
        verbose=verbose,
        auto_normalize=auto_normalize,
        chunking_mode=chunking_mode,
        chunk_overlap=chunk_overlap,
        timeout=DEFAULT_TIMEOUT,
        disable_tables=False,
        mixed_lang_ratio=0.30,
        corruption_thresholds=None,
        mt_config=None
    )

    with ProcessPoolExecutor(max_workers=num_workers, initializer=worker_initializer) as executor:
        futures = {executor.submit(process_pdf_file_enhanced, fp, worker_args): fp for fp in files_to_process}
        from tqdm import tqdm  # Imported earlier, but safe to import again if not present
        for future in tqdm(as_completed(futures), total=len(futures)):
            file_path = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                logger.warning("Error processing %s: %s", file_path, exc)
                failed_files.append(file_path)
                continue

            if result:
                successful_files.append(file_path)
                # write_outputs already called inside process_pdf_file_enhanced
            else:
                failed_files.append(file_path)

    # Optionally normalize metadata after all processing
    if auto_normalize:
        try:
            normalize_metadata_in_directory(output_dir)
        except Exception as exc:
            logger.warning("Metadata normalization failed: %s", exc)

    return {
        'success': len(failed_files) == 0,
        'files_processed': len(successful_files) + len(failed_files),
        'successful': len(successful_files),
        'failed': len(failed_files),
        'low_quality': 0,
        'errors': failed_files
    }
    # --- NEW IMPLEMENTATION END ---

class BatchTextExtractorEnhancedPrerefactor:
    """Enhanced batch processor for PDF files with pre-refactoring features"""
    
    def __init__(self, config: Optional[Dict] = None, project_config: Optional[Union[str, ProjectConfig]] = None):
        """Initialize the batch text extractor
        
        Args:
            config: Optional configuration dictionary
            project_config: Optional project configuration
        """
        self.config = config or {}
        self.project_config = project_config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize Ghostscript environment
        setup_ghostscript_environment()
        
        # Set default configuration
        self._set_default_config()
        
        # Update with provided config
        if config:
            self.config.update(config)
    
    def _set_default_config(self):
        """Set default configuration values"""
        self.config.update({
            'chunking_mode': 'page',
            'chunk_overlap': 1,
            'min_token_threshold': MIN_TOKEN_THRESHOLD,
            'low_quality_token_threshold': LOW_QUALITY_TOKEN_THRESHOLD,
            'chunk_token_threshold': CHUNK_TOKEN_THRESHOLD,
            'timeout': DEFAULT_TIMEOUT,
            'max_retries': MAX_RETRIES,
            'batch_size': BATCH_SIZE,
            'verbose': False,
            'auto_normalize': True
        })
    
    def process_directory(self, input_dir: str, output_dir: str) -> Dict[str, Any]:
        """Process all PDF files in a directory
        
        Args:
            input_dir: Input directory containing PDFs
            output_dir: Output directory for extracted text
            
        Returns:
            dict: Processing results
        """
        try:
            # Create args namespace with configuration
            args = types.SimpleNamespace(
                output_dir=output_dir,
                verbose=self.config.get('verbose', False),
                auto_normalize=self.config.get('auto_normalize', True),
                chunking_mode=self.config.get('chunking_mode', 'page'),
                chunk_overlap=self.config.get('chunk_overlap', 1),
                timeout=self.config.get('timeout', DEFAULT_TIMEOUT),
                disable_tables=False,
                mixed_lang_ratio=0.30,
                corruption_thresholds=None,
                mt_config=None
            )
            
            # Run processing
            results = run_with_paths(
                input_dir=input_dir,
                output_dir=output_dir,
                chunking_mode=args.chunking_mode,
                chunk_overlap=args.chunk_overlap,
                verbose=args.verbose,
                auto_normalize=args.auto_normalize,
                processor_config=self.config
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing directory: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'files_processed': 0,
                'successful': 0,
                'failed': 0,
                'low_quality': 0
            }
    
    def process_file(self, file_path: str, output_dir: str) -> Dict[str, Any]:
        """Process a single PDF file
        
        Args:
            file_path: Path to input PDF file
            output_dir: Output directory for extracted text
            
        Returns:
            dict: Processing results
        """
        try:
            # Create args namespace with configuration
            args = types.SimpleNamespace(
                output_dir=output_dir,
                verbose=self.config.get('verbose', False),
                auto_normalize=self.config.get('auto_normalize', True),
                chunking_mode=self.config.get('chunking_mode', 'page'),
                chunk_overlap=self.config.get('chunk_overlap', 1),
                timeout=self.config.get('timeout', DEFAULT_TIMEOUT),
                disable_tables=False,
                mixed_lang_ratio=0.30,
                corruption_thresholds=None,
                mt_config=None
            )
            
            # Process the file
            result = process_pdf_file_enhanced(file_path, args)
            
            if result:
                return {
                    'success': True,
                    'file_path': file_path,
                    'output_path': str(Path(output_dir) / '_extracted' / f"{Path(file_path).stem}.txt"),
                    'metadata': result.metadata,
                    'quality_metrics': result.quality_metrics
                }
            else:
                return {
                    'success': False,
                    'file_path': file_path,
                    'error': 'Failed to process file'
                }
                
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
            return {
                'success': False,
                'file_path': file_path,
                'error': str(e)
            }

    # --- BACKWARDS-COMPATIBILITY SHIMS ---
    def configure(self, **kwargs):
        """Update internal configuration in-place (legacy support)."""
        self.config.update(kwargs)
        return self.config

    def extract_file(self, file_path: str, output_dir: str):
        """Alias for process_file to maintain older API surface."""
        return self.process_file(file_path, output_dir)

def main():
    """Main entry point when script is run directly"""
    parser = argparse.ArgumentParser(description='Extract text from PDFs')
    parser.add_argument('--config', required=True, help='Path to project config file')
    parser.add_argument('--chunking-mode', default='page', choices=['page', 'token'], help='How to chunk the text')
    parser.add_argument('--chunk-overlap', type=int, default=1, help='Number of pages/tokens to overlap')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--no-normalize', action='store_true', help='Disable metadata normalization')
    args = parser.parse_args()
    
    results = run_with_project_config(
        project=args.config,
            chunking_mode=args.chunking_mode,
            chunk_overlap=args.chunk_overlap,
            verbose=args.verbose,
        auto_normalize=not args.no_normalize
        )
    
    logger.info("\nExtraction Results:")
    logger.info(f"Processed files: {results['processed_files']}")
    logger.info(f"Successful extractions: {results['successful']}")
    logger.warning(f"Failed extractions: {results['failed']}")
    logger.info(f"Low quality files: {results['low_quality']}")
    
    if args.verbose:
        logger.info("\nDetailed Results:")
        logger.info(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()

# ===== CLEANUP FUNCTION =====
def cleanup_worker_temp_dirs():
    """Clean up temporary directories created by workers."""
    try:
        import glob
        env_temp = _PROJECT.get('environment.temp_dir', tempfile.gettempdir())
        base_temp = Path(env_temp) / 'temp_workers'
        worker_dirs = glob.glob(os.path.join(base_temp, "pdf_worker_*") )
        for worker_dir in worker_dirs:
            try:
                import shutil
                shutil.rmtree(worker_dir, ignore_errors=True)
                logger.info(f"Cleaned up temp dir: {worker_dir}")
            except Exception as exc:
                logger.exception("Unhandled exception in cleanup_worker_temp_dirs: %s", exc)
    except Exception as e:
        logger.info(f"Cleanup warning: {str(e)}") 

def normalize_metadata_in_directory(directory: Path) -> None:
    """Normalize metadata in all JSON files in the directory."""
    logger.info("[INFO] Running metadata normalization on output directory...")
    for json_file in directory.glob("**/*.json"):
        try:
            # Check if .bak file already exists
            bak_file = json_file.with_suffix('.json.bak')
            if bak_file.exists():
                bak_file.unlink()  # Remove existing .bak file
                
            # Now safe to rename
            json_file.rename(bak_file)
            
            with open(bak_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Normalize metadata
            if 'metadata' in data:
                data['metadata'] = normalize_metadata_file(data['metadata'])
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Normalized: {json_file}")
            
        except Exception as e:
            logger.error(f"ERROR processing {json_file}: {str(e)}") 
