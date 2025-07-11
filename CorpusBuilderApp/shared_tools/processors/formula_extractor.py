# processors/formula_extractor.py
"""
Enhanced LaTeX formula extraction and preservation for PDF documents.
Handles both extracted text formulas and direct PDF formula preservation.
"""

import re
import json
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import logging
import pytesseract
from PIL import Image
from io import BytesIO
from shared_tools.config.project_config import ProjectConfig
logger = logging.getLogger(__name__)

class FormulaExtractor:
    """Extract and preserve mathematical formulas from PDFs."""
    
    def __init__(self, config: Optional[Dict] = None, project_config: Optional[Dict] = None):
        """Initialize formula extractor
        
        Args:
            config (dict): Optional configuration
            project_config (dict): Optional project configuration
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Use project config if provided, otherwise use provided config or defaults
        if project_config and 'formula_extraction' in project_config:
            self.config = project_config['formula_extraction']
        else:
            self.config = config or self._get_default_config()
        
        # Enhanced formula patterns
        self.formula_patterns = {
            'inline_latex': r'\$([^$]+)\$',
            'display_latex': r'\$\$([^$]+)\$\$',
            'equation_env': r'\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}',
            'align_env': r'\\begin\{align\*?\}(.*?)\\end\{align\*?\}',
            'eqnarray_env': r'\\begin\{eqnarray\*?\}(.*?)\\end\{eqnarray\*?\}',
            'math_env': r'\\begin\{math\}(.*?)\\end\{math\}',
            'displaymath_env': r'\\begin\{displaymath\}(.*?)\\end\{displaymath\}',
            'bracket_inline': r'\\\(([^)]+)\\\)',
            'bracket_display': r'\\\[([^\]]+)\\\]',
            
            # Financial/mathematical expressions
            'percentage': r'\b\d+(?:\.\d+)?%\b',
            'currency': r'[\$€£¥]\s*\d+(?:,\d{3})*(?:\.\d{2})?',
            'scientific_notation': r'\b\d+(?:\.\d+)?[eE][+-]?\d+\b',
            'ratios': r'\b\d+(?:\.\d+)?:\d+(?:\.\d+)?\b',
            'fractions': r'\b\d+/\d+\b',
            'greek_letters': r'\\(?:alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lambda|mu|nu|xi|omicron|pi|rho|sigma|tau|upsilon|phi|chi|psi|omega)\b',
            
            # Statistical formulas
            'probability': r'P\([^)]+\)',
            'expectation': r'E\[[^\]]+\]',
            'variance': r'Var\([^)]+\)',
            'correlation': r'Corr\([^)]+\)',
            
            # Financial formulas
            'volatility': r'σ\s*[²₂]?',
            'returns': r'R_[{\w}]+',
            'derivatives': r'd[A-Z]/d[A-Z]',
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'min_formula_length': 3,
            'max_formula_length': 1000,
            'patterns': {
                'latex': True,
                'mathml': True,
                'inline': True
            }
        }
    
    def extract(self, text: str) -> Dict[str, Any]:
        """Extract formulas from text
        
        Args:
            text (str): Text to analyze
            
        Returns:
            dict: Extraction results
        """
        results = {
            'formulas': [],
            'count': 0
        }
        
        # Extract LaTeX formulas
        if self.config['patterns']['latex']:
            latex_formulas = self._extract_latex(text)
            results['formulas'].extend(latex_formulas)
        
        # Extract MathML formulas
        if self.config['patterns']['mathml']:
            mathml_formulas = self._extract_mathml(text)
            results['formulas'].extend(mathml_formulas)
        
        # Extract inline formulas
        if self.config['patterns']['inline']:
            inline_formulas = self._extract_inline(text)
            results['formulas'].extend(inline_formulas)
        
        # Filter formulas by length
        results['formulas'] = [
            f for f in results['formulas']
            if self.config['min_formula_length'] <= len(f) <= self.config['max_formula_length']
        ]
        
        results['count'] = len(results['formulas'])
        return results
    
    def _extract_latex(self, text: str) -> List[str]:
        """Extract LaTeX formulas"""
        formulas = []
        
        for pattern_name, pattern in self.formula_patterns.items():
            matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                formula_text = match.group(1) if match.groups() else match.group(0)
                
                # Validate formula
                if not self._validate_formula(formula_text, pattern_name):
                    continue
                
                formula_data = {
                    'formula': formula_text.strip(),
                    'type': pattern_name,
                    'position': {
                        'start': match.start(),
                        'end': match.end()
                    },
                    'context': "",
                    'confidence': self._calculate_confidence(formula_text, pattern_name),
                    'metadata': self._extract_formula_metadata(formula_text, pattern_name)
                }
                
                formulas.append(formula_data)
        
        # Remove duplicates and sort by position
        formulas = self._deduplicate_formulas(formulas)
        formulas.sort(key=lambda x: x['position']['start'])
        
        for formula in formulas:
            if 'metadata' not in formula or not formula['metadata']:
                formula['metadata'] = self._extract_formula_metadata(formula.get('formula', ''), formula.get('type', 'unknown'))
            if 'complexity_score' not in formula['metadata']:
                formula['metadata']['complexity_score'] = 0.0
        
        return formulas
    
    def _extract_mathml(self, text: str) -> List[str]:
        """Extract MathML formulas"""
        # Implementation details...
        return []
    
    def _extract_inline(self, text: str) -> List[str]:
        """Extract inline formulas"""
        # Implementation details...
        return []
    
    def _validate_formula(self, formula: str, pattern_type: str) -> bool:
        """Validate if extracted text is likely a genuine formula."""
        if len(formula) < self.config['min_formula_length']:
            return False
        
        if len(formula) > self.config['max_formula_length']:
            return False
        
        # Skip common false positives
        false_positives = [
            r'^\d+$',  # Just numbers
            r'^[a-zA-Z]+$',  # Just words
            r'^\s*$',  # Just whitespace
        ]
        
        for fp_pattern in false_positives:
            if re.match(fp_pattern, formula.strip()):
                return False
        
        # LaTeX validation for LaTeX patterns
        if self.config['patterns']['latex'] and 'latex' in pattern_type:
            return self._validate_latex_syntax(formula)
        
        return True
    
    def _validate_latex_syntax(self, formula: str) -> bool:
        """Basic LaTeX syntax validation."""
        # Check for balanced braces
        brace_count = formula.count('{') - formula.count('}')
        if brace_count != 0:
            return False
        
        # Check for valid LaTeX commands
        commands = re.findall(r'\\[a-zA-Z]+', formula)
        valid_commands = {
            'frac', 'sqrt', 'sum', 'int', 'prod', 'lim', 'exp', 'log', 'ln',
            'sin', 'cos', 'tan', 'sec', 'csc', 'cot', 'arcsin', 'arccos', 'arctan',
            'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta',
            'lambda', 'mu', 'nu', 'pi', 'rho', 'sigma', 'tau', 'phi', 'chi', 'psi', 'omega',
            'partial', 'nabla', 'infty', 'pm', 'mp', 'times', 'div', 'cdot',
            'leq', 'geq', 'neq', 'approx', 'equiv', 'sim', 'propto',
            'in', 'notin', 'subset', 'supset', 'cap', 'cup',
            'left', 'right', 'big', 'Big', 'bigg', 'Bigg',
            'text', 'textbf', 'textit', 'mathrm', 'mathbf', 'mathit', 'mathcal'
        }
        
        for cmd in commands:
            cmd_name = cmd[1:]  # Remove backslash
            if cmd_name not in valid_commands:
                # Unknown command - might still be valid, so we're lenient
                pass
        
        return True
    
    def _calculate_confidence(self, formula: str, pattern_type: str) -> float:
        """Calculate confidence score for formula extraction."""
        confidence = 0.5  # Base confidence
        
        # Higher confidence for explicit LaTeX environments
        if 'env' in pattern_type:
            confidence += 0.3
        elif 'latex' in pattern_type:
            confidence += 0.2
        
        # Higher confidence for mathematical symbols
        math_symbols = ['\\', '^', '_', '{', '}', 'sum', 'int', 'frac', 'sqrt']
        symbol_count = sum(1 for symbol in math_symbols if symbol in formula)
        confidence += min(0.3, symbol_count * 0.05)
        
        # Lower confidence for very short formulas
        if len(formula) < 5:
            confidence -= 0.2
        
        return min(1.0, max(0.0, confidence))
    
    def _extract_formula_metadata(self, formula: str, pattern_type: str) -> Dict[str, Any]:
        """Extract metadata about the formula, with defensive coding for all fields."""
        try:
            complexity_score = self._calculate_complexity(formula)
        except Exception:
            complexity_score = 0.0
        metadata = {
            'length': len(formula),
            'has_greek_letters': bool(re.search(r'\\[a-zA-Z]+', formula)),
            'has_superscript': '^' in formula,
            'has_subscript': '_' in formula,
            'has_fractions': 'frac' in formula or '/' in formula,
            'has_integrals': bool(re.search(r'\\int|∫', formula)),
            'has_summations': bool(re.search(r'\\sum|Σ', formula)),
            'complexity_score': complexity_score,
            'source': pattern_type if pattern_type else 'unknown'
        }
        # Ensure all required keys exist with defaults
        required_keys = ['length', 'has_greek_letters', 'has_superscript', 'has_subscript', 'has_fractions', 'has_integrals', 'has_summations', 'complexity_score', 'source']
        for key in required_keys:
            if key not in metadata:
                metadata[key] = 0 if 'has_' in key or key == 'length' else ''
        return metadata
    
    def _calculate_complexity(self, formula: str) -> float:
        """Calculate complexity score for the formula."""
        complexity = 0
        
        # Count nesting levels
        max_nesting = 0
        current_nesting = 0
        for char in formula:
            if char == '{':
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
            elif char == '}':
                current_nesting -= 1
        
        complexity += max_nesting * 0.2
        
        # Count LaTeX commands
        commands = len(re.findall(r'\\[a-zA-Z]+', formula))
        complexity += commands * 0.1
        
        # Count operators
        operators = len(re.findall(r'[+\-*/=<>≤≥≠∈∉⊂⊃∩∪]', formula))
        complexity += operators * 0.05
        
        return min(1.0, complexity)
    
    def _deduplicate_formulas(self, formulas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate formulas based on content similarity."""
        unique_formulas = []
        seen_formulas = set()
        
        for formula in formulas:
            # Normalize formula text for comparison
            normalized = re.sub(r'\s+', ' ', formula['formula'].strip().lower())
            
            if normalized not in seen_formulas:
                seen_formulas.add(normalized)
                unique_formulas.append(formula)
        
        return unique_formulas
    
    def extract_comprehensive(self, pdf_path: str, text: str) -> Dict[str, Any]:
        """Extract formulas using both PDF structure, text analysis, and OCR."""
        text_formulas = self.extract(text)
        pdf_formulas = self.extract_from_pdf(pdf_path)
        ocr_formulas = self.extract_from_ocr(pdf_path)
        # Combine and deduplicate
        all_formulas = text_formulas['formulas'] + pdf_formulas + ocr_formulas
        unique_formulas = self._deduplicate_formulas(all_formulas)
        # Calculate statistics
        stats = {
            'total_formulas': len(unique_formulas),
            'text_source': len(text_formulas['formulas']),
            'pdf_source': len(pdf_formulas),
            'ocr_source': len(ocr_formulas),
            'avg_confidence': sum(f.get('confidence', 0) for f in unique_formulas) / len(unique_formulas) if unique_formulas else 0,
            'complexity_distribution': self._analyze_complexity_distribution(unique_formulas),
            'formula_types': self._analyze_formula_types(unique_formulas)
        }
        return {
            'formulas': unique_formulas,
            'statistics': stats,
            'extraction_metadata': {
                'config': self.config,
                'patterns_used': list(self.formula_patterns.keys())
            }
        }
    
    def _analyze_complexity_distribution(self, formulas: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze the distribution of formula complexity."""
        distribution = {'simple': 0, 'medium': 0, 'complex': 0}
        
        for formula in formulas:
            complexity = formula['metadata']['complexity_score']
            if complexity < 0.3:
                distribution['simple'] += 1
            elif complexity < 0.7:
                distribution['medium'] += 1
            else:
                distribution['complex'] += 1
        
        return distribution
    
    def _analyze_formula_types(self, formulas: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze the types of formulas found."""
        type_counts = {}
        
        for formula in formulas:
            formula_type = formula['type']
            type_counts[formula_type] = type_counts.get(formula_type, 0) + 1
        
        return type_counts

    def extract_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract formulas directly from PDF structure."""
        formulas = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Extract text blocks with formatting
                blocks = page.get_text("dict")
                
                for block in blocks.get("blocks", []):
                    if "lines" in block:
                        for line in block["lines"]:
                            line_text = ""
                            has_math_font = False
                            
                            for span in line.get("spans", []):
                                text = span.get("text", "")
                                font = span.get("font", "").lower()
                                
                                # Detect mathematical fonts
                                if any(math_font in font for math_font in 
                                      ['symbol', 'math', 'times', 'cmr', 'latin']):
                                    has_math_font = True
                                
                                line_text += text
                            
                            # If line contains mathematical content, extract formulas
                            if has_math_font and line_text.strip():
                                line_formulas = self.extract(line_text)
                                
                                for formula in line_formulas:
                                    formula['page'] = page_num + 1
                                    formula['source'] = 'pdf_structure'
                                    formula['font_based'] = True
                                    formulas.append(formula)
            
            doc.close()
            
        except Exception as e:
            self.logger.error(f"Error extracting formulas from PDF {pdf_path}: {e}")
        
        for formula in formulas:
            if 'metadata' not in formula or not formula['metadata']:
                formula['metadata'] = self._extract_formula_metadata(formula.get('formula', ''), formula.get('type', 'unknown'))
            if 'complexity_score' not in formula['metadata']:
                formula['metadata']['complexity_score'] = 0.0
        
        return formulas
    
    def extract_from_ocr(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract formulas from rendered page images using OCR."""
        formulas = []
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                img = Image.open(BytesIO(pix.tobytes("png")))
                ocr_text = pytesseract.image_to_string(img, config='--psm 6')
                # Heuristic: look for math symbols or patterns
                if any(sym in ocr_text for sym in ['=', '\\frac', '\\sum', '\\int', '+', '-', '*', '/', '^']):
                    formulas.append({
                        'formula': ocr_text.strip(),
                        'type': 'ocr_image',
                        'page': page_num + 1,
                        'confidence': 0.5,  # Placeholder
                        'source': 'ocr_image'
                    })
            doc.close()
        except Exception as e:
            self.logger.error(f"Error extracting formulas via OCR from PDF {pdf_path}: {e}")
        
        for formula in formulas:
            if 'metadata' not in formula or not formula['metadata']:
                formula['metadata'] = self._extract_formula_metadata(formula.get('formula', ''), formula.get('type', 'ocr_image'))
            if 'complexity_score' not in formula['metadata']:
                formula['metadata']['complexity_score'] = 0.0
        
        return formulas

def run_with_project_config(project: 'ProjectConfig', verbose: bool = False):
    """Run formula extraction with project configuration
    
    Args:
        project (ProjectConfig): Project configuration
        verbose (bool): Enable verbose output
        
    Returns:
        dict: Extraction results
    """
    extractor = FormulaExtractor(
        project_config=project.get_processor_config('formula_extraction')
    )
    
    # Process files
    results = extractor.process_directory(project.get_input_dir())
    
    if verbose:
        logger.info("\nFormula Extraction Results:")
        logger.info(f"Processed files: {len(results['processed_files'])}")
        logger.info(f"Total formulas found: {results['total_formulas']}")
        logger.info(f"Files with formulas: {results['files_with_formulas']}")
    
    return results

def main():
    """Main entry point when script is run directly"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract formulas from corpus')
    parser.add_argument('--corpus-dir', required=True, help='Corpus directory')
    parser.add_argument('--project-config', help='Path to project config file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    if args.project_config:
        # Use project config
        from shared_tools.project_config import ProjectConfig
        project = ProjectConfig.load(args.project_config)
        results = run_with_project_config(project, args.verbose)
    else:
        # Use default configuration
        extractor = FormulaExtractor()
        results = extractor.process_directory(args.corpus_dir)
    
    # Save results
    output_file = Path(args.corpus_dir) / 'formula_extraction.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\nExtraction results saved to: {output_file}")

if __name__ == "__main__":
    main()
