# combine_corpora.py
"""
Script to combine multiple corpus directories into a unified structure,
while maintaining domain organization and performing deduplication.
"""

import os
import sys
import json
import shutil
import hashlib
import argparse
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('combine_corpora.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('combine_corpora')

def compute_file_hash(file_path):
    """Compute MD5 hash of a file for deduplication"""
    try:
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return None

def combine_corpora(source_dirs, target_dir):
    """
    Combine multiple corpus directories into a unified structure
    
    Args:
        source_dirs (list): List of source corpus directories
        target_dir (str): Target directory for the combined corpus
        
    Returns:
        dict: Statistics about the combination process
    """
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)
    
    # Track statistics
    stats = {
        "total_files_processed": 0,
        "files_copied": 0,
        "duplicates_skipped": 0,
        "errors": 0,
        "by_domain": {}
    }
    
    # Track file hashes for deduplication
    file_hashes = {}
    
    # Process each source directory
    for source_dir in source_dirs:
        source_path = Path(source_dir)
        if not source_path.exists():
            logger.warning(f"Source directory does not exist: {source_dir}")
            continue
            
        logger.info(f"Processing source directory: {source_dir}")
        
        # Identify domain directories
        domain_dirs = [d for d in source_path.iterdir() if d.is_dir() and not d.name.endswith('_extracted')]
        
        for domain_dir in domain_dirs:
            domain_name = domain_dir.name
            
            # Create target domain directory if it doesn't exist
            target_domain_dir = target_path / domain_name
            target_domain_dir.mkdir(exist_ok=True)
            
            # Create target extracted directory if it doesn't exist
            target_extracted_dir = target_path / f"{domain_name}_extracted"
            target_extracted_dir.mkdir(exist_ok=True)
            
            # Initialize domain stats if not already present
            if domain_name not in stats["by_domain"]:
                stats["by_domain"][domain_name] = {
                    "files_processed": 0,
                    "files_copied": 0,
                    "duplicates_skipped": 0,
                    "errors": 0
                }
            
            # Find all files in the domain directory
            domain_files = list(domain_dir.glob('*.pdf'))
            
            logger.info(f"Found {len(domain_files)} files in domain: {domain_name}")
            
            # Process each file
            for file_path in domain_files:
                stats["total_files_processed"] += 1
                stats["by_domain"][domain_name]["files_processed"] += 1
                
                try:
                    # Compute file hash for deduplication
                    file_hash = compute_file_hash(file_path)
                    
                    if file_hash in file_hashes:
                        # Skip duplicate
                        logger.info(f"Skipping duplicate: {file_path}")
                        stats["duplicates_skipped"] += 1
                        stats["by_domain"][domain_name]["duplicates_skipped"] += 1
                        continue
                    
                    # Add to hash tracking
                    file_hashes[file_hash] = str(file_path)
                    
                    # Copy file to target directory
                    target_file_path = target_domain_dir / file_path.name
                    shutil.copy2(file_path, target_file_path)
                    
                    # Copy metadata if it exists
                    meta_path = file_path.with_suffix(f"{file_path.suffix}.meta")
                    if meta_path.exists():
                        shutil.copy2(meta_path, target_file_path.with_suffix(f"{target_file_path.suffix}.meta"))
                    
                    # Check for extracted text
                    extracted_dir = source_path / f"{domain_name}_extracted"
                    if extracted_dir.exists():
                        extracted_file = extracted_dir / f"{file_path.stem}.txt"
                        if extracted_file.exists():
                            target_extracted_file = target_extracted_dir / f"{file_path.stem}.txt"
                            shutil.copy2(extracted_file, target_extracted_file)
                    
                    stats["files_copied"] += 1
                    stats["by_domain"][domain_name]["files_copied"] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    stats["errors"] += 1
                    stats["by_domain"][domain_name]["errors"] += 1
    
    # Generate combined metadata
    metadata_path = target_path / "combined_corpus_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump({
            "source_directories": source_dirs,
            "target_directory": target_dir,
            "combination_stats": stats,
            "total_unique_files": len(file_hashes)
        }, f, indent=2)
    
    return stats

def main():
    parser = argparse.ArgumentParser(description='Combine multiple corpus directories into a unified structure')
    parser.add_argument('--sources', nargs='+', required=True, help='Source corpus directories')
    parser.add_argument('--target', required=True, help='Target directory for combined corpus')
    args = parser.parse_args()
    
    logger.info(f"Starting corpus combination from {args.sources} to {args.target}")
    
    stats = combine_corpora(args.sources, args.target)
    
    # Print summary
    print("\n=== Corpus Combination Summary ===")
    print(f"Total files processed: {stats['total_files_processed']}")
    print(f"Files copied: {stats['files_copied']}")
    print(f"Duplicates skipped: {stats['duplicates_skipped']}")
    print(f"Errors: {stats['errors']}")
    print("\nDomain breakdown:")
    for domain, domain_stats in stats["by_domain"].items():
        print(f"  {domain}:")
        print(f"    Files processed: {domain_stats['files_processed']}")
        print(f"    Files copied: {domain_stats['files_copied']}")
        print(f"    Duplicates skipped: {domain_stats['duplicates_skipped']}")
        print(f"    Errors: {domain_stats['errors']}")
    
    logger.info("Corpus combination completed")

if __name__ == "__main__":
    main()