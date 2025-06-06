# consolidate_corpus.py
import os
import sys
import shutil
import re
from pathlib import Path
import json
import importlib.util
from datetime import date
import logging
import argparse
from CryptoFinanceCorpusBuilder.config.domain_config import DOMAINS
from CryptoFinanceCorpusBuilder.shared_tools.processors.domain_classifier import DomainClassifier
from CryptoFinanceCorpusBuilder.shared_tools.project_config import ProjectConfig

def setup_logging(config: ProjectConfig = None) -> None:
    """Set up logging configuration."""
    if config:
        log_dir = Path(config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'consolidate_corpus.log'
    else:
        log_file = 'consolidate_corpus.log'
    
logging.basicConfig(
        filename=log_file,
    filemode='a',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)

def standardize_filename(filename, domain=None):
    """
    Standardize a filename for better organization
    - Remove special characters
    - Replace spaces with underscores
    - Add domain prefix if provided
    """
    # Remove special characters and clean up
    clean_name = re.sub(r'[^\w\s-]', '', filename).strip()
    
    # Replace spaces with underscores
    clean_name = clean_name.replace(' ', '_')
    
    # Add domain prefix if provided
    if domain:
        clean_name = f"{domain}_{clean_name}"
    
    return clean_name

def consolidate_corpus(config: ProjectConfig, output_dir: Path = None):
    """
    Consolidate corpus files from config.raw_data_dir to output_dir
    - Organize by domain
    - Standardize filenames
    - Copy extracted text if available
    
    Args:
        config: ProjectConfig instance
        output_dir: Optional output directory (defaults to config.consolidated_dir)
    """
    if output_dir is None:
        output_dir = Path(config.consolidated_dir)
    
    original_corpus_dir = Path(config.raw_data_dir)
    
    logging.info("Starting corpus consolidation...")
    logging.info(f"Source directory: {original_corpus_dir}")
    logging.info(f"Target directory: {output_dir}")
    
    # Initialize classifier
    classifier = DomainClassifier(DOMAINS)
    logging.info("Successfully initialized classifier")
    
    # Create domain directories if they don't exist
    for domain in DOMAINS.keys():
        os.makedirs(output_dir / domain, exist_ok=True)
        os.makedirs(output_dir / f"{domain}_extracted", exist_ok=True)
    
    # Track statistics
    stats = {
        "total_processed": 0,
        "classified": 0,
        "by_domain": {domain: 0 for domain in DOMAINS.keys()}
    }
    
    # Process PDF files in original corpus
    pdf_files = list(original_corpus_dir.glob("**/*.pdf"))
    logging.info(f"Found {len(pdf_files)} PDF files to process")
    
    for pdf_file in pdf_files:
        try:
            # Skip files that are already in new corpus directory
            if str(output_dir) in str(pdf_file):
                continue
            
            # Check for existing extracted text to help with classification
            extracted_text = None
            parent_dir = pdf_file.parent
            
            # Look for corresponding extracted text file
            potential_extracted_dirs = [
                parent_dir.parent / f"{parent_dir.name}_extracted",
                original_corpus_dir / f"{parent_dir.name}_extracted"
            ]
            
            for extracted_dir in potential_extracted_dirs:
                text_file = extracted_dir / f"{pdf_file.stem}.txt"
                if text_file.exists():
                    try:
                        with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
                            extracted_text = f.read()
                            break
                    except Exception as e:
                        logging.error(f"Error reading extracted text for {pdf_file}: {e}")
            
            # Determine domain
            domain = None
            
            # Check if file is already in a domain directory
            for d in DOMAINS.keys():
                if d in str(pdf_file):
                    domain = d
                    break
            
            # If not found by directory, use text classification
            if not domain and extracted_text:
                classification = classifier.classify(extracted_text[:5000])
                domain = classification["domain"]
                confidence = classification["confidence"]
                logging.info(f"Classified {pdf_file.name} as {domain} (confidence: {confidence:.2f})")
                stats["classified"] += 1
            elif not domain:
                # Check for keywords in filename
                filename_lower = pdf_file.name.lower()
                if "crypto" in filename_lower or "bitcoin" in filename_lower or "derivatives" in filename_lower:
                    domain = "crypto_derivatives"
                elif "microstructure" in filename_lower or "market" in filename_lower or "liquidity" in filename_lower:
                    domain = "market_microstructure"
                elif "risk" in filename_lower or "portfolio" in filename_lower:
                    domain = "risk_management"
                elif "high frequency" in filename_lower or "hft" in filename_lower or "algo" in filename_lower:
                    domain = "high_frequency_trading"
                elif "defi" in filename_lower or "finance" in filename_lower:
                    domain = "decentralized_finance"
                else:
                    # Default domain if can't classify
                    domain = "crypto_derivatives"  # Default
                
                logging.info(f"Could not classify {pdf_file.name} using extracted text, used filename: {domain}")
            
            # Standardize filename
            new_filename = standardize_filename(pdf_file.stem, domain) + pdf_file.suffix
            target_path = output_dir / domain / new_filename
            
            # Create directories if they don't exist
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            logging.info(f"Copying {pdf_file} to {target_path}")
            shutil.copy2(pdf_file, target_path)
            
            # Copy extracted text if available
            if extracted_text:
                extracted_target_dir = output_dir / f"{domain}_extracted"
                extracted_target_dir.mkdir(parents=True, exist_ok=True)
                
                extracted_target_path = extracted_target_dir / f"{target_path.stem}.txt"
                with open(extracted_target_path, 'w', encoding='utf-8') as f:
                    f.write(extracted_text)
            
            # Create metadata file
            metadata = {
                "original_path": str(pdf_file),
                "consolidated_path": str(target_path),
                "domain": domain,
                "standardized_name": new_filename,
                "original_name": pdf_file.name,
                "has_extracted_text": extracted_text is not None,
                "consolidation_date": str(date.today())
            }
            
            with open(f"{target_path}.meta", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Update statistics
            stats["total_processed"] += 1
            stats["by_domain"][domain] += 1
            
        except Exception as e:
            logging.error(f"Error processing {pdf_file}: {e}")
    
    # Print summary
    logging.info("\n=== Corpus Consolidation Summary ===")
    logging.info(f"Total files processed: {stats['total_processed']}")
    logging.info(f"Files classified: {stats['classified']}")
    logging.info("\nFiles by domain:")
    for domain, count in stats["by_domain"].items():
        logging.info(f"  {domain}: {count}")
    
    return stats

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Consolidate corpus files into domain-based structure')
    parser.add_argument('--config', required=True, help='Path to config file')
    parser.add_argument('--output-dir', help='Output directory (defaults to config.consolidated_dir)')
    
    args = parser.parse_args()
    
    # Load config
    config = ProjectConfig(args.config)
    
    # Set up logging
    setup_logging(config)
    
    # Get output directory
    output_dir = Path(args.output_dir) if args.output_dir else None
    
    # Run consolidation
    stats = consolidate_corpus(config, output_dir)
    
    # Print summary to console
    print("\n=== Corpus Consolidation Summary ===")
    print(f"Total files processed: {stats['total_processed']}")
    print(f"Files classified: {stats['classified']}")
    print("\nFiles by domain:")
    for domain, count in stats["by_domain"].items():
        print(f"  {domain}: {count}")

if __name__ == '__main__':
    main()