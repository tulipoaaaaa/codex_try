import os
import json
import shutil
import re
from pathlib import Path
from processors.domain_classifier import DomainClassifier
from CryptoFinanceCorpusBuilder.config.domain_config import DOMAINS

# Set up paths
corpus_dir = Path("/workspace/data/corpus_1")

# Valid domains
valid_domains = set(DOMAINS.keys())

# Initialize domain classifier
classifier = DomainClassifier(DOMAINS)

# Create domain directories if they don't exist
for domain in valid_domains:
    os.makedirs(corpus_dir / domain, exist_ok=True)
    os.makedirs(corpus_dir / f"{domain}_extracted", exist_ok=True)

# Function to clean and standardize filenames
def standardize_filename(original_name, domain, md5=None):
    # Extract meaningful parts from the filename
    name_parts = original_name.split('_')
    
    # Try to get a sensible short title
    title_part = original_name[:30].replace('_', ' ').strip()
    
    # Clean title
    title_part = re.sub(r'[^\w\s-]', '', title_part).strip()
    
    # Get MD5 part if available
    md5_part = ""
    if md5:
        md5_part = md5[:8]
    elif len(name_parts) > 1 and len(name_parts[-1]) >= 8:
        md5_part = name_parts[-1][:8]
    
    # Construct new filename
    new_name = f"{domain}_{title_part}_{md5_part}.pdf"
    
    # Replace spaces with underscores and ensure no double underscores
    new_name = new_name.replace(' ', '_').replace('__', '_')
    
    return new_name

# Process all directories to find PDFs
print("Consolidating files to appropriate domains...")
for src_dir in corpus_dir.iterdir():
    # Skip if not a directory or if it's an _extracted directory
    if not src_dir.is_dir() or src_dir.name.endswith("_extracted"):
        continue
    
    # Process each PDF file
    for pdf_file in src_dir.glob("*.pdf"):
        # Skip if the directory is already a valid domain
        if src_dir.name in valid_domains:
            # Standardize filename
            new_name = standardize_filename(pdf_file.stem, src_dir.name)
            new_path = src_dir / new_name
            
            if new_path != pdf_file:
                print(f"Renaming: {pdf_file.name} -> {new_name}")
                # Rename file
                shutil.move(pdf_file, new_path)
                
                # Update metadata file if it exists
                meta_file = Path(str(pdf_file) + ".meta")
                if meta_file.exists():
                    new_meta_file = Path(str(new_path) + ".meta")
                    shutil.move(meta_file, new_meta_file)
            
            continue
        
        # Read PDF file to determine domain
        print(f"Classifying: {pdf_file}")
        try:
            from processors.text_extractor import TextExtractor
            extractor = TextExtractor()
            
            # Extract text sample for classification
            extract_result = extractor.extract(pdf_file)
            if not extract_result or 'text' not in extract_result:
                print(f"  Could not extract text, skipping")
                continue
                
            text_sample = extract_result['text'][:5000]  # First 5000 chars for classification
            
            # Classify the file
            classification = classifier.classify(text_sample)
            target_domain = classification['domain']
            
            if target_domain not in valid_domains:
                target_domain = "crypto_derivatives"  # Default domain
                
            print(f"  Classified as: {target_domain}")
            
            # Create standardized filename
            new_name = standardize_filename(pdf_file.stem, target_domain)
            target_path = corpus_dir / target_domain / new_name
            
            # Move the file
            print(f"  Moving to: {target_path}")
            shutil.move(pdf_file, target_path)
            
            # Create or update metadata
            meta_content = {
                "title": pdf_file.stem.replace('_', ' ')[:50].strip(),
                "domain": target_domain,
                "confidence": classification['confidence'],
                "original_path": str(pdf_file),
                "consolidated_date": "2025-05-08"
            }
            
            # Check for existing metadata
            meta_file = Path(str(pdf_file) + ".meta")
            if meta_file.exists():
                # Read existing metadata
                with open(meta_file, "r") as f:
                    existing_meta = json.load(f)
                
                # Update with existing values
                meta_content.update(existing_meta)
                
                # Delete old metadata file
                os.remove(meta_file)
            
            # Write new metadata
            new_meta_file = Path(str(target_path) + ".meta")
            with open(new_meta_file, "w") as f:
                json.dump(meta_content, f, indent=2)
                
            # Check for extracted text and move it if exists
            original_extracted = src_dir.with_name(f"{src_dir.name}_extracted") / f"{pdf_file.stem}.txt"
            if original_extracted.exists():
                target_extracted = corpus_dir / f"{target_domain}_extracted" / f"{target_path.stem}.txt"
                os.makedirs(target_extracted.parent, exist_ok=True)
                shutil.move(original_extracted, target_extracted)
                
        except Exception as e:
            print(f"  Error processing {pdf_file}: {e}")

# Remove empty directories (except valid domains)
print("\nRemoving empty directories...")
for directory in corpus_dir.iterdir():
    if directory.is_dir() and directory.name not in valid_domains and not directory.name.endswith("_extracted"):
        # Check if directory is empty
        if not any(directory.iterdir()):
            print(f"Removing empty directory: {directory}")
            os.rmdir(directory)

print("\nFile consolidation complete")

# Generate updated corpus statistics
print("\nGenerating updated corpus statistics...")
corpus_stats = {
    "domains": {},
    "total_files": 0,
    "total_size_mb": 0
}

# Count files in each domain
for domain in valid_domains:
    domain_dir = corpus_dir / domain
    if domain_dir.exists():
        pdf_files = list(domain_dir.glob("*.pdf"))
        meta_files = list(domain_dir.glob("*.pdf.meta"))
        
        # Calculate size
        domain_size_bytes = sum(os.path.getsize(f) for f in pdf_files if os.path.exists(f))
        domain_size_mb = domain_size_bytes / (1024 * 1024)
        
        corpus_stats["domains"][domain] = {
            "pdf_files": len(pdf_files),
            "meta_files": len(meta_files),
            "size_mb": round(domain_size_mb, 2)
        }
        
        corpus_stats["total_files"] += len(pdf_files)
        corpus_stats["total_size_mb"] += domain_size_mb

# Round total size
corpus_stats["total_size_mb"] = round(corpus_stats["total_size_mb"], 2)

# Save stats
with open(corpus_dir / "corpus_stats.json", "w") as f:
    json.dump(corpus_stats, f, indent=2)

print("Corpus Statistics:")
print(f"Total Files: {corpus_stats['total_files']}")
print(f"Total Size: {corpus_stats['total_size_mb']} MB")
print("\nDomain Coverage:")
for domain, stats in corpus_stats["domains"].items():
    print(f"  {domain}: {stats['pdf_files']} files, {stats['size_mb']} MB")