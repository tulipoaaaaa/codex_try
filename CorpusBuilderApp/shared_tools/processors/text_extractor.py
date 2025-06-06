# processors/text_extractor.py
import os
import logging
from pathlib import Path
import tempfile
import re
import json
import multiprocessing

class TextExtractor:
    """Extract text from various file formats"""
    
    def __init__(self, output_dir=None, num_workers=None):
        self.output_dir = Path(output_dir) if output_dir else None
        self.num_workers = num_workers or max(1, multiprocessing.cpu_count() - 1)
        
        # Configure logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def extract(self, file_path):
        """Extract text from a file based on its extension"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.error(f"File does not exist: {file_path}")
            return None
            
        try:
            # Determine extraction method based on file extension
            ext = file_path.suffix.lower()
            
            if ext == '.pdf':
                return self._extract_from_pdf(file_path)
            elif ext == '.epub':
                return self._extract_from_epub(file_path)
            elif ext in ['.md', '.markdown']:
                return self._extract_from_markdown(file_path)
            elif ext in ['.ipynb']:
                return self._extract_from_notebook(file_path)
            elif ext in ['.csv', '.tsv']:
                return self._extract_from_csv(file_path)
            elif ext in ['.html', '.htm']:
                return self._extract_from_html(file_path)
            elif ext in ['.txt', '.log', '.py', '.js', '.java', '.c', '.cpp', '.h', '.cs', '.R']:
                return self._extract_from_text(file_path)
            else:
                self.logger.warning(f"Unsupported file format: {ext}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting text from {file_path}: {e}")
            return None
    
    def extract_batch(self, file_paths):
        """Extract text from multiple files in parallel"""
        from concurrent.futures import ProcessPoolExecutor
        
        results = {}
        
        self.logger.info(f"Extracting text from {len(file_paths)} files using {self.num_workers} workers")
        
        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            # Map file paths to extraction tasks
            futures = {executor.submit(self.extract, path): path for path in file_paths}
            
            # Process results as they complete
            from concurrent.futures import as_completed
            for future in as_completed(futures):
                path = futures[future]
                try:
                    result = future.result()
                    if result:
                        results[str(path)] = result
                except Exception as e:
                    self.logger.error(f"Error processing {path}: {e}")
        
        self.logger.info(f"Successfully extracted text from {len(results)} files")
        return results
    
    def _extract_from_pdf(self, file_path):
        """Extract text from PDF file"""
        try:
            import pypdf
            
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                num_pages = len(reader.pages)
                
                # Extract basic metadata
                metadata = {
                    'num_pages': num_pages,
                    'title': reader.metadata.get('/Title', ''),
                    'author': reader.metadata.get('/Author', ''),
                    'subject': reader.metadata.get('/Subject', ''),
                    'creator': reader.metadata.get('/Creator', '')
                }
                
                # Extract text from all pages
                text = ""
                for page_num in range(num_pages):
                    text += reader.pages[page_num].extract_text() + "\n\n"
                
                return {
                    'text': text,
                    'metadata': metadata,
                    'source_file': str(file_path),
                    'file_type': 'pdf'
                }
                
        except ImportError:
            self.logger.error("pypdf not installed. Install it with: pip install pypdf")
            return None
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF {file_path}: {e}")
            return None
    
    def _extract_from_epub(self, file_path):
        """Extract text from EPUB file"""
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
            
            book = epub.read_epub(file_path)
            
            # Extract metadata
            metadata = {
                'title': book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else '',
                'creator': book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else '',
                'language': book.get_metadata('DC', 'language')[0][0] if book.get_metadata('DC', 'language') else '',
                'publisher': book.get_metadata('DC', 'publisher')[0][0] if book.get_metadata('DC', 'publisher') else ''
            }
            
            # Extract content from all HTML files
            chapters = {}
            all_text = ""
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = item.get_content().decode('utf-8')
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Extract text
                    chapter_text = soup.get_text('\n', strip=True)
                    
                    # Store chapter
                    chapters[item.get_name()] = chapter_text
                    all_text += chapter_text + "\n\n"
            
            return {
                'text': all_text,
                'metadata': metadata,
                'chapters': chapters,
                'source_file': str(file_path),
                'file_type': 'epub'
            }
            
        except ImportError:
            self.logger.error("Required packages not installed. Install them with: pip install ebooklib beautifulsoup4")
            return None
        except Exception as e:
            self.logger.error(f"Error extracting text from EPUB {file_path}: {e}")
            return None
    
    def _extract_from_markdown(self, file_path):
        """Extract text from Markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Simple metadata extraction (front matter)
            metadata = {}
            front_matter_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            
            if front_matter_match:
                front_matter = front_matter_match.group(1)
                content = content[front_matter_match.end():]
                
                # Parse front matter
                for line in front_matter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
            
            # Remove markdown formatting (simple approach)
            # Remove headings
            text = re.sub(r'#+\s+(.*)', r'\1', content)
            # Remove links
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
            # Remove images
            text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)
            # Remove code blocks
            text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
            # Remove inline code
            text = re.sub(r'`([^`]+)`', r'\1', text)
            
            return {
                'text': text,
                'metadata': metadata,
                'source_file': str(file_path),
                'file_type': 'markdown'
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting text from Markdown {file_path}: {e}")
            return None
    
    def _extract_from_notebook(self, file_path):
        """Extract text from Jupyter Notebook"""
        try:
            import json
            
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                notebook = json.load(f)
            
            # Extract metadata
            metadata = notebook.get('metadata', {})
            
            # Extract cells content
            text = ""
            code_cells = []
            markdown_cells = []
            
            for cell in notebook.get('cells', []):
                cell_type = cell.get('cell_type')
                
                if cell_type == 'markdown':
                    source = ''.join(cell.get('source', []))
                    markdown_cells.append(source)
                    text += source + "\n\n"
                elif cell_type == 'code':
                    source = ''.join(cell.get('source', []))
                    code_cells.append(source)
                    text += f"```\n{source}\n```\n\n"
            
            return {
                'text': text,
                'metadata': metadata,
                'markdown_cells': markdown_cells,
                'code_cells': code_cells,
                'source_file': str(file_path),
                'file_type': 'notebook'
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting text from Notebook {file_path}: {e}")
            return None
    
    def _extract_from_csv(self, file_path):
        """Extract text from CSV/TSV file"""
        try:
            import csv
            
            delimiter = ',' if file_path.suffix.lower() == '.csv' else '\t'
            
            rows = []
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.reader(f, delimiter=delimiter)
                for row in reader:
                    rows.append(row)
            
            # Separate header
            header = rows[0] if rows else []
            data = rows[1:] if len(rows) > 1 else []
            
            # Convert to text representation
            text = delimiter.join(header) + "\n"
            for row in data:
                text += delimiter.join(row) + "\n"
            
            return {
                'text': text,
                'header': header,
                'data': data,
                'source_file': str(file_path),
                'file_type': 'csv'
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting text from CSV {file_path}: {e}")
            return None
    
    def _extract_from_html(self, file_path):
        """Extract text from HTML file"""
        try:
            from bs4 import BeautifulSoup
            
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract metadata
            metadata = {
                'title': soup.title.string if soup.title else '',
            }
            
            # Extract meta tags
            for meta in soup.find_all('meta'):
                if meta.get('name') and meta.get('content'):
                    metadata[meta.get('name')] = meta.get('content')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return {
                'text': text,
                'metadata': metadata,
                'source_file': str(file_path),
                'file_type': 'html'
            }
            
        except ImportError:
            self.logger.error("BeautifulSoup not installed. Install it with: pip install beautifulsoup4")
            return None
        except Exception as e:
            self.logger.error(f"Error extracting text from HTML {file_path}: {e}")
            return None
    
    def _extract_from_text(self, file_path):
        """Extract text from plain text file or code file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            return {
                'text': content,
                'metadata': {},
                'source_file': str(file_path),
                'file_type': 'text'
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting text from text file {file_path}: {e}")
            return None