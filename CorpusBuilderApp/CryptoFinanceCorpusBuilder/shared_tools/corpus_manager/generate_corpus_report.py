# generate_corpus_report.py
import argparse
import json
import os
import random
from pathlib import Path
from datetime import datetime

def generate_report(args):
    """Generate comprehensive corpus report"""
    corpus_dir = Path(args.corpus_dir)
    output_file = args.output
    include_stats = args.include_stats
    include_examples = args.include_examples
    
    # Load coverage data if available
    coverage_data = {}
    coverage_file = corpus_dir / "final_coverage.json"
    
    if coverage_file.exists():
        try:
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)
        except json.JSONDecodeError:
            print(f"Error reading coverage file: {coverage_file}")
    
    # Find all domains
    domains = [d for d in os.listdir(corpus_dir) 
              if os.path.isdir(os.path.join(corpus_dir, d)) and not d.endswith('_extracted')]
    
    # Collect corpus statistics
    stats = {
        "total_documents": 0,
        "total_size_bytes": 0,
        "domains": {},
        "sources": {},
        "file_types": {}
    }
    
    # Process each domain
    all_files = []
    
    for domain in domains:
        domain_dir = corpus_dir / domain
        files = list(domain_dir.glob("*.pdf"))
        all_files.extend(files)
        
        # Count files and size for domain
        domain_size = sum(os.path.getsize(f) for f in files)
        
        stats["domains"][domain] = {
            "file_count": len(files),
            "size_bytes": domain_size
        }
        
        stats["total_documents"] += len(files)
        stats["total_size_bytes"] += domain_size
        
        # Collect source distribution if available
        for file in files:
            meta_file = Path(str(file) + ".meta")
            
            if meta_file.exists():
                try:
                    with open(meta_file, 'r') as f:
                        metadata = json.load(f)
                        
                    # Track source
                    source = metadata.get("source", "unknown")
                    if source not in stats["sources"]:
                        stats["sources"][source] = 0
                    stats["sources"][source] += 1
                    
                    # Track file type
                    file_type = metadata.get("file_type", "pdf")
                    if file_type not in stats["file_types"]:
                        stats["file_types"][file_type] = 0
                    stats["file_types"][file_type] += 1
                except:
                    pass
    
    # Convert to GB
    stats["total_size_gb"] = stats["total_size_bytes"] / (1024**3)
    
    # Convert domain sizes to MB
    for domain in stats["domains"]:
        stats["domains"][domain]["size_mb"] = stats["domains"][domain]["size_bytes"] / (1024**2)
    
    # Generate report markdown
    report = f"""# Crypto-Finance Corpus Report

## Summary

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This report provides details on the crypto-finance corpus built using a multi-source ingestion strategy.

### Key Statistics

- **Total Documents:** {stats["total_documents"]}
- **Total Size:** {stats["total_size_gb"]:.2f} GB
- **Domains:** {len(domains)}
- **Traditional Finance Percentage:** {coverage_data.get("traditional_finance_percentage", "N/A")}%
- **Crypto-Native Percentage:** {coverage_data.get("crypto_native_percentage", "N/A")}%
- **Balance Score:** {coverage_data.get("balance_score", "N/A")}/100

## Domain Distribution

| Domain | Documents | Size (MB) | Percentage |
|--------|-----------|-----------|------------|
"""

    # Add domain table rows
    for domain, domain_stats in sorted(stats["domains"].items(), 
                                      key=lambda x: x[1]["file_count"], 
                                      reverse=True):
        file_count = domain_stats["file_count"]
        size_mb = domain_stats["size_mb"]
        percentage = (file_count / stats["total_documents"]) * 100 if stats["total_documents"] > 0 else 0
        
        report += f"| {domain} | {file_count} | {size_mb:.2f} | {percentage:.2f}% |\n"

    # Add source distribution if available
    if stats["sources"]:
        report += """
## Source Distribution

| Source | Documents | Percentage |
|--------|-----------|------------|
"""

        # Add source table rows
        for source, count in sorted(stats["sources"].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / stats["total_documents"]) * 100 if stats["total_documents"] > 0 else 0
            report += f"| {source} | {count} | {percentage:.2f}% |\n"

    # Add detailed statistics if requested
    if include_stats and coverage_data:
        report += """
## Detailed Statistics

### Traditional vs Crypto-Native Split

"""
        tf_percent = coverage_data.get("traditional_finance_percentage", 0)
        cn_percent = coverage_data.get("crypto_native_percentage", 0)
        
        report += f"- **Traditional Finance:** {tf_percent:.2f}%\n"
        report += f"- **Crypto-Native:** {cn_percent:.2f}%\n"
        
        # Add token distribution if available
        if "domain_token_counts" in coverage_data:
            report += """
### Token Distribution by Domain

| Domain | Token Count | Percentage |
|--------|-------------|------------|
"""
            
            token_counts = coverage_data["domain_token_counts"]
            total_tokens = sum(token_counts.values())
            
            for domain, count in sorted(token_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_tokens) * 100 if total_tokens > 0 else 0
                report += f"| {domain} | {count:,} | {percentage:.2f}% |\n"

    # Add sample documents if requested
    if include_examples and all_files:
        report += """
## Sample Documents

Below are some example documents from the corpus:

"""
        
        # Sample up to 3 documents per domain (randomly)
        for domain in domains:
            domain_dir = corpus_dir / domain
            files = list(domain_dir.glob("*.pdf"))
            
            if not files:
                continue
                
            report += f"### {domain.replace('_', ' ').title()}\n\n"
            
            # Take random samples
            samples = random.sample(files, min(3, len(files)))
            
            for sample in samples:
                meta_file = Path(str(sample) + ".meta")
                title = sample.stem
                size_mb = os.path.getsize(sample) / (1024 * 1024)
                
                # Get metadata if available
                source = "Unknown"
                authors = ""
                
                if meta_file.exists():
                    try:
                        with open(meta_file, 'r') as f:
                            metadata = json.load(f)
                        
                        if "title" in metadata:
                            title = metadata["title"]
                            
                        if "source" in metadata:
                            source = metadata["source"]
                            
                        if "key_authors" in metadata and metadata["key_authors"]:
                            authors = f" by {', '.join(metadata['key_authors'])}"
                    except:
                        pass
                
                report += f"- **{title}**{authors} ({size_mb:.2f} MB, from {source})\n"
            
            report += "\n"

    # Add implementation details
    report += """
## Implementation Details

This corpus was built using a comprehensive 48-hour execution strategy:

1. **Curated Foundation:** Started with high-quality selected texts and academic papers
2. **Multi-Source Collection:** Integrated content from Anna's Archive, SciDB, arXiv, FRED, GitHub, and specialized web sources
3. **Gap Analysis:** Performed targeted collection to ensure balanced domain coverage
4. **Deduplication & Quality Control:** Removed duplicates and enhanced metadata

### Collection Sources

- **Anna's Archive:** Primary source for textbooks and comprehensive references
- **SciDB:** Academic papers covering quant finance and crypto research
- **arXiv:** Latest research papers in quantitative finance categories
- **FRED:** Economic datasets and documentation
- **GitHub:** Trading algorithms and implementation code
- **Web Sources:** Institutional and specialized content (BIS, IMF, ISDA, etc.)

## Usage Recommendations

To effectively utilize this corpus:

1. **Full-Text Search:** The extracted text is available in domain_extracted folders
2. **Metadata Filtering:** Use the .meta files to filter by source, author, or other attributes
3. **Domain-Specific Analysis:** Each domain contains focused content for specific use cases

## Next Steps

Potential improvements for future corpus expansions:

1. Increase regulatory and compliance content
2. Add more academic papers from specialized journals
3. Include more non-English resources
4. Expand macroeconomic analysis materials
"""

    # Write the report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Generated corpus report at {output_file}")
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate corpus report")
    parser.add_argument("--corpus-dir", required=True, help="Corpus directory")
    parser.add_argument("--output", default="corpus_report.md", help="Output file path")
    parser.add_argument("--include-stats", action="store_true", help="Include detailed statistics")
    parser.add_argument("--include-examples", action="store_true", help="Include example documents")
    
    args = parser.parse_args()
    generate_report(args)