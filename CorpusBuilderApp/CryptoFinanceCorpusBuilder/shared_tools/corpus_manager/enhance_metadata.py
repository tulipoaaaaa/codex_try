# enhance_metadata.py
import argparse
import json
import os
from pathlib import Path

def load_domain_key_authors():
    """Load key authors by domain from config"""
    key_authors = {
        "crypto_derivatives": ["Carol Alexander", "Antoinette Schoar", "Igor Makarov"],
        "high_frequency_trading": ["Ernest Chan", "Paraskevi Katsiampa", "Nikolaos Kyriazis"],
        "market_microstructure": ["Robert Almgren", "Terrence Hendershott", "Albert Menkveld"],
        "risk_management": ["Philip Jorion", "John Hull", "René Stulz"],
        "decentralized_finance": ["Vitalik Buterin", "Hayden Adams", "Robert Leshner"],
        "portfolio_construction": ["Harry Markowitz", "Andrew Ang", "Campbell Harvey"],
        "valuation_models": ["Chris Burniske", "John Pfeffer", "Aswath Damodaran"],
        "regulation_compliance": ["Gary Gensler", "Hester Peirce", "Brian Brooks"]
    }
    return key_authors

def enhance_metadata(args):
    """Enhance metadata for all documents in corpus"""
    corpus_dir = Path(args.corpus_dir)
    domains = [d for d in os.listdir(corpus_dir) 
               if os.path.isdir(os.path.join(corpus_dir, d)) and not d.endswith('_extracted')]
    
    print(f"Enhancing metadata for corpus in {corpus_dir}")
    print(f"Found {len(domains)} domains: {', '.join(domains)}")
    
    # Load key authors if tagging authors
    key_authors = load_domain_key_authors() if args.tag_authors else {}
    
    # Track statistics
    stats = {
        "processed_files": 0,
        "tagged_with_authors": 0,
        "tagged_with_sources": 0,
        "metadata_standardized": 0,
        "by_domain": {}
    }
    
    # Process each domain
    for domain in domains:
        domain_dir = corpus_dir / domain
        domain_stats = {"processed": 0, "enhanced": 0}
        
        # Collect all PDF files
        pdf_files = list(domain_dir.glob("*.pdf"))
        print(f"Found {len(pdf_files)} PDF files in domain '{domain}'")
        
        # Process each file
        for pdf_file in pdf_files:
            meta_file = Path(str(pdf_file) + ".meta")
            
            if not meta_file.exists():
                print(f"No metadata file for {pdf_file.name}, creating one")
                metadata = {
                    "title": pdf_file.stem,
                    "domain": domain,
                    "file_type": "pdf",
                    "enhanced": False
                }
            else:
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except json.JSONDecodeError:
                    print(f"Error parsing metadata for {pdf_file.name}, creating new metadata")
                    metadata = {
                        "title": pdf_file.stem,
                        "domain": domain,
                        "file_type": "pdf",
                        "enhanced": False
                    }
            
            # Ensure basic fields exist
            if "domain" not in metadata:
                metadata["domain"] = domain
                
            if "file_type" not in metadata:
                metadata["file_type"] = "pdf"
            
            # Add/update enhancement flag
            metadata["enhanced"] = True
            metadata_changed = False
            
            # Tag with authors if requested
            if args.tag_authors:
                # Check title and file info for author matches
                domain_authors = key_authors.get(domain, [])
                matched_authors = []
                
                # Search in title
                title = metadata.get("title", "").lower()
                
                # Search in file info
                file_info = metadata.get("file_info", "").lower()
                
                # Combine for searching
                search_text = f"{title} {file_info}"
                
                for author in domain_authors:
                    if author.lower() in search_text:
                        matched_authors.append(author)
                
                if matched_authors:
                    metadata["key_authors"] = matched_authors
                    stats["tagged_with_authors"] += 1
                    metadata_changed = True
            
            # Tag with source info if requested
            if args.tag_sources:
                if "source" not in metadata and "source_path" in metadata:
                    source_path = metadata["source_path"].lower()
                    
                    # Determine source based on path patterns
                    if "annas" in source_path or "corpus_1" in source_path:
                        metadata["source"] = "annas_archive"
                    elif "scidb" in source_path:
                        metadata["source"] = "scidb"
                    elif "arxiv" in source_path:
                        metadata["source"] = "arxiv"
                    elif "github" in source_path:
                        metadata["source"] = "github"
                    elif "fred" in source_path:
                        metadata["source"] = "fred"
                    elif "web" in source_path:
                        # Try to determine specific web source
                        web_sources = ["bis", "imf", "isda", "sec", "finra", "occ", 
                                     "deribit", "dragonfly", "cryptoresearch"]
                        
                        for web_source in web_sources:
                            if web_source in source_path:
                                metadata["source"] = web_source
                                break
                        else:
                            metadata["source"] = "web_collector"
                    elif "curated" in source_path:
                        metadata["source"] = "curated_list"
                    else:
                        metadata["source"] = "unknown"
                    
                    stats["tagged_with_sources"] += 1
                    metadata_changed = True
            
            # Standardize metadata if needed
            if args.standardize:
                # Use consistent keys
                standard_keys = {
                    "title": metadata.get("title", pdf_file.stem),
                    "domain": metadata.get("domain", domain),
                    "file_type": metadata.get("file_type", "pdf"),
                    "source": metadata.get("source", "unknown"),
                    "md5": metadata.get("md5", ""),
                    "source_path": metadata.get("source_path", ""),
                    "enhanced": True
                }
                
                # Optional keys
                if "file_info" in metadata:
                    standard_keys["file_info"] = metadata["file_info"]
                    
                if "key_authors" in metadata:
                    standard_keys["key_authors"] = metadata["key_authors"]
                    
                if "download_date" in metadata:
                    standard_keys["download_date"] = metadata["download_date"]
                
                # Add any additional existing keys
                for key, value in metadata.items():
                    if key not in standard_keys:
                        standard_keys[key] = value
                
                metadata = standard_keys
                stats["metadata_standardized"] += 1
                metadata_changed = True
            
            # Save updated metadata if changed
            if metadata_changed:
                with open(meta_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)
                domain_stats["enhanced"] += 1
            
            domain_stats["processed"] += 1
            stats["processed_files"] += 1
        
        stats["by_domain"][domain] = domain_stats
        print(f"Processed {domain_stats['processed']} files in domain '{domain}', enhanced {domain_stats['enhanced']}")
    
    # Save stats
    stats_file = corpus_dir / "metadata_enhancement_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    print(f"Enhanced metadata for {stats['processed_files']} files")
    print(f"Tagged {stats['tagged_with_authors']} with authors, {stats['tagged_with_sources']} with sources")
    print(f"Standardized {stats['metadata_standardized']} metadata files")
    print(f"Stats saved to {stats_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enhance corpus metadata")
    parser.add_argument("--corpus-dir", required=True, help="Corpus directory")
    parser.add_argument("--tag-authors", action="store_true", help="Tag documents with key authors")
    parser.add_argument("--tag-sources", action="store_true", help="Tag documents with source information")
    parser.add_argument("--standardize", action="store_true", help="Standardize metadata format")
    
    args = parser.parse_args()
    enhance_metadata(args)