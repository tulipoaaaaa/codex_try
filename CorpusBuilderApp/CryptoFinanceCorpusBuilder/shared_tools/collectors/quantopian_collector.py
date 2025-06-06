# sources/specific_collectors/quantopian_collector.py
from CryptoFinanceCorpusBuilder.shared_tools.collectors.base_collector import BaseCollector
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
import time

class QuantopianCollector(BaseCollector):
    """Collector for Quantopian research archives"""
    
    def __init__(self, 
                 config: Union[str, 'ProjectConfig'],
                 delay_range: tuple = (2, 5)):
        """Initialize the Quantopian collector.
        
        Args:
            config: ProjectConfig instance or path to config file
            delay_range: Tuple of (min_delay, max_delay) in seconds between requests
        """
        if isinstance(config, str):
            from shared_tools.project_config import ProjectConfig
            config = ProjectConfig(config, environment='test')
        super().__init__(config)
        self.repo_url = "https://github.com/quantopian/research_public"
        
        # Set up Quantopian-specific directory based on environment
        self.quantopian_dir = self.config.raw_data_dir / 'Quantopian'
        self.quantopian_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Quantopian directory set to: {self.quantopian_dir}")
    
    def _get_output_path(self, filename: str) -> Path:
        """Get the correct output path for Quantopian content.
        
        Args:
            filename: Name of the file
            
        Returns:
            Path object for the output file
        """
        # Save directly in the Quantopian directory
        return self.quantopian_dir / filename
    
    def collect_by_id(self, algorithm_ids: Union[str, List[str]]) -> List[Dict[str, Any]]:
        """Collect specific algorithms by their IDs.
        
        Args:
            algorithm_ids: Single algorithm ID or list of algorithm IDs
            
        Returns:
            List of dictionaries containing algorithm information
        """
        if isinstance(algorithm_ids, str):
            algorithm_ids = [algorithm_ids]
            
        self.logger.info(f"Collecting algorithms by ID: {algorithm_ids}")
        
        # Clone the repository if not already done
        repo_dir = self._clone_repo(self.repo_url)
        if not repo_dir:
            self.logger.error("Failed to clone Quantopian repository")
            return []
            
        results = []
        for algorithm_id in algorithm_ids:
            # Look for notebook with matching ID in filename
            notebook_files = list(repo_dir.glob(f"**/*{algorithm_id}*.ipynb"))
            
            if not notebook_files:
                self.logger.warning(f"No notebook found for algorithm ID: {algorithm_id}")
                continue
                
            for notebook_path in notebook_files:
                # Skip checkpoint files
                if ".ipynb_checkpoints" in str(notebook_path):
                    continue
                    
                # Get relative path for organization
                rel_path = notebook_path.relative_to(repo_dir)
                
                # Process notebook
                notebook_info = self._process_notebook(notebook_path, rel_path)
                
                if notebook_info:
                    # Add algorithm ID to metadata
                    notebook_info['algorithm_id'] = algorithm_id
                    results.append(notebook_info)
                    
        return results
    
    def collect(self) -> List[Dict[str, Any]]:
        """Clone and process the Quantopian research repository.
        
        Returns:
            List of dictionaries containing notebook information
        """
        self.logger.info(f"Collecting Quantopian research from {self.repo_url}")
        
        # Clone the repository
        repo_dir = self._clone_repo(self.repo_url)
        
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
        metadata_path = self._get_output_path("quantopian_notebooks.json")
        
        with open(metadata_path, 'w') as f:
            json.dump(processed_notebooks, f, indent=2)
            
        self.logger.info(f"Saved metadata for {len(processed_notebooks)} notebooks to {metadata_path}")
        
        return processed_notebooks
    
    def _process_notebook(self, 
                         notebook_path: Path,
                         rel_path: Path) -> Optional[Dict[str, Any]]:
        """Extract information from a Jupyter notebook.
        
        Args:
            notebook_path: Path to the notebook file
            rel_path: Relative path for organization
            
        Returns:
            Dictionary containing notebook information, or None if processing failed
        """
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
            
            # Copy notebook to output directory
            target_path = self._get_output_path(str(rel_path))
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
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
            
            # Save metadata
            meta_path = target_path.with_suffix('.meta')
            meta_data = {
                'title': title,
                'path': str(rel_path),
                'kernel': kernelspec.get('display_name', ''),
                'imports': imports,
                'code_cell_count': len(code_cells),
                'markdown_cell_count': len(markdown_cells),
                'total_cell_count': len(notebook.get('cells', [])),
                'language': kernelspec.get('language', ''),
                'download_date': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, indent=2)
            
            return {
                'title': title,
                'path': str(rel_path),
                'saved_path': str(target_path),
                'metadata_path': str(meta_path),
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
    
    def _clone_repo(self, repo_url: str) -> Optional[Path]:
        """Clone a git repository.
        
        Args:
            repo_url: URL of the repository to clone
            
        Returns:
            Path to the cloned repository, or None if cloning failed
        """
        try:
            import git
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            clone_dir = self._get_output_path(repo_name)
            
            if clone_dir.exists():
                self.logger.info(f"Repository already exists at {clone_dir}")
                return clone_dir
                
            self.logger.info(f"Cloning {repo_url} to {clone_dir}")
            git.Repo.clone_from(repo_url, clone_dir)
            return clone_dir
            
        except Exception as e:
            self.logger.error(f"Error cloning repository {repo_url}: {e}")
            return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect data from Quantopian")
    parser.add_argument("--config", required=True, help="Path to config file")
    
    args = parser.parse_args()
    
    collector = QuantopianCollector(args.config)
    results = collector.collect()
    print(f"Collected {len(results)} Quantopian records. Output dir: {collector.output_dir}")