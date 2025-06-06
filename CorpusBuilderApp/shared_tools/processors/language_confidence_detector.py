"""
Language confidence detection module
"""

import re
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from langdetect import detect_langs, LangDetectException
from shared_tools.project_config import ProjectConfig

class LanguageConfidenceDetector:
    """Detect language confidence"""
    
    def __init__(self, config: Optional[Dict] = None, project_config: Optional[Dict] = None):
        """Initialize language confidence detector
        
        Args:
            config (dict): Optional configuration
            project_config (dict): Optional project configuration
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Use project config if provided, otherwise use provided config or defaults
        if project_config:
            if 'processors' in project_config and 'quality_control' in project_config['processors'] and 'checks' in project_config['processors']['quality_control'] and 'language' in project_config['processors']['quality_control']['checks']:
                # New master config structure
                self.config = project_config['processors']['quality_control']['checks']['language']
            elif 'language_confidence' in project_config:
                # Legacy project config structure
                self.config = project_config['language_confidence']
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
            'target_languages': ['en'],
            'excluded_languages': ['und', 'mul'],
            'min_language_ratio': 0.7,
            'max_languages': 2,
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
        required_fields = ['min_confidence', 'min_text_length', 'target_languages']
        for field in required_fields:
            if field not in self.config:
                self.logger.warning(f"Missing required config field: {field}")
                self.config[field] = self._get_default_config()[field]
        
        # Validate numeric fields
        numeric_fields = {
            'min_confidence': (0.0, 1.0),
            'min_text_length': (1, float('inf')),
            'min_language_ratio': (0.0, 1.0),
            'max_languages': (1, float('inf'))
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
        
        # Validate language lists
        list_fields = ['target_languages', 'excluded_languages']
        for field in list_fields:
            if field in self.config:
                if not isinstance(self.config[field], list):
                    self.logger.warning(f"Invalid {field} configuration")
                    self.config[field] = self._get_default_config()[field]
                else:
                    for lang in self.config[field]:
                        if not isinstance(lang, str):
                            self.logger.warning(f"Invalid language code in {field}: {lang}")
                            self.config[field] = self._get_default_config()[field]
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
        """Detect language confidence in text
        
        Args:
            text (str): Text to analyze
            
        Returns:
            dict: Detection results
        """
        if len(text) < self.config['min_text_length']:
            return {
                'confidence': 0.0,
                'reason': 'Text too short'
            }
        
        results = {
            'confidence': 0.0,
            'metrics': {}
        }
        
        # Check grammar
        if self.config['metrics']['grammar_check']:
            grammar_score = self._check_grammar(text)
            results['metrics']['grammar'] = grammar_score
            results['confidence'] = max(results['confidence'], grammar_score)
        
        # Check vocabulary
        if self.config['metrics']['vocabulary_check']:
            vocab_score = self._check_vocabulary(text)
            results['metrics']['vocabulary'] = vocab_score
            results['confidence'] = max(results['confidence'], vocab_score)
        
        # Check fluency
        if self.config['metrics']['fluency_check']:
            fluency_score = self._check_fluency(text)
            results['metrics']['fluency'] = fluency_score
            results['confidence'] = max(results['confidence'], fluency_score)
        
        return results
    
    def _check_grammar(self, text: str) -> float:
        """Check grammar quality"""
        # Implementation details...
        return 0.0
    
    def _check_vocabulary(self, text: str) -> float:
        """Check vocabulary quality"""
        # Implementation details...
        return 0.0
    
    def _check_fluency(self, text: str) -> float:
        """Check text fluency"""
        # Implementation details...
        return 0.0

def run_with_project_config(project: 'ProjectConfig', verbose: bool = False):
    """Run language confidence detection with project configuration
    
    Args:
        project (ProjectConfig): Project configuration
        verbose (bool): Enable verbose output
        
    Returns:
        dict: Detection results
    """
    detector = LanguageConfidenceDetector(
        project_config=project.get_processor_config('language_confidence')
    )
    
    # Process files
    results = detector.process_directory(project.get_input_dir())
    
    if verbose:
        print("\nLanguage Confidence Detection Results:")
        print(f"Processed files: {len(results['processed_files'])}")
        print(f"High confidence: {results['high_confidence_count']}")
        print(f"Low confidence: {results['low_confidence_count']}")
    
    return results

def main():
    """Main entry point when script is run directly"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Detect language confidence in corpus')
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
        detector = LanguageConfidenceDetector()
        results = detector.process_directory(args.corpus_dir)
    
    # Save results
    output_file = Path(args.corpus_dir) / 'language_confidence_detection.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetection results saved to: {output_file}")

if __name__ == "__main__":
    main()

def detect_language_confidence(text, low_conf_threshold=0.85, mixed_lang_ratio=0.15):
    """
    Detects language, confidence, and mixed-language content in text.
    Returns a dict with language, language_confidence, mixed_language_flag, mixed_languages, reasons, severity.
    """
    reasons = []
    severity = 'ok'
    try:
        langs = detect_langs(text)
        if not langs:
            return {'language': 'unknown', 'language_confidence': 0.0, 'mixed_language_flag': False, 'mixed_languages': [], 'reasons': ['No language detected'], 'severity': 'critical'}
        primary = langs[0]
        language = primary.lang
        confidence = primary.prob
        # Simulate confidence if not available
        if confidence is None:
            confidence = 1.0 if language != 'unknown' else 0.0
        # Mixed language detection: segment text and compare
        segments = re.split(r'[.!?\n]', text)
        segment_langs = []
        for seg in segments:
            seg = seg.strip()
            if len(seg.split()) < 5:
                continue
            try:
                seg_lang = detect_langs(seg)[0].lang
                segment_langs.append(seg_lang)
            except Exception:
                continue
        lang_counts = {l: segment_langs.count(l) for l in set(segment_langs)}
        if len(lang_counts) > 1:
            total = sum(lang_counts.values())
            mixed = [(l, c/total) for l, c in lang_counts.items() if c/total > mixed_lang_ratio]
            if mixed:
                reasons.append(f"Mixed languages detected: {mixed}")
                severity = 'warning'
                mixed_language_flag = True
                mixed_languages = [l for l, _ in mixed]
            else:
                mixed_language_flag = False
                mixed_languages = []
        else:
            mixed_language_flag = False
            mixed_languages = []
        # Low confidence
        if confidence < low_conf_threshold:
            reasons.append(f"Low language detection confidence: {confidence:.2f}")
            severity = 'warning'
        return {
            'language': language,
            'language_confidence': confidence,
            'mixed_language_flag': mixed_language_flag,
            'mixed_languages': mixed_languages,
            'reasons': reasons,
            'severity': severity
        }
    except LangDetectException:
        return {'language': 'unknown', 'language_confidence': 0.0, 'mixed_language_flag': False, 'mixed_languages': [], 'reasons': ['Language detection failed'], 'severity': 'critical'} 