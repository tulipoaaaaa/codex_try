"""
Quality control module for corpus content
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from .machine_translation_detector import MachineTranslationDetector
from .language_confidence_detector import LanguageConfidenceDetector
from .corruption_detector import CorruptionDetector
from shared_tools.project_config import ProjectConfig

class QualityControl:
    """Quality control for corpus content"""
    
    def __init__(self, config: Optional[Dict] = None, project_config: Optional[Union[str, ProjectConfig]] = None):
        """Initialize quality control
        
        Args:
            config (dict): Optional configuration
            project_config: ProjectConfig instance or path to config file
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load ProjectConfig if string path provided
        if isinstance(project_config, str):
            project_config = ProjectConfig(project_config)
        
        # Use project config if provided, otherwise use provided config or defaults
        if project_config:
            if hasattr(project_config, 'processors') and 'quality_control' in project_config.processors:
                # New master config structure
                self.config = project_config.processors['quality_control']
            else:
                self.config = config or self._get_default_config()
        else:
            self.config = config or self._get_default_config()
        
        # Initialize detectors with their respective configs
        self.mt_detector = MachineTranslationDetector(
            config=self.config.get('checks', {}).get('translation', {}),
            project_config=project_config
        )
        self.lang_detector = LanguageConfidenceDetector(
            config=self.config.get('checks', {}).get('language', {}),
            project_config=project_config
        )
        self.corruption_detector = CorruptionDetector(
            config=self.config.get('checks', {}).get('corruption', {}),
            project_config=project_config
        )
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'min_token_count': 100,
            'min_quality_score': 0.7,
            'checks': {
                'language': {
                    'enabled': True,
                    'min_confidence': 0.8,
                    'supported_languages': ["en"],
                    'metrics': {
                        'grammar_check': True,
                        'vocabulary_check': True,
                        'fluency_check': True
                    }
                },
                'corruption': {
                    'enabled': True,
                    'min_quality': 0.7,
                    'corruption_threshold': 0.3,
                    'min_text_length': 100,
                    'checks': {
                        'encoding_errors': True,
                        'gibberish': True,
                        'format_errors': True
                    }
                },
                'duplication': {
                    'enabled': True,
                    'similarity_threshold': 0.8
                },
                'translation': {
                    'enabled': True,
                    'min_confidence': 0.9,
                    'min_text_length': 100,
                    'patterns': {
                        'repetitive_phrases': True,
                        'unnatural_word_order': True,
                        'literal_translations': True
                    }
                }
            }
        }
    
    def check_quality(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Check quality of text content
        
        Args:
            text (str): Text content to check
            metadata (dict): Document metadata
            
        Returns:
            dict: Quality check results
        """
        results = {
            'quality_flag': True,
            'quality_score': 0.0,
            'quality_metrics': {}
        }
        
        # Check machine translation
        mt_results = self.mt_detector.detect(text)
        results['quality_metrics']['machine_translation'] = mt_results
        
        # Check language confidence
        lang_results = self.lang_detector.detect(text)
        results['quality_metrics']['language_detection'] = lang_results
        
        # Check corruption
        corruption_results = self.corruption_detector.detect(text)
        results['quality_metrics']['corruption'] = corruption_results
        
        # Calculate overall quality score
        quality_score = self._calculate_quality_score(results['quality_metrics'])
        results['quality_score'] = quality_score
        
        # Set quality flag
        results['quality_flag'] = quality_score >= self.config['min_quality_score']
        
        return results
    
    def _calculate_quality_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall quality score
        
        Args:
            metrics (dict): Quality metrics
            
        Returns:
            float: Quality score (0-1)
        """
        weights = {
            'machine_translation': 0.3,
            'language_detection': 0.3,
            'corruption': 0.4
        }
        
        score = 0.0
        for metric, weight in weights.items():
            if metric in metrics:
                score += metrics[metric].get('score', 0.0) * weight
        
        return score

def run_with_project_config(project: Union[str, ProjectConfig], verbose: bool = False):
    """Run quality control with project configuration
    
    Args:
        project: ProjectConfig instance or path to config file
        verbose (bool): Enable verbose output
        
    Returns:
        dict: Quality control results
    """
    if isinstance(project, str):
        project = ProjectConfig(project)
    
    qc = QualityControl(
        project_config=project
    )
    
    # Process files
    results = qc.process_directory(project.raw_data_dir)
    
    if verbose:
        print("\nQuality Control Results:")
        print(f"Processed files: {len(results['processed_files'])}")
        print(f"Passed quality check: {results['passed_count']}")
        print(f"Failed quality check: {results['failed_count']}")
    
    return results

def main():
    """Main entry point when script is run directly"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run quality control on corpus')
    parser.add_argument('--config', required=True, help='Path to project config file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    results = run_with_project_config(args.config, args.verbose)
    
    # Save results
    output_file = Path(args.config) / 'quality_control_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nQuality control results saved to: {output_file}")

if __name__ == "__main__":
    main() 