# sources/specific_collectors/quantopian_collector.py
from CryptoFinanceCorpusBuilder.shared_tools.collectors.repo_collector import RepoCollector
import os
import re
import json
from pathlib import Path

class QuantopianCollector(RepoCollector):
    """Collector for Quantopian research archives"""
    
    def __init__(self, output_dir, delay_range=(2, 5)):
        super().__init__(output_dir, delay_range=delay_range)
        self.repo_url = "https://github.com/quantopian/research_public"
    
    def collect(self):
        """Clone and process the Quantopian research repository"""
        self.logger.info(f"Collecting Quantopian research from {self.repo_url}")
        
        # Clone the repository
        repo_dir = self.clone_repo(self.repo_url)
        
        if not repo_dir:
            self.logger.error("Failed to clone Quantopian repository")
            return []
            
        # Find all notebook files
        notebook_files = list(repo_dir.glob("**/*.ipynb"))
        self.logger.info(f"Found {len(notebook_files)} notebook files")
        
        # Process each notebook
        processed_notebooks = []
        
        for notebook_path in notebook_files:
            # Skip checkpoint files
            if ".ipynb_checkpoints" in str(notebook_path):
                continue
                
            # Get relative path for organization
            rel_path = notebook_path.relative_to(repo_dir)
            
            # Extract notebook metadata and content
            notebook_info = self._process_notebook(notebook_path, rel_path)
            
            if notebook_info:
                processed_notebooks.append(notebook_info)
                
        # Save metadata about all notebooks
        metadata_path = self.output_dir / "quantopian_notebooks.json"
        
        with open(metadata_path, 'w') as f:
            json.dump(processed_notebooks, f, indent=2)
            
        self.logger.info(f"Saved metadata for {len(processed_notebooks)} notebooks to {metadata_path}")
        
        return processed_notebooks
    
    def _process_notebook(self, notebook_path, rel_path):
        """Extract information from a Jupyter notebook"""
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
                
            # Extract basic metadata
            metadata = notebook.get('metadata', {})
            kernelspec = metadata.get('kernelspec', {})
            
            # Get title from first heading cell or filename
            title = os.path.basename(notebook_path).replace('.ipynb', '')
            
            # Look for title in markdown cells
            for cell in notebook.get('cells', []):
                if cell.get('cell_type') == 'markdown':
                    source = ''.join(cell.get('source', []))
                    # Look for heading
                    heading_match = re.search(r'^#\s+(.+)$', source, re.MULTILINE)
                    if heading_match:
                        title = heading_match.group(1).strip()
                        break
            
            # Create target directory
            parent_dir = os.path.dirname(str(rel_path))
            target_dir = self.output_dir / parent_dir
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy notebook to output directory
            target_path = self.output_dir / rel_path
            
            if not target_path.exists():  # Skip if already exists
                with open(notebook_path, 'rb') as src, open(target_path, 'wb') as dst:
                    dst.write(src.read())
                    
            # Extract information about the notebook
            code_cells = []
            markdown_cells = []
            
            for cell in notebook.get('cells', []):
                cell_type = cell.get('cell_type')
                source = ''.join(cell.get('source', []))
                
                if cell_type == 'code':
                    code_cells.append({
                        'source': source,
                        'outputs': len(cell.get('outputs', []))
                    })
                elif cell_type == 'markdown':
                    markdown_cells.append({
                        'source': source
                    })
            
            # Extract import statements to determine libraries used
            imports = []
            for cell in code_cells:
                source = cell['source']
                # Match import statements
                for match in re.finditer(r'^(?:from\s+(\S+)\s+import|import\s+([^as]+)(?:\s+as\s+\S+)?)', source, re.MULTILINE):
                    module = match.group(1) or match.group(2)
                    module = module.strip().split('.')[0]  # Get base module
                    if module and module not in imports:
                        imports.append(module)
            
            return {
                'title': title,
                'path': str(rel_path),
                'saved_path': str(target_path),
                'kernel': kernelspec.get('display_name', ''),
                'imports': imports,
                'code_cell_count': len(code_cells),
                'markdown_cell_count': len(markdown_cells),
                'total_cell_count': len(notebook.get('cells', [])),
                'language': kernelspec.get('language', '')
            }
            
        except Exception as e:
            self.logger.error(f"Error processing notebook {notebook_path}: {e}")
            return None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Collect data from Quantopian")
    parser.add_argument("--output-dir", required=True, help="Output directory for collected data")
    # Add more arguments as needed for your collector
    args = parser.parse_args()
    from pathlib import Path
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    # Assuming the main collector class is QuantopianCollector
    collector = QuantopianCollector(output_dir)
    results = collector.collect()
    print(f"Collected {len(results)} Quantopian records. Output dir: {output_dir}")