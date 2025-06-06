# Enhancement Plan for Non-PDF Extractors
# Based on your existing batch_nonpdf_extractor.py structure

# 1. SHARED BASE CLASS (90% reusable)
class EnhancedBaseExtractor(BaseExtractor):
    """Enhanced base with all new processing capabilities."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize shared processors (same as PDF pipeline)
        self.formula_extractor = FormulaExtractor()
        self.symbol_processor = FinancialSymbolProcessor()
        self.academic_processor = AcademicPaperProcessor()
        self.memory_optimizer = MemoryOptimizer()
    
    def process_enhancements(self, text: str, file_path: Path, metadata: Dict) -> Dict:
        """Apply all enhancements - works for any text format."""
        
        enhancements = {}
        
        # 1. Formula extraction (text-based - works everywhere)
        enhancements['formulas'] = self.formula_extractor.extract_from_text(text)
        
        # 2. Symbol processing (text-based - works everywhere)  
        enhancements['symbols'] = self.symbol_processor.extract_symbols(text)
        enhancements['symbol_glossary'] = self.symbol_processor.generate_symbol_glossary(
            enhancements['symbols']
        )
        
        # 3. Academic detection (text-based - works everywhere)
        enhancements['academic_analysis'] = self.academic_processor.detect_academic_paper(
            text, metadata
        )
        
        # 4. Format-specific image/chart extraction (override in subclasses)
        enhancements['images'] = self.extract_format_specific_images(file_path, text)
        
        # 5. Enhanced quality scoring
        enhancements['quality_score'] = self.calculate_enhanced_quality(
            text, enhancements, metadata
        )
        
        return enhancements
    
    def extract_format_specific_images(self, file_path: Path, text: str) -> List[Dict]:
        """Override this in format-specific extractors."""
        return []  # Base implementation - no images

# 2. FORMAT-SPECIFIC EXTRACTORS (inherit shared logic)

class EnhancedJupyterExtractor(EnhancedBaseExtractor):
    """Enhanced Jupyter notebook extractor."""
    
    def extract_format_specific_images(self, file_path: Path, text: str) -> List[Dict]:
        """Extract images from Jupyter notebook outputs."""
        images = []
        
        try:
            import nbformat
            with open(file_path, 'r') as f:
                nb = nbformat.read(f, as_version=4)
            
            for cell_idx, cell in enumerate(nb.cells):
                if cell.cell_type == 'code' and cell.get('outputs'):
                    for output_idx, output in enumerate(cell.outputs):
                        # Check for image outputs
                        if hasattr(output, 'data'):
                            for mime_type, data in output.data.items():
                                if mime_type.startswith('image/'):
                                    images.append({
                                        'type': 'notebook_output',
                                        'cell_index': cell_idx,
                                        'output_index': output_idx,
                                        'mime_type': mime_type,
                                        'size': len(str(data)),
                                        'is_chart': self._detect_chart_from_code(cell.source),
                                        'context': cell.source[:200]  # Code that generated it
                                    })
        except Exception as e:
            self.logger.warning(f"Error extracting Jupyter images: {e}")
        
        return images
    
    def _detect_chart_from_code(self, code: str) -> bool:
        """Detect if code likely generates charts."""
        chart_libraries = ['matplotlib', 'seaborn', 'plotly', 'bokeh', 'altair']
        return any(lib in code.lower() for lib in chart_libraries)

class EnhancedMarkdownExtractor(EnhancedBaseExtractor):
    """Enhanced Markdown extractor."""
    
    def extract_format_specific_images(self, file_path: Path, text: str) -> List[Dict]:
        """Extract image references from Markdown."""
        images = []
        
        # Find image links: ![alt](src) or <img src="...">
        import re
        
        # Markdown image syntax
        md_images = re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', text)
        for match in md_images:
            alt_text = match.group(1)
            src = match.group(2)
            
            images.append({
                'type': 'markdown_image',
                'alt_text': alt_text,
                'src': src,
                'position': match.start(),
                'is_chart': self._detect_chart_from_filename(src),
                'context': text[max(0, match.start()-50):match.end()+50]
            })
        
        # HTML img tags in markdown
        html_images = re.finditer(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', text)
        for match in html_images:
            src = match.group(1)
            
            images.append({
                'type': 'html_image_in_markdown', 
                'src': src,
                'position': match.start(),
                'is_chart': self._detect_chart_from_filename(src),
                'context': text[max(0, match.start()-50):match.end()+50]
            })
        
        return images
    
    def _detect_chart_from_filename(self, filename: str) -> bool:
        """Detect charts based on filename patterns."""
        chart_keywords = ['chart', 'graph', 'plot', 'figure', 'diagram']
        return any(keyword in filename.lower() for keyword in chart_keywords)

class EnhancedPythonExtractor(EnhancedBaseExtractor):
    """Enhanced Python code extractor."""
    
    def extract_format_specific_images(self, file_path: Path, text: str) -> List[Dict]:
        """Extract chart generation code from Python files."""
        images = []
        
        try:
            import ast
            tree = ast.parse(text)
            
            for node in ast.walk(tree):
                # Look for plotting function calls
                if isinstance(node, ast.Call):
                    if hasattr(node.func, 'attr'):
                        func_name = node.func.attr
                        plotting_funcs = ['plot', 'scatter', 'bar', 'hist', 'pie', 'show', 'savefig']
                        
                        if func_name in plotting_funcs:
                            # Extract the code around this plotting call
                            line_num = getattr(node, 'lineno', 0)
                            
                            images.append({
                                'type': 'plotting_code',
                                'function': func_name,
                                'line_number': line_num,
                                'is_chart': True,
                                'context': self._get_code_context(text, line_num)
                            })
        
        except Exception as e:
            self.logger.warning(f"Error analyzing Python plotting code: {e}")
        
        return images
    
    def _get_code_context(self, code: str, line_num: int, context_lines: int = 5) -> str:
        """Get code context around a line number."""
        lines = code.splitlines()
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        return '\n'.join(lines[start:end])

# 3. EASY INTEGRATION WITH YOUR EXISTING CODE

def enhance_existing_nonpdf_extractor():
    """Show how to enhance your existing batch_nonpdf_extractor.py"""
    
    # In your existing process_file function, add this:
    
    def process_file_enhanced(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Enhanced version of your existing process_file method."""
        
        try:
            # Your existing extraction logic
            text, metadata = self.extract_text(file_path)
            
            # ADD: Apply enhancements
            enhancements = self.process_enhancements(text, file_path, metadata)
            
            # Merge enhancements into metadata
            metadata.update({
                'enhancement_results': enhancements,
                'enhanced_quality_score': enhancements['quality_score'],
                'is_academic': enhancements['academic_analysis']['is_academic_paper'],
                'formula_count': len(enhancements['formulas']),
                'symbol_count': enhancements['symbols']['statistics']['total_symbols'],
                'image_count': len(enhancements['images'])
            })
            
            # Your existing quality checks and output logic
            # ... rest of existing code unchanged
            
        except Exception as e:
            self.logger.error(f"Error in enhanced processing: {e}")
            # Fallback to original processing
            return self.original_process_file(file_path)

# 4. CONFIGURATION FOR NON-PDF ENHANCEMENTS

NONPDF_ENHANCEMENT_CONFIG = {
    "jupyter": {
        "extract_cell_outputs": True,
        "detect_plotting_code": True,
        "extract_markdown_formulas": True
    },
    "markdown": {
        "extract_math_blocks": True,
        "parse_image_links": True,
        "detect_academic_papers": True
    },
    "python": {
        "extract_docstring_formulas": True,
        "detect_plotting_code": True,
        "analyze_imports": True
    },
    "shared": {
        "financial_symbol_extraction": True,
        "academic_detection": True,
        "memory_optimization": True,
        "enhanced_quality_scoring": True
    }
}

# 5. QUICK MIGRATION STRATEGY

"""
Migration steps for your existing batch_nonpdf_extractor.py:

1. MINIMAL CHANGES (1 hour):
   - Add shared processors to __init__
   - Add process_enhancements() call in process_file()
   - Add enhancement results to metadata

2. FORMAT-SPECIFIC ENHANCEMENTS (2-3 hours):
   - Implement extract_format_specific_images() for each format
   - Add format-specific configuration

3. TESTING (1 hour):
   - Test with small sample of each file type
   - Verify enhancement outputs

4. FULL DEPLOYMENT:
   - Run on full corpus with enhancements enabled

Total effort: ~4-5 hours for full implementation
"""