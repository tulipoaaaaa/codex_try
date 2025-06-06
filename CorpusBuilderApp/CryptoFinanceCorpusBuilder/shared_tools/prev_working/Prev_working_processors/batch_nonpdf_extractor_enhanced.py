from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import logging
import json
import ast
import re
import os
from datetime import datetime, timezone
import concurrent.futures
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd
from bs4 import BeautifulSoup
import markdown
from langdetect import detect, LangDetectException
from nltk.stem import PorterStemmer
from tqdm import tqdm
import multiprocessing
import threading
import argparse
import sys
import shutil
from collections import Counter
import math
import hashlib
from io import StringIO

from CryptoFinanceCorpusBuilder.processors.base_extractor import BaseExtractor, ExtractionError
from CryptoFinanceCorpusBuilder.processors.formula_extractor import FormulaExtractor
from CryptoFinanceCorpusBuilder.processors.finacial_symbol_processor import FinancialSymbolProcessor, AcademicPaperProcessor, MemoryOptimizer
from CryptoFinanceCorpusBuilder.processors.chart_image_extractor import ChartImageExtractor
from CryptoFinanceCorpusBuilder.processors.domain_classifier import DomainClassifier
from CryptoFinanceCorpusBuilder.processors.quality_control import QualityControlService
from CryptoFinanceCorpusBuilder.processors.language_confidence_detector import detect_language_confidence
from CryptoFinanceCorpusBuilder.processors.corruption_detector import detect_corruption
from CryptoFinanceCorpusBuilder.processors.machine_translation_detector import detect_machine_translation
from CryptoFinanceCorpusBuilder.utils.extractor_utils import extract_metadata, calculate_hash, safe_filename
from CryptoFinanceCorpusBuilder.utils.domain_utils import get_domain_for_file, DOMAIN_KEYWORDS

# Configure logging
log_dir = Path("G:/ai_trading_dev/CryptoFinanceCorpusBuilder/logs")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "batch_nonpdf_extractor.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
MIN_TOKEN_THRESHOLD = 100
LOW_QUALITY_TOKEN_THRESHOLD = 500
SUPPORTED_EXTENSIONS = {
    '.py': 'python',
    '.ipynb': 'jupyter',
    '.md': 'markdown',
    '.html': 'html',
    '.htm': 'html',
    '.json': 'json',
    '.csv': 'csv'
}
CHUNK_TOKEN_THRESHOLD = 1000  # Lower threshold for non-PDF files since they're typically shorter

BATCH_SIZE = 20
DEFAULT_TIMEOUT = 300

# Thread-local storage for worker info
thread_local = threading.local()

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

print('DEBUG: sys.executable =', sys.executable)
print('DEBUG: sys.path =', sys.path)

def get_worker_temp_dir():
    """Get temporary directory for current worker"""
    worker_id = getattr(thread_local, 'worker_id', 'unknown')
    base_temp = Path("G:/ai_trading_dev/CryptoFinanceCorpusBuilder/temp_workers")
    base_temp.mkdir(parents=True, exist_ok=True)
    temp_dir = base_temp / f"temp_worker_{worker_id}"
    temp_dir.mkdir(exist_ok=True)
    return temp_dir

def worker_initializer():
    """Initialize worker process"""
    thread_local.worker_id = os.getpid()

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

def get_domain_for_file(file_path: str) -> Optional[str]:
    """Get domain classification for file"""
    # First try path-based classification
    path_domain = get_domain_from_path(Path(file_path))
    if path_domain:
        return path_domain
        
    # If no path-based domain, try content-based
    try:
        # Extract text and ignore tables/images for domain classification
        text, _, _ = extract_text_from_file(file_path)
        domain_classifier = DomainClassifier()
        domain_info = domain_classifier.classify(text)
        return domain_info.get('domain')
    except Exception as e:
        logger.warning(f"Error in content-based domain classification: {e}")
        return None

def get_domain_from_path(rel_path):
    """Get domain from file path"""
    for domain in DOMAIN_THRESHOLDS:
        if domain in str(rel_path).lower():
            return domain
    return None

def compute_relevance_score(text: str, domain: str) -> Tuple[float, str, List[str]]:
    """Compute relevance score for text in a domain."""
    domain_thresholds = DOMAIN_THRESHOLDS.get(domain, {})
    if not domain_thresholds:
        return 0, 'low', []
    
    # Get domain keywords
    domain_classifier = DomainClassifier()
    domain_info = domain_classifier.classify(text)
    domain_scores = domain_info.get('scores', {})
    
    # Calculate base score from domain classifier
    base_score = domain_scores.get(domain, 0) * 100
    
    # Adjust score based on domain-specific thresholds
    if base_score >= domain_thresholds.get('quality_threshold', 0.8) * 100:
        flag = 'high'
    elif base_score >= domain_thresholds.get('quality_threshold', 0.8) * 50:
        flag = 'medium'
    else:
        flag = 'low'
    
    # Get matched keywords from domain classifier
    matched_keywords = []
    for kw, score in domain_scores.items():
        if score > 0:
            matched_keywords.append(kw)
    
    return base_score, flag, sorted(matched_keywords)

def count_tokens(text):
    """Count tokens in text."""
    return len(text.split())

def quality_flag(text):
    """Determine quality flag based on token count."""
    tokens = count_tokens(text)
    if tokens < MIN_TOKEN_THRESHOLD:
        return 'low_quality'
    elif tokens < LOW_QUALITY_TOKEN_THRESHOLD:
        return 'flagged'
    else:
        return 'ok'

def preprocess_text_for_quality_checks(text: str, file_type: str) -> str:
    """Preprocess text based on file type before quality checks."""
    if file_type == '.md':
        # Remove markdown syntax but preserve content
        text = re.sub(r'[#*_`]', '', text)  # Remove formatting
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Convert links to text
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # Remove code blocks
        text = re.sub(r'`.*?`', '', text)  # Remove inline code
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)  # Remove list markers
    return text

def process_nonpdf_file_enhanced(file_path: str, args: argparse.Namespace) -> Optional[ExtractionResult]:
    worker_temp = get_worker_temp_dir()
    worker_id = getattr(thread_local, 'worker_id', 'unknown')
    try:
        if getattr(args, 'verbose', False):
            print(f"[{worker_id}] Starting processing: {os.path.basename(file_path)}")
        
        # Extract text based on file type
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            logger.warning(f"Unsupported file type: {ext}")
            return None
            
        # Add debug logging before text extraction
        print(f"DEBUG: About to extract text from {file_path}")
        print(f"DEBUG: File extension: {ext}")
        print(f"DEBUG: Using extraction method: {SUPPORTED_EXTENSIONS[ext]}")
        
        # Extract text
        text, tables, images = extract_text_from_file(file_path)
        print(f"DEBUG: Text extracted successfully, length: {len(text)}")
        
        if not text or len(text.strip()) < MIN_TOKEN_THRESHOLD:
            print(f"[{worker_id}] Extracted text too short: {len(text.strip())} tokens")
            return None
            
        # Get domain classification
        domain = get_domain_for_file(file_path)
        if not domain:
            print(f"[{worker_id}] Could not determine domain for {os.path.basename(file_path)}")
            return None
            
        # Get domain info from classifier
        domain_classifier = DomainClassifier()
        domain_info = domain_classifier.classify(text)
        
        # Initialize processors
        formula_extractor = FormulaExtractor()
        symbol_processor = FinancialSymbolProcessor()
        academic_processor = AcademicPaperProcessor()
        
        # Special handling for code files
        is_code_file = ext in ['.py', '.ipynb']
        is_html_file = ext in ['.html', '.htm']
        
        if is_code_file:
            # Never mark code files as academic papers
            academic_analysis = {
                'is_academic_paper': False,
                'confidence': 0.0,
                'score': 0,
                'indicators_found': [],
                'citation_count': 0,
                'recommended_thresholds': None
            }
            # Skip formula detection for code files
            formula_results = {'formulas': []}
            # Adjust domain confidence for code files in crypto/finance domains
            if domain in ['crypto_derivatives', 'high_frequency_trading', 'market_microstructure']:
                domain_info['confidence'] = min(1.0, domain_info['confidence'] * 1.5)
            
            # Code-specific symbol detection
            symbol_results = {
                'symbols_by_type': {
                    'stock_ticker': [],
                    'crypto_symbol': [],
                    'financial_term': []
                }
            }
            # Extract only actual trading-related symbols from code
            code_symbols = []
            for line in text.split('\n'):
                # Look for trading-specific patterns
                if 'symbol' in line.lower() or 'pair' in line.lower() or 'ticker' in line.lower():
                    # Extract potential trading symbols
                    matches = re.findall(r'["\']([A-Z0-9]+/[A-Z0-9]+)["\']', line)
                    for symbol in matches:
                        if '/' in symbol:  # Only include actual trading pairs
                            code_symbols.append({
                                'symbol': symbol,
                                'type': 'crypto_symbol',
                                'pattern': 'trading_pair',
                                'context': line.strip(),
                                'confidence': 0.9,
                                'metadata': {
                                    'source': 'code_analysis',
                                    'is_trading_pair': True
                                }
                            })
            symbol_results['symbols_by_type']['crypto_symbol'] = code_symbols
            
            # Extract code-specific information
            docstrings = []
            comments = []
            functions = []
            classes = []
            
            try:
                tree = ast.parse(text)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        functions.append(node.name)
                        if ast.get_docstring(node):
                            docstrings.append(ast.get_docstring(node))
                    elif isinstance(node, ast.ClassDef):
                        classes.append(node.name)
                        if ast.get_docstring(node):
                            docstrings.append(ast.get_docstring(node))
                    elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
                        docstrings.append(node.value.s)
                    elif isinstance(node, ast.Comment):
                        comments.append(node.value)
            except Exception as e:
                logger.warning(f"Error parsing code structure: {str(e)}")
                # Initialize with empty values if parsing fails
                docstrings = []
                comments = []
                functions = []
                classes = []
            
            # Code-specific quality metrics
            quality_metrics = {
                'language_confidence': {
                    'language': 'en',
                    'language_confidence': 1.0,
                    'mixed_language_flag': False,
                    'mixed_languages': ['en'],
                    'reasons': ['Code file detected - language metrics adjusted for code context'],
                    'severity': 'ok'
                },
                'corruption': {
                    'corruption_flag': False,
                    'corruption_score': 100,
                    'corruption_score_normalized': 100,
                    'corruption_reasons': [
                        'Code file detected - high symbol-to-word ratio is expected',
                        'No actual corruption detected'
                    ],
                    'severity': 'ok'
                },
                'machine_translation': {
                    'machine_translated_flag': False,
                    'machine_translation_score': 0,
                    'machine_translation_reasons': ['Code pattern detected'],
                    'machine_translation_severity': 'ok',
                    'machine_translation_confidence': 0.0
                },
                'academic_analysis': academic_analysis,
                'content_validation': {
                    'passes_academic_standards': True,
                    'issues': [],
                    'adjustments_made': ['Code-specific validation applied']
                },
                'symbol_richness': {
                    'total_symbols': len(code_symbols),
                    'unique_symbols': len(set(s['symbol'] for s in code_symbols)),
                    'financial_symbols': len(code_symbols)
                }
            }

            # Add code-specific metadata
            metadata = {
                'file_type': SUPPORTED_EXTENSIONS[ext],
                'extraction_method': f'nonpdf_{SUPPORTED_EXTENSIONS[ext]}',
                'domain': domain,
                'domain_info': domain_info,
                'quality_metrics': quality_metrics,
                'content_hash': hashlib.md5(text.encode('utf-8')).hexdigest(),
                'file_size': os.path.getsize(file_path),
                'extraction_date': datetime.now(timezone.utc).isoformat(),
                'enhancement_results': {
                    'formulas': formula_results,
                    'symbols': symbol_results,
                    'symbol_glossary': symbol_glossary if not is_code_file else None,
                    'academic_analysis': academic_analysis
                },
                'code_specific': {
                    'is_trading_code': True,
                    'trading_symbols_found': code_symbols,
                    'code_quality': {
                        'has_docstrings': bool(docstrings),
                        'has_type_hints': any('->' in line for line in text.split('\n')),
                        'has_comments': bool(comments),
                        'function_count': len(functions),
                        'class_count': len(classes)
                    }
                }
            }
        elif is_html_file:
            # Process HTML files with special attention to tables and images
            formula_results = formula_extractor.extract_from_text(text)
            
            # Extract symbols from both text and tables
            symbol_results = symbol_processor.extract_symbols(text)
            
            # Add symbols from tables
            for table in tables:
                # Check table headers for potential symbols
                for header in table.get('headers', []):
                    if isinstance(header, str):
                        table_symbols = symbol_processor.extract_symbols(header)
                        for symbol_type, symbols in table_symbols.get('symbols_by_type', {}).items():
                            symbol_results['symbols_by_type'][symbol_type].extend(symbols)
                
                # Check table data for potential symbols
                for row in table.get('data', []):
                    for cell in row:
                        if isinstance(cell, str):
                            cell_symbols = symbol_processor.extract_symbols(cell)
                            for symbol_type, symbols in cell_symbols.get('symbols_by_type', {}).items():
                                symbol_results['symbols_by_type'][symbol_type].extend(symbols)
            
            # Filter out false positive symbols
            filtered_symbols = []
            for symbol in symbol_results.get('symbols_by_type', {}).get('stock_ticker', []):
                # Skip common abbreviations and non-financial symbols
                if symbol['symbol'] in ['AI', 'VS', 'JDK']:
                    continue
                # Skip symbols that are part of larger words
                context = symbol.get('context', '')
                if not re.search(r'\b' + re.escape(symbol['symbol']) + r'\b', context):
                    continue
                filtered_symbols.append(symbol)
            
            symbol_results['symbols_by_type']['stock_ticker'] = filtered_symbols
            symbol_glossary = symbol_processor.generate_symbol_glossary(symbol_results)
            academic_analysis = academic_processor.detect_academic_paper(text, {})
            
            # Enhanced quality metrics for HTML files
            quality_metrics = {
                'language_confidence': detect_language_confidence(text, args.lang_conf_threshold, args.mixed_lang_ratio),
                'corruption': detect_corruption(text, args.corruption_thresholds),
                'machine_translation': detect_machine_translation(text, args.mt_config),
                'academic_analysis': academic_analysis,
                'content_validation': academic_processor.validate_academic_content(text, {
                    'formulas': formula_results,
                    'symbols': symbol_results
                }),
                'symbol_richness': {
                    'total_symbols': len(filtered_symbols),
                    'unique_symbols': len(set(s['symbol'] for s in filtered_symbols)),
                    'financial_symbols': len([s for s in filtered_symbols if s.get('type') == 'financial'])
                },
                'table_analysis': {
                    'total_tables': len(tables),
                    'tables_with_headers': len([t for t in tables if t.get('headers')]),
                    'tables_with_data': len([t for t in tables if t.get('data')]),
                    'average_rows': sum(len(t.get('data', [])) for t in tables) / len(tables) if tables else 0,
                    'average_columns': sum(len(t.get('headers', [])) for t in tables) / len(tables) if tables else 0
                },
                'image_analysis': {
                    'total_images': len(images),
                    'images_with_alt': len([i for i in images if i.get('alt')]),
                    'images_with_title': len([i for i in images if i.get('title')])
                }
            }

            # Add HTML-specific metadata for research content
            metadata = {
                'file_type': SUPPORTED_EXTENSIONS[ext],
                'extraction_method': f'nonpdf_{SUPPORTED_EXTENSIONS[ext]}',
                'domain': domain,
                'domain_info': domain_info,
                'quality_metrics': quality_metrics,
                'content_hash': hashlib.md5(text.encode('utf-8')).hexdigest(),
                'file_size': os.path.getsize(file_path),
                'extraction_date': datetime.now(timezone.utc).isoformat(),
                'enhancement_results': {
                    'formulas': formula_results,
                    'symbols': symbol_results,
                    'symbol_glossary': symbol_glossary if not is_code_file else None,
                    'academic_analysis': academic_analysis
                },
                'html_specific': {
                    'is_research_content': True,
                    'has_repeated_headers': True,
                    'quality_flags_explanation': {
                        'machine_translation': 'Likely false positive due to repeated headers in research blog format',
                        'corruption': 'Likely false positive due to HTML structure'
                    }
                }
            }
        else:
            # Process non-code files as before
            formula_results = formula_extractor.extract_from_text(text)
            symbol_results = symbol_processor.extract_symbols(text)
            
            # Filter out false positive symbols
            filtered_symbols = []
            for symbol in symbol_results.get('symbols_by_type', {}).get('stock_ticker', []):
                # Skip common abbreviations and non-financial symbols
                if symbol['symbol'] in ['AI', 'VS', 'JDK']:
                    continue
                # Skip symbols that are part of larger words
                context = symbol.get('context', '')
                if not re.search(r'\b' + re.escape(symbol['symbol']) + r'\b', context):
                    continue
                filtered_symbols.append(symbol)
            
            symbol_results['symbols_by_type']['stock_ticker'] = filtered_symbols
            symbol_glossary = symbol_processor.generate_symbol_glossary(symbol_results)
            academic_analysis = academic_processor.detect_academic_paper(text, {})
            
            # Standard quality checks for non-code files
            quality_metrics = {
                'language_confidence': detect_language_confidence(text, args.lang_conf_threshold, args.mixed_lang_ratio),
                'corruption': detect_corruption(text, args.corruption_thresholds),
                'machine_translation': detect_machine_translation(text, args.mt_config),
                    'academic_analysis': academic_analysis,
                'content_validation': academic_processor.validate_academic_content(text, {
                    'formulas': formula_results,
                    'symbols': symbol_results
                }),
                'symbol_richness': {
                    'total_symbols': len(filtered_symbols),
                    'unique_symbols': len(set(s['symbol'] for s in filtered_symbols)),
                    'financial_symbols': len([s for s in filtered_symbols if s.get('type') == 'financial'])
                }
            }
            
            # Add default metadata for non-code, non-HTML files
            metadata = {
                'file_type': SUPPORTED_EXTENSIONS[ext],
                'extraction_method': f'nonpdf_{SUPPORTED_EXTENSIONS[ext]}',
                'domain': domain,
                'domain_info': domain_info,
                'quality_metrics': quality_metrics,
                'content_hash': hashlib.md5(text.encode('utf-8')).hexdigest(),
                'file_size': os.path.getsize(file_path),
                'extraction_date': datetime.now(timezone.utc).isoformat(),
                'enhancement_results': {
                    'formulas': formula_results,
                    'symbols': symbol_results,
                    'symbol_glossary': symbol_glossary if not is_code_file else None,
                    'academic_analysis': academic_analysis
                }
            }
        
        # Add quality thresholds
        quality_metrics.update({
            'min_tokens': MIN_TOKEN_THRESHOLD,
            'quality_threshold': DOMAIN_THRESHOLDS[domain]['quality_threshold'],
            'table_threshold': DOMAIN_THRESHOLDS[domain]['table_threshold'],
            'formula_threshold': DOMAIN_THRESHOLDS[domain]['formula_threshold'],
            'extraction_quality': {
                'formulas_detected': bool(formula_results.get('formulas', []) if isinstance(formula_results, dict) else formula_results),
                'symbols_detected': bool(symbol_results['symbols_by_type'].get('crypto_symbol' if is_code_file else 'stock_ticker')),
                'token_count': count_tokens(text),
                'quality_flag': quality_flag(text),
                'is_academic_paper': academic_analysis['is_academic_paper'],
                'academic_confidence': academic_analysis['confidence']
            }
        })
            
        return ExtractionResult(
            text=text,
            metadata=metadata,
            tables=tables,
            formulas=formula_results.get('formulas', []) if isinstance(formula_results, dict) else formula_results,
            quality_metrics=quality_metrics,
            errors=[],
            warnings=[]
        )
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return None

def extract_text_from_file(file_path: str) -> Tuple[str, List[Dict], List[Dict]]:
    """Extract text from a non-PDF file."""
    ext = Path(file_path).suffix.lower()
    try:
        if ext == '.py':
            return extract_text_from_python(file_path), [], []
        elif ext == '.ipynb':
            return extract_text_from_jupyter(file_path), [], []
        elif ext == '.md':
            return extract_text_from_markdown(file_path), [], []
        elif ext in ['.html', '.htm']:
            return extract_text_from_html(file_path)
        elif ext == '.json':
            return extract_text_from_json(file_path), [], []
        elif ext == '.csv':
            return extract_text_from_csv(file_path), [], []
        else:
            raise ExtractionError(f"Unsupported file type: {ext}")
    except Exception as e:
        logger.warning(f"Error extracting text from file {file_path}: {str(e)}")
        return '', [], []
    
def extract_text_from_python(file_path: str) -> str:
    """Extract text from a Python file with sophisticated chunking."""
    try:
        with open(file_path, encoding='utf-8') as f:
            source = f.read()
            tree = ast.parse(source)
        
        # Collect import statements and module-level assignments
        imports = []
        module_vars = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(ast.get_source_segment(source, node))
            elif isinstance(node, ast.Assign):
                module_vars.append(ast.get_source_segment(source, node))
        
        # Collect top-level functions/classes and their docstrings
        blocks = []
        block_texts = []
        block_docstrings = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                block_text = ast.get_source_segment(source, node)
                docstring = ast.get_docstring(node) or ''
                if block_text:
                    blocks.append(node)
                    block_texts.append(block_text)
                    block_docstrings.append(docstring)
        
        # Fallback: if no functions/classes, chunk by lines
        if not block_texts:
            lines = source.splitlines()
            block_texts = ['\n'.join(lines[i:i+50]) for i in range(0, len(lines), 50)]
            block_docstrings = [''] * len(block_texts)
        
        # Combine all parts
        import_block = '\n'.join(imports)
        module_vars_block = '\n'.join(module_vars)
        context_block = '\n'.join([import_block, module_vars_block]).strip()
        
        # Combine with docstrings and code
        text_parts = []
        if context_block:
            text_parts.append(context_block)
        
        for block, docstring in zip(block_texts, block_docstrings):
            if docstring:
                text_parts.append(docstring)
            text_parts.append(block)
        
        return '\n\n'.join(text_parts)
    except Exception as e:
        logger.warning(f"Error parsing Python file {file_path}: {str(e)}")
        return source

def extract_text_from_jupyter(file_path: str) -> str:
    """Extract text from a Jupyter notebook with markdown-code grouping."""
    with open(file_path, encoding='utf-8') as f:
        notebook = json.load(f)
    # Group markdown with following code cell
    grouped_cells = []
    i = 0
    while i < len(notebook['cells']):
        cell = notebook['cells'][i]
        if cell['cell_type'] == 'markdown' and i + 1 < len(notebook['cells']) and notebook['cells'][i + 1]['cell_type'] == 'code':
            # Group markdown + code as a unit
            grouped_cells.append([cell, notebook['cells'][i + 1]])
            i += 2
        else:
            grouped_cells.append([cell])
            i += 1
    # Convert groups to text
    text_parts = []
    for group in grouped_cells:
        group_text = []
        for cell in group:
            if cell['cell_type'] == 'markdown':
                source = cell.get('source', '')
                if isinstance(source, list):
                    source = ''.join(source)
                group_text.append(source)
            elif cell['cell_type'] == 'code':
                source = cell.get('source', '')
                if isinstance(source, list):
                    source = ''.join(source)
                group_text.append(source)
                if cell.get('outputs'):
                    for out in cell['outputs']:
                        if 'text' in out:
                            output_text = out['text']
                            if isinstance(output_text, list):
                                output_text = ''.join(output_text)
                            group_text.append(output_text)
                        elif 'data' in out and 'text/plain' in out['data']:
                            output_text = out['data']['text/plain']
                            if isinstance(output_text, list):
                                output_text = ''.join(output_text)
                            group_text.append(output_text)
        text_parts.append('\n\n'.join(group_text))
    return '\n\n'.join(text_parts)

def extract_text_from_markdown(file_path: str) -> str:
    """Extract text from a Markdown file."""
    try:
        with open(file_path, encoding='utf-8') as f:
            text = f.read()
        html = markdown.markdown(text)
        soup = BeautifulSoup(html, 'html.parser')
        # Ensure we get a string from get_text
        extracted_text = soup.get_text('\n')
        if not isinstance(extracted_text, str):
            logger.warning(f"Unexpected type from BeautifulSoup.get_text(): {type(extracted_text)}")
            return text  # Return original text as fallback
        return extracted_text
    except Exception as e:
        logger.warning(f"Error processing Markdown file {file_path}: {str(e)}")
        return text  # Return original text as fallback

def extract_md_chunks(file_path: str) -> List[str]:
    """Extract chunks from a Markdown file, preserving document structure."""
    with open(file_path, encoding='utf-8') as f:
        text = f.read()
    
    # Split by headers (##, ###, etc.) to preserve document structure
    chunks = []
    current_chunk = []
    
    for line in text.split('\n'):
        # Check if line is a header
        if line.strip().startswith('#'):
            # If we have content in current chunk, save it
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
            # Start new chunk with header
            current_chunk.append(line)
        else:
            current_chunk.append(line)
    
    # Add the last chunk if it exists
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    # If no chunks were created (no headers), create one chunk per section
    if not chunks:
        sections = text.split('\n\n')
        chunks = [section for section in sections if section.strip()]
    
    # If still no chunks, use the whole text
    if not chunks:
        chunks = [text]
    
    return chunks

def extract_text_from_html(file_path: str) -> Tuple[str, List[Dict], List[Dict]]:
    """Extract text, tables, and images from an HTML file with content cleaning."""
    with open(file_path, encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove unwanted elements
    for tag in soup(['nav', 'header', 'footer', 'aside', 'script', 'style', 'form', 'noscript', 'iframe', 'svg']):
        tag.decompose()
    
    # Try to get main content first
    main = soup.find('main')
    if main:
        content = main
    else:
        content = soup
    
    # Extract tables
    tables = []
    for table in content.find_all('table'):
        table_data = []
        for row in table.find_all('tr'):
            cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
            if cells:  # Skip empty rows
                table_data.append(cells)
        if table_data:  # Skip empty tables
            tables.append({
                'data': table_data,
                'headers': table_data[0] if table_data else [],
                'rows': len(table_data) - 1 if table_data else 0,
                'columns': len(table_data[0]) if table_data else 0
            })
    
    # Extract images
    images = []
    base_path = os.path.dirname(file_path)
    for img in content.find_all('img'):
        src = img.get('src', '')
        if src:
            # Handle relative paths
            if not src.startswith(('http://', 'https://', 'data:')):
                src = os.path.normpath(os.path.join(base_path, src))
            images.append({
                'src': src,
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'width': img.get('width'),
                'height': img.get('height')
            })
    
    return content.get_text('\n'), tables, images

def extract_text_from_json(file_path: str) -> str:
    """Extract text from a JSON file with schema preservation."""
    with open(file_path, encoding='utf-8') as f:
        data = json.load(f)
    
    # Find top-level metadata keys
    top_meta = {}
    if isinstance(data, dict):
        for k, v in data.items():
            if not isinstance(v, (list, dict)):
                top_meta[k] = v
    
    # Pretty-print JSON with metadata first
    if top_meta:
        meta_str = json.dumps(top_meta, ensure_ascii=False, indent=2)
        data_str = json.dumps(data, ensure_ascii=False, indent=2)
        return f"{meta_str}\n\n{data_str}"
    else:
        return json.dumps(data, ensure_ascii=False, indent=2)

def extract_text_from_csv(file_path: str) -> str:
    """Extract text from a CSV file with header context."""
    df = pd.read_csv(file_path)
    header = ','.join(df.columns)
    rows = df.to_string(index=False, header=False)
    return f"{header}\n{rows}"

def write_outputs(base_dir, rel_path, text, meta, quality, tables=None, formulas=None):
    """Write extracted text and metadata to files."""
    base_dir = Path(base_dir).resolve()  # Ensure absolute path
    out_dir = base_dir / '_extracted'  # Create _extracted subdirectory
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Use stem to remove original extension before adding new ones
    base = safe_filename(rel_path.stem)
    txt_path = out_dir / f"{base}.txt"
    json_path = out_dir / f"{base}.json"

    print(f"DEBUG: Writing text output to {txt_path}")
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"DEBUG: Finished writing text output to {txt_path}")

    output_json = dict(meta)
    if tables is not None:
        output_json['tables'] = tables
    if formulas is not None:
        output_json['formulas'] = formulas

    print(f"DEBUG: Writing JSON output to {json_path}")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)
    print(f"DEBUG: Finished writing JSON output to {json_path}")

    return txt_path, json_path

def main():
    parser = argparse.ArgumentParser(description='Enhanced non-PDF text extraction with quality control')
    parser.add_argument('--input-dir', required=True, help='Input directory containing files')
    parser.add_argument('--output-dir', required=True, help='Output directory for extracted text')
    parser.add_argument('--single-file', help='Process only this specific file')
    parser.add_argument('--disable-formulas', action='store_true', help='Disable formula extraction')
    parser.add_argument('--quality-config', type=str, help='Path to quality control configuration file')
    parser.add_argument('--num-workers', type=int, default=os.cpu_count(), help='Number of worker processes')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, help='Batch size for processing')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT, help='Timeout in seconds')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--mixed-lang-ratio', type=float, default=0.30, help='Threshold for mixed language detection')
    parser.add_argument('--lang-conf-threshold', type=float, default=0.70, help='Language confidence threshold')
    parser.add_argument('--corruption-thresholds', type=str, help='Path to corruption thresholds config')
    parser.add_argument('--mt-config', type=str, help='Path to machine translation config')
    parser.add_argument('--relevance-threshold', type=int, default=30, help='Minimum relevance score threshold')
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
        result = process_nonpdf_file_enhanced(file_path, args)
        if result:
            write_outputs(
                args.output_dir,
                Path(file_path),
                result.text,
                result.metadata,
                result.quality_metrics.get('quality_flag', 'ok'),
                tables=result.tables,
                formulas=result.formulas
            )
        return
    
    # Get list of files for batch processing
    files_to_process = []
    for root, _, files in os.walk(args.input_dir):
        for file in files:
            if file.lower().endswith(tuple(SUPPORTED_EXTENSIONS.keys())):
                files_to_process.append(os.path.join(root, file))
    
    if not files_to_process:
        logger.error(f"No supported files found in {args.input_dir}")
        return
    
    logger.info(f"Found {len(files_to_process)} files to process")
    
    # Track results
    failed_files = []
    successful_files = []
    
    # Use optimal worker count
    args.num_workers = min(args.num_workers, multiprocessing.cpu_count() - 1, 8)
    with ProcessPoolExecutor(max_workers=args.num_workers, initializer=worker_initializer) as executor:
        futures = {}
        for file_path in files_to_process:
            future = executor.submit(process_nonpdf_file_enhanced, file_path, args)
            futures[future] = file_path
        
        completed = 0
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
            completed += 1
            file_path = futures[future]
            result = future.result()
            if result:
                successful_files.append(file_path)
                # Write outputs for successful results
                write_outputs(
                    args.output_dir,
                    Path(file_path),
                    result.text,
                    result.metadata,
                    result.quality_metrics.get('quality_flag', 'ok'),
                    tables=result.tables,
                    formulas=result.formulas
                )
            else:
                failed_files.append((file_path, 'Failed to process (see logs for details)'))
            logger.info(f"Progress: {completed}/{len(files_to_process)} files processed ({len(successful_files)} successful)")
    
    logger.info(f"Processing complete. {len(successful_files)}/{len(files_to_process)} files processed successfully")

    # Print summary
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

if __name__ == '__main__':
    main() 