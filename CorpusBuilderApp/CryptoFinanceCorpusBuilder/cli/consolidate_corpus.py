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

# Set up logging
logging.basicConfig(
    filename='consolidate_corpus.log',
    filemode='a',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)

# Define paths
original_corpus_dir = Path("./data/pdfs")
new_corpus_dir = Path("./data/corpus_1")

logging.info("Starting corpus consolidation with sudo privileges...")

# Find required modules
domain_classifier_paths = []
domain_config_paths = []

for root, dirs, files in os.walk('.'):
    if 'domain_classifier.py' in files:
        domain_classifier_paths.append(os.path.join(root, 'domain_classifier.py'))
    if 'domain_config.py' in files:
        domain_config_paths.append(os.path.join(root, 'domain_config.py'))

if not domain_classifier_paths or not domain_config_paths:
    logging.error("Could not find domain_classifier.py and domain_config.py")
    sys.exit(1)

# Import modules
logging.info(f"Importing DomainClassifier from {domain_classifier_paths[0]}")
logging.info(f"Importing DOMAINS from {domain_config_paths[0]}")

# Import domain_config
spec = importlib.util.spec_from_file_location("domain_config", domain_config_paths[0])
domain_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(domain_config)
DOMAINS = domain_config.DOMAINS

# Import domain_classifier
spec = importlib.util.spec_from_file_location("domain_classifier", domain_classifier_paths[0])
domain_classifier_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(domain_classifier_module)
DomainClassifier = domain_classifier_module.DomainClassifier

# Initialize classifier
classifier = DomainClassifier(DOMAINS)
logging.info("Successfully initialized classifier")

# Function to standardize filenames
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

# Function to consolidate corpus
def consolidate_corpus():
    """
    Consolidate corpus files from original_corpus_dir to new_corpus_dir
    - Organize by domain
    - Standardize filenames
    - Copy extracted text if available
    """
    # Create domain directories if they don't exist
    for domain in DOMAINS.keys():
        os.makedirs(new_corpus_dir / domain, exist_ok=True)
        os.makedirs(new_corpus_dir / f"{domain}_extracted", exist_ok=True)
    
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
            if str(new_corpus_dir) in str(pdf_file):
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
            target_path = new_corpus_dir / domain / new_filename
            
            # Create directories if they don't exist
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            logging.info(f"Copying {pdf_file} to {target_path}")
            shutil.copy2(pdf_file, target_path)
            
            # Copy extracted text if available
            if extracted_text:
                extracted_target_dir = new_corpus_dir / f"{domain}_extracted"
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
        logging.info(f"  {domain}: {count} files")
    
    # Save summary to file
    with open(new_corpus_dir / "consolidation_summary.json", 'w') as f:
        json.dump(stats, f, indent=2)
    
    return stats

# Run the consolidation
consolidation_stats = consolidate_corpus()
logging.info("Consolidation complete!")