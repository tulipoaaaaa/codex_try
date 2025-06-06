# domainsmanager.py
import os
import json
from pathlib import Path
import logging
from CryptoFinanceCorpusBuilder.config.domain_config import DOMAINS

class DomainManager:
    """Manager for crypto-finance corpus domains"""
    
    def __init__(self, domains_config=None, base_dir="/workspace/data/corpus_1"):
        """Initialize with domain configuration"""
        self.base_dir = Path(base_dir)
        
        # Load domain configuration if provided or use default
        if domains_config:
            self.domains = domains_config
        else:
            try:
                from shared_tools.config.domain_config import DOMAINS
                self.domains = DOMAINS
            except ImportError:
                # Default domain configuration if domain_config.py is not available
                self.domains = {
                    "crypto_derivatives": {"allocation": 0.20},
                    "high_frequency_trading": {"allocation": 0.15},
                    "market_microstructure": {"allocation": 0.15},
                    "risk_management": {"allocation": 0.15},
                    "decentralized_finance": {"allocation": 0.12},
                    "portfolio_construction": {"allocation": 0.10},
                    "valuation_models": {"allocation": 0.08},
                    "regulation_compliance": {"allocation": 0.05}
                }
        
        # Create domain directories
        self._create_domain_directories()
        
        # Set up logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging for the domain manager"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            handlers=[
                logging.FileHandler(self.base_dir / "domain_manager.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("DomainManager")
        self.logger.info(f"Domain Manager initialized with {len(self.domains)} domains")
    
    def _create_domain_directories(self):
        """Create directories for each domain"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        for domain in self.domains:
            domain_dir = self.base_dir / domain
            domain_dir.mkdir(exist_ok=True)
            
            # Create extracted text directory if needed
            extracted_dir = self.base_dir / f"{domain}_extracted"
            extracted_dir.mkdir(exist_ok=True)
    
    def get_domain_allocation(self, total_downloads=1200):
        """Calculate how many downloads to allocate per domain"""
        allocation = {}
        
        for domain, config in self.domains.items():
            percentage = config.get("allocation", 0)
            allocation[domain] = int(total_downloads * percentage)
        
        # Ensure all downloads are allocated by assigning any remainder to first domain
        assigned = sum(allocation.values())
        if assigned < total_downloads:
            first_domain = next(iter(allocation))
            allocation[first_domain] += (total_downloads - assigned)
        
        return allocation
    
    def get_domain_stats(self):
        """Get statistics for each domain"""
        stats = {}
        
        for domain in self.domains:
            domain_dir = self.base_dir / domain
            extracted_dir = self.base_dir / f"{domain}_extracted"
            
            # Count files by type
            if domain_dir.exists():
                pdf_files = list(domain_dir.glob("*.pdf"))
                epub_files = list(domain_dir.glob("*.epub"))
                mobi_files = list(domain_dir.glob("*.mobi"))
                meta_files = list(domain_dir.glob("*.meta"))
                
                # Calculate size
                domain_size = sum(f.stat().st_size for f in pdf_files + epub_files + mobi_files if f.exists())
                
                # Count extracted text files
                extracted_files = list(extracted_dir.glob("*.txt")) if extracted_dir.exists() else []
                
                stats[domain] = {
                    "pdf_files": len(pdf_files),
                    "epub_files": len(epub_files),
                    "mobi_files": len(mobi_files),
                    "meta_files": len(meta_files),
                    "extracted_files": len(extracted_files),
                    "total_files": len(pdf_files) + len(epub_files) + len(mobi_files),
                    "size_bytes": domain_size,
                    "size_mb": domain_size / (1024 * 1024)
                }
        
        return stats
    
    def get_search_terms(self, domain):
        """Get search terms for a specific domain"""
        if domain not in self.domains:
            self.logger.warning(f"Domain {domain} not found in configuration")
            return []
        
        return self.domains[domain].get("search_terms", [])
    
    def get_all_search_terms(self):
        """Get all search terms across all domains"""
        all_terms = {}
        
        for domain, config in self.domains.items():
            all_terms[domain] = config.get("search_terms", [])
        
        return all_terms
    
    def extract_text_from_pdfs(self, domains=None):
        """Extract text from PDFs in specified domains or all domains"""
        try:
            import PyPDF2
        except ImportError:
            self.logger.error("PyPDF2 not installed. Please install it with: pip install PyPDF2")
            return False
        
        # Process all domains if none specified
        if domains is None:
            domains = list(self.domains.keys())
        
        for domain in domains:
            if domain not in self.domains:
                self.logger.warning(f"Domain {domain} not found. Skipping.")
                continue
            
            domain_dir = self.base_dir / domain
            extracted_dir = self.base_dir / f"{domain}_extracted"
            
            if not domain_dir.exists():
                self.logger.warning(f"Directory for domain {domain} does not exist. Skipping.")
                continue
            
            # Create extracted text directory if it doesn't exist
            extracted_dir.mkdir(exist_ok=True)
            
            # Find all PDFs in the domain directory
            pdf_files = list(domain_dir.glob("*.pdf"))
            self.logger.info(f"Found {len(pdf_files)} PDFs in domain {domain}")
            
            # Extract text from each PDF
            for pdf_file in pdf_files:
                output_file = extracted_dir / f"{pdf_file.stem}.txt"
                
                # Skip if already extracted
                if output_file.exists():
                    self.logger.info(f"Text already extracted for {pdf_file.name}. Skipping.")
                    continue
                
                try:
                    self.logger.info(f"Extracting text from {pdf_file.name}")
                    
                    with open(pdf_file, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        
                        for page_num in range(len(reader.pages)):
                            text += reader.pages[page_num].extract_text() + "\n\n"
                    
                    # Save extracted text
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(text)
                        
                    self.logger.info(f"Extracted text saved to {output_file}")
                    
                except Exception as e:
                    self.logger.error(f"Error extracting text from {pdf_file.name}: {e}")
        
        self.logger.info(f"Text extraction completed for domains: {domains}")
        return True
    
    def generate_corpus_stats(self):
        """Generate comprehensive corpus statistics"""
        stats = {
            "total_size_bytes": 0,
            "total_files": 0,
            "domains": self.get_domain_stats()
        }
        
        # Calculate totals
        for domain, domain_stats in stats["domains"].items():
            stats["total_size_bytes"] += domain_stats["size_bytes"]
            stats["total_files"] += domain_stats["total_files"]
        
        # Convert total size to MB and GB
        stats["total_size_mb"] = stats["total_size_bytes"] / (1024 * 1024)
        stats["total_size_gb"] = stats["total_size_bytes"] / (1024 * 1024 * 1024)
        
        # Save stats to file
        stats_file = self.base_dir / "corpus_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        self.logger.info(f"Corpus statistics saved to {stats_file}")
        return stats
    
    def print_corpus_stats(self):
        """Print corpus statistics to console"""
        stats = self.generate_corpus_stats()
        
        print("\nCorpus Analysis:")
        print(f"Total size: {stats['total_size_mb']:.2f} MB ({stats['total_size_gb']:.2f} GB)")
        print(f"Total files: {stats['total_files']}")
        
        print("\nDomain breakdown:")
        for domain, domain_stats in stats["domains"].items():
            print(f"  {domain}:")
            print(f"    Files: {domain_stats['total_files']} ({domain_stats['pdf_files']} PDFs, {domain_stats['epub_files']} EPUBs, {domain_stats['mobi_files']} MOBIs)")
            print(f"    Metadata: {domain_stats['meta_files']} files")
            print(f"    Extracted: {domain_stats['extracted_files']} text files")
            print(f"    Size: {domain_stats['size_mb']:.2f} MB")