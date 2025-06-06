import os
import json
from collections import Counter, defaultdict
import random
from pathlib import Path
from typing import Optional, Union, Dict, List, Any

try:
    from CryptoFinanceCorpusBuilder.shared_tools.project_config import ProjectConfig
except ImportError:
    ProjectConfig = None

def find_json_files(base_dir: Union[str, Path, ProjectConfig]) -> List[Path]:
    """Find JSON files in the base directory.
    
    Args:
        base_dir: Base directory or ProjectConfig instance
        
    Returns:
        List of JSON file paths
    """
    if isinstance(base_dir, ProjectConfig):
        base_dir = Path(base_dir.processed_dir)
    else:
        base_dir = Path(base_dir)
        
    json_files = []
    for subdir in ['_extracted', 'low_quality']:
        dir_path = base_dir / subdir
        if dir_path.exists():
            json_files.extend(dir_path.glob('*.json'))
    return json_files

def analyze_metadata(json_files: List[Path]) -> Dict[str, Any]:
    """Analyze metadata from JSON files.
    
    Args:
        json_files: List of JSON file paths
        
    Returns:
        Dictionary containing analysis results
    """
    domain_stats = defaultdict(int)
    file_type_stats = defaultdict(int)
    quality_stats = defaultdict(int)
    total_tokens = 0
    total_files = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            domain = metadata.get('domain', 'unknown')
            file_type = metadata.get('file_type', 'unknown')
            quality = metadata.get('quality_flag', 'unknown')
            tokens = metadata.get('token_count', 0)
            
            domain_stats[domain] += 1
            file_type_stats[file_type] += 1
            quality_stats[quality] += 1
            total_tokens += tokens
            total_files += 1
            
        except Exception as e:
            print(f"Error processing {json_file}: {str(e)}")
            
    return {
        'domain_distribution': dict(domain_stats),
        'file_type_distribution': dict(file_type_stats),
        'quality_distribution': dict(quality_stats),
        'total_tokens': total_tokens,
        'total_files': total_files
    }

def generate_report(analysis: Dict[str, Any]) -> str:
    """Generate a formatted report from analysis results.
    
    Args:
        analysis: Analysis results dictionary
        
    Returns:
        Formatted report string
    """
    report = []
    report.append("=== Corpus Analysis Report ===")
    report.append(f"\nTotal Files: {analysis['total_files']}")
    report.append(f"Total Tokens: {analysis['total_tokens']:,}")
    
    report.append("\nDomain Distribution:")
    for domain, count in sorted(analysis['domain_distribution'].items()):
        report.append(f"  {domain}: {count:,} files")
        
    report.append("\nFile Type Distribution:")
    for file_type, count in sorted(analysis['file_type_distribution'].items()):
        report.append(f"  {file_type}: {count:,} files")
        
    report.append("\nQuality Distribution:")
    for quality, count in sorted(analysis['quality_distribution'].items()):
        report.append(f"  {quality}: {count:,} files")
        
    return "\n".join(report)

def main(base_dir: Union[str, Path, ProjectConfig]) -> str:
    """Main function to generate corpus report.
    
    Args:
        base_dir: Base directory or ProjectConfig instance
        
    Returns:
        Formatted report string
    """
    json_files = find_json_files(base_dir)
    analysis = analyze_metadata(json_files)
    return generate_report(analysis)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Generate corpus analysis report')
    parser.add_argument('--config', required=True, help='Path to project config file')
    args = parser.parse_args()
    
    if args.config:
        project = ProjectConfig(args.config)
        report = main(project)
        print(report)
    else:
        print("Error: --config argument is required") 