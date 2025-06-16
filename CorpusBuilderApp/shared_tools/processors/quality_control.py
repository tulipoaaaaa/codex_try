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
logger = logging.getLogger(__name__)

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
        
        # Keep reference for later helpers (GUI wrappers rely on this)
        self.project_config = project_config
        
        # Use project config if provided, otherwise use provided config or defaults
        if project_config:
            if hasattr(project_config, 'get') and project_config.get('processors.quality_control'):
                # New master config structure
                self.config = project_config.get('processors.quality_control')
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

    # ------------------------------------------------------------------
    # Pragmatic directory-level quality pass that relies **solely** on the
    # metrics already written by the extractors. This avoids expensive re-runs
    # of NLP heuristics while still filtering obviously bad documents.
    # ------------------------------------------------------------------

    def _passes_quality(self, meta: Dict[str, Any]) -> tuple[bool, float, str]:
        """Return (flag, score, reason) based on extractor-supplied metadata."""

        metrics: Dict[str, Any] = meta.get("quality_metrics", {})
        score = meta.get("quality_score")

        # If extractor saved an overall score we trust it.
        if isinstance(score, (int, float)):
            return (score >= self.config.get("min_quality_score", 0.4), score, "score")

        # Otherwise compute a rough score from sub-metrics (may be empty)
        if not metrics and score is None:
            # No metrics at all -> accept (assume extractor didn't compute)
            return (True, 1.0, "no_metrics")

        score = self._calculate_quality_score(metrics)

        # Fallback length heuristic – too short ⇒ reject
        token_count = meta.get("token_count") or meta.get("num_tokens")
        if token_count is None and "num_tokens" in metrics:
            token_count = metrics.get("num_tokens")

        if token_count is not None and token_count < self.config.get("min_token_count", 50):
            return (False, score, "too_short")

        return (score >= self.config.get("min_quality_score", 0.4), score, "computed")

    # -------------------------------
    # Public API used by wrappers / CLI
    # -------------------------------

    def process_directory(self, processed_dir: Path | str) -> Dict[str, Any]:
        """Walk *processed_dir* and move files into QC buckets.

        This relies on the metadata JSON files written by extractors. It **does
        not** re-run NLP detectors – fast and deterministic.
        """

        processed_path = Path(processed_dir).expanduser().resolve()
        if not processed_path.exists():
            raise FileNotFoundError(processed_path)

        # Exclude helper folders that are outputs themselves
        EXCLUDED_FOLDERS = {"_extracted", "quality_checked", "low_quality"}

        passed_count = failed_count = 0
        moved_files: list[str] = []

        for json_file in processed_path.rglob("*.json"):
            # Skip excluded roots early for speed
            if any(part in EXCLUDED_FOLDERS for part in json_file.parts):
                continue

            meta: Dict[str, Any] = {}
            try:
                meta = json.loads(json_file.read_text(encoding="utf-8", errors="ignore"))
            except Exception as exc:  # pragma: no cover
                self.logger.warning("QC – could not read metadata %s: %s", json_file, exc)
                failed = True
                score = 0.0
                reason = "bad_metadata"
            else:
                passed, score, reason = self._passes_quality(meta)
                failed = not passed

            # Derive domain & paths
            domain = (meta.get("domain") if isinstance(meta, dict) else None) or "unknown"
            domain = domain.lower()

            txt_file = json_file.with_suffix(".txt")

            target_root = processed_path / ("quality_checked" if not failed else "low_quality") / domain
            target_root.mkdir(parents=True, exist_ok=True)

            for src in (json_file, txt_file):
                try:
                    if src.exists():
                        dst = target_root / src.name
                        dst.write_bytes(src.read_bytes())
                        moved_files.append(str(dst))
                except Exception as exc:  # pragma: no cover – disk issues
                    self.logger.warning("QC – failed to copy %s: %s", src, exc)

            if failed:
                failed_count += 1
            else:
                passed_count += 1

        # Summary
        results = {
            "processed_files": len(moved_files) // 2,  # count pairs
            "passed_count": passed_count,
            "failed_count": failed_count,
        }

        # Persist simple log
        try:
            logs_dir = processed_path.parent / "../logs"
            logs_dir = logs_dir.resolve()
            logs_dir.mkdir(parents=True, exist_ok=True)
            with (logs_dir / "quality_control.log").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(results) + "\n")
        except Exception:
            pass

        return results

    # ------------------------------------------------------------------
    # Convenience entry point so UI wrappers (QualityControlWrapper.start)
    # can simply call processor.start() without needing to know about paths.
    # ------------------------------------------------------------------

    def start(self):
        """Run QC pass on the corpus defined by project configuration."""
        processed_dir = None
        try:
            if hasattr(self, 'project_config') and self.project_config:
                processed_dir = self.project_config.get_processed_dir()
        except Exception:
            pass

        if processed_dir is None:
            # Fallback – assume current working dir contains processed/
            processed_dir = Path.cwd() / 'corpus_1' / 'processed'

        return self.process_directory(processed_dir)

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
        logger.info("\nQuality Control Results:")
        logger.info(f"Processed files: {len(results['processed_files'])}")
        logger.info(f"Passed quality check: {results['passed_count']}")
        logger.warning(f"Failed quality check: {results['failed_count']}")
    
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
    
    logger.info(f"\nQuality control results saved to: {output_file}")

if __name__ == "__main__":
    main() 
