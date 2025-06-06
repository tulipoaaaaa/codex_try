import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import json
import hashlib
from datetime import datetime
import os

try:
    from CryptoFinanceCorpusBuilder.shared_tools.project_config import ProjectConfig
except ImportError:
    ProjectConfig = None

def safe_filename(filename: str) -> str:
    """Convert a string to a safe filename.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename with special characters replaced
    """
    # Remove invalid characters
    safe = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))
    # Replace spaces with underscores
    safe = safe.replace(' ', '_')
    # Remove multiple underscores
    safe = re.sub(r'_+', '_', safe)
    return safe

def count_tokens(text: str) -> int:
    """Count the number of tokens in text.
    
    Args:
        text: Text to count tokens in
        
    Returns:
        Number of tokens
    """
    # Simple whitespace-based tokenization
    return len(text.split())

def extract_metadata(file_path: Union[str, Path], project_config: Optional[ProjectConfig] = None) -> Dict:
    """Extract metadata from a file.
    
    Args:
        file_path: Path to the file
        project_config: Optional ProjectConfig instance
        
    Returns:
        Dictionary containing metadata
    """
    file_path = Path(file_path)
    metadata = {
        'filename': file_path.name,
        'file_size': file_path.stat().st_size,
        'file_type': file_path.suffix.lower(),
        'content_hash': calculate_hash(file_path),
        'extraction_date': None  # Will be set by caller
    }
    
    if project_config:
        metadata['project_name'] = project_config.project_name
        metadata['project_version'] = project_config.version
    
    return metadata

def calculate_hash(file_path: Union[str, Path]) -> str:
    """Calculate MD5 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MD5 hash as hex string
    """
    file_path = Path(file_path)
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def load_json_config(config_path: Union[str, Path, ProjectConfig]) -> Dict:
    """Load and validate a JSON configuration file.
    
    Args:
        config_path: Path to the JSON config file or ProjectConfig instance
        
    Returns:
        Dictionary containing configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    if isinstance(config_path, ProjectConfig):
        return config_path.config
    
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_metadata(metadata: Dict, output_path: Union[str, Path, ProjectConfig]) -> None:
    """Save metadata to a JSON file.
    
    Args:
        metadata: Dictionary containing metadata
        output_path: Path to save metadata to or ProjectConfig instance
    """
    if isinstance(output_path, ProjectConfig):
        output_path = Path(output_path.processed_dir) / '_extracted' / 'metadata.json'
    else:
        output_path = Path(output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

def chunk_text(text: str, 
               chunk_size: int = 10000,
               overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks.
    
    Args:
        text: Text to split
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        # Try to find a sentence boundary
        if end < text_len:
            # Look for sentence ending
            for punct in ['. ', '! ', '? ', '\n\n']:
                pos = text.rfind(punct, start, end)
                if pos != -1:
                    end = pos + len(punct)
                    break
        
        chunks.append(text[start:end])
        start = end - overlap
    
    return chunks

def detect_file_type(file_path: Path) -> str:
    """Detect the type of a file based on its extension and content.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File type as string (e.g., 'pdf', 'markdown', 'python', etc.)
    """
    ext = file_path.suffix.lower()
    
    # Common file types
    type_map = {
        '.pdf': 'pdf',
        '.md': 'markdown',
        '.txt': 'text',
        '.py': 'python',
        '.ipynb': 'jupyter',
        '.html': 'html',
        '.htm': 'html',
        '.json': 'json',
        '.csv': 'csv'
    }
    
    return type_map.get(ext, 'unknown')

def normalize_text(text: str) -> str:
    """Normalize text for comparison and processing.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    # Convert to lowercase
    text = text.lower()
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using Jaccard similarity.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    # Normalize texts
    text1 = normalize_text(text1)
    text2 = normalize_text(text2)
    
    # Get word sets
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0 