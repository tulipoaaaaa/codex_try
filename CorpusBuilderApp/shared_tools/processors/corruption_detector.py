"""
Corruption detection module
"""

import re
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from shared_tools.project_config import ProjectConfig

def detect_corruption(text: str, config: Optional[Dict] = None) -> Dict[str, Any]:
    """Detect corruption in text using CorruptionDetector
    
    Args:
        text (str): Text to analyze
        config (dict, optional): Configuration for corruption detection
        
    Returns:
        dict: Detection results
    """
    detector = CorruptionDetector(config=config)
    return detector.detect(text)

class CorruptionDetector:
    """Detect corrupted content"""
    
    def __init__(self, config: Optional[Dict] = None, project_config: Optional[Dict] = None):
        """Initialize corruption detector
        
        Args:
            config (dict): Optional configuration
            project_config (dict): Optional project configuration
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Use project config if provided, otherwise use provided config or defaults
        if project_config:
            if 'processors' in project_config and 'quality_control' in project_config['processors'] and 'checks' in project_config['processors']['quality_control'] and 'corruption' in project_config['processors']['quality_control']['checks']:
                # New master config structure
                self.config = project_config['processors']['quality_control']['checks']['corruption']
            elif 'corruption_detection' in project_config:
                # Legacy project config structure
                self.config = project_config['corruption_detection']
            else:
                self.config = config or self._get_default_config()
        else:
            self.config = config or self._get_default_config()
        
        # Validate configuration
        self._validate_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'enabled': True,
            'min_confidence': 0.8,
            'min_text_length': 100,
            'checks': {
                'encoding_errors': True,
                'garbled_text': True,
                'incomplete_sentences': True,
                'missing_content': True
            },
            'encoding_patterns': [
                r'\\x[0-9a-fA-F]{2}',
                r'\\u[0-9a-fA-F]{4}',
                r'\\U[0-9a-fA-F]{8}',
                r'\\N{[^}]+}',
                r'\\[0-7]{1,3}'
            ],
            'garbled_patterns': [
                r'[^\x00-\x7F]{3,}',
                r'[A-Za-z]{20,}',
                r'[0-9]{20,}',
                r'[^A-Za-z0-9\s]{10,}'
            ],
            'sentence_endings': ['.', '!', '?', ';'],
            'min_sentence_length': 10,
            'max_sentence_length': 200,
            'min_paragraph_length': 50,
            'max_paragraph_length': 1000,
            'high_precision': False,
            'verbose': False,
            'processing': {
                'max_workers': 4,
                'batch_size': 100,
                'timeout': 30
            }
        }
    
    def _validate_config(self) -> None:
        """Validate configuration values"""
        required_fields = ['min_confidence', 'min_text_length', 'checks']
        for field in required_fields:
            if field not in self.config:
                self.logger.warning(f"Missing required config field: {field}")
                self.config[field] = self._get_default_config()[field]
        
        # Validate numeric fields
        numeric_fields = {
            'min_confidence': (0.0, 1.0),
            'min_text_length': (1, float('inf')),
            'min_sentence_length': (1, float('inf')),
            'max_sentence_length': (1, float('inf')),
            'min_paragraph_length': (1, float('inf')),
            'max_paragraph_length': (1, float('inf'))
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in self.config:
                try:
                    value = float(self.config[field])
                    if not min_val <= value <= max_val:
                        self.logger.warning(f"Config field {field} value {value} outside valid range [{min_val}, {max_val}]")
                        self.config[field] = self._get_default_config()[field]
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid numeric value for config field: {field}")
                    self.config[field] = self._get_default_config()[field]
        
        # Validate boolean fields
        boolean_fields = ['enabled', 'high_precision', 'verbose']
        for field in boolean_fields:
            if field in self.config and not isinstance(self.config[field], bool):
                self.logger.warning(f"Invalid boolean value for config field: {field}")
                self.config[field] = self._get_default_config()[field]
        
        # Validate checks
        if 'checks' in self.config:
            if not isinstance(self.config['checks'], dict):
                self.logger.warning("Invalid checks configuration")
                self.config['checks'] = self._get_default_config()['checks']
            else:
                for check, value in self.config['checks'].items():
                    if not isinstance(value, bool):
                        self.logger.warning(f"Invalid boolean value for check: {check}")
                        self.config['checks'][check] = self._get_default_config()['checks'][check]
        
        # Validate patterns
        pattern_fields = ['encoding_patterns', 'garbled_patterns']
        for field in pattern_fields:
            if field in self.config:
                if not isinstance(self.config[field], list):
                    self.logger.warning(f"Invalid {field} configuration")
                    self.config[field] = self._get_default_config()[field]
                else:
                    for pattern in self.config[field]:
                        if not isinstance(pattern, str):
                            self.logger.warning(f"Invalid pattern in {field}: {pattern}")
                            self.config[field] = self._get_default_config()[field]
                            break
        
        # Validate sentence endings
        if 'sentence_endings' in self.config:
            if not isinstance(self.config['sentence_endings'], list):
                self.logger.warning("Invalid sentence endings configuration")
                self.config['sentence_endings'] = self._get_default_config()['sentence_endings']
            else:
                for ending in self.config['sentence_endings']:
                    if not isinstance(ending, str):
                        self.logger.warning(f"Invalid sentence ending: {ending}")
                        self.config['sentence_endings'] = self._get_default_config()['sentence_endings']
                        break
        
        # Validate processing settings
        if 'processing' in self.config:
            if not isinstance(self.config['processing'], dict):
                self.logger.warning("Invalid processing configuration")
                self.config['processing'] = self._get_default_config()['processing']
            else:
                processing_fields = {
                    'max_workers': (1, float('inf')),
                    'batch_size': (1, float('inf')),
                    'timeout': (1, float('inf'))
                }
                for field, (min_val, max_val) in processing_fields.items():
                    if field in self.config['processing']:
                        try:
                            value = int(self.config['processing'][field])
                            if not min_val <= value <= max_val:
                                self.logger.warning(f"Processing field {field} value {value} outside valid range [{min_val}, {max_val}]")
                                self.config['processing'][field] = self._get_default_config()['processing'][field]
                        except (ValueError, TypeError):
                            self.logger.warning(f"Invalid numeric value for processing field: {field}")
                            self.config['processing'][field] = self._get_default_config()['processing'][field]

    def detect(self, text: str) -> Dict[str, Any]:
        """Detect corruption in text
        
        Args:
            text (str): Text to analyze
            
        Returns:
            dict: Detection results
        """
        if len(text) < self.config['min_text_length']:
            return {
                'is_corrupted': False,
                'corruption_score': 0.0,
                'reason': 'Text too short'
            }
        
        results = {
            'is_corrupted': False,
            'corruption_score': 0.0,
            'issues_found': []
        }
        
        # Check for encoding errors
        if self.config['checks']['encoding_errors']:
            encoding_score = self._check_encoding_errors(text)
            if encoding_score > 0.3:
                results['issues_found'].append('encoding_errors')
                results['corruption_score'] = max(results['corruption_score'], encoding_score)
        
        # Check for gibberish
        if self.config['checks']['gibberish']:
            gibberish_score = self._check_gibberish(text)
            if gibberish_score > 0.3:
                results['issues_found'].append('gibberish')
                results['corruption_score'] = max(results['corruption_score'], gibberish_score)
        
        # Check for format errors
        if self.config['checks']['format_errors']:
            format_score = self._check_format_errors(text)
            if format_score > 0.3:
                results['issues_found'].append('format_errors')
                results['corruption_score'] = max(results['corruption_score'], format_score)
        
        # Set final result
        results['is_corrupted'] = results['corruption_score'] >= self.config['corruption_threshold']
        
        return results
    
    def _check_encoding_errors(self, text: str) -> float:
        """Check for encoding errors"""
        # Implementation details...
        return 0.0
    
    def _check_gibberish(self, text: str) -> float:
        """Check for gibberish content"""
        # Implementation details...
        return 0.0
    
    def _check_format_errors(self, text: str) -> float:
        """Check for format errors"""
        # Implementation details...
        return 0.0

def run_with_project_config(project: 'ProjectConfig', verbose: bool = False):
    """Run corruption detection with project configuration
    
    Args:
        project (ProjectConfig): Project configuration
        verbose (bool): Enable verbose output
        
    Returns:
        dict: Detection results
    """
    detector = CorruptionDetector(
        project_config=project.get_processor_config('corruption')
    )
    
    # Process files
    results = detector.process_directory(project.get_input_dir())
    
    if verbose:
        print("\nCorruption Detection Results:")
        print(f"Processed files: {len(results['processed_files'])}")
        print(f"Corrupted files: {results['corrupted_count']}")
        print(f"Clean files: {results['clean_count']}")
    
    return results

def main():
    """Main entry point when script is run directly"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Detect corruption in corpus')
    parser.add_argument('--corpus-dir', required=True, help='Corpus directory')
    parser.add_argument('--project-config', help='Path to project config file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    if args.project_config:
        # Use project config
        project = ProjectConfig.load(args.project_config)
        results = run_with_project_config(project, args.verbose)
    else:
        # Use default configuration
        detector = CorruptionDetector()
        results = detector.process_directory(args.corpus_dir)
    
    # Save results
    output_file = Path(args.corpus_dir) / 'corruption_detection.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetection results saved to: {output_file}")

if __name__ == "__main__":
    main() 