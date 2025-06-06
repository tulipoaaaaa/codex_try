from abc import ABC, abstractmethod
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

from ..models.quality_config import QualityConfig
from ..utils.extractor_utils import (
    safe_filename,
    count_tokens,
    extract_metadata,
    calculate_hash,
    load_json_config,
    save_metadata,
    chunk_text,
    detect_file_type,
    normalize_text,
    calculate_similarity
)
from .quality_control import QualityControl
from .domain_classifier import DomainClassifier
from .language_confidence_detector import detect_language_confidence
from .corruption_detector import CorruptionDetector

class ExtractionError(Exception):
    """Custom exception for extraction errors."""
    pass

class BaseExtractor(ABC):
    """Base class for all text extractors in the corpus pipeline."""
    
    def __init__(self, 
                 config: Union[str, 'ProjectConfig'],
                 num_workers: int = 4,
                 quality_config: Optional[Union[str, Path]] = None,
                 domain_config: Optional[Union[str, Path]] = None):
        """Initialize the base extractor.
        
        Args:
            config: ProjectConfig instance or path to config file
            num_workers: Number of worker processes for parallel processing
            quality_config: Path to quality control configuration file
            domain_config: Path to domain classification configuration file
        """
        if isinstance(config, str):
            from shared_tools.project_config import ProjectConfig
            config = ProjectConfig(config, environment='test')
        
        self.config = config
        self.input_dir = Path(config.raw_data_dir)
        self.output_dir = Path(config.processed_dir)
        self.num_workers = num_workers
        
        # Load and validate configurations
        if quality_config:
            config_data = load_json_config(quality_config)
            self.quality_config = QualityConfig.parse_obj(config_data)
        else:
            self.quality_config = QualityConfig()
        
        # Initialize services
        self.quality_service = QualityControl(quality_config=self.quality_config)
        self.domain_classifier = DomainClassifier(domain_config=domain_config)
        
        # Create output directories
        self.extracted_dir = self.output_dir / "_extracted"
        self.low_quality_dir = self.output_dir / "low_quality"
        self.extracted_dir.mkdir(parents=True, exist_ok=True)
        self.low_quality_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        # Add file handler if not already present
        if not self.logger.handlers:
            log_dir = Path(config.log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "extraction.log"
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
    
    @abstractmethod
    def extract_text(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract text and metadata from a file.
        
        Args:
            file_path: Path to the file to extract from
            
        Returns:
            Tuple of (extracted_text, metadata_dict)
            
        Raises:
            ExtractionError: If extraction fails
        """
        pass
    
    def process_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Process a single file through the extraction pipeline.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Dictionary containing processing results and metadata, or None if processing failed
        """
        try:
            # Extract text and basic metadata
            text, metadata = self.extract_text(file_path)
            
            # Add file metadata
            file_metadata = extract_metadata(file_path)
            metadata.update(file_metadata)
            metadata.update({
                'source_file': str(file_path),
                'extraction_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'extractor': self.__class__.__name__,
                'file_type': detect_file_type(file_path),
                'text_hash': calculate_hash(text)
            })
            
            # Run quality checks
            quality_checks = self.quality_service.check_quality(text, metadata)
            metadata.update(quality_checks)
            
            # Detect language
            lang_info = detect_language_confidence(text)
            metadata.update(lang_info)
            
            # Detect corruption
            detector = CorruptionDetector()
            corruption_info = detector.detect(text)
            metadata.update(corruption_info)
            
            # Classify domain
            domain_info = self.domain_classifier.classify(text, metadata)
            metadata.update(domain_info)
            
            # Determine output location based on quality
            if quality_checks.get('quality_flag') == 'low_quality':
                output_dir = self.low_quality_dir
            else:
                output_dir = self.extracted_dir
            
            # Save extracted text
            text_file = output_dir / f"{safe_filename(file_path.stem, 128)}.txt"
            text_file.write_text(text, encoding='utf-8')
            
            # Save metadata
            metadata_file = output_dir / f"{safe_filename(file_path.stem, 128)}.json"
            save_metadata(metadata, metadata_file)
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {str(e)}")
            return None
    
    def process_batch(self, file_paths: List[Path]) -> Dict[str, List[Dict[str, Any]]]:
        """Process a batch of files in parallel.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Dictionary containing successful and failed processing results
        """
        results: Dict[str, List[Dict[str, Any]]] = {
            'successful': [],
            'failed': []
        }
        
        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            future_to_file = {
                executor.submit(self.process_file, file_path): file_path 
                for file_path in file_paths
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    if result:
                        results['successful'].append(result)
                    else:
                        results['failed'].append({
                            'file': str(file_path),
                            'error': 'Processing failed'
                        })
                except Exception as e:
                    results['failed'].append({
                        'file': str(file_path),
                        'error': str(e)
                    })
        
        return results
    
    def run(self) -> Dict[str, List[Dict[str, Any]]]:
        """Run the extractor on all files in the input directory.
        
        Returns:
            Dictionary containing successful and failed processing results
        """
        file_paths = []
        for ext in ['.pdf', '.doc', '.docx', '.txt']:
            file_paths.extend(list(self.input_dir.glob(f'**/*{ext}')))
        
        self.logger.info(f"Found {len(file_paths)} files to process")
        return self.process_batch(file_paths) 