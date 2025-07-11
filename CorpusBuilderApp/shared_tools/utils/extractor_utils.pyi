import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

try:
    from shared_tools.project_config import ProjectConfig  # type: ignore
<<<<<<< HEAD
=======
    
>>>>>>> my-feature-branch
except ImportError:
    ProjectConfig = None

def safe_filename(filename: str) -> str: ...
def count_tokens(text: str) -> int: ...
def extract_metadata(file_path: Union[str, Path], project_config: Optional[ProjectConfig] = ...) -> Dict: ...
def calculate_hash(file_path: Union[str, Path]) -> str: ...
def load_json_config(config_path: Union[str, Path, ProjectConfig]) -> Dict: ...
def save_metadata(metadata: Dict, output_path: Union[str, Path, ProjectConfig]) -> None: ...
def chunk_text(text: str, chunk_size: int = ..., overlap: int = ...) -> List[str]: ...
def detect_file_type(file_path: Path) -> str: ...
def normalize_text(text: str) -> str: ...
def calculate_similarity(text1: str, text2: str) -> float: ... 