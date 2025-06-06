# storage/corpus_manager.py
import os
import json
import shutil
import logging
import datetime
from pathlib import Path
import uuid
from CryptoFinanceCorpusBuilder.config.domain_config import DOMAINS

class CorpusManager:
    """Manage the crypto-finance corpus structure"""
    
    def __init__(self, base_dir, domain_config=None):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Load domain configuration if not provided
        if domain_config is None:
            try:
                from CryptoFinanceCorpusBuilder.config.domain_config import DOMAINS
                self.domain_config = DOMAINS
            except ImportError:
                self.domain_config = {}
        else:
            self.domain_config = domain_config
        
        # Create domain directories
        self._create_domain_directories()
        
        # Configure logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
            # Add file handler
            log_dir = Path("G:/ai_trading_dev/CryptoFinanceCorpusBuilder/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_dir / "corpus_manager.log")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Metadata storage
        self.metadata_file = self.base_dir / "corpus_metadata.json"
        self.metadata = self._load_metadata()
        
        self.logger.info(f"Initialized corpus manager at {self.base_dir}")
    
    def _create_domain_directories(self):
        """Create directories for each domain"""
        for domain in self.domain_config:
            domain_dir = self.base_dir / domain
            domain_dir.mkdir(exist_ok=True)
            
            # Create extracted text directory
            extracted_dir = self.base_dir / f"{domain}_extracted"
            extracted_dir.mkdir(exist_ok=True)
    
    def _load_metadata(self):
        """Load corpus metadata from file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading metadata: {e}")
                return self._initialize_metadata()
        else:
            return self._initialize_metadata()
    
    def _initialize_metadata(self):
        """Initialize empty metadata structure"""
        metadata = {
            "creation_date": datetime.datetime.now().isoformat(),
            "last_updated": datetime.datetime.now().isoformat(),
            "total_documents": 0,
            "domains": {},
            "sources": {},
            "documents": {}
        }
        
        # Initialize domain stats
        for domain in self.domain_config:
            metadata["domains"][domain] = {
                "document_count": 0,
                "extracted_count": 0,
                "total_size_bytes": 0
            }
        
        return metadata
    
    def _save_metadata(self):
        """Save metadata to file"""
        try:
            self.metadata["last_updated"] = datetime.datetime.now().isoformat()
            
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
                
            self.logger.debug("Saved corpus metadata")
        except Exception as e:
            self.logger.error(f"Error saving metadata: {e}")
    
    def add_document(self, source_path, domain, metadata=None, move=False):
        """Add a document to the corpus"""
        source_path = Path(source_path)
        
        if not source_path.exists():
            self.logger.error(f"Source file does not exist: {source_path}")
            return None
        
        # Verify domain exists
        if domain not in self.domain_config:
            self.logger.warning(f"Unknown domain: {domain}, creating it")
            domain_dir = self.base_dir / domain
            domain_dir.mkdir(exist_ok=True)
            
            extracted_dir = self.base_dir / f"{domain}_extracted"
            extracted_dir.mkdir(exist_ok=True)
            
            # Add to domain config
            self.domain_config[domain] = {"allocation": 0.0, "search_terms": []}
            
            # Add to metadata
            if domain not in self.metadata["domains"]:
                self.metadata["domains"][domain] = {
                    "document_count": 0,
                    "extracted_count": 0,
                    "total_size_bytes": 0
                }
        
        # Generate document ID if not in metadata
        doc_id = str(uuid.uuid4())
        
        # Determine target path
        target_dir = self.base_dir / domain
        
        # Use original filename or clean version of it
        filename = source_path.name
        
        # Ensure filename doesn't already exist, append ID if needed
        target_path = target_dir / filename
        if target_path.exists():
            # Append first 8 chars of ID to filename
            name_parts = source_path.stem, source_path.suffix
            new_filename = f"{name_parts[0]}_{doc_id[:8]}{name_parts[1]}"
            target_path = target_dir / new_filename
        
        # Copy or move the file
        try:
            if move:
                shutil.move(str(source_path), str(target_path))
                self.logger.info(f"Moved {source_path} to {target_path}")
            else:
                shutil.copy2(str(source_path), str(target_path))
                self.logger.info(f"Copied {source_path} to {target_path}")
        except Exception as e:
            self.logger.error(f"Error copying/moving file: {e}")
            return None
        
        # Prepare document metadata
        doc_metadata = {
            "id": doc_id,
            "domain": domain,
            "filename": target_path.name,
            "path": str(target_path),
            "source_path": str(source_path),
            "size_bytes": target_path.stat().st_size,
            "date_added": datetime.datetime.now().isoformat(),
            "file_type": target_path.suffix.lstrip('.').lower()
        }
        
        # Add user-provided metadata
        if metadata:
            doc_metadata.update(metadata)
        
        # Add to metadata
        self.metadata["documents"][doc_id] = doc_metadata
        self.metadata["domains"][domain]["document_count"] += 1
        self.metadata["domains"][domain]["total_size_bytes"] += doc_metadata["size_bytes"]
        self.metadata["total_documents"] += 1
        
        # Track source if available
        source = metadata.get("source") if metadata else None
        if source:
            if source not in self.metadata["sources"]:
                self.metadata["sources"][source] = {
                    "document_count": 0,
                    "total_size_bytes": 0
                }
            self.metadata["sources"][source]["document_count"] += 1
            self.metadata["sources"][source]["total_size_bytes"] += doc_metadata["size_bytes"]
        
        # Save metadata
        self._save_metadata()
        
        return doc_id
    
    def add_extracted_text(self, doc_id, text_content, metadata=None):
        """Add extracted text for a document"""
        if doc_id not in self.metadata["documents"]:
            self.logger.error(f"Document not found: {doc_id}")
            return False
        
        doc_info = self.metadata["documents"][doc_id]
        domain = doc_info["domain"]
        
        # Create output path
        extracted_dir = self.base_dir / f"{domain}_extracted"
        filename = Path(doc_info["filename"]).stem + ".txt"
        output_path = extracted_dir / filename
        
        # Write extracted text to file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
                
            # Update metadata
            doc_info["extracted_text_path"] = str(output_path)
            doc_info["extraction_date"] = datetime.datetime.now().isoformat()
            
            if metadata:
                if "extraction_metadata" not in doc_info:
                    doc_info["extraction_metadata"] = {}
                doc_info["extraction_metadata"].update(metadata)
            
            # Update domain stats
            self.metadata["domains"][domain]["extracted_count"] += 1
            
            # Save metadata
            self._save_metadata()
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving extracted text: {e}")
            return False
    
    def get_corpus_stats(self):
        """Get statistics for the corpus"""
        stats = {
            "total_documents": self.metadata["total_documents"],
            "total_size_bytes": sum(domain["total_size_bytes"] for domain in self.metadata["domains"].values()),
            "total_extracted": sum(domain["extracted_count"] for domain in self.metadata["domains"].values()),
            "domains": {},
            "sources": self.metadata["sources"],
            "last_updated": self.metadata["last_updated"]
        }
        
        # Add domain stats
        for domain, domain_info in self.metadata["domains"].items():
            stats["domains"][domain] = {
                "document_count": domain_info["document_count"],
                "extracted_count": domain_info["extracted_count"],
                "total_size_mb": domain_info["total_size_bytes"] / (1024 * 1024)
            }
        
        # Add overall size in MB and GB
        stats["total_size_mb"] = stats["total_size_bytes"] / (1024 * 1024)
        stats["total_size_gb"] = stats["total_size_bytes"] / (1024 * 1024 * 1024)
        
        return stats
    
    def print_corpus_stats(self):
        """Print corpus statistics to console"""
        stats = self.get_corpus_stats()
        
        print("\n=== Crypto-Finance Corpus Statistics ===")
        print(f"Total documents: {stats['total_documents']}")
        print(f"Total size: {stats['total_size_mb']:.2f} MB ({stats['total_size_gb']:.2f} GB)")
        print(f"Documents with extracted text: {stats['total_extracted']}")
        print(f"Last updated: {stats['last_updated']}")
        
        print("\nDomain breakdown:")
        for domain, domain_stats in stats["domains"].items():
            print(f"  {domain}:")
            print(f"    Documents: {domain_stats['document_count']}")
            print(f"    Extracted: {domain_stats['extracted_count']}")
            print(f"    Size: {domain_stats['total_size_mb']:.2f} MB")
        
        print("\nSource breakdown:")
        for source, source_stats in stats["sources"].items():
            size_mb = source_stats["total_size_bytes"] / (1024 * 1024)
            print(f"  {source}: {source_stats['document_count']} documents ({size_mb:.2f} MB)")